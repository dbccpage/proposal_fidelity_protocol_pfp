"""Legacy threshold examples retained with Companion 007.

Every duration, metric, and execution status below is a supplied value. These
examples check chosen thresholds and count supplied status fields. They are not
measurements of attention or learning, and they do not execute any notebook.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

# --- Legacy toy models (supplied values only) ---


@dataclass(frozen=True)
class MicroAttentionPulse:
    pulse_index: int
    duration_minutes: Fraction
    concept_id: str
    target_tier: str  # 'tangible', 'algorithmic', 'undergraduate', 'research'

    def is_within_half_life(self, max_half_life: Fraction = Fraction(5, 1)) -> bool:
        """Check a supplied duration against a chosen 3-to-5-minute window."""
        return self.duration_minutes <= max_half_life and self.duration_minutes >= Fraction(3, 1)


@dataclass(frozen=True)
class LearningCheckMetrics:
    diagnostic_pass_rate: Fraction  # supplied value, not a measurement
    transfer_index: Fraction  # supplied value, not a measurement
    teaching_efficiency: Fraction  # supplied value, not a measurement

    def meets_certification_standards(self) -> bool:
        """Compare supplied values with chosen thresholds 9/10, 17/20, and 4/5."""
        return (
            self.diagnostic_pass_rate >= Fraction(9, 10)
            and self.transfer_index >= Fraction(17, 20)
            and self.teaching_efficiency >= Fraction(4, 5)
        )


def evaluate_headless_notebook_grade(cells: list[dict[str, Any]]) -> Fraction:
    """Count supplied 'ok' statuses among code cells that contain an assert."""
    if not cells:
        return Fraction(0, 1)
    passed_cells = 0
    total_eval_cells = 0
    for c in cells:
        if c.get("cell_type") == "code" and "assert" in c.get("source", ""):
            total_eval_cells += 1
            if c.get("execution_status") == "ok":
                passed_cells += 1
    if total_eval_cells == 0:
        return Fraction(0, 1)
    return Fraction(passed_cells, total_eval_cells)


# --- Tests of the legacy toy models ---


def test_micro_attention_pulse_half_life():
    valid_pulse = MicroAttentionPulse(
        pulse_index=1,
        duration_minutes=Fraction(4, 1),
        concept_id="c01_discrete_difference",
        target_tier="tangible",
    )
    assert valid_pulse.is_within_half_life()

    too_long = MicroAttentionPulse(
        pulse_index=2,
        duration_minutes=Fraction(7, 1),
        concept_id="c02_cycle_defect",
        target_tier="algorithmic",
    )
    assert not too_long.is_within_half_life()


def test_learning_metrics_threshold():
    passing_metrics = LearningCheckMetrics(
        diagnostic_pass_rate=Fraction(92, 100),
        transfer_index=Fraction(88, 100),
        teaching_efficiency=Fraction(85, 100),
    )
    assert passing_metrics.meets_certification_standards()

    failing_metrics = LearningCheckMetrics(
        diagnostic_pass_rate=Fraction(85, 100),  # below the chosen 9/10
        transfer_index=Fraction(88, 100),
        teaching_efficiency=Fraction(85, 100),
    )
    assert not failing_metrics.meets_certification_standards()


def test_headless_notebook_automated_grading():
    cells = [
        {"cell_type": "markdown", "source": "# Lesson 1"},
        {"cell_type": "code", "source": "x = 10\nassert x == 10", "execution_status": "ok"},
        {"cell_type": "code", "source": "y = 20\nassert y == 20", "execution_status": "ok"},
        {"cell_type": "code", "source": "z = 30\nassert z == 40", "execution_status": "error"},
    ]
    grade = evaluate_headless_notebook_grade(cells)
    assert grade == Fraction(2, 3)
