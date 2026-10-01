#!/usr/bin/env python3
"""
experiments/l02_xeb_resolution.py
L02: XEB resolution test (Theorem T3).
Simulate Porter-Thomas samples, verify E and Var of XEB estimator,
show N needed for F = 2.3e-3.
"""
import sys
import pathlib
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.utils import save_json
from svqa.theory.xeb import xeb_var, xeb_N_for_sigma

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

F_LIST = [1e-3, 2.3e-3, 1e-2]
N_SAMPLES_LIST = [1000, 10000, 100000, 1000000]
N_MONTE_CARLO = 2000
Z_SIGMA = 5


def simulate_xeb_estimator(F: float, N: int, n_q: int = 20, n_trials: int = 500,
                            seed: int = 42) -> dict:
    """
    Simulate XEB estimator using Porter-Thomas distributed ideal probabilities.
    """
    rng = np.random.default_rng(seed)
    D = 2 ** n_q
    xeb_values = []
    for _ in range(n_trials):
        # Sample ideal probabilities from Porter-Thomas (exponential distribution)
        ideal_probs = rng.exponential(1.0 / D, size=D)
        ideal_probs /= ideal_probs.sum()
        # Simulate measurements: mixture of ideal and uniform
        # p_meas = F * p_ideal + (1-F) * 1/D
        p_meas = F * ideal_probs + (1 - F) / D
        # Draw N samples
        samples = rng.choice(D, size=N, p=p_meas)
        counts = np.bincount(samples, minlength=D)
        # XEB: sum_x (freq_x * (D * p_ideal_x - 1))
        freq = counts / N
        xeb = float(np.sum(freq * (D * ideal_probs - 1)))
        xeb_values.append(xeb)
    xeb_arr = np.array(xeb_values)
    return {
        "F": F,
        "N": N,
        "mean_xeb": float(xeb_arr.mean()),
        "var_xeb": float(xeb_arr.var()),
        "theory_var": float(xeb_var(F, N)),
        "var_match_ok": abs(xeb_arr.var() - xeb_var(F, N)) / xeb_var(F, N) < 0.15,
        "sigma_ratio": float(xeb_arr.mean() / (np.sqrt(xeb_var(F, N)) + 1e-12)),
    }


def run_l02():
    t0 = time.time()
    print("=== L02: XEB Resolution ===")
    records = []

    # T3: N needed for 5-sigma detection at various F
    print("\n--- T3: Samples needed for 5σ detection ---")
    for F in F_LIST:
        N_needed = xeb_N_for_sigma(F, Z_SIGMA)
        print(f"  F={F:.1e}: N_5sigma = {N_needed:.3e}")
        records.append({"type": "N_for_sigma", "F": F, "z": Z_SIGMA, "N_needed": N_needed})

    # Verify theory: F=2.3e-3, z=5 -> ~4.7e6
    N_theory = xeb_N_for_sigma(2.3e-3, 5)
    theory_check = {"computed": N_theory, "expected": 4.7e6,
                    "pass": abs(N_theory - 4.7e6) / 4.7e6 < 0.05}
    print(f"\n  T3 check: {N_theory:.3e} (expected ~4.7e6) — {'PASS' if theory_check['pass'] else 'FAIL'}")

    # Monte-Carlo validation at small N
    print("\n--- Monte-Carlo XEB variance validation (n_q=12 for speed) ---")
    mc_records = []
    for F in [1e-2, 2.3e-3]:
        for N in [1000, 10000]:
            sim = simulate_xeb_estimator(F, N, n_q=12, n_trials=300)
            status = "PASS" if sim["var_match_ok"] else "FAIL"
            print(f"  [{status}] F={F:.1e}, N={N}: mean={sim['mean_xeb']:.4f}, "
                  f"var_sim={sim['var_xeb']:.3e}, var_theory={sim['theory_var']:.3e}")
            mc_records.append(sim)

    wall_s = time.time() - t0
    result = {
        "experiment": "L02",
        "wall_seconds": round(wall_s, 2),
        "N_for_sigma": records,
        "theory_check_T3": theory_check,
        "monte_carlo": mc_records,
    }
    out = RESULTS_DIR / "l02_xeb_resolution.json"
    save_json(result, out)
    print(f"\nSaved to {out}")
    print(f"Wall time: {wall_s:.1f}s")
    return result


if __name__ == "__main__":
    run_l02()
