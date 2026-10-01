"""
src/svqa/circuits/io.py
Circuit serialisation utilities.
"""
from qiskit import qasm2
from qiskit.qpy import dump as qpy_dump, load as qpy_load
import io as _io
import pathlib


def to_qasm2(qc) -> str:
    return qasm2.dumps(qc)


def save_qpy(qc, path: str):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        qpy_dump(qc, f)


def load_qpy(path: str):
    with open(path, "rb") as f:
        return qpy_load(f)[0]
