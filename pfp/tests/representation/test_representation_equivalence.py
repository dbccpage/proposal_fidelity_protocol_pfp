"""Test Representation Equivalence and Mutation Kill Gates (U25).

Asserts information completeness and exact round-trip preservation across
GlyphPacketRepresentation and PlainTextRepresentation.
Zero floating-point arithmetic.
AuthorityEffect: None.
"""
from __future__ import annotations

import json
import pytest

from pfp.domain.representation.models import TurnView
from pfp.infrastructure.adapters.representation.glyph_packet_representation import (
    GlyphPacketRepresentation,
)
from pfp.infrastructure.adapters.representation.plain_text_representation import (
    PlainTextRepresentation,
)


def _build_test_corpus() -> list[TurnView]:
    return [
        # Case 0: Minimal empty state
        TurnView(
            round_seq=0,
            phi1=0,
            gamma2=0,
            open_constraints=(),
            decided_values=(),
            refused_moves=(),
            prompt_regime="standard",
            authority_effect="None",
        ),
        # Case 1: Standard realistic Symbol Game turn
        TurnView(
            round_seq=5,
            phi1=2,
            gamma2=1,
            open_constraints=(
                ("chord_ab", "pi(b) - pi(a) = 4"),
                ("chord_bc", "pi(c) - pi(b) = -2"),
            ),
            decided_values=(
                ("a", 0),
                ("b", 4),
            ),
            refused_moves=(
                ("cut_k4_chord", "REPEATED_SETTLED_ASSERT"),
                ("cycle_retract", "CYCLE_OBSTRUCTION"),
            ),
            prompt_regime="hieroglyphic_ddc",
            authority_effect="None",
        ),
        # Case 2: Deep state with negative integers and multiple constraints
        TurnView(
            round_seq=42,
            phi1=10,
            gamma2=7,
            open_constraints=(
                ("span_1", "x1 + x2 - x3 = -100"),
                ("span_2", "x4 = 50"),
                ("span_3", "x5 - x1 = 0"),
            ),
            decided_values=(
                ("x1", -25),
                ("x2", -75),
                ("x3", 0),
                ("x4", 50),
            ),
            refused_moves=(
                ("move_alpha", "NON_DESCENT_STEP: phi1 increased"),
                ("move_beta", "STABILIZER_FAILURE: int_overflow"),
                ("move_gamma", "DANGER_QUARANTINE: signal_1_and_2"),
            ),
            prompt_regime="standard_rop",
            authority_effect="None",
        ),
    ]


def test_glyph_packet_round_trip_preservation() -> None:
    """Verify bidirectional round-trip parse(render(v)) == v for glyph packets."""
    adapter = GlyphPacketRepresentation()
    assert adapter.representation_id == "GLYPH_PACKET"

    for view in _build_test_corpus():
        rendered = adapter.render(view)
        assert isinstance(rendered, str)
        parsed = adapter.parse(rendered)
        assert parsed == view
        assert parsed.round_seq == view.round_seq
        assert parsed.phi1 == view.phi1
        assert parsed.gamma2 == view.gamma2
        assert parsed.open_constraints == view.open_constraints
        assert parsed.decided_values == view.decided_values
        assert parsed.refused_moves == view.refused_moves
        assert parsed.prompt_regime == view.prompt_regime
        assert parsed.authority_effect == "None"


def test_plain_text_round_trip_preservation() -> None:
    """Verify bidirectional round-trip parse(render(v)) == v for plain text."""
    adapter = PlainTextRepresentation()
    assert adapter.representation_id == "PLAIN_TEXT"

    for view in _build_test_corpus():
        rendered = adapter.render(view)
        assert isinstance(rendered, str)
        parsed = adapter.parse(rendered)
        assert parsed == view
        assert parsed.round_seq == view.round_seq
        assert parsed.phi1 == view.phi1
        assert parsed.gamma2 == view.gamma2
        assert parsed.open_constraints == view.open_constraints
        assert parsed.decided_values == view.decided_values
        assert parsed.refused_moves == view.refused_moves
        assert parsed.prompt_regime == view.prompt_regime
        assert parsed.authority_effect == "None"


def test_mutation_kill_gate_omit_refused_moves_plain_text() -> None:
    """Mutation Kill Gate (U25):

    Omission of refused_moves table in plain text renderer MUST turn round-trip RED.
    """
    view = _build_test_corpus()[1]
    assert len(view.refused_moves) > 0

    adapter = PlainTextRepresentation()
    valid_rendered = adapter.render(view)

    # Mutate by stripping out the refused moves section
    lines = valid_rendered.splitlines()
    mutated_lines: list[str] = []
    skip = False
    for line in lines:
        if line.startswith("## Refused Moves"):
            skip = True
            continue
        if skip and line.startswith("## "):
            skip = False
        if not skip:
            mutated_lines.append(line)

    mutated_rendered = "\n".join(mutated_lines)
    parsed_mutated = adapter.parse(mutated_rendered)

    # The mutated view must NOT equal original view
    assert parsed_mutated != view
    assert parsed_mutated.refused_moves == ()
    assert parsed_mutated.refused_moves != view.refused_moves


def test_glyph_packet_invalid_header_rejection() -> None:
    """Verify that corrupt or invalid packet header raises ValueError."""
    adapter = GlyphPacketRepresentation()
    view = _build_test_corpus()[0]
    payload = json.loads(adapter.render(view))
    payload["header"] = "INVALID_HEADER_V99"

    with pytest.raises(ValueError, match="Invalid glyph packet header"):
        adapter.parse(json.dumps(payload))
