#!/usr/bin/env python3
"""
experiments/l10_noisy_preflight.py
L10: Noisy simulation pre-flight for hardware.
Verify T1 inequality in simulation and choose Q-series circuit sizes.
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
from svqa.sim.noisy import noisy_peak_fraction
from svqa.sim.aer_sv import peak_probability
from svqa.theory.stats import t1_test, wilson_ci

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [12]
G_LIST = [40, 80]
EPS_LIST = [0.003, 0.006]
THETA = 0.1
N_SHOTS = 1000
N_SEEDS = 2


def run_l10():
    t0 = time.time()
    print("=== L10: Noisy Simulation Pre-flight ===")
    records = []

    for n in N_LIST:
        depth_for_G = {}
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        n_edges = sum(len(c) for c in colors)
        # Map G -> depth: each depth step adds n_edges CZ gates
        for G in G_LIST:
            d = max(2, G // max(n_edges, 1))
            depth_for_G[G] = d

        for G in G_LIST:
            depth = depth_for_G[G]
            for eps in EPS_LIST:
                for seed in range(N_SEEDS):
                    rng = np.random.default_rng(seed)
                    s_bits = [int(b) for b in rng.integers(0, 2, n)]
                    try:
                        C, n_cz, delta_pred = perturbed_mirror(n, colors, depth, THETA, s_bits, rng)
                        # Ideal peak probability
                        p_ideal = peak_probability(C, s_bits)
                        # Noisy
                        p_noisy = noisy_peak_fraction(C, s_bits, eps, eps * 0.5, N_SHOTS, seed)
                        # T1 test: p_noisy >= delta * F_pred
                        # Estimate F_pred from noise model: exp(-eps * n_cz)
                        F_pred = float(np.exp(-eps * n_cz))
                        p_pred = delta_pred * F_pred
                        z, t1_holds = t1_test(p_noisy, p_pred, N_SHOTS)
                        lo, hi = wilson_ci(int(p_noisy * N_SHOTS), N_SHOTS)
                        records.append(dict(
                            n=n, depth=depth, G=G, n_cz=n_cz, eps=eps, seed=seed,
                            delta_pred=float(delta_pred), F_pred=float(F_pred),
                            p_pred=float(p_pred), p_ideal=float(p_ideal),
                            p_noisy=float(p_noisy), t1_holds=t1_holds,
                            t1_z=float(z), wilson_lo=float(lo), wilson_hi=float(hi),
                        ))
                    except Exception as e:
                        records.append({"n": n, "G": G, "eps": eps, "seed": seed, "error": str(e)})

        print(f"  n={n}: {len([r for r in records if r.get('n') == n])} runs completed")

    t1_pass_rate = np.mean([r.get("t1_holds", False) for r in records
                             if "error" not in r and "t1_holds" in r])
    print(f"\n  T1 inequality satisfied in {t1_pass_rate*100:.1f}% of runs")

    wall_s = time.time() - t0
    result = {
        "experiment": "L10",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "G_list": G_LIST,
        "eps_list": EPS_LIST,
        "theta": THETA,
        "n_shots": N_SHOTS,
        "t1_pass_rate": float(t1_pass_rate),
        "records": records,
    }
    out = RESULTS_DIR / "l10_noisy_preflight.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l10()
