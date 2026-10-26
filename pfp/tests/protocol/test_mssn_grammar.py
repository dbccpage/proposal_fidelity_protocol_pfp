"""Tests for omega_engine_pfp.domain.tower.grammar against the real golden_corpus (Grammar
section 17's canonical test corpus, transcribed verbatim from the source doc).

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[2]


REPO_ROOT = _find_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_pfp.domain.tower import (
    golden_corpus,
    grammar,  # noqa: E402
)

# --- Obligation 1 (doc section 18): raw parsing is deterministic -----------


@pytest.mark.parametrize("text", golden_corpus.VALID)
def test_parsing_is_deterministic(text: str) -> None:
    assert grammar.parse(text) == grammar.parse(text)


# --- Obligation 2: serialize(parse(x)) is the identity on the AST ----------


@pytest.mark.parametrize("text", golden_corpus.VALID)
def test_valid_corpus_round_trips(text: str) -> None:
    packet = grammar.parse(text)
    assert grammar.serialize(packet) == text


@pytest.mark.parametrize("text", golden_corpus.CANONICAL_SEQUENCE)
def test_canonical_sequence_round_trips(text: str) -> None:
    assert grammar.serialize(grammar.parse(text)) == text


def test_deficit_receipt_fixture_round_trips() -> None:
    assert (
        grammar.serialize(grammar.parse(golden_corpus.DEFICIT_RECEIPT_2D))
        == golden_corpus.DEFICIT_RECEIPT_2D
    )


# --- Obligation 3: no invalid character is admitted ------------------------
# The first five INVALID entries are raw SYNTAX errors (comma, stray content,
# unwrapped child, unclosed application). The sixth is deliberately NOT a
# syntax error -- see test_sixth_invalid_entry_is_a_level_failure_not_a_syntax_failure
# below, and golden_corpus.INVALID's own docstring.

SYNTAX_INVALID = golden_corpus.INVALID[:5]
LEVEL_INVALID_TEXT, LEVEL_INVALID_DOC_REASON = golden_corpus.INVALID[5]


@pytest.mark.parametrize("text,doc_reason", SYNTAX_INVALID)
def test_syntax_invalid_entries_raise(text: str, doc_reason: str) -> None:
    with pytest.raises(grammar.GrammarError) as exc_info:
        grammar.parse(text)
    assert exc_info.value.reason
    assert doc_reason


def test_sixth_invalid_entry_is_a_level_failure_not_a_syntax_failure() -> None:
    """`op<<101><2><0><1><10>>` is syntactically LEGAL under Grammar --
    `2` is an ordinary Sigma36 atom word. What the source doc calls invalid
    ("inactive decimal glyph 2 in strict MSS1 data mode") is a semantic,
    level-activation fact, not a grammar fact. This is the precise reason
    `is_active_at_level` exists as a check separate from `parse`.
    """
    packet = grammar.parse(LEVEL_INVALID_TEXT)  # must NOT raise
    assert grammar.is_active_at_level(packet, level=1) is False


# --- Level activation: MSS-0 admits nothing but the bare genesis distinction


def test_genesis_diff_is_active_at_level_0() -> None:
    assert grammar.is_active_at_level(grammar.parse("<>"), level=0) is True


@pytest.mark.parametrize("text", golden_corpus.MSS0_FORBIDDEN)
def test_mss0_forbidden_imports_parse_but_are_inactive_at_level_0(text: str) -> None:
    assert text in golden_corpus.VALID
    packet = grammar.parse(text)  # must NOT raise
    assert grammar.is_active_at_level(packet, level=0) is False


@pytest.mark.parametrize("text", golden_corpus.VALID)
def test_full_valid_corpus_is_active_at_level_1(text: str) -> None:
    assert grammar.is_active_at_level(grammar.parse(text), level=1) is True


def test_level_activation_raises_for_an_undeclared_level() -> None:
    with pytest.raises(ValueError):
        grammar.is_active_at_level(grammar.parse("<>"), level=7)


# --- Atom construction hygiene ----------------------------------------------


def test_atom_rejects_empty_word() -> None:
    with pytest.raises(ValueError):
        grammar.Atom("")


def test_atom_rejects_out_of_alphabet_glyph() -> None:
    with pytest.raises(ValueError):
        grammar.Atom("a,b")


# --- Trailing content after the outer packet is rejected (parsing law 1) --


def test_trailing_content_after_outer_packet_is_rejected() -> None:
    with pytest.raises(grammar.GrammarError):
        grammar.parse("<><>")
