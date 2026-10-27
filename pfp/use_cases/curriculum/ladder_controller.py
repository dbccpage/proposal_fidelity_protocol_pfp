"""Ladder controller use case (U23).

Executes progressive curriculum evaluations along difficulty axes,
tracking failure frontiers and enforcing judge fixity invariants.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from pfp.domain.curriculum.models import (
    JudgeChangedError,
    LadderResult,
    LevelSummary,
)


class LadderController:
    """Controls multi-level ladder progressions against certified benchmarks."""

    def __init__(
        self,
        axis_name: str = "b1_cycle_rank",
        axis_values: Sequence[int] = (1, 2, 3, 4, 5),
        pass_threshold: int = 8,
        trials_per_level: int = 10,
    ) -> None:
        self.axis_name = axis_name
        self.axis_values = list(axis_values)
        self.pass_threshold = pass_threshold
        self.trials_per_level = trials_per_level

    def _extract_digest(self, checker: Any) -> str:
        if isinstance(checker, str):
            return checker
        if callable(checker):
            res = checker()
            if isinstance(res, str):
                return res
        if hasattr(checker, "checker_digest"):
            return str(checker.checker_digest)
        if hasattr(checker, "digest") and callable(checker.digest):
            return str(checker.digest())
        raise ValueError(f"Unable to extract checker digest from {checker!r}")

    def run_ladder(
        self,
        proposer: Callable[[int, int], bool] | Any,
        checker: Any,
        ladder_name: str = "cochain_repair_ladder",
    ) -> LadderResult:
        """Runs the ladder across configured axis values.

        Raises:
            JudgeChangedError: If checker digest changes mid-run.
        """
        initial_digest = self._extract_digest(checker)
        summaries: list[LevelSummary] = []
        frontier_axis_val: int | None = None
        all_passed = True

        for axis_val in self.axis_values:
            passes = 0
            for trial in range(self.trials_per_level):
                # Verify judge fixity invariant at every step
                current_digest = self._extract_digest(checker)
                if current_digest != initial_digest:
                    raise JudgeChangedError(
                        f"JUDGE_CHANGED: expected {initial_digest}, got {current_digest}"
                    )

                # Query proposer
                if callable(proposer):
                    success = bool(proposer(axis_val, trial))
                elif hasattr(proposer, "propose"):
                    success = bool(proposer.propose(axis_val, trial))
                else:
                    raise ValueError(f"Proposer {proposer!r} must be callable or have .propose()")

                if success:
                    passes += 1

            passed = passes >= self.pass_threshold
            rate_str = f"{passes}/{self.trials_per_level}"
            summaries.append(
                LevelSummary(
                    axis_value=axis_val,
                    trials=self.trials_per_level,
                    passes=passes,
                    pass_rate=rate_str,
                    passed=passed,
                )
            )

            if not passed:
                all_passed = False
                if frontier_axis_val is None:
                    frontier_axis_val = axis_val

        return LadderResult(
            ladder_name=ladder_name,
            axis_name=self.axis_name,
            checker_digest=initial_digest,
            frontier_axis_value=frontier_axis_val,
            level_summaries=summaries,
            all_passed=all_passed,
            authority_effect="None",
        )
