#!/usr/bin/env python3
"""
experiments/l00_env.py
L00: Environment check, version logging, and unit tests.
"""
import sys
import platform
import subprocess
import json
import pathlib
import time

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def check_versions() -> dict:
    versions = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
    }
    packages = ["qiskit", "qiskit_aer", "qiskit_ibm_runtime", "numpy", "scipy",
                "pandas", "networkx", "statsmodels", "sklearn", "pyzx", "stim"]
    for pkg in packages:
        try:
            mod = __import__(pkg.replace("-", "_"))
            versions[pkg] = getattr(mod, "__version__", "installed")
        except ImportError:
            versions[pkg] = "NOT INSTALLED"
    # cotengra / quimb
    for pkg in ["cotengra", "quimb"]:
        try:
            mod = __import__(pkg)
            versions[pkg] = getattr(mod, "__version__", "installed")
        except ImportError:
            versions[pkg] = "NOT INSTALLED"
    return versions


def check_memory() -> dict:
    import resource
    mem_bytes = resource.getrlimit(resource.RLIMIT_DATA)[0]
    try:
        import subprocess
        result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True
        )
        total_ram_gb = int(result.stdout.strip()) / (1024**3) if result.stdout.strip().isdigit() else "unknown"
    except Exception:
        total_ram_gb = "unknown"
    return {"total_ram_gb": total_ram_gb}


def run_theory_unit_tests() -> dict:
    """Quick numeric checks against closed-form values from THEORY_AND_PROOFS.md"""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
    from svqa.theory.xeb import xeb_N_for_sigma
    from svqa.theory.mps_bound import chi_min
    from svqa.theory.shots import N_collision

    results = {}

    # T3: xeb_N_for_sigma(2.3e-3, 5) ≈ 4.7e6
    val = xeb_N_for_sigma(2.3e-3, 5)
    expected = 4.7e6
    tol = 0.05
    results["T3_xeb_samples"] = {
        "computed": val,
        "expected": expected,
        "pass": abs(val - expected) / expected < tol,
    }

    # T5: chi_min(2.3e-3, 30, 61) ≈ 8.5e5
    val2 = chi_min(2.3e-3, 30, 61)
    expected2 = 8.5e5
    results["T5_chi_min"] = {
        "computed": val2,
        "expected": expected2,
        "pass": abs(val2 - expected2) / expected2 < tol,
    }

    return results


def run_circuit_unit_tests() -> dict:
    """Test perturbed-mirror circuit generation and transpiler guard."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
    import numpy as np
    from svqa.circuits.planted import perturbed_mirror
    from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
    from svqa.sim.aer_sv import peak_probability, argmax_bitstring
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    try:
        from qiskit_aer import AerSimulator
        backend_sim = AerSimulator()
    except Exception:
        backend_sim = None

    n = 10
    depth = 6
    rng = np.random.default_rng(42)
    edges = line_graph_edges(n)
    colors = edge_color_matchings(edges)
    s_bits = [int(b) for b in rng.integers(0, 2, n)]
    results = {}

    for theta in [0.0, 0.15, 0.30]:
        C, n_cz, delta_pred = perturbed_mirror(n, colors, depth, theta, s_bits, rng)
        p_peak = peak_probability(C, s_bits)
        am = argmax_bitstring(C, n)
        argmax_ok = (am == s_bits)
        delta_ok = abs(p_peak - delta_pred) < 0.15  # large tolerance for small n fluctuation
        results[f"theta_{theta:.2f}"] = {
            "n_cz": n_cz,
            "delta_pred": round(delta_pred, 4),
            "p_peak": round(float(p_peak), 4),
            "argmax_matches_s": argmax_ok,
            "delta_within_tol": delta_ok,
        }

    # Transpiler guard test
    if backend_sim is not None:
        rng2 = np.random.default_rng(0)
        C2, n_cz2, _ = perturbed_mirror(n, colors, depth, 0.2, s_bits, rng2)
        # Without barrier it would collapse (we keep barriers so should be preserved)
        pm = generate_preset_pass_manager(optimization_level=1, backend=backend_sim)
        transpiled = pm.run(C2)
        actual_cz = transpiled.count_ops().get("cz", 0)
        results["transpiler_guard"] = {
            "expected_cz": n_cz2,
            "actual_cz_after_transpile_level1": actual_cz,
            "guard_pass": actual_cz == n_cz2,
        }

    return results


if __name__ == "__main__":
    t0 = time.time()
    print("=== L00: Environment Check ===")
    versions = check_versions()
    mem = check_memory()
    theory_tests = run_theory_unit_tests()
    circuit_tests = run_circuit_unit_tests()

    all_theory_pass = all(v.get("pass", False) for v in theory_tests.values())
    transpiler_guard = circuit_tests.get("transpiler_guard", {}).get("guard_pass", "N/A")

    print("\n--- Package Versions ---")
    for k, v in versions.items():
        print(f"  {k}: {v}")
    print(f"\n  RAM: {mem['total_ram_gb']} GB")

    print("\n--- Theory Unit Tests ---")
    for k, v in theory_tests.items():
        status = "PASS" if v.get("pass") else "FAIL"
        print(f"  [{status}] {k}: computed={v['computed']:.3e}, expected={v['expected']:.3e}")

    print("\n--- Circuit Unit Tests ---")
    for k, v in circuit_tests.items():
        if k == "transpiler_guard":
            status = "PASS" if v.get("guard_pass") else "FAIL"
            print(f"  [{status}] transpiler_guard: {v}")
        else:
            print(f"  {k}: {v}")

    result_data = {
        "experiment": "L00",
        "wall_seconds": round(time.time() - t0, 2),
        "versions": versions,
        "memory": mem,
        "theory_unit_tests": theory_tests,
        "circuit_unit_tests": circuit_tests,
        "all_theory_pass": all_theory_pass,
    }

    def _to_serializable(obj):
        import numpy as np
        if isinstance(obj, dict):
            return {k: _to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_to_serializable(v) for v in obj]
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return obj

    out_path = RESULTS_DIR / "l00_env.json"
    with open(out_path, "w") as f:
        json.dump(_to_serializable(result_data), f, indent=2)
    print(f"\nResults saved to {out_path}")
    print(f"Wall time: {result_data['wall_seconds']:.1f}s")
