"""Public-owner controls for the PDF's omitted active-constraint witness.

The protected-query comparison is explicit and test-local. The representation
validator establishes wire/binding integrity, not arbitrary semantic equality.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from pfp.domain.prompt_representations.common import (
    SYMBOLIC_TO_ROLE,
    sha256_digest,
)
from pfp.domain.prompt_representations.symbolic_prompt_representation import (
    WIRE_PAIR_REGEX,
    SymbolicPromptRepresentation,
)

TEXTS = {
    "s0": "solve the meron sign problem inside our finite system",
    "s1": "Case: spinless U=t; periodic four-site even chain; two repetitions; exact q=3.",
    "s2": "Preserve signed partition and staggered-square observable numerator.",
    "s3": "Preserve original CAR signs, breakup weights, complete equal-weight orbits and positive scalar.",
    "s4": "Host-selected source/checker bindings are immutable; recompute every certificate field.",
    "s5": "Native receipts describe their actual witness scope; missing physical adapters and measurements remain HOLD/BLOCKED.",
    "s6": "No general sign-problem theorem, guessed telemetry, inherited acceptance or zero-billing claim.",
    "s7": "Return only the supplied PFP response schema; use its declared refusal route when obligations cannot be met.",
}
ROLES = [("s0", "task"), *[(f"s{i}", "constraint") for i in range(1, 7)], ("s7", "output")]


def packet(texts=None):
    selected = TEXTS if texts is None else texts
    source = json.dumps(selected, ensure_ascii=False, sort_keys=True)
    return SymbolicPromptRepresentation.from_bindings(
        source_id="pfp.symbolic-constraint-binding.v001.host-control",
        source_sha256=sha256_digest(source),
        proposal_sha256=sha256_digest(source),
        grammar_sha256=sha256_digest("mss-boundary-v1"),
        slot_roles=ROLES,
        slot_texts=selected,
    )


def protected_query(value):
    """Read the actual active wire and inline codebook at the comparison consumer."""
    legend, wire, codebook = value.render().split("\n", 2)
    assert legend == value.legend
    decoded = json.loads(codebook)["bindings"]
    return tuple((slot, SYMBOLIC_TO_ROLE[role], decoded[slot].encode("utf-8"))
                 for role, slot in WIRE_PAIR_REGEX.findall(wire))


def test_complete_meron_binding_preserves_declared_query():
    value = packet()
    expected = tuple((slot, role, TEXTS[slot].encode("utf-8")) for slot, role in ROLES)
    assert protected_query(value) == expected
    assert SymbolicPromptRepresentation.model_validate_json(value.model_dump_json()).render() == value.render()


def test_benign_quoted_unicode_instruction_roundtrips():
    texts = {**TEXTS, "s3": 'Preserve "CAR" signs; glyph data: 𓂀 <>.\nNo physical emergence asserted.'}
    value = packet(texts)
    assert protected_query(value)[3] == ("s3", "constraint", texts["s3"].encode("utf-8"))


@pytest.mark.parametrize("wire", [
    "<<p><v1><<q><s0>><<c><s1>><<c><s2>><<c><s3>><<c><s4>><<c><s5>>>",
    "<<p><v1><<q><s0>><<c><s1>><<c><s2>><<c><s3>><<c><s4>><<c><s5>><<c><s6>><<o><s6>>>",
    "<<p><v1><<q><s0>><<c><s1>><<c><s2>><<c><s3>><<c><s4>><<c><s5>><<c><s6>><<o><s7>>",
])
def test_missing_duplicate_or_malformed_active_binding_is_rejected(wire):
    data = packet().model_dump()
    data["wire"] = wire
    with pytest.raises(ValidationError):
        SymbolicPromptRepresentation.model_validate(data)


def test_unbound_codebook_slot_is_rejected():
    data = packet().model_dump()
    data["bindings"]["s8"] = "A constraint added without updating the active wire."
    with pytest.raises(ValidationError, match="BINDINGS_TOTALITY_ERROR"):
        SymbolicPromptRepresentation.model_validate(data)


def test_coherently_rebound_wrong_scope_needs_independent_comparison():
    baseline = packet()
    harmful = packet({**TEXTS, "s1": "Case: every fermion model and its continuum limit."})
    assert SymbolicPromptRepresentation.model_validate_json(harmful.model_dump_json()).wire == baseline.wire
    assert harmful.source_sha256 != baseline.source_sha256
    assert protected_query(harmful) != protected_query(baseline)
