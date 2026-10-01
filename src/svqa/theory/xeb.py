"""
src/svqa/theory/xeb.py
XEB statistics from Theorem T3 of THEORY_AND_PROOFS.md
"""
import numpy as np


def xeb_var(F: float, N: int) -> float:
    """Variance of XEB estimator for fidelity F with N samples."""
    return (1 + 2 * F - F ** 2) / N


def xeb_N_for_sigma(F: float, z: float) -> float:
    """
    T3: number of samples needed to detect fidelity F at z sigma.
    F=2.3e-3, z=5 -> ~4.7e6
    """
    return z ** 2 * (1 + 2 * F - F ** 2) / F ** 2


def xeb_estimator(counts: dict, ideal_probs: dict) -> float:
    """
    Compute linear XEB from measured counts and ideal probabilities.
    counts: {bitstring: count}; ideal_probs: {bitstring: probability}
    """
    N = sum(counts.values())
    n_q = len(next(iter(counts)))
    D = 2 ** n_q
    xeb = 0.0
    for bs, cnt in counts.items():
        p_ideal = ideal_probs.get(bs, 0.0)
        xeb += (cnt / N) * (D * p_ideal - 1)
    return xeb
