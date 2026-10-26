"""
test_symbol_game_domain_promoted.py
===================================

Unit tests validating that domain aggregates, entities, value objects, invariants,
and diff parser are accessible and operational directly from root `omega_engine_pfp.domain`.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain import (
    DiffParseResult,
    DomainError,
    ForbiddenAuthorityError,
    InvariantViolationError,
    ObstructionScore,
    PacketCodec,
    ProposalEvaluator,
    aggregates,
    entities,
    parse_unified_diff,
    validate_authority_effect_none,
    validate_residual_witness,
    value_objects,
)
from omega_engine_pfp.domain.aggregates.prompt_artifact import (
    EliminationReceiptV1,
    PromptArtifactV1,
)
from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.shared_kernel import (
    AuthorityEffect,
    Code,
    ContentDigest,
    DemandId,
    FieldName,
    ObjectiveTypedV1,
    PromptArtifactId,
    ReceiptId,
    Regime,
    RegimeKind,
    ResidualColour,
    SchemaVersion,
)


def test_domain_aggregates_prompt_artifact():
    digest = ContentDigest.from_bytes(b"canonical spec body")
    regime_digest = ContentDigest.from_bytes(b"witten-airy-critical-v1")
    from omega_engine_pfp.use_cases.prompt_artifact import compile_prompt_artifact
    artifact = compile_prompt_artifact(
        regime_kind="prose-regime",
        regime_definition_bytes=b"witten-airy-critical-v1",
        prompt_body_bytes=b"canonical spec body",
        objective_typed=ObjectiveTypedV1(kind="prompt_turn", summary="retract cochain"),
    )
    assert artifact.prompt_artifact_id.startswith("sha256:") or len(artifact.prompt_artifact_id) == 64
    assert artifact.authority_effect == "None"


def test_domain_invariants_authority_none():
    validate_authority_effect_none("None")
    with pytest.raises((InvariantViolationError, ForbiddenAuthorityError)):
        validate_authority_effect_none("ElevatedRoot")


def test_domain_diff_parser_unified():
    valid_diff = (
        "diff --git a/domain/order.py b/domain/order.py\n"
        "--- a/domain/order.py\n"
        "+++ b/domain/order.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-old\n"
        "+new\n"
    )
    result = parse_unified_diff(valid_diff)
    assert isinstance(result, DiffParseResult)
    assert result.is_valid is True
    assert "domain/order.py" in result.touched_paths
