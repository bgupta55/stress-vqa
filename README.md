# stress-vqa

**Stress-Testing Verifiable Quantum Advantage**

Code and experiments for the paper *"Stress-Testing a Verifiable Quantum Advantage Protocol"*.
We implement a family of **planted-peak circuits** (perturbed-mirror, C5a) whose output is verifiable
by classical post-processing, then subject them to a systematic battery of classical attacks and
IBM hardware runs to characterise exactly where the quantum–classical gap opens and closes.

---

## Structure

```
stress-vqa/
├── src/svqa/           # Library (circuits, attacks, simulation, theory, hardware utils)
│   ├── circuits/       # Brickwork, mirror, planted-peak, layout helpers
│   ├── attacks/        # Marginal peakfinder, ZX / T-count, structure detector, severing
│   ├── sim/            # Aer statevector / MPS wrappers, cotengra cost estimator
│   ├── theory/         # MPS bound, XEB sample complexity, Wilson CIs, shot formulae
│   ├── hardware/       # IBM backend access, job ledger, result parser
│   └── analysis/       # ε_eff and contraction-width fitting
├── experiments/
│   ├── l00–l12_*.py    # Classical experiments (laptop / HPC, no QPU needed)
│   └── q0–q5_*.py      # IBM hardware experiments
├── configs/            # YAML configs for backends, noise models, attack parameters
├── tests/              # pytest unit tests
├── docs/               # Pre-registration and notes
└── results.md          # Populated result tables (filled after experiments run)
```

---

## Quick start

```bash
# 1. Create a virtual environment and install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run environment check + unit tests
make l00
make test

# 3. Smoke test (no QPU, uses AerSimulator)
make smoke          # or: python experiments/q0_dry_run.py --no-qpu

# 4. Run all classical experiments (no QPU required)
make all_classical
```

---

## IBM Hardware experiments

Hardware jobs require an **IBM Quantum / IBM Cloud account**.  
Set credentials as environment variables — **never hardcode them in source files**.

```bash
export QISKIT_IBM_TOKEN="<your-ibm-cloud-api-key>"
export QISKIT_IBM_INSTANCE="<your-crn-or-instance-id>"   # e.g. crn:v1:bluemix:...
```

Then run:

```bash
# Timing probe (small, uses a few QPU seconds)
make q0

# Full Q1–Q5 experiment suite  (budget ≤ 240 s QPU)
make q_series

# Dry run via AerSimulator (zero QPU seconds)
make q_series_dry
```

> **Note:** The default backend is `ibm_kingston` (Heron r2, 156 qubits).  
> Change it in `configs/hardware.yaml` or pass `--backend <name>` on the command line.

---

## Experiments at a glance

| ID | Script | What it measures |
|----|--------|-----------------|
| L00 | `l00_env.py` | Dependency versions, theory unit tests |
| L01 | `l01_ground_truth.py` | Exact peak probability (Aer statevector) |
| L02 | `l02_xeb_resolution.py` | XEB signal resolution vs shot count |
| L03 | `l03_contraction_cost.py` | Tensor-network contraction cost (M12 fit) |
| L04 | `l04_mps_barrier.py` | MPS fidelity vs T5 theoretical bound |
| L05 | `l05_zx_tcount.py` | ZX-calculus T-count reduction attack |
| L06 | `l06_marginal_peakfinder.py` | Local-marginal peak estimator (T6) |
| L07 | `l07_structure_detector.py` | Structure detector on control family C5a |
| L08 | `l08_beam_search.py` | Beam-search peak finder |
| L09 | `l09_severing.py` | Score-spoofing / severing attack |
| L10 | `l10_noisy_preflight.py` | Noisy Aer simulation preflight |
| L12 | `l12_hqap_geometry_cost.py` | Heavy-hex routing overhead |
| Q0 | `q0_probe.py` | IBM hardware timing calibration |
| Q1–Q5 | `q1_q5_hardware.py` | Full hardware suite (mirror baseline → n=40 peak) |

---

## Pre-registration

Hypotheses H1–H6 are listed in [`docs/preregistration.md`](docs/preregistration.md).  
Fill in the date and git hash **before** running any QPU jobs.

---

## Dependencies

Core: `qiskit ≥ 1.0`, `qiskit-aer`, `qiskit-ibm-runtime ≥ 0.20`, `numpy`, `scipy`, `pandas`,
`networkx`, `statsmodels`, `scikit-learn`, `stim ≥ 1.12`, `pyzx ≥ 0.7`.  
Optional (tensor-network cost): `quimb`, `cotengra`, `opt_einsum`, `kahypar`.

See [`requirements.txt`](requirements.txt) for pinned versions.

---

## Security note

This repository contains **no credentials**.  
IBM API keys and CRN instance IDs are read exclusively from the environment variables
`QISKIT_IBM_TOKEN` and `QISKIT_IBM_INSTANCE`.  
A `.gitignore` is provided to prevent accidental commit of `.env` files or `data/secret/`.
