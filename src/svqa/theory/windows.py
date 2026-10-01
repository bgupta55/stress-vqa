"""
src/svqa/theory/windows.py
Quantum-classical window forecast (T9, M12).
"""
import numpy as np
from .shots import G_max, L


def frontier_seconds(complex_ops: float, eta: float = 0.2, peak_pflops: float = 1.685e18) -> float:
    """Convert complex ops to Frontier-equivalent seconds (r2 paper conventions)."""
    machine_flops = 8 * complex_ops
    return machine_flops / (eta * peak_pflops)


def window_forecast(
    n_list,
    eps_eff: float,
    shots: int,
    eta: float = 0.01,
    a_sq: float = 0.23,
    a_hex: float = 0.15,
    geometry: str = "square",
):
    """
    For each n in n_list, compute:
      - G_max_q: maximum gates before quantum peak vanishes (T9)
      - G_max_c: classical contraction knee depth * sqrt(n) / a
      - window_open: True if G_max_q > G_max_c

    Returns list of dicts.
    """
    a = a_sq if geometry == "square" else a_hex
    results = []
    for n in n_list:
        delta = 1.0  # perturbed mirror at theta=0
        gq = G_max(eps_eff, delta, shots, n, eta)
        d_star = np.sqrt(n) / a
        gc = d_star * (n * a)  # approximate classical cost knee at w = n
        results.append(dict(n=n, G_max_quantum=gq, G_max_classical=gc, window_open=gq > gc))
    return results
