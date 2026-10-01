"""
src/svqa/hardware/ledger.py
Budget ledger: persists billed QPU seconds across jobs/crashes.
"""
import json
import pathlib
import time


class Ledger:
    def __init__(self, path: str = "data/hardware_raw/ledger.json"):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            with open(self.path) as f:
                self._data = json.load(f)
        else:
            self._data = {"entries": [], "billed_total": 0.0}

    @property
    def billed(self) -> float:
        return self._data["billed_total"]

    def add(self, tag: str, job_id: str, billed_seconds: float):
        entry = {
            "tag": tag,
            "job_id": job_id,
            "billed_seconds": billed_seconds,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        self._data["entries"].append(entry)
        self._data["billed_total"] += billed_seconds
        self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def summary(self) -> dict:
        return {
            "total_billed_s": self.billed,
            "n_jobs": len(self._data["entries"]),
            "entries": self._data["entries"],
        }
