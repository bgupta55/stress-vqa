"""
src/svqa/sim/cotengra_cost.py
Tensor-network contraction cost estimation (L03, M12).
"""
import math
import numpy as np

try:
    import quimb.tensor as qtn
    import cotengra as ctg
    HAS_COTENGRA = True
except ImportError:
    HAS_COTENGRA = False

try:
    import kahypar
    HAVE_KAHYPAR = True
except ImportError:
    HAVE_KAHYPAR = False


def cost_record(qc, budget_s: float, seed: int = 42) -> dict:
    """
    Estimate tensor-network contraction cost for a circuit amplitude.
    Returns dict with log10_cost, width, budget_s, optimizer.
    [VERIFY import/method names for your quimb/cotengra version]
    """
    if not HAS_COTENGRA:
        raise ImportError("quimb and cotengra are required for L03")

    from qiskit import qasm2 as _qasm2
    try:
        qasm_str = _qasm2.dumps(qc)
        circ = qtn.Circuit.from_openqasm2_str(qasm_str)
    except Exception as e:
        raise RuntimeError(f"Failed to convert circuit to quimb: {e}")

    target = "0" * qc.num_qubits
    tn_data = circ.amplitude_rehearse(b=target, simplify_sequence="ADCRS")
    tn = tn_data["tn"]

    methods = ["greedy", "kahypar"] if HAVE_KAHYPAR else ["greedy"]
    opt = ctg.HyperOptimizer(
        max_time=budget_s,
        minimize="flops",
        seed=seed,
        progbar=False,
        methods=methods,
    )
    tree = tn.contraction_tree(optimize=opt)
    log10_cost = math.log10(max(tree.contraction_cost(), 1.0))
    width = tree.contraction_width()
    return dict(
        log10_cost=log10_cost,
        log2_width=width,
        complex_ops=tree.contraction_cost(),
        machine_flops=8 * tree.contraction_cost(),
        budget_s=budget_s,
        optimizer=methods,
    )
