"""Independent operator admission and witnessed offspring. AuthorityEffect: None."""

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from ..infrastructure.cas import ContentAddressedStorageV1
from .custody import PromptCustodyLedgerV1
from .forge import MutationOperatorCandidateV1, PromptMutationEngineV1
from ..domain.models import PromptGenomeV1, ProtectedSpanV1


@dataclass(frozen=True)
class MutationOperatorAdmissionV1:
    decision_id: str
    operator_id: str
    operator_digest: str
    actor_id: str
    scope: tuple[str, ...]
    external_receipt: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.scope) is not tuple or any(type(item) is not str or not item for item in self.scope):
            raise ValueError("OPERATOR_SCOPE_INVALID")

    def signed_bytes(self) -> bytes:
        payload = asdict(self)
        del payload["external_receipt"]
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


class OperatorAdmissionVerifier(Protocol):
    def verify(self, decision: MutationOperatorAdmissionV1) -> bool: ...


class MutationOperatorRegistryV1:
    def __init__(
        self, database: Path, verifier: OperatorAdmissionVerifier,
        prompts: PromptCustodyLedgerV1, cas: ContentAddressedStorageV1,
    ) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database)
        self.connection.execute("PRAGMA synchronous=FULL")
        self.verifier, self.prompts, self.cas = verifier, prompts, cas
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS operators (
                operator_id TEXT PRIMARY KEY, producer_actor TEXT NOT NULL,
                descriptor TEXT NOT NULL, source BLOB NOT NULL, digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS operator_admissions (
                operator_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL UNIQUE, receipt TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.connection.close()

    def submit(self, operator: MutationOperatorCandidateV1, producer_actor: str, source: bytes) -> str:
        if not producer_actor or not source:
            raise ValueError("OPERATOR_SOURCE_AND_ACTOR_REQUIRED")
        descriptor = json.dumps(asdict(operator), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(
            descriptor.encode("utf-8") + b"\0" + source
        ).hexdigest()
        with self.connection:
            prior = self.connection.execute(
                "SELECT producer_actor, digest FROM operators WHERE operator_id=?", (operator.operator_id,),
            ).fetchone()
            if prior and prior != (producer_actor, digest):
                raise ValueError("OPERATOR_IDENTITY_CONFLICT")
            self.connection.execute(
                "INSERT OR IGNORE INTO operators VALUES (?, ?, ?, ?, ?)",
                (operator.operator_id, producer_actor, descriptor, source, digest),
            )
        return digest

    def admit(self, decision: MutationOperatorAdmissionV1) -> None:
        row = self.connection.execute(
            "SELECT producer_actor, digest FROM operators WHERE operator_id=?", (decision.operator_id,),
        ).fetchone()
        if row is None or decision.operator_digest != row[1]:
            raise ValueError("OPERATOR_REVIEW_SUBJECT_MISMATCH")
        if decision.actor_id in (row[0], decision.operator_id):
            raise PermissionError("SELF_ADMISSION_REFUSED")
        if decision.authority_effect != "None" or not decision.scope or not decision.external_receipt or self.verifier.verify(decision) is not True:
            raise PermissionError("EXTERNAL_OPERATOR_REVIEW_NOT_AUTHENTICATED")
        payload = json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        with self.connection:
            previous = self.connection.execute(
                "SELECT receipt FROM operator_admissions WHERE operator_id=?", (decision.operator_id,),
            ).fetchone()
            if previous and previous[0] != payload:
                raise ValueError("OPERATOR_ADMISSION_IDENTITY_CONFLICT")
            self.connection.execute(
                "INSERT OR IGNORE INTO operator_admissions VALUES (?, ?, ?)",
                (decision.operator_id, decision.decision_id, payload),
            )

    def realize_offspring(
        self, operator_id: str, parent: PromptGenomeV1, original: bytes, *,
        scope: str, edit_start: int, edit_end: int, replacement: bytes,
    ) -> PromptGenomeV1:
        row = self.connection.execute(
            "SELECT o.producer_actor, o.digest, a.receipt FROM operators o "
            "JOIN operator_admissions a USING(operator_id) WHERE operator_id=?", (operator_id,),
        ).fetchone()
        if row is None:
            raise PermissionError("OPERATOR_NOT_ADMITTED")
        allowed_scope = json.loads(row[2])["scope"]
        if type(allowed_scope) is not list or any(type(item) is not str or not item for item in allowed_scope):
            raise ValueError("OPERATOR_SCOPE_INVALID")
        if scope not in allowed_scope:
            raise PermissionError("REFUSE_SCOPE_ESCALATION")
        if self.prompts.genome(parent.prompt_id) != parent:
            raise ValueError("PARENT_GENOME_MISMATCH")
        original_digest = hashlib.sha256(original).hexdigest()
        if not any(ref.get("sha256", "").removeprefix("sha256:") == original_digest for ref in parent.source_packet_refs):
            raise ValueError("PARENT_BYTES_MISMATCH")
        child_bytes = PromptMutationEngineV1().apply_mutation(
            original_bytes=original, protected_spans=parent.protected_spans,
            edit_start_byte=edit_start, edit_end_byte=edit_end, replacement_bytes=replacement,
        )
        digest = self.cas.store(child_bytes)
        delta = len(replacement) - (edit_end - edit_start)
        spans = tuple(
            ProtectedSpanV1(span.name, span.start_byte + delta, span.end_byte + delta)
            if span.start_byte >= edit_end else span for span in parent.protected_spans
        )
        witness = hashlib.sha256(json.dumps(
            [operator_id, row[1], parent.prompt_id, digest, edit_start, edit_end],
            separators=(",", ":"),
        ).encode()).hexdigest()
        child = PromptGenomeV1(
            source_packet_refs=[{"packet_id": digest, "sha256": digest, "packet_kind": "prompt-artifact"}],
            domain_model=parent.domain_model,
            parents=[{
                "prompt_id": parent.prompt_id, "generation": parent.generation,
                "relationship": "DirectMutation", "witness_receipt_digest": witness,
            }],
            generation=parent.generation + 1, protected_spans=spans,
        )
        self.prompts.submit_candidate(child, row[0], prohibited_actors=(operator_id,))
        return child


OperatorCustodyLifecycleV1 = MutationOperatorRegistryV1

__all__ = [
    "MutationOperatorAdmissionV1",
    "MutationOperatorRegistryV1",
    "OperatorAdmissionVerifier",
    "OperatorCustodyLifecycleV1",
]
