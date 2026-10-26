"""Concrete repository implementations for the Symbol Game bounded context."""

from __future__ import annotations

import dataclasses

from ...domain import (
    CandidateArtifactV1,
    CanonicalizationError,
    EliminationReceiptV1,
    LlmTurnContentArtifactV1,
    LlmTurnPayloadV1,
    LlmTurnRunRootV1,
    PromptArtifactV1,
    llm_turn_task_packet_sha256,
)
from ...domain.ports import (
    IPromptRepository,
    ITurnRepository,
)
from .file_context import SymbolGameDbContext
from .memory_context import InMemoryDbContext


class MemoryPromptRepository(IPromptRepository):
    """In-memory implementation of IPromptRepository."""

    def __init__(self, context: InMemoryDbContext | None = None) -> None:
        self.context = context or InMemoryDbContext()

    def save_prompt_artifact(self, artifact: PromptArtifactV1) -> None:
        self.context.prompts[str(artifact.prompt_artifact_id)] = artifact.to_dict()

    def get_prompt_artifact(self, artifact_id: str) -> PromptArtifactV1 | None:
        data = self.context.prompts.get(str(artifact_id))
        return PromptArtifactV1.from_dict(data) if data else None

    def save_elimination_receipt(self, receipt: EliminationReceiptV1) -> None:
        self.context.receipts[str(receipt.elimination_receipt_id)] = receipt.to_dict()

    def get_elimination_receipt(self, receipt_id: str) -> EliminationReceiptV1 | None:
        data = self.context.receipts.get(str(receipt_id))
        return EliminationReceiptV1.from_dict(data) if data else None


class FilePromptRepository(IPromptRepository):
    """File-based implementation of IPromptRepository."""

    def __init__(self, db_context: SymbolGameDbContext) -> None:
        self.db = db_context

    def save_prompt_artifact(self, artifact: PromptArtifactV1) -> None:
        path = self.db.prompts_dir / f"{artifact.prompt_artifact_id}.json"
        self.db.write_json(path, artifact.to_dict())

    def get_prompt_artifact(self, artifact_id: str) -> PromptArtifactV1 | None:
        path = self.db.prompts_dir / f"{artifact_id}.json"
        data = self.db.read_json(path)
        return PromptArtifactV1.from_dict(data) if data else None

    def save_elimination_receipt(self, receipt: EliminationReceiptV1) -> None:
        path = self.db.receipts_dir / f"{receipt.elimination_receipt_id}.json"
        self.db.write_json(path, receipt.to_dict())

    def get_elimination_receipt(self, receipt_id: str) -> EliminationReceiptV1 | None:
        path = self.db.receipts_dir / f"{receipt_id}.json"
        data = self.db.read_json(path)
        return EliminationReceiptV1.from_dict(data) if data else None


class MemoryTurnRepository(ITurnRepository):
    """In-memory implementation of ITurnRepository."""

    def __init__(self, context: InMemoryDbContext | None = None) -> None:
        self.context = context or InMemoryDbContext()

    # `to_dict` is the serializer, so `from_dict` is the deserializer. The
    # previous body hand-rolled a reconstruction against
    # `LlmTurnRunRootV1.create`, which does not exist, and read `payload` and
    # `candidates` keys that `to_dict` does not emit -- the aggregate is a
    # ledger of `candidate_ids` and `content_ids`. Every read raised
    # `KeyError: 'payload'`.
    #
    # Round-tripping through the aggregate's own pair re-validates a stored
    # record through `__post_init__` on the way back in, which a hand-rolled
    # constructor call bypassed. But that pair alone is not enough to *resume* a
    # run: `identity_fields` deliberately omits `explicit_payload` and
    # `explicit_task_id`, so a loaded root came back with `payload is None` and
    # a `task_id` degraded to the packet digest. Both use cases dereference
    # `run_root.payload.candidate_budget` immediately, so every
    # create -> save -> load -> submit sequence died with
    # `AttributeError: 'NoneType' object has no attribute 'candidate_budget'`.
    # The ledger shape round-tripped; the state the controller needs did not.
    #
    # The task payload is therefore stored beside the ledger record and
    # reattached on load. It is kept out of `to_dict` on purpose -- it is task
    # input, not run evidence -- so it travels as its own field rather than
    # being smuggled into the aggregate's wire form.
    def save_run_root(self, run_root: LlmTurnRunRootV1) -> None:
        payload = run_root.payload
        self.context.runs[str(run_root.run_root_id)] = {
            "root": run_root.to_dict(),
            "explicit_task_id": run_root.explicit_task_id,
            "payload": payload.to_dict() if payload is not None else None,
        }

    def get_run_root(self, run_root_id: str) -> LlmTurnRunRootV1 | None:
        record = self.context.runs.get(str(run_root_id))
        if not record:
            return None
        root = LlmTurnRunRootV1.from_dict(record["root"])
        payload_wire = record.get("payload")
        if payload_wire is None:
            return dataclasses.replace(
                root, explicit_task_id=record.get("explicit_task_id")
            )
        # The sidecar is reattached only if it is the packet this root was
        # opened for. Storing it beside the ledger and trusting it back was a
        # hole: a swapped or stale payload changed the budget, the required
        # reply fields and the kill conditions with no id changing and nothing
        # objecting. `task_packet_sha256` lives inside the canonical root, so
        # recomputing the digest and comparing is a check the record cannot
        # talk its way out of.
        payload = LlmTurnPayloadV1.from_dict(payload_wire)
        if llm_turn_task_packet_sha256(payload) != root.task_packet_sha256:
            raise CanonicalizationError(
                "stored llm-turn payload does not match the run root's "
                "task_packet_sha256"
            )
        return dataclasses.replace(
            root,
            explicit_task_id=record.get("explicit_task_id"),
            explicit_payload=payload,
        )

    # The content pair had the same defect as `get_run_root` above: it keyed on
    # `content_artifact_id` and rebuilt through `LlmTurnContentArtifactV1.create`,
    # neither of which exists. The artifact's identity is the derived
    # `content_id` digest, and `to_dict`/`from_dict` are its serializer pair.
    #
    # `to_dict` emits `identity_fields` only, so `explicit_payload` -- the
    # submission body carrying the reply text -- does not survive the round
    # trip. That is the aggregate's design, not a loss here: the artifact binds
    # a digest and byte count, never the bytes. `EvaluateCandidateUseCase`
    # refuses a rehydrated artifact for exactly that reason rather than scoring
    # an empty reply as though it had been read.
    def save_content_artifact(self, artifact: LlmTurnContentArtifactV1) -> None:
        self.context.content_artifacts[str(artifact.content_id)] = artifact.to_dict()

    def get_content_artifact(self, artifact_id: str) -> LlmTurnContentArtifactV1 | None:
        data = self.context.content_artifacts.get(str(artifact_id))
        if not data:
            return None
        return LlmTurnContentArtifactV1.from_dict(data)

    # `ITurnRepository` declares this pair and `TurnController.submit_candidate`
    # calls `save_candidate_artifact` on every submission, but
    # `MemoryTurnRepository` never defined either -- so the only repository
    # wired into the turn path raised `AttributeError` the moment a candidate
    # reached persistence.
    def save_candidate_artifact(self, candidate: CandidateArtifactV1) -> None:
        self.context.candidates[str(candidate.candidate_id)] = candidate.to_dict()

    def get_candidate_artifact(self, candidate_id: str) -> CandidateArtifactV1 | None:
        data = self.context.candidates.get(str(candidate_id))
        if not data:
            return None
        return CandidateArtifactV1.from_dict(data)
