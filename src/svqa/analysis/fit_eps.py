"""
src/svqa/analysis/fit_eps.py
Fit effective noise rate ε_eff from hardware data.
"""
import numpy as np


def fit_eps_eff(n_cz_list: list, p_hat_list: list, delta: float = 1.0) -> dict:
    """
    WLS fit of ln(p_hat/delta) = -eps_eff * G to get eps_eff.
    Returns dict with eps_eff, stderr, R2.
    """
    G = np.array(n_cz_list, dtype=float)
    p_hat = np.array(p_hat_list, dtype=float)
    # Weights: 1/variance ~ p_hat * (1 - p_hat) / N approx p_hat for small p_hat
    ln_p = np.log(np.clip(p_hat / delta, 1e-10, None))
    # WLS: fit ln_p = -eps * G
    w = p_hat / (1 - p_hat + 1e-6)
    eps_eff = -np.sum(w * G * ln_p) / np.sum(w * G ** 2)
    residuals = ln_p + eps_eff * G
    ss_res = np.sum(w * residuals ** 2)
    ss_tot = np.sum(w * (ln_p - np.average(ln_p, weights=w)) ** 2)
    R2 = 1 - ss_res / max(ss_tot, 1e-12)
    # Bootstrap stderr
    from scipy.optimize import curve_fit

    def model(G, eps):
        return -eps * G

    try:
        popt, pcov = curve_fit(model, G, ln_p, p0=[eps_eff], sigma=1.0 / np.sqrt(np.clip(w, 1e-9, None)))
        stderr = float(np.sqrt(pcov[0, 0]))
        eps_fit = float(popt[0])
    except Exception:
        eps_fit = float(eps_eff)
        stderr = None

    return dict(eps_eff=eps_fit, stderr=stderr, R2=float(R2))
