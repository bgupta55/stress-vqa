"""
src/svqa/circuits/mirror.py
Plain mirror circuit U†U for mirror-baseline measurements (Q1).
"""
import numpy as np
from qiskit import QuantumCircuit
from .planted import brickwork_U


def plain_mirror(n: int, edges_by_color: list, depth: int, input_bits: list, rng: np.random.Generator):
    """
    Plain mirror U†|input> → should return to |input> under perfect conditions.
    Used for ε_eff estimation in Q1.

    input_bits: list of 0/1, sets the input Hamming-weight ~ n/2 state.
    """
    U = brickwork_U(n, edges_by_color, depth, rng)
    C = QuantumCircuit(n)
    for q, b in enumerate(input_bits):
        if b:
            C.x(q)
    C.barrier()
    C.compose(U, inplace=True)
    C.barrier()
    C.compose(U.inverse(), inplace=True)
    n_cz = 2 * sum(len(edges_by_color[c % len(edges_by_color)]) for c in range(depth))
    return C, n_cz
