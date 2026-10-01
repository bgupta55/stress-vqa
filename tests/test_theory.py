"""
tests/test_theory.py
Unit tests for theory functions (T1–T6, T9, P8).
"""
import sys
import pathlib
import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.theory.shots import L, N_general, N_collision, G_max
from svqa.theory.xeb import xeb_var, xeb_N_for_sigma
from svqa.theory.mps_bound import chi_min, mps_fidelity_bound


class TestT2Shots:
    def test_L_formula(self):
        # L(10, 0.01) = 10*log(2) + log(100) ≈ 11.51
        val = L(10, 0.01)
        expected = 10 * np.log(2) + np.log(100)
        assert abs(val - expected) < 1e-9

    def test_N_general_positive(self):
        N = N_general(0.01, 20, 0.01)
        assert N > 0

    def test_N_collision_positive(self):
        N = N_collision(0.01, 0.01)
        assert N > 0

    def test_G_max_positive(self):
        G = G_max(0.005, 1.0, 10000, 20, 0.01)
        assert G > 0


class TestT3XEB:
    def test_xeb_N_for_sigma_r2_value(self):
        """T3: F=2.3e-3, z=5 -> ~4.7e6"""
        val = xeb_N_for_sigma(2.3e-3, 5)
        assert abs(val - 4.7e6) / 4.7e6 < 0.05

    def test_xeb_var_formula(self):
        F, N = 0.01, 10000
        var = xeb_var(F, N)
        expected = (1 + 2 * F - F ** 2) / N
        assert abs(var - expected) < 1e-12

    def test_xeb_N_positive(self):
        assert xeb_N_for_sigma(1e-3, 3) > 0


class TestT5MPSBound:
    def test_chi_min_r2_value(self):
        """T5: f=2.3e-3, m=30, n=61 -> ~8.5e5"""
        val = chi_min(2.3e-3, 30, 61)
        assert abs(val - 8.5e5) / 8.5e5 < 0.05

    def test_mps_bound_n24(self):
        """T5 example: n=24, m=12, chi=64 -> f <= 64/1024 = 0.0625"""
        bound = mps_fidelity_bound(64, 12, 24)
        expected = 64 / 1024
        assert abs(bound - expected) < 1e-6

    def test_mps_bound_increases_with_chi(self):
        b1 = mps_fidelity_bound(64, 12, 24)
        b2 = mps_fidelity_bound(128, 12, 24)
        assert b2 > b1


class TestP8PerturbedMirror:
    def test_delta_prediction(self):
        """P8: delta_pred = cos(theta/2)^(2n)"""
        from svqa.circuits.planted import perturbed_mirror
        from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
        from svqa.sim.aer_sv import peak_probability

        n = 10
        depth = 6
        rng = np.random.default_rng(0)
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        s_bits = [int(b) for b in rng.integers(0, 2, n)]

        for theta in [0.0, 0.15, 0.30]:
            C, n_cz, delta_pred = perturbed_mirror(n, colors, depth, theta, s_bits, rng)
            expected = np.cos(theta / 2) ** (2 * n)
            assert abs(delta_pred - expected) < 1e-9

    def test_argmax_equals_s_at_theta_zero(self):
        """P8: at theta=0, argmax = s (perfect mirror)"""
        from svqa.circuits.planted import perturbed_mirror
        from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
        from svqa.sim.aer_sv import argmax_bitstring, peak_probability

        n = 8
        depth = 4
        rng = np.random.default_rng(42)
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        s_bits = [int(b) for b in rng.integers(0, 2, n)]
        C, n_cz, delta_pred = perturbed_mirror(n, colors, depth, 0.0, s_bits, rng)
        p = peak_probability(C, s_bits)
        am = argmax_bitstring(C, n)
        assert am == s_bits, f"argmax {am} != s_bits {s_bits}"
        assert abs(p - 1.0) < 1e-4  # theta=0: perfect mirror, p=1

    def test_transpiler_guard(self):
        """Transpiler at level 0 preserves CZ count."""
        from svqa.circuits.planted import perturbed_mirror
        from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_aer import AerSimulator

        n = 10
        depth = 6
        rng = np.random.default_rng(1)
        edges = line_graph_edges(n)
        colors = edge_color_matchings(edges)
        s_bits = [int(b) for b in rng.integers(0, 2, n)]
        C, n_cz, _ = perturbed_mirror(n, colors, depth, 0.2, s_bits, rng)
        backend = AerSimulator()
        pm = generate_preset_pass_manager(optimization_level=0, backend=backend)
        transpiled = pm.run(C)
        actual = transpiled.count_ops().get("cz", 0)
        assert actual == n_cz, f"expected {n_cz} CZ gates, got {actual}"
