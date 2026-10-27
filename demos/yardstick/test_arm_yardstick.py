"""The yardstick's statistics on hand-computed cases.

Ported from an internal test suite. Two source files are merged here: the
yardstick statistics tests and the schedule-learning tests that build on the
same module. AuthorityEffect: None.
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest

from arm_yardstick import (
    SeatContribution,
    Trial,
    distance_to_reference,
    mcnemar_exact,
    operad_retirement_audit,
    operad_yield_per_dollar,
    pareto_frontier,
    promote_candidate_operand,
    record_schedule_telemetry,
    seat_value,
    summarize,
    thompson_sampling_schedule,
    wilson_interval,
)


def trial(arm, task, ok, cost="0.1", wall=10.0, tokens=100):
    return Trial(arm=arm, task=task, success=ok, cost_usd=Decimal(cost), wall_seconds=wall, tokens=tokens)


# --- Arm statistics -------------------------------------------------------


@pytest.mark.parametrize("wins,n,low,high", [(0, 10, 0.0, 0.2775), (10, 10, 0.7225, 1.0),
                                             (5, 10, 0.2366, 0.7634), (1, 1, 0.2065, 1.0)])
def test_wilson_matches_published_values(wins, n, low, high):
    lo, hi = wilson_interval(wins, n)
    assert math.isclose(lo, low, abs_tol=1e-4) and math.isclose(hi, high, abs_tol=1e-4)


@pytest.mark.parametrize("bad", [(-1, 3), (4, 3), (True, 3)])
def test_wilson_refuses_impossible_counts(bad):
    with pytest.raises(ValueError, match="WILSON_COUNTS_INVALID"):
        wilson_interval(*bad)


def test_summary_reports_cost_and_time_per_correct_answer():
    stats = summarize([trial("a", "t1", True, "0.30", 10), trial("a", "t2", False, "0.10", 30)])["a"]
    assert (stats.trials, stats.successes, stats.rate) == (2, 1, 0.5)
    assert stats.mean_cost_usd == Decimal("0.20") and stats.cost_per_success_usd == Decimal("0.40")
    assert stats.median_wall_seconds == 20 and stats.wall_per_success_seconds == 40
    assert summarize([trial("z", "t", False)])["z"].cost_per_success_usd is None


def test_mcnemar_exact_on_discordant_pairs():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(0, 5) == pytest.approx(0.0625)
    assert mcnemar_exact(3, 3) == 1.0
    assert mcnemar_exact(1, 9) == pytest.approx(2 * (1 + 10) / 1024)


def test_distance_uses_only_tasks_both_arms_ran():
    trials = [trial("w", "t1", True, "1.0", 100), trial("w", "t2", False, "1.0", 100),
              trial("ref", "t1", True, "0.1", 10), trial("ref", "t2", True, "0.1", 10),
              trial("ref", "t3", True, "0.1", 10)]
    gap = distance_to_reference(trials, "w", "ref")
    assert gap["shared_tasks"] == 2 and gap["rate_difference"] == -0.5
    assert (gap["only_arm_correct"], gap["only_reference_correct"]) == (0, 1)
    assert gap["cost_ratio"] == 10.0 and gap["wall_ratio"] == 10.0
    assert distance_to_reference(trials, "w", "missing")["shared_tasks"] == 0


def test_distance_pairs_every_repeat_not_only_the_first():
    trials = [trial("w", "t", ok) for ok in (True, True, True)] + [trial("ref", "t", ok) for ok in (False, False, True)]
    gap = distance_to_reference(trials, "w", "ref")
    assert gap["pairs"] == 3 and (gap["only_arm_correct"], gap["only_reference_correct"]) == (2, 0)
    assert gap["rate_difference"] == round(1 - 1 / 3, 4)


def test_pareto_keeps_only_undominated_arms():
    stats = summarize([trial("cheap", "t", True, "0.01", 5), trial("dear", "t", True, "1.0", 50),
                       trial("wrong", "t", False, "0.001", 1)])
    assert pareto_frontier(stats) == ["cheap", "wrong"]


# --- Seat value -------------------------------------------------------------


def test_seat_value_credits_only_findings_no_other_seat_raised():
    run = [SeatContribution("a", "review", ("Off by one", "Missing case"), Decimal("0.02")),
           SeatContribution("b", "review", ("off by one ",), Decimal("0.03")),
           SeatContribution("c", "review", (), Decimal("0.05"))]
    rows = {row["role_id"]: row for row in seat_value([run])}
    assert rows["a"]["unique_findings"] == 1 and rows["a"]["findings"] == 2
    assert rows["b"]["unique_findings"] == 0 and rows["c"]["cost_per_unique_finding_usd"] is None
    assert rows["a"]["cost_per_unique_finding_usd"] == "0.020000"


def test_seat_value_counts_a_repeated_finding_once_per_seat_and_run():
    run = [SeatContribution("defect_hunter", "review", ("Off by one",), Decimal("0.01")),
           SeatContribution("defect_hunter", "learning_review", ("off by one",), Decimal("0.01"))]
    row = seat_value([run])[0]
    assert (row["calls"], row["findings"], row["unique_findings"]) == (2, 1, 1)


# --- Schedule learning built on the yardstick -------------------------------


def test_record_schedule_telemetry_captures_seat_value_and_obstructions():
    contributions = [
        SeatContribution(
            role_id="boundary_fuzzer",
            phase="review",
            findings=("defect_a", "defect_b"),
            cost_usd=Decimal("0.004"),
        ),
        SeatContribution(
            role_id="overconfidence_probe",
            phase="review",
            findings=("defect_b",),
            cost_usd=Decimal("0.002"),
        ),
    ]
    rec = record_schedule_telemetry(
        run_id="run-001",
        schedule="quorum3",
        contributions=contributions,
        resolved_obstructions=("OBST_BOUNDARY_01",),
    )
    assert rec["run_id"] == "run-001"
    assert rec["schedule"] == "quorum3"
    assert rec["total_cost_usd"] == "0.006000"
    assert rec["resolved_obstructions"] == ["OBST_BOUNDARY_01"]
    fuzzer = next(r for r in rec["seat_value"] if r["role_id"] == "boundary_fuzzer")
    assert fuzzer["unique_findings"] == 1


def test_thompson_sampling_selects_high_correctness_per_cost_schedule():
    schedules = ("quorum3", "core", "full_blind")
    history = {
        "quorum3": {"successes": 48, "failures": 2, "mean_cost_usd": 0.05},
        "core": {"successes": 8, "failures": 35, "mean_cost_usd": 0.04},
        "full_blind": {"successes": 45, "failures": 5, "mean_cost_usd": 0.45},
    }
    assert thompson_sampling_schedule(schedules, history, random_seed=42) == "quorum3"

    with pytest.raises(ValueError, match="SCHEDULE_CANDIDATES_EMPTY"):
        thompson_sampling_schedule((), history)


def test_promote_candidate_operand_gates_on_yardstick_delta():
    candidate = {"operand_id": "op_quorum_repair", "composition": ["defect_hunter", "boundary_fuzzer"]}
    promoted = promote_candidate_operand(
        candidate, baseline_yield=0.50, trial_yield=0.58, threshold_delta=0.05
    )
    assert promoted["promoted"] is True
    assert promoted["disposition"] == "ADMITTED_OPERAND"

    retained = promote_candidate_operand(
        candidate, baseline_yield=0.50, trial_yield=0.52, threshold_delta=0.05
    )
    assert retained["promoted"] is False
    assert retained["disposition"] == "RETAINED_CANDIDATE"


def test_operad_yield_per_dollar_and_retirement_audit():
    assert operad_yield_per_dollar(4, Decimal("0.02")) == Decimal("200")
    assert operad_yield_per_dollar(4, Decimal("0")) == Decimal("0")

    with pytest.raises(ValueError, match="OPERAD_YIELD_COUNTS_INVALID"):
        operad_yield_per_dollar(True, Decimal("0.01"))

    active, retired = operad_retirement_audit(
        [
            {"operad_id": "op_useful", "eval_runs": 5, "yield_per_dollar": Decimal("120")},
            {"operad_id": "op_unused", "eval_runs": 4, "yield_per_dollar": Decimal("0")},
            {"operad_id": "op_new", "eval_runs": 1, "yield_per_dollar": Decimal("0")},
        ],
        min_evaluation_runs=3,
    )
    assert active == ["op_useful", "op_new"]
    assert retired == ["op_unused"]
