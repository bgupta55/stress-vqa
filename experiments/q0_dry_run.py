#!/usr/bin/env python3
"""
experiments/q0_dry_run.py
Q0 dry-run: transpile + assertions only, uses 0 QPU seconds.
Run with --no-qpu (default) to just validate circuits without submitting.
"""
import sys
import pathlib
import argparse
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.utils import save_json
from svqa.circuits.planted import perturbed_mirror
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
from svqa.hardware.ledger import Ledger

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Q0 spec: 6 circuits, C5a (θ=0) at n=12, G ∈ {40, 120}, 2000 shots each
N_Q0 = 12
G_Q0 = [40, 120]
SHOTS_Q0 = 2000
THETA_Q0 = 0.0


def build_q0_circuits():
    """Build Q0 probe circuits."""
    edges = line_graph_edges(N_Q0)
    colors = edge_color_matchings(edges)
    n_edges = sum(len(c) for c in colors)
    circuits = []
    meta = []
    for G in G_Q0:
        depth = max(2, G // max(n_edges, 1))
        for seed in range(3):
            rng = np.random.default_rng(seed)
            s_bits = [int(b) for b in rng.integers(0, 2, N_Q0)]
            C, n_cz, delta_pred = perturbed_mirror(N_Q0, colors, depth, THETA_Q0, s_bits, rng)
            circuits.append(C)
            meta.append({"seed": seed, "G": G, "depth": depth, "n_cz": n_cz,
                          "delta_pred": delta_pred, "s_bits": s_bits})
    return circuits, meta


def run_q0_dry(no_qpu: bool = True):
    t0 = time.time()
    print("=== Q0 Dry Run ===")
    circuits, meta = build_q0_circuits()
    print(f"  Built {len(circuits)} circuits for Q0 probe")

    results = {"circuits_built": len(circuits), "meta": meta}

    if not no_qpu:
        print("  --no-qpu not set: would submit to QPU (skipping in dry run)")

    # Validate with Aer
    try:
        from qiskit_aer import AerSimulator
        backend_sim = AerSimulator()
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        pm = generate_preset_pass_manager(optimization_level=0, backend=backend_sim)
        for i, (qc, m) in enumerate(zip(circuits, meta)):
            transpiled = pm.run(qc)
            actual_cz = transpiled.count_ops().get("cz", 0)
            guard_pass = actual_cz == m["n_cz"]
            results.setdefault("transpile_guard", []).append({
                "circuit": i, "expected_cz": m["n_cz"],
                "actual_cz": actual_cz, "pass": guard_pass,
            })
            status = "PASS" if guard_pass else "FAIL"
            print(f"  [{status}] Circuit {i}: expected_cz={m['n_cz']}, actual_cz={actual_cz}")
    except Exception as e:
        print(f"  AerSimulator not available for dry run validation: {e}")
        results["aer_error"] = str(e)

    wall_s = time.time() - t0
    results["wall_seconds"] = round(wall_s, 2)
    results["experiment"] = "Q0_dry_run"

    out = RESULTS_DIR / "q0_dry_run.json"
    save_json(results, out)
    print(f"\nSaved to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-qpu", action="store_true", default=True)
    args = parser.parse_args()
    run_q0_dry(no_qpu=args.no_qpu)
