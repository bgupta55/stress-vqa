#!/usr/bin/env python3
"""
experiments/l08_beam_search.py
L08: Beam-search peak finder with approximate conditional marginals.
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
from svqa.attacks.marginal_peakfinder import exact_z_marginals, recover_peak_from_marginals

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_LIST = [12, 16, 20]
DELTA_LIST = [0.95, 0.8, 0.6, 0.4]
BEAM_SIZES = [8, 64]
N_SEEDS = 5
DEPTH = 8


def beam_search_peak(sv: np.ndarray, n: int, beam: int) -> list:
    """
    Beam-search peak finder using exact marginals.
    Returns best candidate bitstring.
    """
    from svqa.attacks.marginal_peakfinder import exact_z_marginals
    # Greedy bit-by-bit: pick bits maximizing <Z_k> signal
    z_margs = exact_z_marginals(sv, n)
    # Simple: sort qubits by |<Z_k>| confidence, assign bits greedily
    best_candidates = [[]]
    for k in range(n):
        new_candidates = []
        for cand in best_candidates:
            b0 = list(cand) + [0]
            b1 = list(cand) + [1]
            new_candidates.extend([b0, b1])
        # Score each candidate by sum of |z_k| * (1 if z_k sign matches bit, else -1)
        def score(cand):
            return sum(abs(z_margs[k]) * (1 if (z_margs[k] < 0) == bool(cand[k]) else -1)
                       for k in range(len(cand)))
        new_candidates.sort(key=score, reverse=True)
        best_candidates = new_candidates[:beam]
    return best_candidates[0] if best_candidates else [0] * n


def run_l08():
    t0 = time.time()
    print("=== L08: Beam Search Peak Finder ===")
    records = []

    for n in N_LIST:
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)

        for theta in DELTA_LIST:
            # Map theta values to delta approximately
            delta_pred = np.cos(theta * np.pi / 4) ** (2 * n) if theta < 1 else theta

            for beam in BEAM_SIZES:
                successes = []
                bits_correct_list = []

                for seed in range(N_SEEDS):
                    rng = np.random.default_rng(seed)
                    s_bits = [int(b) for b in rng.integers(0, 2, n)]
                    try:
                        C, n_cz, d_pred = perturbed_mirror(n, colors, DEPTH, theta, s_bits, rng)
                        sv = statevector_simulate(C)
                        s_found = beam_search_peak(sv, n, beam)
                        n_correct = sum(a == b for a, b in zip(s_bits, s_found))
                        success = (s_found == s_bits)
                        successes.append(int(success))
                        bits_correct_list.append(n_correct)
                        records.append({"n": n, "theta": theta, "delta_pred": float(d_pred),
                                        "beam": beam, "seed": seed, "success": success,
                                        "bits_correct": n_correct})
                    except Exception as e:
                        records.append({"n": n, "theta": theta, "beam": beam, "seed": seed,
                                        "error": str(e)})
                if successes:
                    print(f"  n={n:2d}, θ={theta:.2f}, beam={beam}: "
                          f"success={np.mean(successes):.2f}, bits_correct={np.mean(bits_correct_list):.1f}/{n}")

    wall_s = time.time() - t0
    result = {
        "experiment": "L08",
        "wall_seconds": round(wall_s, 2),
        "n_list": N_LIST,
        "beam_sizes": BEAM_SIZES,
        "records": records,
    }
    out = RESULTS_DIR / "l08_beam_search.json"
    save_json(result, out)
    print(f"\nSaved {len(records)} records to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l08()
