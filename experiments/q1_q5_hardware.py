#!/usr/bin/env python3
"""
experiments/q1_q5_hardware.py
Q1–Q5: Full IBM hardware experiment suite (C5a circuits).
All Q-series jobs in one script. Budget: ≤ 240 s QPU.

Usage:
  python q1_q5_hardware.py --backend ibm_kingston [--dry-run]

Environment:
  QISKIT_IBM_TOKEN, QISKIT_IBM_INSTANCE
"""
import sys
import os
import pathlib
import argparse
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.circuits.planted import perturbed_mirror
from svqa.circuits.mirror import plain_mirror
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
from svqa.hardware.backend import get_service, calibration_snapshot, save_calibration
from svqa.hardware.run import run_batch, estimate_shots_time, PLAN_CAP_S
from svqa.hardware.ledger import Ledger
from svqa.hardware.parse import peak_fraction_from_counts, analyze_hardware_results
from svqa.theory.stats import t1_test, wilson_ci
from svqa.analysis.fit_eps import fit_eps_eff

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Q-series configuration
Q1_N = 20;   Q1_G = [40, 80, 160, 240]; Q1_SEEDS = 3; Q1_SHOTS = 3000
Q2_N = 20;   Q2_G = [40, 80, 160, 240]; Q2_SEEDS = 3; Q2_SHOTS = 8000
Q3_N = 20;   Q3_THETA = [0.0, 0.2, 0.4]; Q3_G = 120; Q3_SEEDS = 3; Q3_SHOTS = 8000
Q4_N = [12, 20, 28]; Q4_G_FACTOR = 6; Q4_SEEDS = 3; Q4_SHOTS = 8000
Q5_N = 40;   Q5_G = [100, 200]; Q5_SHOTS = 20000


def build_circuits_q1(colors, n_edges):
    """Q1: Mirror baseline for ε_eff estimation."""
    circuits, meta, expected_cz = [], [], []
    for G in Q1_G:
        depth = max(2, G // max(n_edges, 1))
        for seed in range(Q1_SEEDS):
            rng = np.random.default_rng(seed)
            input_bits = [int(b) for b in rng.integers(0, 2, Q1_N)]
            # Balance Hamming weight ≈ n/2
            n_ones = sum(input_bits)
            if n_ones > Q1_N // 2:
                input_bits = [1 - b for b in input_bits]
            C, n_cz = plain_mirror(Q1_N, colors, depth, input_bits, rng)
            C.measure_all()
            circuits.append(C)
            meta.append({"tag": f"Q1_n{Q1_N}_G{G}_s{seed}", "n": Q1_N, "G": G, "depth": depth,
                          "n_cz": n_cz, "s_bits": input_bits, "theta": 0.0,
                          "delta_pred": 1.0, "F_pred": None})
            expected_cz.append(n_cz)
    return circuits, meta, expected_cz


def build_circuits_q2(colors, n_edges):
    """Q2: Peak vs G — T1 test and ε_eff fit."""
    circuits, meta, expected_cz = [], [], []
    for G in Q2_G:
        depth = max(2, G // max(n_edges, 1))
        for seed in range(Q2_SEEDS):
            rng = np.random.default_rng(seed + 200)
            s_bits = [int(b) for b in rng.integers(0, 2, Q2_N)]
            C, n_cz, delta_pred = perturbed_mirror(Q2_N, colors, depth, 0.0, s_bits, rng)
            C.measure_all()
            circuits.append(C)
            meta.append({"tag": f"Q2_n{Q2_N}_G{G}_s{seed}", "n": Q2_N, "G": G, "depth": depth,
                          "n_cz": n_cz, "s_bits": s_bits, "theta": 0.0,
                          "delta_pred": float(delta_pred), "F_pred": None})
            expected_cz.append(n_cz)
    return circuits, meta, expected_cz


def build_circuits_q3(colors, n_edges):
    """Q3: δ sweep — peak vs peakedness at fixed G."""
    circuits, meta, expected_cz = [], [], []
    depth = max(2, Q3_G // max(n_edges, 1))
    for theta in Q3_THETA:
        for seed in range(Q3_SEEDS):
            rng = np.random.default_rng(seed + 300)
            s_bits = [int(b) for b in rng.integers(0, 2, Q3_N)]
            C, n_cz, delta_pred = perturbed_mirror(Q3_N, colors, depth, theta, s_bits, rng)
            C.measure_all()
            circuits.append(C)
            meta.append({"tag": f"Q3_n{Q3_N}_theta{theta:.2f}_s{seed}", "n": Q3_N, "G": Q3_G,
                          "depth": depth, "n_cz": n_cz, "s_bits": s_bits, "theta": theta,
                          "delta_pred": float(delta_pred), "F_pred": None})
            expected_cz.append(n_cz)
    return circuits, meta, expected_cz


def build_circuits_q4_q5(backend_n_qubits: int = 156):
    """Q4 (size sweep) and Q5 (n=40 planted peak)."""
    circuits, meta, expected_cz = [], [], []
    for n in Q4_N:
        if n > backend_n_qubits:
            continue
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        n_edges = sum(len(c) for c in colors)
        G = Q4_G_FACTOR * n
        depth = max(2, G // max(n_edges, 1))
        for seed in range(Q4_SEEDS):
            rng = np.random.default_rng(seed + 400)
            s_bits = [int(b) for b in rng.integers(0, 2, n)]
            C, n_cz, delta_pred = perturbed_mirror(n, colors, depth, 0.0, s_bits, rng)
            C.measure_all()
            circuits.append(C)
            meta.append({"tag": f"Q4_n{n}_G{G}_s{seed}", "n": n, "G": G, "depth": depth,
                          "n_cz": n_cz, "s_bits": s_bits, "theta": 0.0,
                          "delta_pred": float(delta_pred), "F_pred": None})
            expected_cz.append(n_cz)

    # Q5: n=40
    if Q5_N <= backend_n_qubits:
        edges_40 = line_graph_edges(Q5_N)
        colors_40 = edge_color_matchings(edges_40)
        n_edges_40 = sum(len(c) for c in colors_40)
        for G in Q5_G:
            depth = max(2, G // max(n_edges_40, 1))
            rng = np.random.default_rng(999)
            s_bits = [int(b) for b in rng.integers(0, 2, Q5_N)]
            C, n_cz, delta_pred = perturbed_mirror(Q5_N, colors_40, depth, 0.0, s_bits, rng)
            C.measure_all()
            circuits.append(C)
            meta.append({"tag": f"Q5_n{Q5_N}_G{G}", "n": Q5_N, "G": G, "depth": depth,
                          "n_cz": n_cz, "s_bits": s_bits, "theta": 0.0,
                          "delta_pred": float(delta_pred), "F_pred": None})
            expected_cz.append(n_cz)

    return circuits, meta, expected_cz


def analyze_job(job_id: str, meta: list, ledger: Ledger) -> list:
    """Parse and analyze a hardware job result."""
    from svqa.hardware.parse import load_counts, peak_fraction_from_counts
    results = []
    try:
        counts_list = load_counts(job_id)
        for i, (cd, m) in enumerate(zip(counts_list, meta)):
            counts = cd.get("counts", {})
            s_bits = m["s_bits"]
            k, N, p_hat = peak_fraction_from_counts(counts, s_bits)
            lo, hi = wilson_ci(k, N)
            delta_pred = m.get("delta_pred", 1.0)
            # F_pred estimated from ε_eff (placeholder; replaced after Q1 fit)
            F_pred = m.get("F_pred") or 1.0
            p_pred = delta_pred * F_pred
            z, t1_holds = t1_test(p_hat, p_pred, N)
            argmax_bs = max(counts, key=counts.get) if counts else ""
            target_bs = "".join(str(b) for b in reversed(s_bits))
            results.append(dict(
                job_id=job_id, tag=m.get("tag", ""), n=m["n"], G=m.get("G"),
                n_cz=m["n_cz"], theta=m.get("theta", 0.0),
                k=k, N=N, p_hat=float(p_hat), p_pred=float(p_pred),
                delta_pred=float(delta_pred), F_pred=float(F_pred),
                wilson_lo=float(lo), wilson_hi=float(hi),
                t1_z=float(z), t1_holds=bool(t1_holds),
                mode_matches=(argmax_bs == target_bs),
                argmax_bs=argmax_bs, target_bs=target_bs,
            ))
    except Exception as e:
        results.append({"job_id": job_id, "error": str(e)})
    return results


def run_q_series(backend_name: str = "ibm_kingston", dry_run: bool = False):
    t0 = time.time()
    print("=== Q1-Q5: IBM Hardware Experiments ===")

    token = os.environ.get("QISKIT_IBM_TOKEN")
    instance = os.environ.get("QISKIT_IBM_INSTANCE")

    if not token and not dry_run:
        print("ERROR: QISKIT_IBM_TOKEN not set. Use --dry-run for simulation.")
        return None

    ledger = Ledger()
    all_results = {"experiment": "Q1_Q5", "jobs": [], "analysis": []}

    if not dry_run:
        svc = get_service(token, instance)
        backend = svc.backend(backend_name)
        print(f"  Backend: {backend.name}, {backend.num_qubits} qubits")
        snap = calibration_snapshot(backend)
        save_calibration(snap, "data/hardware_raw/q_series_calibration.json")
        n_qubits = backend.num_qubits
    else:
        print("  DRY RUN MODE — using AerSimulator")
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
        n_qubits = 100

    # Build Q1 circuits (n=20, line graph)
    edges_20 = line_graph_edges(Q1_N)
    colors_20 = edge_color_matchings(edges_20)
    n_edges_20 = sum(len(c) for c in colors_20)

    job_configs = [
        ("Q1_mirror_baseline", *build_circuits_q1(colors_20, n_edges_20), Q1_SHOTS),
        ("Q2_peak_vs_G", *build_circuits_q2(colors_20, n_edges_20), Q2_SHOTS),
        ("Q3_delta_sweep", *build_circuits_q3(colors_20, n_edges_20), Q3_SHOTS),
    ]
    q4q5_circs, q4q5_meta, q4q5_cz = build_circuits_q4_q5(n_qubits)
    job_configs.append(("Q4_Q5_size_sweep", q4q5_circs, q4q5_meta, q4q5_cz, Q4_SHOTS))

    for tag, circuits, meta, expected_cz, shots in job_configs:
        if ledger.billed >= PLAN_CAP_S - 30:
            print(f"  Budget guard: {ledger.billed:.1f}s billed, skipping {tag}")
            break
        print(f"\n  Submitting {tag}: {len(circuits)} circuits × {shots} shots")
        try:
            if dry_run:
                # Simulate with Aer
                from qiskit_aer import AerSimulator
                sim = AerSimulator()
                from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
                pm = generate_preset_pass_manager(optimization_level=0, backend=sim)
                isa = [pm.run(c) for c in circuits]
                job = sim.run(isa, shots=shots)
                raw_result = job.result()
                import uuid
                fake_job_id = f"dry_run_{tag}_{uuid.uuid4().hex[:8]}"
                # Convert to expected counts format
                counts_list = []
                for i in range(len(circuits)):
                    try:
                        counts = raw_result.get_counts(i)
                    except Exception:
                        counts = {}
                    counts_list.append({"circuit_idx": i, "counts": counts})
                # Save counts
                import json as _json
                out_dir = pathlib.Path("data/hardware_raw")
                out_dir.mkdir(parents=True, exist_ok=True)
                with open(out_dir / f"{fake_job_id}_counts.json", "w") as f:
                    _json.dump(counts_list, f, indent=2)
                with open(out_dir / f"{fake_job_id}_meta.json", "w") as f:
                    _json.dump({"job_id": fake_job_id, "tag": tag,
                                "n_circuits": len(circuits), "dry_run": True}, f, indent=2)
                job_id = fake_job_id
                ledger.add(tag, job_id, 0.0)  # no billed seconds in dry run
                print(f"    [DRY RUN] Simulated job_id: {job_id}")
            else:
                _, job_id = run_batch(backend, circuits, expected_cz, shots, tag, ledger)
                print(f"    Job ID: {job_id}, billed: {ledger.billed:.1f}s")

            job_result = analyze_job(job_id, meta, ledger)
            all_results["jobs"].append({"tag": tag, "job_id": job_id, "meta": meta})
            all_results["analysis"].extend(job_result)

        except Exception as e:
            print(f"    ERROR in {tag}: {e}")
            all_results["jobs"].append({"tag": tag, "error": str(e)})

    # ε_eff fit from Q2
    q2_analysis = [r for r in all_results["analysis"] if "Q2" in r.get("tag", "")]
    if q2_analysis:
        n_cz_list = [r["n_cz"] for r in q2_analysis if "error" not in r]
        p_hat_list = [r["p_hat"] for r in q2_analysis if "error" not in r]
        if len(n_cz_list) >= 3:
            eps_fit = fit_eps_eff(n_cz_list, p_hat_list)
            all_results["eps_eff_fit"] = eps_fit
            print(f"\n  ε_eff fit from Q2: {eps_fit['eps_eff']:.4f} ± {eps_fit.get('stderr', 'N/A')}")

    # T1 pass rate
    t1_results = [r for r in all_results["analysis"] if "t1_holds" in r]
    if t1_results:
        t1_rate = np.mean([r["t1_holds"] for r in t1_results])
        all_results["t1_pass_rate"] = float(t1_rate)
        print(f"  T1 inequality satisfied: {t1_rate*100:.1f}% of hardware circuits")

    # Q5 headline
    q5_results = [r for r in all_results["analysis"] if "Q5" in r.get("tag", "")]
    if q5_results:
        for r in q5_results:
            print(f"\n  Q5 HEADLINE: n=40, G={r.get('G')}, p_hat={r['p_hat']:.4f}, "
                  f"mode_match={r['mode_match']}, job_id={r['job_id']}")

    wall_s = time.time() - t0
    all_results["wall_seconds"] = round(wall_s, 2)
    all_results["total_billed_s"] = ledger.billed
    all_results["ledger"] = ledger.summary()

    out = RESULTS_DIR / "q1_q5_hardware.json"
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved to {out}")
    print(f"Wall time: {wall_s:.1f}s, QPU billed: {ledger.billed:.1f}s")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="ibm_kingston")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()
    run_q_series(args.backend, dry_run=args.dry_run)
