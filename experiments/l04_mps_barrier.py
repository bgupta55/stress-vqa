#!/usr/bin/env python3
"""
experiments/l04_mps_barrier.py
L04: MPS vs T5 barrier — fidelity vs bond dimension.
"""
import sys
import pathlib
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.utils import save_json
from svqa.circuits.brickwork import random_brickwork
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
from svqa.sim.aer_sv import statevector_simulate
from svqa.sim.aer_mps import mps_fidelity
from svqa.theory.mps_bound import mps_fidelity_bound

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [12, 16, 20]   # keep small for laptop; max 24 with 16GB
CHI_LIST = [2, 4, 8, 16, 32, 64]
DEPTH_LIST = [2, 4, 8, 12, 16, 20]
N_SEEDS = 3


def run_l04():
    t0 = time.time()
    print("=== L04: MPS vs T5 Barrier ===")
    records = []
    violations = []

    for n in N_LIST:
        m = n // 2  # middle cut
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)

        for depth in DEPTH_LIST:
            for chi in CHI_LIST:
                for seed in range(N_SEEDS):
                    rng = np.random.default_rng(seed * 1000 + depth)
                    try:
                        qc = random_brickwork(n, colors, depth, rng)
                        exact_sv = statevector_simulate(qc)
                        f = mps_fidelity(qc, exact_sv, chi)
                        bound = mps_fidelity_bound(chi, m, n)
                        violates = f > bound + 1e-6
                        if violates:
                            violations.append({"n": n, "m": m, "depth": depth, "chi": chi,
                                               "seed": seed, "f": f, "bound": bound})
                        record = dict(n=n, m=m, depth=depth, chi=chi, seed=seed,
                                      fidelity=float(f), bound=float(bound),
                                      violates_H4=violates)
                        records.append(record)
                    except Exception as e:
                        records.append(dict(n=n, m=m, depth=depth, chi=chi, seed=seed,
                                            error=str(e)))

        print(f"  n={n}: completed {len(DEPTH_LIST) * len(CHI_LIST) * N_SEEDS} runs")

    h4_pass = len(violations) == 0
    print(f"\n  H4 (no MPS bound violation): {'PASS' if h4_pass else 'FAIL — ' + str(len(violations)) + ' violations'}")

    # Example T5 bound check: n=24, m=12, chi=64 -> f <= 64/1024 = 0.0625
    ex_bound = mps_fidelity_bound(64, 12, 24)
    print(f"  T5 example: n=24, m=12, chi=64 -> bound = {ex_bound:.6f} (expected ~0.0625)")

    wall_s = time.time() - t0
    result = {
        "experiment": "L04",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "chi_list": CHI_LIST,
        "depth_list": DEPTH_LIST,
        "records": records,
        "h4_pass": h4_pass,
        "n_violations": len(violations),
        "violations": violations,
        "t5_example_bound": ex_bound,
    }
    out = RESULTS_DIR / "l04_mps_barrier.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l04()
