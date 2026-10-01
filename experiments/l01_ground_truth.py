#!/usr/bin/env python3
"""
experiments/l01_ground_truth.py
L01: Exact ground truth for C5a — statevector δ vs P8 prediction; argmax = s
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
from svqa.sim.aer_sv import peak_probability, argmax_bitstring

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [8, 12, 16, 20, 24]
THETA_LIST = [0.0, 0.1, 0.2, 0.3]
N_SEEDS = 10
DEPTH_FACTOR = 1.5  # depth = int(DEPTH_FACTOR * sqrt(n))


def run_l01():
    t0 = time.time()
    print("=== L01: Exact Ground Truth for C5a ===")
    records = []

    for n in N_LIST:
        depth = max(4, int(DEPTH_FACTOR * np.sqrt(n)))
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)

        for theta in THETA_LIST:
            delta_pred_theory = np.cos(theta / 2) ** (2 * n)
            measured_deltas = []

            for seed in range(N_SEEDS):
                rng = np.random.default_rng(seed)
                s_bits = [int(b) for b in rng.integers(0, 2, n)]
                try:
                    C, n_cz, delta_pred = perturbed_mirror(n, colors, depth, theta, s_bits, rng)
                    p_peak = peak_probability(C, s_bits)
                    am = argmax_bitstring(C, n)
                    argmax_ok = (am == s_bits)
                    measured_deltas.append(float(p_peak))
                    record = dict(
                        n=n, depth=depth, theta=theta, seed=seed, n_cz=n_cz,
                        delta_pred=float(delta_pred),
                        delta_measured=float(p_peak),
                        argmax_ok=argmax_ok,
                        error=None,
                    )
                except Exception as e:
                    record = dict(
                        n=n, depth=depth, theta=theta, seed=seed, n_cz=0,
                        delta_pred=float(delta_pred_theory),
                        delta_measured=None, argmax_ok=None,
                        error=str(e),
                    )
                records.append(record)

            if measured_deltas:
                mean_d = np.mean(measured_deltas)
                std_d = np.std(measured_deltas)
                se_d = std_d / np.sqrt(len(measured_deltas))
                within_3se = abs(mean_d - delta_pred_theory) < 3 * se_d + 0.01
                print(f"  n={n:2d} θ={theta:.1f}: pred={delta_pred_theory:.4f}, "
                      f"meas={mean_d:.4f}±{se_d:.4f}, within_3SE={within_3se}")

    wall_s = time.time() - t0
    result = {
        "experiment": "L01",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "theta_list": THETA_LIST,
        "n_seeds": N_SEEDS,
        "records": records,
    }
    out = RESULTS_DIR / "l01_ground_truth.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l01()
