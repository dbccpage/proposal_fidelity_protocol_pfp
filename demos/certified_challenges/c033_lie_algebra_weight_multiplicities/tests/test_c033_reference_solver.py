"""Tests for C033 Reference Solver and Lie Algebra Kernel.

AuthorityEffect: None.
"""

from __future__ import annotations

from c033_lie_algebra_weight_multiplicities.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
    DDCTracer,
)
from c033_lie_algebra_weight_multiplicities.reference_solver.lie_algebra import (
    freudenthal_multiplicities,
    tensor_product_decomposition,
    weyl_dimension,
    weyl_orbit_size,
)


def test_weyl_dimension_classical_benchmarks():
    """Validates Weyl dimension formula on classical representations."""
    # A1
    assert weyl_dimension("A1", [1]) == 2
    assert weyl_dimension("A1", [2]) == 3
    # A2
    assert weyl_dimension("A2", [1, 0]) == 3
    assert weyl_dimension("A2", [0, 1]) == 3
    assert weyl_dimension("A2", [1, 1]) == 8
    # B2 (C2)
    assert weyl_dimension("B2", [1, 0]) == 5  # vector
    assert weyl_dimension("B2", [0, 1]) == 4  # spinor
    # G2
    assert weyl_dimension("G2", [1, 0]) == 7
    assert weyl_dimension("G2", [0, 1]) == 14
    # F4
    assert weyl_dimension("F4", [0, 0, 0, 1]) == 26
    assert weyl_dimension("F4", [1, 0, 0, 0]) == 52


def test_weyl_orbit_sizes_and_stabilizers():
    """Validates Weyl orbit size calculations across parabolic stabilizers."""
    # A2: generic [1, 1] has size 6; [1, 0] has size 3; [0, 0] has size 1
    assert weyl_orbit_size("A2", [1, 1]) == 6
    assert weyl_orbit_size("A2", [1, 0]) == 3
    assert weyl_orbit_size("A2", [0, 0]) == 1

    # G2: generic [1, 1] has size 12; [1, 0] has size 6; [0, 1] has size 6; [0, 0] has size 1
    assert weyl_orbit_size("G2", [1, 1]) == 12
    assert weyl_orbit_size("G2", [1, 0]) == 6
    assert weyl_orbit_size("G2", [0, 1]) == 6
    assert weyl_orbit_size("G2", [0, 0]) == 1


def test_freudenthal_multiplicities_and_orbit_sum():
    """Validates Freudenthal recursion and asserts exact agreement with Weyl dimension."""
    # A2 adjoint [1, 1]
    mults = freudenthal_multiplicities("A2", [1, 1])
    assert mults == {(1, 1): 1, (0, 0): 2}
    total_dim = sum(m * weyl_orbit_size("A2", w) for w, m in mults.items())
    assert total_dim == 8

    # G2 fundamental [1, 0] (7)
    mults_g2 = freudenthal_multiplicities("G2", [1, 0])
    assert mults_g2 == {(1, 0): 1, (0, 0): 1}
    total_dim_g2 = sum(m * weyl_orbit_size("G2", w) for w, m in mults_g2.items())
    assert total_dim_g2 == 7


def test_tensor_product_decompositions():
    """Validates tensor product decompositions via Brauer-Klimyk."""
    # A2: 3 x 3bar = 8 + 1
    t1 = tensor_product_decomposition("A2", [1, 0], [0, 1])
    assert t1 == {(1, 1): 1, (0, 0): 1}

    # A2: 3 x 3 = 6 + 3bar
    t2 = tensor_product_decomposition("A2", [1, 0], [1, 0])
    assert t2 == {(2, 0): 1, (0, 1): 1}

    # G2: 7 x 7 = 1 + 7 + 14 + 27
    t3 = tensor_product_decomposition("G2", [1, 0], [1, 0])
    assert t3 == {(2, 0): 1, (0, 1): 1, (1, 0): 1, (0, 0): 1}


def test_solver_ddc_tracer_receipt_chaining():
    """Validates DDC 8-letter operational tracer step chaining."""
    tracer = DDCTracer()
    tracer.record_step("C", {"action": "case_intake"})
    tracer.record_step("D", {"action": "reflect_chamber"})
    tracer.record_step("I", {"action": "integrate_multiplicities"})
    tracer.record_step("R", {"action": "dimension_residual"})
    tracer.record_step("E", {"action": "exact_enclosure"})
    tracer.record_step("T", {"action": "terminal_verdict"})

    exp = tracer.export_trace()
    assert exp["step_count"] == 6
    assert all(l in VALID_DDC_LETTERS for l in exp["letters"])
    assert len(exp["final_digest"]) == 64
