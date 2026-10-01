"""
src/svqa/sim/noisy.py
Noisy simulation using Aer Pauli noise model (L10 pre-flight).
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError


def build_pauli_noise_model(eps_2q: float, eps_readout: float) -> NoiseModel:
    """
    Simple Pauli noise model:
      - Depolarizing error eps_2q on each 2-qubit (CZ) gate
      - Symmetric readout error eps_readout
    """
    noise_model = NoiseModel()
    # 2-qubit depolarizing
    error_2q = depolarizing_error(eps_2q, 2)
    noise_model.add_all_qubit_quantum_error(error_2q, ["cz"])
    # Readout error (symmetric)
    ro_err = ReadoutError([[1 - eps_readout, eps_readout], [eps_readout, 1 - eps_readout]])
    noise_model.add_all_qubit_readout_error(ro_err)
    return noise_model


def noisy_shots(qc: QuantumCircuit, eps_2q: float, eps_readout: float, shots: int, seed: int = 0) -> dict:
    """
    Run noisy simulation and return counts dict.
    """
    noise_model = build_pauli_noise_model(eps_2q, eps_readout)
    qc2 = qc.copy()
    qc2.measure_all()
    sim = AerSimulator(noise_model=noise_model)
    job = sim.run(qc2, shots=shots, seed_simulator=seed)
    return job.result().get_counts()


def noisy_peak_fraction(qc: QuantumCircuit, s_bits: list, eps_2q: float, eps_readout: float,
                        shots: int, seed: int = 0) -> float:
    """Return fraction of shots that measured the target peak bitstring."""
    counts = noisy_shots(qc, eps_2q, eps_readout, shots, seed)
    target = "".join(str(b) for b in reversed(s_bits))
    return counts.get(target, 0) / shots
