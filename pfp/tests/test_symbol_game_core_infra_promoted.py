"""Tests for promoted core and infrastructure layers in omega_engine_pfp."""

from __future__ import annotations

import tempfile

import pytest

from omega_engine_pfp.domain.aggregates.prompt_artifact import ObjectiveTypedV1
from omega_engine_pfp.domain.exceptions import CanonicalizationError
from omega_engine_pfp.domain.validation.validation import (
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_int,
    _require_string,
    is_valid_hex64,
    normalize_utf8_lf,
    raw_content_sha256,
)
from omega_engine_pfp.infrastructure.adapters.cec_bridge_adapter import CecBridgeAdapter
from omega_engine_pfp.infrastructure.adapters.obstruction_adapter import (
    ObstructionLedgerAdapter,
)
from omega_engine_pfp.infrastructure.adapters.oesos_evidence_adapter import (
    OesosEvidenceAdapter,
)
from omega_engine_pfp.infrastructure.persistence.file_context import SymbolGameDbContext
from omega_engine_pfp.infrastructure.persistence.repositories import (
    FilePromptRepository,
    MemoryPromptRepository,
)


def test_core_validation_primitives() -> None:
    """Test scalar validation rules in root core layer."""
    assert is_valid_hex64("a" * 64) is True
    assert is_valid_hex64("a" * 63) is False
    assert is_valid_hex64("G" * 64) is False

    assert normalize_utf8_lf(b"hello\r\nworld\r") == b"hello\nworld\n"

    sha, length = raw_content_sha256(b"omega")
    assert len(sha) == 64
    assert length == 5

    assert _require_string("hello", "field") == "hello"
    with pytest.raises(CanonicalizationError):
        _require_string(123, "field")  # type: ignore

    assert _require_int(42, "num") == 42
    with pytest.raises(CanonicalizationError):
        _require_int("42", "num")  # type: ignore

    assert _require_digest("a" * 64, "digest") == "a" * 64
    with pytest.raises(CanonicalizationError):
        _require_digest("bad", "digest")

    d = {"a": 1, "b": "val"}
    _require_exact_dict(d, "dict_field")
    _require_fields(d, frozenset({"a", "b"}), "dict_field")
    with pytest.raises(CanonicalizationError):
        _require_fields(d, frozenset({"a"}), "dict_field")


def test_infrastructure_in_memory_and_file_repositories() -> None:
    """Test in-memory and file persistence in root infrastructure layer."""
    from omega_engine_pfp.use_cases.prompt_artifact import compile_prompt_artifact

    art = compile_prompt_artifact(
        regime_kind="prose-regime",
        regime_definition_bytes=b"regime_content",
        prompt_body_bytes=b"body_content",
        objective_typed=ObjectiveTypedV1(kind="prompt_turn", summary="test obj"),
    )

    # Memory repository
    mem_repo = MemoryPromptRepository()
    mem_repo.save_prompt_artifact(art)
    loaded = mem_repo.get_prompt_artifact(str(art.prompt_artifact_id))
    assert loaded is not None
    assert str(loaded.prompt_artifact_id) == str(art.prompt_artifact_id)

    # File repository
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SymbolGameDbContext(tmpdir)
        file_repo = FilePromptRepository(db)
        file_repo.save_prompt_artifact(art)
        file_loaded = file_repo.get_prompt_artifact(str(art.prompt_artifact_id))
        assert file_loaded is not None
        assert str(file_loaded.prompt_artifact_id) == str(art.prompt_artifact_id)


def test_infrastructure_adapters() -> None:
    """Test external bridge adapters in root infrastructure layer."""
    cec = CecBridgeAdapter()
    res = cec.evaluate_metric("target_01", {"key": "val"})
    assert res["status"] == "REFUSED"
    assert res["refusal_code"] == "CEC_EVALUATOR_UNAVAILABLE"
    assert res["metric_score"] is None
    assert res["authority_effect"] == "None"

    obs = ObstructionLedgerAdapter()
    ev = obs.record_transition(
        step=1,
        obstruction_id="obs_001",
        disposition="CLOSED",
        magnitude=0.0,
        witness="wit_001",
    )
    assert int(ev.step) == 1
    assert len(obs.get_events()) == 1

    oesos = OesosEvidenceAdapter()
    rec = oesos.build_evidence_receipt([])
    assert rec["events_count"] == 0
    assert rec["authority_effect"] == "None"
