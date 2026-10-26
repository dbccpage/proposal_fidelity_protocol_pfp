"""Regressions preventing a local challenge script from impersonating the city execution."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.swarm.budget_controller import (
    BudgetController,
    BudgetExhaustedRefusal,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.swarm.cohomology_solver import (
    CohomologySolver,
    verify_independent_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.swarm.lggr_detector import (
    LggrDetector,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.swarm.woland_overseer import (
    WolandCohomologyOverseer,
)


class RefusingPort:
    def __init__(self):
        self.calls = []
        self.result = {
            "status": "UNKNOWN",
            "refusal": "NATIVE_OPERATION_UNAVAILABLE",
            "detail": {"evidence": "retained"},
        }

    def solve(self, case):
        self.calls.append(case)
        return self.result


def test_legacy_c011_facade_keeps_native_refusal():
    port = RefusingPort()
    certificate = CohomologySolver(solver=port).solve({"nodes": []})
    assert port.calls == [{"nodes": [], "challenge": "c011"}]
    assert certificate.to_canonical_dict() == port.result
    assert certificate.status == "UNKNOWN"
    assert certificate.native_verified is False
    assert certificate.independent_verified is False


def test_direct_host_does_not_create_second_execution_path():
    class Host:
        def __getattr__(self, name):
            raise AssertionError("No direct native execution from the legacy front end")

    cert = CohomologySolver(host=Host()).solve({"nodes": []})
    assert cert.status == "UNKNOWN"
    assert cert.to_canonical_dict()["refusal"] == "EXECUTION_UNAVAILABLE"


def test_overseer_refuses_without_emitting_fake_acts_or_receipts(tmp_path):
    overseer = WolandCohomologyOverseer(tmp_path)
    result = overseer.execute_challenge("c011", {"nodes": []}, task_key="test")
    assert result.verdict == "REFUSE"
    assert result.refusal == "WOLAND_EXECUTION_UNAVAILABLE"
    assert result.receipt_sha256 is None
    assert result.certificate is None
    assert result.billed_cost_usd is None
    assert list(tmp_path.iterdir()) == []


def test_battery_never_promotes_unexecuted_cases(tmp_path):
    result = WolandCohomologyOverseer(tmp_path).execute_battery([{"id": "a"}, {"id": "b"}])
    assert result.total_cases == 2
    assert result.passed_cases == 0
    assert result.verdict == "REFUSE"
    assert all(case["refusal"] == "WOLAND_EXECUTION_UNAVAILABLE" for case in result.case_results)
    assert list(tmp_path.iterdir()) == []


def test_missing_lggr_execution_does_not_guess_phi_or_cycle_rank():
    result = LggrDetector().evaluate(["u", "v"], [("u", "v"), ("v", "u")], {}, phi1=Fraction(0))
    assert result.status == "UNKNOWN"
    assert result.is_local_green is None
    assert result.is_global_red is None
    assert result.phi1 is None
    assert result.cycle_rank is None
    assert result.ddc_rune is None


def test_budget_controller_thresholds_and_accounting():
    """Verify BudgetController enforces < $0.05 target and <= $0.25 ceiling."""
    ctrl = BudgetController()
    assert ctrl.is_within_target() is True

    # Nominal micro-charge
    ctrl.charge("op1", "test_solver", 100, 50, Decimal("0.0001"), Decimal("0.0002"))
    assert ctrl.total_cost < Decimal("0.05")
    assert ctrl.is_within_target() is True

    # Exceed hard ceiling should raise refusal
    with pytest.raises(BudgetExhaustedRefusal):
        ctrl.charge("op_huge", "expensive", 1_000_000, 1_000_000, Decimal("1.0"), Decimal("1.0"))

    # Test accounting export
    acc = ctrl.to_accounting_dict()
    assert acc["schema_version"] == "omega.accounting.v1"
    assert acc["hard_ceiling_usd"] == "0.25"
    assert acc["target_ceiling_usd"] == "0.05"


def test_checker_mutation_suite_rejects_corrupted_certificates():
    """Verify independent checker detects and rejects corrupted certificates."""
    nodes = ["a", "b", "c"]
    edges = [("a", "b"), ("b", "c"), ("a", "c")]
    claims = {("a", "b"): Fraction(2), ("b", "c"): Fraction(3), ("a", "c"): Fraction(5)}
    weights = {("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("a", "c"): Fraction(1)}

    potential = {"a": Fraction(0), "b": Fraction(2), "c": Fraction(5)}
    repair = {"a->b": Fraction(0), "b->c": Fraction(0), "a->c": Fraction(0)}
    dual = {"a->b": Fraction(0), "b->c": Fraction(0), "a->c": Fraction(0)}
    phi1 = Fraction(0)

    # Valid
    ok, gap = verify_independent_certificate(
        nodes, edges, claims, weights, potential, repair, dual, phi1
    )
    assert ok is True
    assert gap == Fraction(0)

    # Mutation 1: Potential off by one
    bad_pot = {"a": Fraction(0), "b": Fraction(3), "c": Fraction(5)}
    ok_mut1, _ = verify_independent_certificate(
        nodes, edges, claims, weights, bad_pot, repair, dual, phi1
    )
    assert ok_mut1 is False

    # Mutation 2: Dual unbounded (|y_e| > w_e)
    bad_dual = {"a->b": Fraction(2), "b->c": Fraction(0), "a->c": Fraction(0)}
    ok_mut2, _ = verify_independent_certificate(
        nodes, edges, claims, weights, potential, repair, bad_dual, phi1
    )
    assert ok_mut2 is False

    # Mutation 3: Non-circulation dual (net flow at vertex != 0)
    bad_circ = {"a->b": Fraction(1), "b->c": Fraction(0), "a->c": Fraction(0)}
    ok_mut3, _ = verify_independent_certificate(
        nodes, edges, claims, weights, potential, repair, bad_circ, phi1
    )
    assert ok_mut3 is False
