#!/usr/bin/env python3
"""
experiments/q0_probe.py
Q0: IBM hardware probe — measures per-shot time, per-job overhead.
Requires QISKIT_IBM_TOKEN and QISKIT_IBM_INSTANCE env vars.

Usage:
  python q0_probe.py --backend ibm_kingston
"""
import sys
import os
import pathlib
import argparse
import time
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from svqa.utils import save_json
from svqa.circuits.planted import perturbed_mirror
from svqa.circuits.layouts import edge_color_matchings, line_graph_edges
from svqa.hardware.backend import get_service, calibration_snapshot, save_calibration
from svqa.hardware.run import run_batch, billed_seconds, PLAN_CAP_S
from svqa.hardware.ledger import Ledger

RESULTS_DIR = pathlib.Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_Q0 = 12
G_Q0 = [40, 120]
SHOTS_Q0 = 2000


def build_q0_circuits():
    edges = line_graph_edges(N_Q0)
    colors = edge_color_matchings(edges)
    n_edges = sum(len(c) for c in colors)
    circuits = []
    meta = []
    for G in G_Q0:
        depth = max(2, G // max(n_edges, 1))
        for seed in range(3):
            rng = np.random.default_rng(seed)
            s_bits = [int(b) for b in rng.integers(0, 2, N_Q0)]
            C, n_cz, delta_pred = perturbed_mirror(N_Q0, colors, depth, 0.0, s_bits, rng)
            C.measure_all()
            circuits.append(C)
            meta.append({"seed": seed, "G": G, "depth": depth, "n_cz": n_cz,
                          "delta_pred": float(delta_pred), "s_bits": s_bits, "n": N_Q0})
    return circuits, meta


def run_q0(backend_name: str = None):
    t0 = time.time()
    print("=== Q0: IBM Hardware Probe ===")

    token = os.environ.get("QISKIT_IBM_TOKEN")
    instance = os.environ.get("QISKIT_IBM_INSTANCE")
    if not token:
        print("ERROR: QISKIT_IBM_TOKEN not set")
        return None

    svc = get_service(token, instance)
    backend = svc.backend(backend_name or "ibm_kingston")
    print(f"  Backend: {backend.name}, {backend.num_qubits} qubits")

    # Save calibration
    snap = calibration_snapshot(backend)
    save_calibration(snap, "data/hardware_raw/q0_calibration.json")

    circuits, meta = build_q0_circuits()
    ledger = Ledger()
    expected_cz = [m["n_cz"] for m in meta]

    try:
        res, job_id = run_batch(backend, circuits, expected_cz, SHOTS_Q0, "Q0", ledger)
        print(f"  Job ID: {job_id}")
        print(f"  Billed so far: {ledger.billed:.1f}s")
        wall_s = time.time() - t0
        t_per_shot = (ledger.billed) / (SHOTS_Q0 * len(circuits))
        print(f"  Estimated t_shot = {t_per_shot*1000:.2f} ms/shot")

        result = {
            "experiment": "Q0",
            "job_id": job_id,
            "backend": backend.name,
            "wall_seconds": round(wall_s, 2),
            "billed_seconds": ledger.billed,
            "t_per_shot_ms": t_per_shot * 1000,
            "n_circuits": len(circuits),
            "meta": meta,
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        result = {"experiment": "Q0", "error": str(e), "wall_seconds": round(time.time() - t0, 2)}

    out = RESULTS_DIR / "q0_probe.json"
    save_json(result, out)
    print(f"\nSaved to {out}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=None)
    args = parser.parse_args()
    run_q0(args.backend)
