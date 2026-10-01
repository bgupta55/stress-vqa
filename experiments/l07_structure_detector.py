#!/usr/bin/env python3
"""
experiments/l07_structure_detector.py
L07: Mirror/palindrome structure detector (Hypothesis H5).
C5a vs random brickwork classification.
"""
import sys
import pathlib
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.utils import save_json
from svqa.circuits.planted import perturbed_mirror
from svqa.circuits.brickwork import random_brickwork
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
from svqa.attacks.structure_detect import mirror_score, detect_mirror, classify_circuits

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [8, 12, 16, 20, 24, 28]
N_INSTANCES_PER_CLASS = 50
DEPTH = 8
THETA = 0.2


def run_l07():
    t0 = time.time()
    print("=== L07: Structure Detector ===")

    all_records = []
    c5a_circuits = []
    rand_circuits = []

    for n in N_LIST:
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        n_c5a = []
        n_rand = []

        for seed in range(N_INSTANCES_PER_CLASS):
            rng = np.random.default_rng(seed)
            s_bits = [int(b) for b in rng.integers(0, 2, n)]

            # C5a
            rng_c = np.random.default_rng(seed + 500)
            C5a, _, _ = perturbed_mirror(n, colors, DEPTH, THETA, s_bits, rng_c)
            score_c5a = mirror_score(C5a)
            n_c5a.append(C5a)
            c5a_circuits.append(C5a)
            all_records.append({"n": n, "seed": seed, "family": "C5a", "mirror_score": score_c5a,
                                 "detected": score_c5a >= 0.8})

            # Random brickwork
            rng_r = np.random.default_rng(seed + 5000)
            qc_rand = random_brickwork(n, colors, DEPTH, rng_r)
            score_rand = mirror_score(qc_rand)
            n_rand.append(qc_rand)
            rand_circuits.append(qc_rand)
            all_records.append({"n": n, "seed": seed, "family": "random", "mirror_score": score_rand,
                                 "detected": score_rand >= 0.8})

        # Per-n metrics
        tp = sum(1 for r in all_records if r["n"] == n and r["family"] == "C5a" and r["detected"])
        fp = sum(1 for r in all_records if r["n"] == n and r["family"] == "random" and r["detected"])
        c5a_rate = tp / N_INSTANCES_PER_CLASS
        fpr = fp / N_INSTANCES_PER_CLASS
        h5_pass = c5a_rate >= 0.95
        print(f"  n={n:2d}: C5a detection={c5a_rate:.2f}, FPR={fpr:.2f} "
              f"[H5 {'PASS' if h5_pass else 'FAIL'}]")

    # Overall classification metrics
    overall = classify_circuits(c5a_circuits, rand_circuits)
    print(f"\n  Overall: AUC proxy: C5a rate={overall['c5a_detection_rate']:.3f}, FPR={overall['false_positive_rate']:.3f}")

    wall_s = time.time() - t0
    result = {
        "experiment": "L07",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "depth": DEPTH,
        "theta": THETA,
        "n_instances_per_class": N_INSTANCES_PER_CLASS,
        "overall_classification": overall,
        "records": all_records,
    }
    out = RESULTS_DIR / "l07_structure_detector.json"
    save_json(result, out)
    print(f"\nSaved {len(all_records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l07()
