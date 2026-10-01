#!/usr/bin/env python3
"""
experiments/l03_contraction_cost.py
L03: Contraction-cost scaling and M12 fit.
Build amplitude TNs, search paths with cotengra, record log2 C and width vs depth.
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
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges, square_lattice_edges
from svqa.sim.cotengra_cost import cost_record, HAS_COTENGRA
from svqa.analysis.fit_width import fit_width_model

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# n_list for square lattice (perfect squares)
N_SQUARE = [9, 16, 25]   # reduced from [16,25,36,49] for laptop speed
DEPTH_RANGE = range(2, 12, 2)
BUDGET_S = 30  # cotengra search budget per circuit (B0)
N_SEEDS = 2


def run_l03():
    t0 = time.time()
    print("=== L03: Contraction Cost Scaling ===")

    if not HAS_COTENGRA:
        print("  WARNING: cotengra/quimb not installed — recording circuit metadata only")

    records = []
    n_list_used = []
    depth_list_used = []
    width_list_used = []

    for n in N_SQUARE:
        rows = int(np.sqrt(n))
        cols = n // rows
        edges = square_lattice_edges(rows, cols)
        colors = edge_color_matchings(edges)

        for depth in DEPTH_RANGE:
            for seed in range(N_SEEDS):
                rng = np.random.default_rng(seed + depth * 100)
                try:
                    qc = random_brickwork(n, colors, depth, rng)
                    rec = {"n": n, "depth": depth, "seed": seed, "geometry": "square"}
                    if HAS_COTENGRA:
                        cost = cost_record(qc, budget_s=BUDGET_S, seed=seed)
                        rec.update(cost)
                        n_list_used.append(n)
                        depth_list_used.append(depth)
                        width_list_used.append(cost["log2_width"])
                    else:
                        # Count 2q gates as proxy
                        n_cz = qc.count_ops().get("cz", 0)
                        rec["n_cz"] = n_cz
                        rec["log10_cost"] = None
                        rec["log2_width"] = None
                    records.append(rec)
                    if HAS_COTENGRA:
                        print(f"  n={n}, d={depth}, seed={seed}: "
                              f"log10_cost={rec['log10_cost']:.2f}, width={rec['log2_width']}")
                    else:
                        print(f"  n={n}, d={depth}, seed={seed}: n_cz={rec.get('n_cz')}")
                except Exception as e:
                    print(f"  ERROR n={n}, d={depth}, seed={seed}: {e}")
                    records.append({"n": n, "depth": depth, "seed": seed, "error": str(e)})

    # Fit M12 if we have width data
    fit_result = None
    if width_list_used:
        fit_result = fit_width_model(n_list_used, depth_list_used, width_list_used)
        print(f"\n  M12 fit: a = {fit_result['a']:.4f} ± {fit_result.get('stderr', 'N/A')}, "
              f"R2 = {fit_result.get('R2', 'N/A'):.4f}")
        h3_pass = fit_result["a"] is not None and 0.18 <= fit_result["a"] <= 0.28
        print(f"  H3 (a ≈ 0.23 ± 0.05): {'PASS' if h3_pass else 'FAIL/INCONCLUSIVE'}")

    wall_s = time.time() - t0
    result = {
        "experiment": "L03",
        "wall_seconds": round(wall_s, 2),
        "has_cotengra": HAS_COTENGRA,
        "n_square": N_SQUARE,
        "depth_range": list(DEPTH_RANGE),
        "budget_s_per_circuit": BUDGET_S,
        "records": records,
        "m12_fit": fit_result,
    }
    out = RESULTS_DIR / "l03_contraction_cost.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l03()
