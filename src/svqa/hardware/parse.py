"""
src/svqa/hardware/parse.py
Parse hardware results and compute T1-test metrics.
"""
import json
import pathlib
import numpy as np
from ..theory.stats import wilson_ci, t1_test, holm_correction


def load_counts(job_id: str, data_dir: str = "data/hardware_raw") -> list:
    """Load counts for a job from saved JSON."""
    path = pathlib.Path(data_dir) / f"{job_id}_counts.json"
    with open(path) as f:
        return json.load(f)


def peak_fraction_from_counts(counts: dict, s_bits: list) -> tuple:
    """
    Return (k, N, p_hat) where k = peak counts, N = total shots, p_hat = k/N.
    s_bits: target bitstring as list of 0/1.
    """
    target = "".join(str(b) for b in reversed(s_bits))
    N = sum(counts.values())
    k = counts.get(target, 0)
    p_hat = k / max(N, 1)
    return k, N, p_hat


def analyze_hardware_results(job_id: str, circuits_meta: list, data_dir: str = "data/hardware_raw") -> list:
    """
    Analyze hardware results for a batch of circuits.
    circuits_meta: list of dicts with keys: s_bits, delta_pred, F_pred, n_cz, tag
    Returns list of result dicts.
    """
    counts_list = load_counts(job_id, data_dir)
    results = []
    for i, (circ_counts_data, meta) in enumerate(zip(counts_list, circuits_meta)):
        counts = circ_counts_data.get("counts", {})
        s_bits = meta["s_bits"]
        delta_pred = meta.get("delta_pred", 1.0)
        F_pred = meta.get("F_pred", 1.0)
        p_pred = delta_pred * F_pred

        k, N, p_hat = peak_fraction_from_counts(counts, s_bits)
        lo, hi = wilson_ci(k, N)
        z, t1_holds = t1_test(p_hat, p_pred, N)

        # Argmax check
        argmax_bs = max(counts, key=counts.get) if counts else ""
        target_bs = "".join(str(b) for b in reversed(s_bits))
        mode_matches = (argmax_bs == target_bs)

        results.append(dict(
            job_id=job_id,
            circuit_idx=i,
            tag=meta.get("tag", ""),
            n=meta.get("n", None),
            n_cz=meta.get("n_cz", None),
            k=k, N=N, p_hat=p_hat,
            p_pred=p_pred,
            delta_pred=delta_pred,
            F_pred=F_pred,
            wilson_lo=lo, wilson_hi=hi,
            t1_z=z, t1_holds=t1_holds,
            kappa_gap=np.log(p_pred / max(p_hat, 1e-10)) / max(meta.get("n_cz", 1), 1),
            mode_matches=mode_matches,
            argmax_bs=argmax_bs,
            target_bs=target_bs,
        ))
    return results
