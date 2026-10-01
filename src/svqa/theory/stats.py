"""
src/svqa/theory/stats.py
Statistical helpers: Wilson intervals, Holm correction, etc.
"""
import numpy as np
from scipy import stats as sp_stats


def wilson_ci(k: int, n: int, alpha: float = 0.05):
    """Wilson confidence interval for a proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    z = sp_stats.norm.ppf(1 - alpha / 2)
    p_hat = k / n
    denom = 1 + z ** 2 / n
    centre = (p_hat + z ** 2 / (2 * n)) / denom
    halfwidth = z * np.sqrt(p_hat * (1 - p_hat) / n + z ** 2 / (4 * n ** 2)) / denom
    return (max(0.0, centre - halfwidth), min(1.0, centre + halfwidth))


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05):
    """Clopper-Pearson exact confidence interval."""
    if n == 0:
        return (0.0, 1.0)
    lo = sp_stats.beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = sp_stats.beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (lo, hi)


def holm_correction(p_values: list, alpha: float = 0.05) -> list:
    """Holm-Bonferroni correction; returns list of booleans (reject)."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    reject = [False] * m
    for rank, (orig_idx, pval) in enumerate(indexed):
        threshold = alpha / (m - rank)
        if pval <= threshold:
            reject[orig_idx] = True
        else:
            break
    return reject


def t1_test(p_hat: float, p_pred: float, n_shots: int):
    """
    T1 test: z-score for p_hat >= delta * F_pred.
    Returns z and whether the inequality holds (z >= 0).
    """
    se = np.sqrt(p_hat * (1 - p_hat) / n_shots)
    z = (p_hat - p_pred) / (se + 1e-12)
    return z, p_hat >= p_pred
