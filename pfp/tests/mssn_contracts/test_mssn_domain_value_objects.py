"""Focused unit, integration, security, and mutation-killing MSSN value tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib.util import find_spec
from pathlib import Path

import pytest

from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    ExactRationalMatrix,
)
from omega_engine_pfp.domain.mssn_research.grammar.lexical import (
    Alphabet,
    ProbabilityMass,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    ContentDigest,
    Rational,
    StageLevel,
    ValueParseCode,
)
from omega_engine_pfp.domain.mssn_research.grammar.entities import (
    TowerGrammar,
)


def test_domain_modules_are_cohesive_and_legacy_monolith_is_retired() -> None:
    grammar_root = Path(__file__).parents[2] / "domain" / "mssn_research" / "grammar"
    assert find_spec(
        "omega_engine_pfp.infrastructure.adapters.mssn_research.contracts.grammar.value_objects"
    ) is None
    assert all(len(path.read_text(encoding="utf-8").splitlines()) < 1_000 for path in grammar_root.glob("*.py"))


def test_rational_wire_parser_uses_typed_railway_results() -> None:
    admitted = Rational.parse_wire(" 2/4 ")
    refused = Rational.parse_wire("1/0")

    assert admitted == Ok(Rational(1, 2))
    assert isinstance(refused, Refusal)
    assert refused.refusal.code is ValueParseCode.FORMAT


def test_digest_parser_rejects_oversized_untrusted_input_without_reflection() -> None:
    attack = "a" * 100_000
    result = ContentDigest.parse_wire(attack)

    assert isinstance(result, Refusal)
    assert result.refusal.code is ValueParseCode.TOO_LONG
    assert attack not in result.refusal.message
    assert len(result.refusal.message) < 100


def test_digest_parser_preserves_normalized_serialized_schema() -> None:
    result = ContentDigest.parse_wire("AB" * 32)
    short = ContentDigest.parse_wire("a" * 63)

    assert isinstance(result, Ok)
    assert result.value.digest_hex == "ab" * 32
    assert isinstance(short, Refusal)
    assert short.refusal.code is ValueParseCode.FORMAT


def test_value_objects_remain_frozen_and_exactly_typed() -> None:
    alphabet = Alphabet.level_1()

    with pytest.raises(FrozenInstanceError):
        alphabet.stage_level = StageLevel(2)  # type: ignore[misc]
    assert alphabet != frozenset("01")


def test_matrix_equality_and_rational_wire_form_survive_relocation() -> None:
    left = ExactRationalMatrix.from_nested_fractions([[1, 2], [3, 4]])
    right = ExactRationalMatrix.from_nested_rationals(
        [[Rational(1, 1), Rational(2, 1)], [Rational(3, 1), Rational(4, 1)]]
    )

    assert left == right
    assert Rational(6, 8).to_wire() == "3/4"


def test_probability_upper_bound_assertion_kills_off_by_one_mutant() -> None:
    assert ProbabilityMass(Rational(1, 1)).is_one()
    with pytest.raises(ValueError, match="cannot exceed 1"):
        ProbabilityMass(Rational(2, 1))


def test_outward_grammar_adapter_consumes_canonical_domain_values() -> None:
    grammar = TowerGrammar.for_stage(StageLevel(2))

    assert type(grammar.alphabet) is Alphabet
    assert grammar.alphabet.stage_level == StageLevel(2)
