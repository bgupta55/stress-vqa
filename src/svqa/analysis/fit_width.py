"""
src/svqa/analysis/fit_width.py
Fit M12 contraction-width model: w = min(a * d * sqrt(n), n).
"""
import numpy as np


def fit_width_model(n_list: list, depth_list: list, width_list: list) -> dict:
    """
    Fit the M12 model w = min(a * d * sqrt(n), n) to data.
    Returns dict with a, stderr, R2.
    """
    from scipy.optimize import curve_fit

    x_data = []
    y_data = []
    for n, d, w in zip(n_list, depth_list, width_list):
        x_data.append((n, d))
        y_data.append(w)

    def model(X, a):
        n_arr, d_arr = X
        return np.minimum(a * d_arr * np.sqrt(n_arr), n_arr)

    X = (np.array([x[0] for x in x_data], dtype=float),
         np.array([x[1] for x in x_data], dtype=float))
    y = np.array(y_data, dtype=float)

    try:
        popt, pcov = curve_fit(model, X, y, p0=[0.23], bounds=(0.01, 2.0))
        a_fit = float(popt[0])
        stderr = float(np.sqrt(pcov[0, 0]))
        y_pred = model(X, a_fit)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        R2 = 1 - ss_res / max(ss_tot, 1e-12)
        return dict(a=a_fit, stderr=stderr, R2=float(R2))
    except Exception as e:
        return dict(a=0.23, stderr=None, R2=None, error=str(e))
