"""DetectorRule refuses booleans, floats and non-finite values where it needs ints.

Counterexamples (review, 2026-09-29): `generation=True`, `half_life_runs=True`
and `affinity_score=nan` were accepted, because the checks used `isinstance`,
which treats `bool` as `int`, and never tested finiteness.
"""

from __future__ import annotations

import math

import pytest

from omega_engine_epistemic_immune_system.domain.value_objects import DetectorRule


def _rule(**overrides: object) -> DetectorRule:
    fields: dict[str, object] = {"rule_id": "r", "target_epitope": "e", "match_pattern": "x"}
    fields.update(overrides)
    return DetectorRule(**fields)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["generation", "half_life_runs", "runs_idle"])
@pytest.mark.parametrize("value", [True, False, 2.0])
def test_integer_fields_refuse_bool_and_float(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _rule(**{field: value})


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True, "1", -0.5])
def test_affinity_refuses_non_finite_bool_text_and_negative(value: object) -> None:
    with pytest.raises(ValueError):
        _rule(affinity_score=value)


def test_ordinary_values_are_accepted() -> None:
    rule = _rule(generation=2, half_life_runs=3, runs_idle=1, affinity_score=1.5)
    assert rule.generation == 2 and rule.affinity_score == 1.5
    assert _rule(affinity_score=0).affinity_score == 0
