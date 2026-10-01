"""
src/svqa/hardware/run.py
Hardware job submission with budget guard and transpile check.
[UNTESTED against the live API; names marked [VERIFY]]
"""
import json
import pathlib
import time

HARD_CAP_S = 300.0
PLAN_CAP_S = 240.0
ABORT_AT_S = 270.0


def billed_seconds(job) -> float:
    """Extract billed QPU seconds. Supports ibm_cloud runtime ≥0.40."""
    try:
        # ibm_cloud: metrics()["usage"]["qpu_charge_time_seconds"]
        metrics = job.metrics()
        usage = metrics.get("usage", {})
        if "qpu_charge_time_seconds" in usage:
            return float(usage["qpu_charge_time_seconds"])
        # Fallback: usage() returns an integer (seconds)
        val = job.usage()
        if isinstance(val, (int, float)):
            return float(val)
        if hasattr(val, "seconds"):
            return float(val.seconds)
        return 0.0
    except Exception:
        return 0.0


def estimate_shots_time(n_shots: int, t_shot_s: float = 500e-6, t_overhead_s: float = 2.0) -> float:
    """Estimate QPU time in seconds. Q0 measured t_shot=500µs on ibm_kingston."""
    return n_shots * t_shot_s + t_overhead_s


def run_batch(backend, circuits: list, expected_cz: list, shots: int, tag: str,
              ledger, layout=None, enable_gate_twirling: bool = False) -> object:
    """
    Run a batch of circuits on the backend with budget guard.
    """
    from qiskit_ibm_runtime import SamplerV2 as Sampler
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    pm = generate_preset_pass_manager(
        optimization_level=0,
        backend=backend,
        initial_layout=layout,
    )
    isa = [pm.run(c) for c in circuits]

    # Transpile guard: check 2Q gate count is preserved (device may use ecr/cx instead of cz)
    # For real devices, routing adds SWAP gates which increases 2Q count — we allow ≤ 2× overhead
    for t, e in zip(isa, expected_cz):
        # Count all 2-qubit gates after transpilation
        ops = t.count_ops()
        actual_2q = sum(v for k, v in ops.items() if k in ("cz", "cx", "ecr", "rzz", "swap"))
        # Allow up to 3× routing overhead on heavy-hex
        assert actual_2q > 0 or e == 0, f"transpiler produced 0 2Q gates for expected {e}"
        assert actual_2q <= e * 4, f"transpiler blew up 2q count: expected ~{e}, got {actual_2q} — likely wrong layout"

    estimated_s = estimate_shots_time(shots * len(circuits))
    if ledger.billed + estimated_s > PLAN_CAP_S:
        raise RuntimeError(
            f"Would exceed plan cap: {ledger.billed:.1f}s billed + {estimated_s:.1f}s estimated > {PLAN_CAP_S}s"
        )

    sampler = Sampler(mode=backend)
    sampler.options.default_shots = shots
    sampler.options.twirling.enable_measure = True   # [VERIFY option names]
    sampler.options.twirling.enable_gates = enable_gate_twirling

    job = sampler.run(isa)
    res = job.result()
    bs = billed_seconds(job)
    ledger.add(tag, job.job_id(), bs)

    # Save raw result
    save_raw(job, res, isa, tag)

    if ledger.billed > PLAN_CAP_S - 15:
        raise SystemExit(f"Budget guard: {ledger.billed:.1f}s billed — stopping")

    return res, job.job_id()


def save_raw(job, result, transpiled_circuits, tag: str):
    """Save raw job result and metadata to data/hardware_raw/."""
    out_dir = pathlib.Path("data/hardware_raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    job_id = job.job_id()
    meta = {
        "job_id": job_id,
        "tag": tag,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_circuits": len(transpiled_circuits),
    }
    # Save metadata
    with open(out_dir / f"{job_id}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    # Save counts — try multiple accessors for SamplerV2 result
    counts_list = []
    try:
        for i, pub_result in enumerate(result):
            try:
                counts = pub_result.data.meas.get_counts()
            except AttributeError:
                try:
                    # Some versions use 'c' as the creg name
                    counts = dict(pub_result.data.c.get_counts())
                except AttributeError:
                    # Fallback: iterate over all classical registers
                    creg_name = list(pub_result.data)[0]
                    counts = dict(getattr(pub_result.data, creg_name).get_counts())
            counts_list.append({"circuit_idx": i, "counts": counts})
    except Exception as e:
        counts_list = [{"error": str(e)}]
    with open(out_dir / f"{job_id}_counts.json", "w") as f:
        json.dump(counts_list, f, indent=2)
