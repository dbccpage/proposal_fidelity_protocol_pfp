"""Tests for Symbol Game Domain Value Objects and Clean Architecture Invariants.

Enforces:
1. Exact-type equality invariant: type(self) is type(other) in __eq__
2. Composite __hash__ implementation
3. Invariant validation guards
4. Zero infrastructure imports in use_cases/
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import re
import pytest

from pfp.domain.models import (
    AuthorityEffect,
    ObstructionScore,
    ProblemReductionResult,
    StepVerdict,
    SymbolGameEnvelope,
    SymbolGameStepOutcome,
    SymbolToken,
)
from pfp.domain.exceptions import ForbiddenAuthorityError


@dataclass(frozen=True)
class MockOtherType:
    token_id: str
    symbol_text: str
    dimension_weight: float = 1.0


def test_symbol_token_exact_type_equality_and_hash():
    t1 = SymbolToken(token_id="tok1", symbol_text="x", dimension_weight=1.0)
    t2 = SymbolToken(token_id="tok1", symbol_text="x", dimension_weight=1.0)
    mock = MockOtherType(token_id="tok1", symbol_text="x", dimension_weight=1.0)

    assert t1 == t2
    assert hash(t1) == hash(t2)
    # Rejects cross-class comparison
    assert t1 != mock
    assert not (t1 == mock)


def test_symbol_token_validation():
    with pytest.raises(ValueError, match="token_id"):
        SymbolToken(token_id="", symbol_text="x")

    with pytest.raises(TypeError, match="symbol_text"):
        SymbolToken(token_id="t1", symbol_text=123)  # type: ignore

    with pytest.raises(ValueError, match="dimension_weight"):
        SymbolToken(token_id="t1", symbol_text="x", dimension_weight=-0.5)


def test_symbol_game_envelope_exact_type_equality_and_hash():
    e1 = SymbolGameEnvelope(task_id="t1", initial_input="input1")
    e2 = SymbolGameEnvelope(task_id="t1", initial_input="input1")
    
    @dataclass(frozen=True)
    class EnvelopeImposter:
        task_id: str
        initial_input: str
        sparse_dimension: int = 28
        constraints: tuple = ()
        authority_effect: AuthorityEffect = AuthorityEffect.NONE

    imposter = EnvelopeImposter(task_id="t1", initial_input="input1")
    assert e1 == e2
    assert hash(e1) == hash(e2)
    assert e1 != imposter


def test_symbol_game_envelope_validation():
    with pytest.raises(ValueError, match="task_id"):
        SymbolGameEnvelope(task_id="", initial_input="input")

    with pytest.raises(ForbiddenAuthorityError):
        SymbolGameEnvelope(task_id="t1", initial_input="input", authority_effect="Autonomous")


def test_symbol_game_step_outcome_verdict_and_exact_type():
    o1 = SymbolGameStepOutcome(
        step_id="s1",
        purity=Fraction(9, 10),
        l1_obstruction=Fraction(1, 10),
        is_exact=False,
        verdict=StepVerdict.SELECT,
        evidence_sha256="abc",
    )
    o2 = SymbolGameStepOutcome(
        step_id="s1",
        purity=Fraction(9, 10),
        l1_obstruction=Fraction(1, 10),
        is_exact=False,
        verdict="SELECT",  # string coercion
        evidence_sha256="abc",
    )
    assert o1 == o2
    assert hash(o1) == hash(o2)
    assert o1.verdict == StepVerdict.SELECT

    @dataclass(frozen=True)
    class OutcomeImposter:
        step_id: str
        purity: Fraction
        l1_obstruction: Fraction
        is_exact: bool
        verdict: StepVerdict
        evidence_sha256: str
        authority_effect: AuthorityEffect = AuthorityEffect.NONE

    imposter = OutcomeImposter(
        step_id="s1",
        purity=Fraction(9, 10),
        l1_obstruction=Fraction(1, 10),
        is_exact=False,
        verdict=StepVerdict.SELECT,
        evidence_sha256="abc",
    )
    assert o1 != imposter


def test_obstruction_score_properties_and_strict_descent():
    score1 = ObstructionScore(gamma_2=Fraction(1, 2), phi_1=Fraction(4, 5), active_count=3)
    score2 = ObstructionScore(gamma_2=Fraction(1, 2), phi_1=Fraction(4, 5), active_count=3)
    improved = ObstructionScore(gamma_2=Fraction(3, 10), phi_1=Fraction(2, 5), active_count=1)
    exact = ObstructionScore(gamma_2=Fraction(0), phi_1=Fraction(0), active_count=0)

    assert score1 == score2
    assert hash(score1) == hash(score2)
    assert not score1.is_exact
    assert exact.is_exact

    assert improved.strictly_improves(score1)
    assert not score1.strictly_improves(improved)

    # Inward exact-type guard in strictly_improves
    with pytest.raises(TypeError):
        improved.strictly_improves("not_a_score")  # type: ignore


def test_problem_reduction_result_value_object():
    score = ObstructionScore(gamma_2=Fraction(0), phi_1=Fraction(0), active_count=0)
    r1 = ProblemReductionResult(
        task_id="t1",
        status="PASSED",
        steps_executed=2,
        final_score=score,
        is_resolved=True,
        artifacts={"steps": 2},
    )
    r2 = ProblemReductionResult(
        task_id="t1",
        status="PASSED",
        steps_executed=2,
        final_score=score,
        is_resolved=True,
        artifacts={"steps": 2},
    )
    assert r1 == r2
    assert hash(r1) == hash(r2)
    assert r1.artifacts["steps"] == 2

    # Cross-class check
    @dataclass(frozen=True)
    class ReductionImposter:
        task_id: str
        status: str
        steps_executed: int
        final_score: ObstructionScore
        is_resolved: bool
        artifacts: dict
        authority_effect: AuthorityEffect = AuthorityEffect.NONE

    imposter = ReductionImposter(
        task_id="t1",
        status="PASSED",
        steps_executed=2,
        final_score=score,
        is_resolved=True,
        artifacts={"steps": 2},
    )
    assert r1 != imposter


def test_clean_architecture_use_cases_zero_infrastructure_imports():
    """Verify that use_cases/ has zero dependencies on infrastructure/."""
    use_cases_dir = Path(__file__).resolve().parent.parent / "use_cases"
    py_files = list(use_cases_dir.glob("**/*.py"))
    assert len(py_files) > 0, "No use case files found to scan"

    infra_import_pattern = re.compile(r"^\s*(from|import)\s+.*infrastructure.*", re.MULTILINE)

    violations = []
    for f in py_files:
        content = f.read_text(encoding="utf-8")
        matches = infra_import_pattern.findall(content)
        if matches:
            violations.append(f"{f.name}: {matches}")

    assert not violations, f"Clean Architecture inward dependency violation: {violations}"
