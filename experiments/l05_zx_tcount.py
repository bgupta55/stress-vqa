#!/usr/bin/env python3
"""
experiments/l05_zx_tcount.py
L05: ZX/T-count reduction feature for C5a vs random brickwork.
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
from svqa.attacks.zx_tcount import circuit_tcount_features

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [8, 12, 16, 20]
N_SEEDS = 5
DEPTH = 8
THETA = 0.2


def run_l05():
    t0 = time.time()
    print("=== L05: ZX/T-count Reduction ===")
    records = []

    for n in N_LIST:
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)

        for seed in range(N_SEEDS):
            rng = np.random.default_rng(seed)
            s_bits = [int(b) for b in rng.integers(0, 2, n)]

            # C5a (perturbed mirror)
            rng2 = np.random.default_rng(seed)
            C5a, n_cz, _ = perturbed_mirror(n, colors, DEPTH, THETA, s_bits, rng2)
            feats_c5a = circuit_tcount_features(C5a)
            feats_c5a.update({"n": n, "seed": seed, "family": "C5a", "n_cz": n_cz})
            records.append(feats_c5a)

            # Random brickwork
            rng3 = np.random.default_rng(seed + 1000)
            qc_rand = random_brickwork(n, colors, DEPTH, rng3)
            feats_rand = circuit_tcount_features(qc_rand)
            feats_rand.update({"n": n, "seed": seed, "family": "random_brickwork",
                                "n_cz": qc_rand.count_ops().get("cz", 0)})
            records.append(feats_rand)

    # Summarize
    c5a_recs = [r for r in records if r["family"] == "C5a" and r.get("t_before") is not None]
    rand_recs = [r for r in records if r["family"] == "random_brickwork" and r.get("t_before") is not None]
    if c5a_recs:
        mean_c5a_red = np.mean([r["reduction_fraction"] for r in c5a_recs])
        print(f"  C5a mean T-count reduction fraction: {mean_c5a_red:.3f}")
    if rand_recs:
        mean_rand_red = np.mean([r["reduction_fraction"] for r in rand_recs])
        print(f"  Random mean T-count reduction fraction: {mean_rand_red:.3f}")

    wall_s = time.time() - t0
    result = {
        "experiment": "L05",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "depth": DEPTH,
        "theta": THETA,
        "records": records,
    }
    out = RESULTS_DIR / "l05_zx_tcount.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l05()
