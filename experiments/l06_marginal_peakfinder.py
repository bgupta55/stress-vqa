#!/usr/bin/env python3
"""
experiments/l06_marginal_peakfinder.py
L06: Local-marginal peak finder (Theorem T6).
Recover s from sign(<Z_k>) for delta > 1/2.
"""
import sys
import pathlib
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.utils import save_json
from svqa.circuits.planted import perturbed_mirror
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
from svqa.sim.aer_sv import statevector_simulate
from svqa.attacks.marginal_peakfinder import exact_z_marginals, marginal_success

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [8, 12, 16]
THETA_LIST = [0.05, 0.2, 0.4, 0.7]   # delta ~ 1.00, 0.82, 0.45, 0.10
N_SEEDS = 5
DEPTH = 8


def run_l06():
    t0 = time.time()
    print("=== L06: Local-Marginal Peak Finder ===")
    records = []

    for n in N_LIST:
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)

        for theta in THETA_LIST:
            delta_pred = np.cos(theta / 2) ** (2 * n)
            successes = []

            for seed in range(N_SEEDS):
                rng = np.random.default_rng(seed)
                s_bits = [int(b) for b in rng.integers(0, 2, n)]
                try:
                    C, n_cz, _ = perturbed_mirror(n, colors, DEPTH, theta, s_bits, rng)
                    sv = statevector_simulate(C)
                    z_margs = exact_z_marginals(sv, n)
                    result = marginal_success(s_bits, z_margs)
                    result.update({"n": n, "theta": theta, "seed": seed,
                                   "delta_pred": float(delta_pred), "n_cz": n_cz})
                    records.append(result)
                    successes.append(int(result["success"]))
                except Exception as e:
                    records.append({"n": n, "theta": theta, "seed": seed,
                                    "delta_pred": float(delta_pred), "error": str(e)})

            if successes:
                rate = np.mean(successes)
                h6_ok = (delta_pred > 0.5 and rate > 0.5) or (delta_pred <= 0.5)
                print(f"  n={n:2d}, θ={theta:.2f}, δ_pred={delta_pred:.3f}: "
                      f"success_rate={rate:.2f} {'[H6-PASS]' if h6_ok else '[H6-FAIL]'}")

    # Summary by delta
    wall_s = time.time() - t0
    result = {
        "experiment": "L06",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "theta_list": THETA_LIST,
        "n_seeds": N_SEEDS,
        "records": records,
    }
    out = RESULTS_DIR / "l06_marginal_peakfinder.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l06()
