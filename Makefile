# stress-vqa Makefile

PYTHON=python3
PYTEST=pytest
SRC=src

.PHONY: install test smoke l00 l01 l02 l03 l04 l05 l06 l07 l08 l09 l10 q0_dry q0 q_series all_classical results clean

install:
	pip install -r requirements.txt

test:
	$(PYTEST) tests/ -v

smoke: test
	$(PYTHON) experiments/q0_dry_run.py --no-qpu

l00:
	$(PYTHON) experiments/l00_env.py

l01:
	$(PYTHON) experiments/l01_ground_truth.py

l02:
	$(PYTHON) experiments/l02_xeb_resolution.py

l03:
	$(PYTHON) experiments/l03_contraction_cost.py

l04:
	$(PYTHON) experiments/l04_mps_barrier.py

l05:
	$(PYTHON) experiments/l05_zx_tcount.py

l06:
	$(PYTHON) experiments/l06_marginal_peakfinder.py

l07:
	$(PYTHON) experiments/l07_structure_detector.py

l08:
	$(PYTHON) experiments/l08_beam_search.py

l09:
	$(PYTHON) experiments/l09_severing.py

l10:
	$(PYTHON) experiments/l10_noisy_preflight.py

q0_dry:
	$(PYTHON) experiments/q0_dry_run.py --no-qpu

q0:
	$(PYTHON) experiments/q0_probe.py

q_series:
	$(PYTHON) experiments/q1_q5_hardware.py

q_series_dry:
	$(PYTHON) experiments/q1_q5_hardware.py --dry-run

all_classical: l00 l01 l02 l03 l04 l05 l06 l07 l08 l09 l10

results:
	$(PYTHON) scripts/generate_results_md.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
