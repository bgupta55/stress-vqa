"""
src/svqa/theory/shots.py
Shot count bounds from Theorems T2, T9 of THEORY_AND_PROOFS.md
"""
import numpy as np


def L(n: int, eta: float) -> float:
    """Log factor: n log 2 + log(1/eta)."""
    return n * np.log(2) + np.log(1 / eta)


def N_general(p: float, n: int, eta: float, qmax: float = None) -> float:
    """
    T2a: general peak-detection shot bound.
    p: peak probability; qmax: competitor probability (default p/2).
    """
    qmax = p / 2 if qmax is None else qmax
    D = p - qmax
    return (2 * (p + qmax) + 4 * D / 3) * L(n, eta) / D ** 2


def N_collision(p: float, eta: float) -> float:
    """T2b: collision-based shot bound. Valid when N * qmax <= 1/2."""
    return 8 * np.log(2 / eta) / p


def G_max(eps: float, delta: float, N: int, n: int, eta: float, regime: str = "general") -> float:
    """
    T9: maximum circuit depth (gates) for which the peak remains detectable.
    eps: effective noise per gate; delta: target peak probability floor;
    N: shots; n: qubits; eta: confidence.
    """
    if regime == "general":
        pmin = 18 * L(n, eta) / N
    else:
        pmin = 8 * np.log(2 / eta) / N
    return (np.log(delta) - np.log(pmin)) / eps
