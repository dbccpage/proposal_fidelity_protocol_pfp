"""C032 regression tests: quartic fold for SU(2), SU(3), Sp(1) and the weight-system route.

Conventions: tr_R F^2 = A^R tr F^2 and tr_R F^4 = B^R tr F^4 + C^R (tr F^2)^2, with the
normalizations of V. Kumar, D. R. Morrison and W. Taylor, "Mapping 6D N=1 supergravities
to F-theory", JHEP 02 (2010) 099, arXiv:0911.3393. For SU(2), SU(3) and Sp(1) the
fundamental satisfies tr F^4 = 1/2 (tr F^2)^2, so B^R = 0 and C_fund = 1/2,
C_adj = 8 (SU(2), Sp(1)) or 9 (SU(3)). The values are re-derived here from weight
systems, not read from a table.

Counterexample named by these tests: the pre-fix table (C_fund = 0, C_adj = 6 for SU(2)
and SU(3); C_adj = 3 for Sp(1)) gives b.b = -2 for SU(2) with 10 fundamentals at T = 1,
so both checkers rejected the correct answer b.b = -1.
"""

from __future__ import annotations

import inspect
from fractions import Fraction

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers import (
    sugra_matrix_checker,
    weight_systems,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.reference_solver.solver import (
    solve,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.reference_solver.sugra_6d import (
    get_group_dim,
    get_group_lambda,
    get_rep_dim,
    get_trace_coefficients,
)

HALF = Fraction(1, 2)


@pytest.mark.parametrize(
    ("group", "rep", "expected"),
    [
        ("SU(2)", "fund", (Fraction(1), Fraction(0), HALF)),
        ("SU(2)", "adj", (Fraction(4), Fraction(0), Fraction(8))),
        ("SU(3)", "fund", (Fraction(1), Fraction(0), HALF)),
        ("SU(3)", "adj", (Fraction(6), Fraction(0), Fraction(9))),
        ("Sp(1)", "fund", (Fraction(1), Fraction(0), HALF)),
        ("Sp(1)", "adj", (Fraction(4), Fraction(0), Fraction(8))),
    ],
)
def test_quartic_trace_folded_into_c(
    group: str, rep: str, expected: tuple[Fraction, Fraction, Fraction]
) -> None:
    assert get_trace_coefficients(group, rep) == expected
    assert weight_systems.trace_coefficients(group, rep) == expected


def test_sp1_equals_su2_on_every_representation() -> None:
    for rep in ("fund", "adj"):
        assert get_trace_coefficients("Sp(1)", rep) == get_trace_coefficients("SU(2)", rep)


def _all_supported_pairs() -> list[tuple[str, str]]:
    pairs = []
    for group in sorted(weight_systems.SUPPORTED_GROUPS):
        reps = ["adj"] if group == "E8" else ["adj", "fund"]
        if group.startswith("SU("):
            reps += ["antisym", "sym"]
        elif group.startswith("SO("):
            reps += ["spinor"]
        elif group.startswith("Sp("):
            reps += ["antisym"]
        pairs += [(group, rep) for rep in reps]
    return pairs


@pytest.mark.parametrize(("group", "rep"), _all_supported_pairs())
def test_weight_route_agrees_with_reference_table(group: str, rep: str) -> None:
    """The reference table must equal the weight-system derivation on every supported pair."""
    assert weight_systems.trace_coefficients(group, rep) == get_trace_coefficients(group, rep)
    assert weight_systems.rep_dim(group, rep) == get_rep_dim(group, rep)
    assert weight_systems.group_dim(group) == get_group_dim(group)
    assert weight_systems.normalization_lambda(group) == get_group_lambda(group)


def test_quartic_casimir_existence_is_derived_not_listed() -> None:
    without = {
        g for g in weight_systems.SUPPORTED_GROUPS if not weight_systems.has_independent_quartic(g)
    }
    assert without == {"SU(2)", "SU(3)", "Sp(1)", "G2", "F4", "E6", "E7", "E8"}


def test_second_checker_does_not_import_reference_solver() -> None:
    source = inspect.getsource(sugra_matrix_checker)
    assert "reference_solver" not in source
    assert "reference_solver" not in inspect.getsource(weight_systems)


@pytest.mark.parametrize(
    ("group", "n_fund", "neutral"),
    [("SU(2)", 10, 227), ("SU(3)", 12, 216), ("Sp(1)", 10, 227)],
)
def test_minus_one_curve_models_at_t1(group: str, n_fund: int, neutral: int) -> None:
    """SU(2)+10 fund and SU(3)+12 fund at T=1 give b.b = -1 and a.b = -1.

    b.b = (1/3)(n C_fund - C_adj) = (1/3)(10/2 - 8) = -1 for SU(2), (1/3)(12/2 - 9) = -1 for SU(3);
    a.b = (1/6)(A_adj - n A_fund) = (4 - 10)/6 = -1 and (6 - 12)/6 = -1.
    """
    case = {
        "id": f"minus_one_{group}",
        "T": 1,
        "gauge_group": [group],
        "hypers": [{"multiplicity": n_fund, "reps": ["fund"]}],
        "neutral_hypers": neutral,
    }
    result = solve(case)
    assert result["verdict"] == "PASSES_NECESSARY_CONDITIONS"
    assert result["coefficients"] == {"a.a": "8", "a.b": ["-1"], "b.b": ["-1"]}
    dual = evaluate_dual(case, result)
    assert dual["verdict"] == "PASS" and dual["agreement"] is True, dual

    # The pre-fix answer (b.b = -2) must now be rejected by both checkers.
    stale = dict(result)
    stale["coefficients"] = {"a.a": "8", "a.b": ["-1"], "b.b": ["-2"]}
    dual_stale = evaluate_dual(case, stale)
    assert dual_stale["checker1"]["passed"] is False
    assert dual_stale["checker2"]["passed"] is False


def test_weight_route_rejects_unsupported_representation() -> None:
    with pytest.raises(weight_systems.WeightDerivationError):
        weight_systems.trace_coefficients("E8", "fund")
    with pytest.raises(weight_systems.WeightDerivationError):
        weight_systems.trace_coefficients("SO(8)", "fund")
