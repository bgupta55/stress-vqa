#!/usr/bin/env python3
"""
experiments/l09_severing.py
L09: Severing/score spoofing at small n.
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
from svqa.sim.aer_sv import get_probabilities
from svqa.attacks.severing import severed_distribution, severing_score, fit_spoofing_rate

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [12, 16]
DEPTH_LIST = [2, 4, 6, 8, 10, 12]
N_SEEDS = 10
THETA = 0.0


def run_l09():
    t0 = time.time()
    print("=== L09: Severing / Score Spoofing ===")
    records = []
    scores_by_depth = {}

    for n in N_LIST:
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        # Cut first half of qubits
        cut_qubits = list(range(n // 2))

        scores_by_depth[n] = {}
        for depth in DEPTH_LIST:
            depth_scores = []
            for seed in range(N_SEEDS):
                rng = np.random.default_rng(seed)
                s_bits = [int(b) for b in rng.integers(0, 2, n)]
                try:
                    C, n_cz, _ = perturbed_mirror(n, colors, depth, THETA, s_bits, rng)
                    target_probs = get_probabilities(C)
                    severed = severed_distribution(target_probs, n, cut_qubits)
                    score = severing_score(target_probs, severed)
                    depth_scores.append(float(score))
                    records.append({"n": n, "depth": depth, "seed": seed,
                                    "cut_size": len(cut_qubits), "spoofing_score": float(score)})
                except Exception as e:
                    records.append({"n": n, "depth": depth, "seed": seed, "error": str(e)})
            scores_by_depth[n][depth] = depth_scores
            if depth_scores:
                print(f"  n={n:2d}, d={depth}: mean_score={np.mean(depth_scores):.4f}")

        # Fit decay rate
        fit = fit_spoofing_rate(scores_by_depth[n])
        print(f"  n={n:2d} fit: c={fit.get('c', 'N/A')}, K={fit.get('K', 'N/A')}, R2={fit.get('R2', 'N/A')}")

    wall_s = time.time() - t0
    result = {
        "experiment": "L09",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "depth_list": DEPTH_LIST,
        "records": records,
    }
    out = RESULTS_DIR / "l09_severing.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l09()
