"""
src/svqa/hardware/backend.py
IBM backend access and calibration snapshot utilities.
"""
import json
import time
import pathlib


def get_service(token: str = None, instance: str = None):
    """Get QiskitRuntimeService. Reads from env if not passed."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    import os
    t = token or os.environ.get("QISKIT_IBM_TOKEN")
    i = instance or os.environ.get("QISKIT_IBM_INSTANCE")
    if t:
        # Use ibm_cloud channel (ibm_quantum was deprecated in runtime ≥0.40)
        return QiskitRuntimeService(channel="ibm_cloud", token=t, instance=i)
    return QiskitRuntimeService()


def list_backends(service) -> list:
    """List all available backends with status."""
    backends = []
    for b in service.backends():
        try:
            status = b.status()
            backends.append({
                "name": b.name,
                "num_qubits": b.num_qubits,
                "operational": status.operational,
                "pending_jobs": status.pending_jobs,
            })
        except Exception:
            backends.append({"name": b.name, "num_qubits": getattr(b, "num_qubits", "?")})
    return backends


def calibration_snapshot(backend) -> dict:
    """Capture calibration data from backend target."""
    try:
        target = backend.target
        snap = {
            "backend_name": backend.name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "qubits": {},
            "gates": {},
        }
        # Readout errors
        for q in range(backend.num_qubits):
            try:
                ro_err = target["measure"][(q,)].error
                snap["qubits"][str(q)] = {"readout_error": ro_err}
            except Exception:
                snap["qubits"][str(q)] = {"readout_error": None}
        # 2-qubit gate errors
        for inst_name in ["cz", "ecr", "cx"]:
            try:
                props = target.operation_properties(inst_name)
                if props:
                    for qargs, prop in props.items():
                        if prop and hasattr(prop, "error") and prop.error is not None:
                            snap["gates"][f"{inst_name}_{qargs}"] = {"error": prop.error}
            except Exception:
                pass
        return snap
    except Exception as e:
        return {"error": str(e), "backend_name": backend.name,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}


def save_calibration(snap: dict, path: str):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(snap, f, indent=2)
