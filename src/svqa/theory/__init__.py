"""
src/svqa/theory/__init__.py
"""
from .shots import L, N_general, N_collision, G_max
from .xeb import xeb_var, xeb_N_for_sigma, xeb_estimator
from .mps_bound import chi_min, mps_fidelity_bound
from .stats import wilson_ci, clopper_pearson_ci, holm_correction, t1_test
from .windows import frontier_seconds, window_forecast
