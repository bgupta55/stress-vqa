"""
src/svqa/sim/aer_sv.py
Statevector simulation via Qiskit Aer.
"""
import numpy as np
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit


def statevector_simulate(qc: QuantumCircuit, precision: str = "single") -> np.ndarray:
    """
    Run statevector simulation. Returns complex numpy array of amplitudes.
    precision: 'single' or 'double'
    """
    from qiskit.circuit.library import Measure
    # Add save_statevector instruction
    qc2 = qc.copy()
    qc2.save_statevector()
    sim = AerSimulator(method="statevector", precision=precision)
    job = sim.run(qc2, shots=1)
    result = job.result()
    sv = result.get_statevector(qc2)
    return np.asarray(sv)


def get_probabilities(qc: QuantumCircuit, precision: str = "single") -> np.ndarray:
    """Return probability distribution from statevector simulation."""
    sv = statevector_simulate(qc, precision)
    return np.abs(sv) ** 2


def peak_probability(qc: QuantumCircuit, s_bits: list, precision: str = "single") -> float:
    """Return probability of measuring the target bitstring s_bits."""
    probs = get_probabilities(qc, precision)
    idx = int("".join(str(b) for b in reversed(s_bits)), 2)
    return float(probs[idx])


def argmax_bitstring(qc: QuantumCircuit, n: int, precision: str = "single") -> list:
    """Return the bitstring with highest probability."""
    probs = get_probabilities(qc, precision)
    idx = int(np.argmax(probs))
    return [int(b) for b in format(idx, f"0{n}b")][::-1]
