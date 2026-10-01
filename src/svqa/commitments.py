"""
src/svqa/commitments.py
SHA-256 peak commitment protocol (single-developer procedural separation).
"""
import hashlib
import secrets
import json
import pathlib


def commit(s_bits: list) -> tuple:
    """
    Commit to a peak bitstring before running attacks.
    Returns (hash, salt). Write hash to data/commitments/; keep (s_bits, salt) in data/secret/.
    """
    salt = secrets.token_hex(16)
    h = hashlib.sha256(("".join(map(str, s_bits)) + salt).encode()).hexdigest()
    return h, salt


def save_commitment(label: str, s_bits: list, commitments_dir: str = "data/commitments",
                    secret_dir: str = "data/secret"):
    """
    Save commitment hash (public) and secret (git-ignored private).
    label: e.g. 'c5a_n20_seed0'
    """
    h, salt = commit(s_bits)
    # Public: hash only
    pub_path = pathlib.Path(commitments_dir) / "peaks_committed.json"
    pub_path.parent.mkdir(parents=True, exist_ok=True)
    pub_data = {}
    if pub_path.exists():
        with open(pub_path) as f:
            pub_data = json.load(f)
    pub_data[label] = {"hash": h, "n": len(s_bits)}
    with open(pub_path, "w") as f:
        json.dump(pub_data, f, indent=2)
    # Private: s_bits + salt
    sec_path = pathlib.Path(secret_dir) / "peaks.json"
    sec_path.parent.mkdir(parents=True, exist_ok=True)
    sec_data = {}
    if sec_path.exists():
        with open(sec_path) as f:
            sec_data = json.load(f)
    sec_data[label] = {"s_bits": s_bits, "salt": salt, "hash": h}
    with open(sec_path, "w") as f:
        json.dump(sec_data, f, indent=2)
    return h, salt


def verify_commitment(label: str, s_bits: list,
                      commitments_dir: str = "data/commitments",
                      secret_dir: str = "data/secret") -> bool:
    """Verify that s_bits matches the committed hash."""
    pub_path = pathlib.Path(commitments_dir) / "peaks_committed.json"
    sec_path = pathlib.Path(secret_dir) / "peaks.json"
    with open(pub_path) as f:
        pub_data = json.load(f)
    with open(sec_path) as f:
        sec_data = json.load(f)
    committed_hash = pub_data[label]["hash"]
    salt = sec_data[label]["salt"]
    h = hashlib.sha256(("".join(map(str, s_bits)) + salt).encode()).hexdigest()
    return h == committed_hash
