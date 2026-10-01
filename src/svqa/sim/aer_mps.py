"""
src/svqa/sim/aer_mps.py
MPS simulation via Qiskit Aer for fidelity barrier experiments (L04).
"""
import numpy as np
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit


def mps_statevector(qc: QuantumCircuit, chi: int, precision: str = "single") -> np.ndarray:
    """
    Run MPS simulation with bond dimension chi.
    Returns approximate statevector.
    [VERIFY option names for your Aer version]
    """
    qc2 = qc.copy()
    qc2.save_statevector()
    sim = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=chi,
        matrix_product_state_truncation_threshold=1e-16,
        precision=precision,
    )
    job = sim.run(qc2, shots=1)
    result = job.result()
    sv = result.get_statevector(qc2)
    return np.asarray(sv)


def mps_fidelity(qc: QuantumCircuit, exact_sv: np.ndarray, chi: int, precision: str = "single") -> float:
    """
    Compute fidelity between MPS approximation (bond dim chi) and exact statevector.
    fidelity = |<exact|mps>|^2
    """
    mps_sv = mps_statevector(qc, chi, precision)
    overlap = np.abs(np.dot(np.conj(exact_sv), mps_sv)) ** 2
    return float(overlap)
