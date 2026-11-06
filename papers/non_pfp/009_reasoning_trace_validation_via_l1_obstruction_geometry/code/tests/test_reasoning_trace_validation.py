"""Unit tests for path-additive coboundary defect validation in reasoning traces."""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mod_reasoning_trace_validation_core import (  # noqa: E402
    STATUS_BUDGET_EXCEEDED,
    STATUS_CARRIER_FAILURE,
    STATUS_EXACT,
    STATUS_OBSTRUCTION,
    CarrierGraph,
    PathDefectAuditor,
    TraceValidator,
)


def test_linear_reasoning_trace_exact_repair():
    """Consistent linear reasoning chain repairs exactly with phi_1 = 0."""
    graph = CarrierGraph.create(["v0", "v1", "v2"], [("v0", "v1"), ("v1", "v2")])
    omega = {
        ("v0", "v1"): Fraction(2, 1),
        ("v1", "v2"): Fraction(-1, 1)
    }
    verdict = TraceValidator.validate_trace(graph, omega)
    assert verdict.status == STATUS_EXACT
    assert verdict.phi_1 == Fraction(0, 1)
    assert verdict.diagnostics["certified"] is True
    assert verdict.diagnostics["duality_gap"] == Fraction(0, 1)
    assert verdict.repair_potential["v0"] == Fraction(0, 1)
    assert verdict.repair_potential["v1"] == Fraction(2, 1)
    assert verdict.repair_potential["v2"] == Fraction(1, 1)


def test_exact_repair_survives_large_denominators():
    """A coboundary with denominators far above 1000 is decided exactly, not snapped to a false obstruction."""
    tree = CarrierGraph.create(["v0", "v1"], [("v0", "v1")])
    verdict = TraceValidator.validate_trace(tree, {("v0", "v1"): Fraction(1, 1001)})
    assert verdict.status == STATUS_EXACT
    assert verdict.phi_1 == Fraction(0)
    assert verdict.repair_potential["v1"] == Fraction(1, 1001)

    path = CarrierGraph.create(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("d", "c")])
    omega = {("a", "b"): Fraction(7, 12345), ("b", "c"): Fraction(-3, 99991), ("d", "c"): Fraction(5, 7)}
    verdict = TraceValidator.validate_trace(path, omega)
    assert verdict.status == STATUS_EXACT
    assert TraceValidator.coboundary_d0(path, verdict.repair_potential) == omega
    assert verdict.diagnostics["certified"] is True


def test_cyclic_inconsistent_trace_obstruction():
    """Unresolvable cycle in reasoning trace yields nonzero phi_1 and certified dual circulation."""
    graph = CarrierGraph.create(["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")])
    omega = {
        ("A", "B"): Fraction(1, 1),
        ("B", "C"): Fraction(1, 1),
        ("C", "A"): Fraction(1, 1)
    }
    verdict = TraceValidator.validate_trace(graph, omega)
    assert verdict.status == STATUS_OBSTRUCTION
    assert verdict.phi_1 == Fraction(3, 1)
    assert verdict.diagnostics["certified"] is True
    assert verdict.diagnostics["duality_gap"] == Fraction(0, 1)
    assert verdict.diagnostics["divergence_defect"] == Fraction(0, 1)
    assert verdict.diagnostics["is_circulation"] is True
    # Dual witness must be unit circulation
    assert verdict.dual_witness[("A", "B")] == Fraction(1, 1)
    assert verdict.dual_witness[("B", "C")] == Fraction(1, 1)
    assert verdict.dual_witness[("C", "A")] == Fraction(1, 1)
    # The exact potential realises the bound: residual mass 3 on exactly one edge.
    residual = {e: omega[e] - d for e, d in TraceValidator.coboundary_d0(graph, verdict.repair_potential).items()}
    assert TraceValidator.l1_norm(graph, residual) == Fraction(3)


def test_cycle_obstruction_with_large_denominators_is_certified_exactly():
    """phi_1 = 3/1001 on a unit cycle of 1/1001 defects, certified by an exact primal/dual pair."""
    graph = CarrierGraph.create(["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")])
    omega = {e: Fraction(1, 1001) for e in graph.edges}
    verdict = TraceValidator.validate_trace(graph, omega)
    assert verdict.status == STATUS_OBSTRUCTION
    assert verdict.phi_1 == Fraction(3, 1001)
    assert verdict.diagnostics["certified"] is True
    assert verdict.diagnostics["phi_1_lower_bound"] == Fraction(3, 1001)
    assert verdict.diagnostics["duality_gap"] == Fraction(0)
    assert TraceValidator.certify_dual(graph, omega, verdict.dual_witness) == Fraction(3, 1001)


def test_commuting_diamond_path_bound():
    """Reasoning diamond with mismatching branches yields noncommutativity bounded by path defect."""
    # diamond: A -> B -> D and A -> C -> D
    edges = [("A", "B"), ("B", "D"), ("A", "C"), ("C", "D")]
    graph = CarrierGraph.create(["A", "B", "C", "D"], edges)
    omega = {
        ("A", "B"): Fraction(1, 1),
        ("B", "D"): Fraction(1, 1),
        ("A", "C"): Fraction(1, 1),
        ("C", "D"): Fraction(3, 1),  # branch mismatch!
    }
    path_1 = [("A", "B"), ("B", "D")]
    path_2 = [("A", "C"), ("C", "D")]

    audit = PathDefectAuditor.audit_paths(omega, path_1, path_2)
    assert audit["path_a_defect"] == Fraction(2, 1)
    assert audit["path_b_defect"] == Fraction(4, 1)
    assert audit["noncommutativity_delta"] == Fraction(-2, 1)
    assert audit["abs_delta"] == Fraction(2, 1)
    assert audit["bound_satisfied"] is True

    verdict = TraceValidator.validate_trace(graph, omega)
    assert verdict.status == STATUS_OBSTRUCTION
    assert verdict.phi_1 == Fraction(2, 1)
    assert verdict.diagnostics["certified"] is True
    assert verdict.diagnostics["duality_gap"] == Fraction(0, 1)


def test_dual_certificate_rejects_non_circulations_and_box_violations():
    graph = CarrierGraph.create(["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")])
    omega = {e: Fraction(1) for e in graph.edges}
    not_circulation = {("A", "B"): Fraction(1), ("B", "C"): Fraction(0), ("C", "A"): Fraction(1)}
    assert TraceValidator.certify_dual(graph, omega, not_circulation) is None
    too_large = {e: Fraction(2) for e in graph.edges}
    assert TraceValidator.certify_dual(graph, omega, too_large) is None
    unit = {e: Fraction(1) for e in graph.edges}
    assert TraceValidator.certify_dual(graph, omega, unit) == Fraction(3)


def test_budget_exceeded_is_refused_not_partially_evaluated():
    graph = CarrierGraph.create(["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")])
    omega = {e: Fraction(1) for e in graph.edges}
    verdict = TraceValidator.validate_trace(graph, omega, step_budget=5)
    assert verdict.status == STATUS_BUDGET_EXCEEDED
    assert verdict.repair_potential is None
    assert verdict.diagnostics["carrier_size"] == 6
    assert TraceValidator.validate_trace(graph, omega, step_budget=6).status == STATUS_OBSTRUCTION


def test_carrier_failure_on_invalid_edges():
    """Edges referencing undeclared vertices trigger typed CarrierFailure."""
    graph = CarrierGraph.create(["A", "B"], [("A", "Z")])
    omega = {("A", "Z"): Fraction(1, 1)}
    verdict = TraceValidator.validate_trace(graph, omega)
    assert verdict.status == STATUS_CARRIER_FAILURE
    assert "undeclared" in verdict.diagnostics["error"]


def test_carrier_failure_on_inexact_values_duplicate_edges_and_unknown_edges():
    graph = CarrierGraph.create(["A", "B"], [("A", "B")])
    inexact = TraceValidator.validate_trace(graph, {("A", "B"): 0.5})  # type: ignore[dict-item]
    assert inexact.status == STATUS_CARRIER_FAILURE
    assert "exact rational" in inexact.diagnostics["error"]
    boolean = TraceValidator.validate_trace(graph, {("A", "B"): True})  # type: ignore[dict-item]
    assert boolean.status == STATUS_CARRIER_FAILURE
    unknown = TraceValidator.validate_trace(graph, {("B", "A"): Fraction(1)})
    assert unknown.status == STATUS_CARRIER_FAILURE
    assert "undeclared edge" in unknown.diagnostics["error"]
    duplicate = CarrierGraph.create(["A", "B"], [("A", "B"), ("A", "B")])
    assert TraceValidator.validate_trace(duplicate, {("A", "B"): Fraction(1)}).status == STATUS_CARRIER_FAILURE
