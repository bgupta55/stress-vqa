"""
src/svqa/circuits/brickwork.py
Random brickwork circuits (without planted peak) for use as controls.
"""
import numpy as np
from qiskit import QuantumCircuit
from .planted import rand_su2_layer


def random_brickwork(n: int, edges_by_color: list, depth: int, rng: np.random.Generator) -> QuantumCircuit:
    """
    Plain random brickwork circuit with no planted structure.
    Used as control in L07 (structure detector).
    """
    qc = QuantumCircuit(n)
    for c in range(depth):
        rand_su2_layer(qc, range(n), rng)
        for (a, b) in edges_by_color[c % len(edges_by_color)]:
            qc.cz(a, b)
    return qc
