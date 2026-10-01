"""
src/svqa/circuits/planted.py
Perturbed-mirror planted circuit family (Proposition P8).
[TESTED logic on a line graph, Qiskit 2.5.2]
"""
import numpy as np
from qiskit import QuantumCircuit


def rand_su2_layer(qc: QuantumCircuit, qubits, rng: np.random.Generator):
    """Haar-random SU(2) layer via RZ RX RZ parametrisation."""
    for q in qubits:
        qc.rz(rng.uniform(0, 2 * np.pi), q)
        qc.rx(np.arccos(rng.uniform(-1, 1)), q)
        qc.rz(rng.uniform(0, 2 * np.pi), q)


def brickwork_U(n: int, edges_by_color: list, depth: int, rng: np.random.Generator) -> QuantumCircuit:
    """
    edges_by_color: list of matchings (lists of (a, b)) covering the device subgraph.
    Returns a brickwork circuit of given depth with random SU(2) single-qubit gates
    and CZ two-qubit gates.
    """
    qc = QuantumCircuit(n)
    for c in range(depth):
        rand_su2_layer(qc, range(n), rng)
        for (a, b) in edges_by_color[c % len(edges_by_color)]:
            qc.cz(a, b)
    return qc


def perturbed_mirror(
    n: int,
    edges_by_color: list,
    depth: int,
    theta: float,
    s_bits: list,
    rng: np.random.Generator,
):
    """
    Constructs C = X^s · U† · R_y(theta) · U

    Returns:
        C: QuantumCircuit
        n_cz: total number of CZ gates (2 * depth * edges_per_layer)
        delta_pred: predicted peak probability = cos(theta/2)^(2n) (P8)

    Note: barriers are REQUIRED to prevent transpiler from collapsing the mirror.
    """
    U = brickwork_U(n, edges_by_color, depth, rng)
    C = QuantumCircuit(n)
    C.compose(U, inplace=True)
    C.barrier()
    for q in range(n):
        C.ry(theta, q)
    C.barrier()
    C.compose(U.inverse(), inplace=True)
    for q, b in enumerate(s_bits):
        if b:
            C.x(q)

    n_cz = 2 * sum(len(edges_by_color[c % len(edges_by_color)]) for c in range(depth))
    delta_pred = float(np.cos(theta / 2) ** (2 * n))
    return C, n_cz, delta_pred
