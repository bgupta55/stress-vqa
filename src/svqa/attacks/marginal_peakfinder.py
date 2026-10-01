"""
src/svqa/attacks/marginal_peakfinder.py
Local-marginal peak finder using Theorem T6.
Recover s from sign(<Z_k>) for delta > 1/2.
"""
import numpy as np
from qiskit import QuantumCircuit


def exact_z_marginals(sv: np.ndarray, n: int) -> np.ndarray:
    """
    Compute <Z_k> for each qubit k from exact statevector.
    <Z_k> = sum_{x: x_k=0} |sv_x|^2 - sum_{x: x_k=1} |sv_x|^2
    Vectorized over all indices at once.
    """
    probs = np.abs(sv) ** 2
    indices = np.arange(len(probs), dtype=np.int64)
    z_exp = np.zeros(n)
    for k in range(n):
        bit_k = (indices >> k) & 1        # shape (2^n,)
        signs = 1 - 2 * bit_k             # +1 for 0-bit, -1 for 1-bit
        z_exp[k] = float(np.dot(probs, signs))
    return z_exp


def recover_peak_from_marginals(z_marginals: np.ndarray) -> list:
    """
    T6: recover s_bits from sign of <Z_k>.
    s_k = 1 if <Z_k> < 0, else 0.
    """
    return [int(z < 0) for z in z_marginals]


def marginal_success(s_true: list, z_marginals: np.ndarray) -> dict:
    """
    Compare recovered peak with true peak.
    Returns dict with success flag and number of correct bits.
    """
    s_recovered = recover_peak_from_marginals(z_marginals)
    n_correct = sum(a == b for a, b in zip(s_true, s_recovered))
    n = len(s_true)
    return dict(
        success=(s_recovered == s_true),
        bits_correct=n_correct,
        n=n,
        fraction_correct=n_correct / n,
        s_true=s_true,
        s_recovered=s_recovered,
    )


def pauli_propagate_z(circuit_ops: list, qubit: int, w_cap: int, coeff_cut: float) -> float:
    """
    Truncated Pauli propagation to estimate <Z_qubit>.
    circuit_ops: list of (gate_name, params, qubits)

    [DESIGN: implement with bit-packed symplectic Paulis for large n]
    This is a simplified version for n <= ~20.
    """
    # Pauli represented as (pauli_string, coefficient)
    # Start with Z on the target qubit
    n_qubits = max(max(q) for _, _, q in circuit_ops) + 1 if circuit_ops else qubit + 1

    def weight(pstr):
        return sum(1 for p in pstr if p != "I")

    def pauli_z(k, n):
        return "I" * k + "Z" + "I" * (n - k - 1)

    # Initialize: {Z_qubit: 1.0}
    P = {pauli_z(qubit, n_qubits): 1.0}

    for gate_name, params, qubits in reversed(circuit_ops):
        new_P = {}
        for pstr, coeff in P.items():
            new_terms = conjugate_pauli(pstr, gate_name, params, qubits)
            for np_str, nc in new_terms.items():
                if weight(np_str) <= w_cap and abs(nc * coeff) >= coeff_cut:
                    new_P[np_str] = new_P.get(np_str, 0.0) + coeff * nc
        P = new_P

    # <0|P|0> = sum of coefficients of I/Z-only Pauli strings
    result = 0.0
    for pstr, coeff in P.items():
        if all(c in "IZ" for c in pstr):
            result += coeff
    return result


def conjugate_pauli(pstr: str, gate_name: str, params: list, qubits: list) -> dict:
    """
    Conjugate a Pauli string through a single gate.
    Returns dict of {new_pstr: coefficient}.
    [Simplified: handles CZ and Ry; extend as needed]
    """
    n = len(pstr)
    plist = list(pstr)

    if gate_name == "cz":
        q0, q1 = qubits[0], qubits[1]
        p0, p1 = plist[q0], plist[q1]
        # CZ conjugation rules on Pauli strings (simplified)
        if p0 == "X" and p1 == "I":
            plist[q1] = "Z"
        elif p0 == "I" and p1 == "X":
            plist[q0] = "Z"
        elif p0 == "X" and p1 == "X":
            plist[q0] = "Y"
            plist[q1] = "Y"
        return {"".join(plist): 1.0}

    elif gate_name in ("ry", "rx", "rz"):
        q = qubits[0]
        theta = params[0] if params else 0.0
        p = plist[q]
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        plist_copy = list(plist)
        # Ry(theta): X -> cos(theta)X + sin(theta)Z; Z -> cos(theta)Z - sin(theta)X
        if gate_name == "ry":
            if p == "X":
                term1 = plist_copy.copy(); term1[q] = "X"
                term2 = plist_copy.copy(); term2[q] = "Z"
                return {"".join(term1): cos_t, "".join(term2): sin_t}
            elif p == "Z":
                term1 = plist_copy.copy(); term1[q] = "Z"
                term2 = plist_copy.copy(); term2[q] = "X"
                return {"".join(term1): cos_t, "".join(term2): -sin_t}
        return {"".join(plist): 1.0}

    else:
        return {"".join(plist): 1.0}
