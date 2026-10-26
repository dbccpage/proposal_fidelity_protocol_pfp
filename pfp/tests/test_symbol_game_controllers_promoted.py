"""Tests for promoted controllers in omega_engine_pfp."""

from __future__ import annotations

from omega_engine_pfp.controllers import (
    CodeChangeController,
    PromptController,
    TurnController,
)
from omega_engine_pfp.domain import (
    CodeChangeRunRootV1,
    LlmTurnRunRootV1,
    PromptArtifactV1,
)
from omega_engine_pfp.infrastructure import (
    MemoryPromptRepository,
    MemoryTurnRepository,
)
from omega_engine_pfp.use_cases import CodeChangeSession


def test_turn_controller_lifecycle() -> None:
    """Test TurnController in root controllers layer."""
    repo = MemoryTurnRepository()
    ctrl = TurnController(repository=repo)

    run_root = ctrl.create_turn(
        task_id="turn_task_001",
        objective="Resolve obstruction OBS-1",
        candidate_budget=2,
        operation_budget=8,
    )
    assert isinstance(run_root, LlmTurnRunRootV1)
    assert str(run_root.task_id) == "turn_task_001"
    assert int(run_root.payload.candidate_budget) == 2


def test_code_change_controller_lifecycle() -> None:
    """Test CodeChangeController in root controllers layer.

    Stage 1 now yields a `CodeChangeSession`, not a `CodeChangeRunRootV1`. The
    run root is the *result* of `evaluate_code_change_candidate`, so this walks
    the whole lifecycle to obtain one rather than asserting on a record of an
    evaluation that has not happened.
    """
    ctrl = CodeChangeController()
    session = ctrl.create_proposal(
        task_id="code_task_001",
        objective="Fix typo in domain logic",
        base_revision="main@HEAD",
        owned_paths=("omega_engine_pfp/domain",),
        protected_paths=(".canon",),
    )
    assert isinstance(session, CodeChangeSession)
    assert session.task_id == "code_task_001"

    target = "omega_engine_pfp/domain/x.py"
    session, bound = ctrl.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=f"--- a/{target}\n+++ b/{target}\n@@ -0,0 +1,1 @@\n+x = 1\n",
    )
    receipts = ctrl.evaluate_patch_gates(session=session, bound=bound)
    run_root = ctrl.finalize_run(
        session=session, bound=bound, gate_receipts=receipts
    )

    assert isinstance(run_root, CodeChangeRunRootV1)
    assert run_root.task_packet_id == session.packet_id
    assert run_root.candidate_ids == (bound.candidate.candidate_id,)


def test_prompt_controller_lifecycle() -> None:
    """Test PromptController in root controllers layer."""
    repo = MemoryPromptRepository()
    ctrl = PromptController(repository=repo)
    art = ctrl.compile_prompt(
        prompt_artifact_id="art_ctrl_001",
        regime_kind="fence_only",
        prompt_body="System instructions and objective",
    )
    assert isinstance(art, PromptArtifactV1)
    assert str(art.prompt_artifact_id) == "art_ctrl_001"


def test_prompt_controller_validates_reply_keys_not_substrings() -> None:
    """A required field must be a top-level key of a JSON object reply."""
    ctrl = PromptController(repository=MemoryPromptRepository())
    art = ctrl.compile_prompt(
        prompt_artifact_id="art_ctrl_002",
        regime_kind="fence_only",
        prompt_body="Reply with status and step_claims",
        required_reply_fields=("status", "step_claims"),
    )
    assert ctrl.validate_reply(art, '{"status": "PASS", "step_claims": []}') is True
    assert ctrl.validate_reply(art, '{"status": "PASS", "note": "step_claims"}') is False
    assert ctrl.validate_reply(art, "status step_claims") is False
    assert ctrl.validate_reply(art, '["status", "step_claims"]') is False


def test_prompt_controller_records_an_elimination_receipt() -> None:
    """The controller builds the receipt through the host constructor and stores it."""
    repo = MemoryPromptRepository()
    receipt = PromptController(repository=repo).eliminate_obstruction(
        packet_id="a" * 64,
        prior_residual_colour="Open",
        new_residual_colour="Closed",
        evidence_root="b" * 64,
        eliminated_obstruction_ids=("o2", "o1", "o2"),
    )
    assert receipt.eliminated_obstruction_ids == ("o1", "o2")
    assert repo.get_elimination_receipt(receipt.elimination_receipt_id) == receipt
