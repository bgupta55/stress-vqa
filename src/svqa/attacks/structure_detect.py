"""
src/svqa/attacks/structure_detect.py
Mirror/palindrome structure detector (L07, Hypothesis H5).
"""
import numpy as np
from qiskit import QuantumCircuit


def gate_sequence(qc: QuantumCircuit) -> list:
    """Return list of (gate_name, qubits) for all non-barrier ops."""
    ops = []
    for inst in qc.data:
        if inst.operation.name == "barrier":
            continue
        qubits = tuple(qc.find_bit(q).index for q in inst.qubits)
        ops.append((inst.operation.name, qubits))
    return ops


def mirror_score(qc: QuantumCircuit) -> float:
    """
    Compute palindrome score: fraction of positional 2q-gate matches
    between the first half and the reversed second half of the circuit.

    C5a (perturbed mirror U† Ry U) has this structure by construction → score ≈ 1.
    Random brickwork has no such symmetry → score ≈ 0.
    """
    ops = gate_sequence(qc)
    # Keep only 2-qubit gates in order
    two_q = [(name, q) for name, q in ops if len(q) == 2]
    n_total = len(two_q)
    if n_total < 2:
        return 0.0
    # Split into first half and second half (mirror structure: U† | Ry | U → 2q gates symmetric)
    half = n_total // 2
    first = two_q[:half]
    second = list(reversed(two_q[half if n_total % 2 == 0 else half + 1:]))
    min_len = min(len(first), len(second))
    if min_len == 0:
        return 0.0
    positional_matches = sum(
        1 for (n1, q1), (n2, q2) in zip(first[:min_len], second[:min_len])
        if n1 == n2 and set(q1) == set(q2)
    )
    return positional_matches / min_len


def detect_mirror(qc: QuantumCircuit, threshold: float = 0.8) -> bool:
    """Return True if the circuit is detected as mirror (C5a-like)."""
    return mirror_score(qc) >= threshold


def classify_circuits(circuits_c5a: list, circuits_random: list) -> dict:
    """
    Classify a list of C5a and random brickwork circuits.
    Returns dict with accuracy metrics.
    """
    tp = sum(1 for qc in circuits_c5a if detect_mirror(qc))
    fp = sum(1 for qc in circuits_random if detect_mirror(qc))
    fn = len(circuits_c5a) - tp
    tn = len(circuits_random) - fp
    accuracy = (tp + tn) / (len(circuits_c5a) + len(circuits_random))
    c5a_detection_rate = tp / max(len(circuits_c5a), 1)
    return dict(
        tp=tp, fp=fp, fn=fn, tn=tn,
        accuracy=accuracy,
        c5a_detection_rate=c5a_detection_rate,
        false_positive_rate=fp / max(len(circuits_random), 1),
    )
