"""
src/svqa/attacks/severing.py
Severing/score spoofing attack (L09).
"""
import numpy as np
from itertools import product as it_product


def severed_distribution(probs: np.ndarray, n: int, cut_qubits: list) -> np.ndarray:
    """
    Compute the severed-product distribution by factorising at the cut.
    cut_qubits: list of qubit indices at which to cut (sever) the circuit.

    Returns marginal probability array.
    """
    # Compute marginals for each qubit
    marginals = []
    for k in range(n):
        p0 = 0.0
        for idx in range(len(probs)):
            if ((idx >> k) & 1) == 0:
                p0 += probs[idx]
        marginals.append([p0, 1 - p0])

    # Severed distribution: product of marginals for cut qubits, exact otherwise
    severed = np.zeros(2 ** n)
    for idx in range(2 ** n):
        bits = [(idx >> k) & 1 for k in range(n)]
        p = 1.0
        for k in cut_qubits:
            p *= marginals[k][bits[k]]
        severed[idx] = p

    # Normalise
    total = severed.sum()
    if total > 0:
        severed /= total
    return severed


def severing_score(target_probs: np.ndarray, severed_probs: np.ndarray) -> float:
    """
    Inner product (TV-similarity) between severed and target distributions.
    Also known as the XEB-like score spoofing metric.
    """
    return float(np.dot(target_probs, severed_probs))


def fit_spoofing_rate(scores_by_depth: dict) -> dict:
    """
    Fit chi(d) ~ K * c^(b/4 * d) where b is number of severed CZ gates.
    scores_by_depth: {depth: [score, ...]}
    Returns dict with c, K, R2.
    """
    depths = sorted(scores_by_depth.keys())
    if len(depths) < 2:
        return dict(c=None, K=None, R2=None)
    mean_scores = [np.mean(scores_by_depth[d]) for d in depths]
    log_scores = np.log(np.clip(mean_scores, 1e-30, None))
    # Fit log(score) = log(K) + d * log(c)
    x = np.array(depths, dtype=float)
    coeffs = np.polyfit(x, log_scores, 1)
    c = float(np.exp(coeffs[0]))
    K = float(np.exp(coeffs[1]))
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((log_scores - y_pred) ** 2)
    ss_tot = np.sum((log_scores - log_scores.mean()) ** 2)
    R2 = 1 - ss_res / max(ss_tot, 1e-30)
    return dict(c=c, K=K, R2=R2)
