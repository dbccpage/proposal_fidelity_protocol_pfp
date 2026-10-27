"""Unit tests for LadderController (U23).

Verifies failure frontier detection, fixed-judge invariant kill gates,
and replay deterministic stability.
AuthorityEffect: None.
"""

import pytest

from pfp.domain.curriculum.models import (
    JudgeChangedError,
)
from pfp.use_cases.curriculum.ladder_controller import (
    LadderController,
)

PINNED_CHECKER = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_ladder_detects_frontier() -> None:
    """Proposer succeeds for b1 < 4 and fails for b1 >= 4.

    Frontier should be identified exactly at b1 = 4.
    """
    controller = LadderController(
        axis_name="b1_cycle_rank",
        axis_values=[1, 2, 3, 4, 5],
        pass_threshold=8,
        trials_per_level=10,
    )

    def scripted_proposer(b1: int, _trial: int) -> bool:
        return b1 < 4

    result = controller.run_ladder(scripted_proposer, PINNED_CHECKER)

    assert result.frontier_axis_value == 4
    assert not result.all_passed
    assert result.authority_effect == "None"
    assert len(result.level_summaries) == 5

    # Check level summaries
    for summary in result.level_summaries:
        if summary.axis_value < 4:
            assert summary.passed is True
            assert summary.passes == 10
            assert summary.pass_rate == "10/10"
        else:
            assert summary.passed is False
            assert summary.passes == 0
            assert summary.pass_rate == "0/10"


def test_ladder_all_pass() -> None:
    """Proposer succeeds across all difficulty levels."""
    controller = LadderController(
        axis_name="b1_cycle_rank",
        axis_values=[1, 2, 3],
        pass_threshold=8,
        trials_per_level=10,
    )

    def perfect_proposer(_b1: int, _trial: int) -> bool:
        return True

    result = controller.run_ladder(perfect_proposer, PINNED_CHECKER)
    assert result.frontier_axis_value is None
    assert result.all_passed is True


def test_fixed_judge_invariant_detects_mid_run_change() -> None:
    """Mutating checker digest mid-run triggers JudgeChangedError."""
    controller = LadderController(
        axis_name="b1_cycle_rank",
        axis_values=[1, 2, 3],
        pass_threshold=8,
        trials_per_level=10,
    )

    step_counter = 0

    def dynamic_judge() -> str:
        nonlocal step_counter
        step_counter += 1
        # Change digest after 12 steps (during level 2)
        if step_counter > 12:
            return "sha256:mutated_digest_kill_gate"
        return PINNED_CHECKER

    with pytest.raises(JudgeChangedError, match="JUDGE_CHANGED"):
        controller.run_ladder(lambda _b, _t: True, dynamic_judge)


def test_deterministic_replay() -> None:
    """Identical runs yield identical LevelSummary tuples and digests."""
    controller = LadderController(
        axis_name="b1_cycle_rank",
        axis_values=[1, 2, 3],
        pass_threshold=5,
        trials_per_level=5,
    )

    def proposer(b1: int, trial: int) -> bool:
        return (b1 + trial) % 2 == 0

    res1 = controller.run_ladder(proposer, PINNED_CHECKER)
    res2 = controller.run_ladder(proposer, PINNED_CHECKER)

    assert res1.frontier_axis_value == res2.frontier_axis_value
    assert res1.all_passed == res2.all_passed
    assert res1.level_summaries == res2.level_summaries
