"""
src/svqa/attacks/zx_tcount.py
ZX-calculus T-count reduction feature extractor (L05).
"""
try:
    import pyzx as zx
    HAS_PYZX = True
except ImportError:
    HAS_PYZX = False

from qiskit import QuantumCircuit
from qiskit import qasm2 as _qasm2


def circuit_tcount_features(qc: QuantumCircuit) -> dict:
    """
    Extract T-count before and after ZX simplification.
    Returns dict with t_before, t_after, clifford_fraction, reduction.
    """
    if not HAS_PYZX:
        return dict(
            t_before=None, t_after=None,
            clifford_fraction=None, reduction=None,
            error="pyzx not installed",
        )

    try:
        qasm_str = _qasm2.dumps(qc)
        circ_zx = zx.Circuit.from_qasm(qasm_str)
        t_before = circ_zx.tcount()

        g = circ_zx.to_graph()
        zx.simplify.full_reduce(g)
        circ_opt = zx.extract_circuit(g)
        t_after = circ_opt.tcount()

        total_gates = sum(1 for _ in qc.data)
        clifford_gates = sum(1 for inst in qc.data if inst.operation.name in
                             ("h", "s", "sdg", "cx", "cz", "x", "y", "z", "swap"))
        clifford_fraction = clifford_gates / max(total_gates, 1)

        return dict(
            t_before=t_before,
            t_after=t_after,
            clifford_fraction=clifford_fraction,
            reduction=t_before - t_after,
            reduction_fraction=(t_before - t_after) / max(t_before, 1),
        )
    except Exception as e:
        return dict(
            t_before=None, t_after=None,
            clifford_fraction=None, reduction=None,
            error=str(e),
        )
