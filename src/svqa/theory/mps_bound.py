"""
src/svqa/theory/mps_bound.py
MPS fidelity bound from Theorem T5 of THEORY_AND_PROOFS.md
"""
import numpy as np


def chi_min(f: float, m: int, n: int) -> float:
    """
    T5: minimum bond dimension needed for MPS to achieve fidelity f.
    m: min cut size (number of qubits on smaller side of bipartition)
    n: total qubits

    r2-like: f=2.3e-3, m=30, n=61 -> ~8.5e5
    """
    dA = 2 ** m
    dB = 2 ** (n - m)
    return f * dA / (1 + np.sqrt(dA / dB)) ** 2


def mps_fidelity_bound(chi: int, m: int, n: int) -> float:
    """
    Maximum achievable fidelity for MPS with bond dimension chi
    at a cut of size m in an n-qubit system.
    f <= chi * (1 + sqrt(dA/dB))^2 / dA
    """
    dA = 2 ** m
    dB = 2 ** (n - m)
    return chi * (1 + np.sqrt(dA / dB)) ** 2 / dA
