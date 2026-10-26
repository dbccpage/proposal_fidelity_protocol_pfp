"""Shared Kernel: LLM Turn Payload Value Object constructed from enriched sub-Value Objects.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ..exceptions import CanonicalizationError
from .authority_effect import AuthorityEffect
from .budget import CandidateBudget, OperationBudget
from .bytes import ByteCount
from .code import Code
from .content_digest import ContentDigest
from .id import PacketId, PromptArtifactId, TaskId
from .kind import RoleKind
from .required_reply_fields import DEFAULT_REQUIRED_FIELDS, RequiredReplyFields
from .schema import SchemaVersion
from .task_objective import TaskObjective
from .turn import TurnKind, TurnModality, TurnRole

LLM_TURN_SCHEMA: str = "omega.symbol-game.llm-turn.v1"
LLM_TURN_FAMILY: str = "llm_turn"
LLM_TURN_PACKET_FAMILY: str = "llm_turn_v1"
PAYLOAD_DOMAIN: str = "omega.symbol-game.llm-turn-payload.v1"
TURN_MANIFEST_DOMAIN: str = "omega.symbol-game.llm-turn-manifest.v1"
LLM_TURN_TERMINAL_TARGET: str = "TypedTurnOrProsePromptRefused"
LLM_TURN_EVIDENCE_CEILING: str = "ReplayableLabEvidence"
LLM_TURN_ORACLE_POLICY: str = "IndependentHostEvaluationRequired"

ALLOWED_ROLES: frozenset[str] = frozenset({"user", "assistant", "system", "tool"})
ALLOWED_TURN_KINDS: frozenset[str] = frozenset(
    modality.value for modality in TurnModality
)
CONSEQUENTIAL_TURN_KINDS: frozenset[str] = frozenset(
    {
        "code_change",
        "claimed_result",
        "repair_candidate",
        "elimination_proposal",
    }
)
MAX_CONTENT_BYTES: int = 1024 * 1024
MAX_CANDIDATE_BUDGET: int = 32
MAX_OPERATION_BUDGET: int = 4096
MAX_CANONICAL_PAYLOAD_BYTES: int = 256 * 1024
MAX_KILL_CONDITIONS: int = 256
REQUIRED_REPLY_FIELD_IDS: frozenset[str] = frozenset(
    DEFAULT_REQUIRED_FIELDS
) | frozenset({"status", "step_claims", "obstruction_receipts"})


def _wire_string(value: object, label: str) -> str:
    if type(value) is not str:
        raise CanonicalizationError(f"{label} must be an exact string")
    return value


def _wire_int(value: object, label: str) -> int:
    if type(value) is not int:
        raise CanonicalizationError(f"{label} must be an exact integer")
    return value


def _wire_optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _wire_string(value, label)


def _wire_string_list(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise CanonicalizationError(f"{label} must be an array of strings")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_wire_string(item, f"{label}[{index}]"))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class LlmTurnPayloadV1:
    """Composite Value Object containing the specification for an LLM turn task.

    Decomposed into rich Value Objects:
    - schema_version: SchemaVersion
    - task_id: TaskId
    - objective: TaskObjective
    - role: TurnRole
    - turn_kind: TurnKind
    - candidate_budget: CandidateBudget
    - operation_budget: OperationBudget
    - required_reply_fields: RequiredReplyFields
    - content_sha256: ContentDigest
    - content_byte_count: ByteCount
    - prompt_artifact_id: PromptArtifactId | None
    - parent_packet_id: PacketId | None
    - conversation_root_id: PacketId | None
    - kill_conditions: tuple[Code, ...]
    - authority_effect: AuthorityEffect
    """

    objective: TaskObjective
    role: TurnRole
    turn_kind: TurnKind
    content_sha256: ContentDigest
    content_byte_count: ByteCount
    candidate_budget: CandidateBudget
    operation_budget: OperationBudget
    required_reply_fields: RequiredReplyFields = field(
        default_factory=lambda: RequiredReplyFields(DEFAULT_REQUIRED_FIELDS)
    )
    terminal_target: str = field(default=LLM_TURN_TERMINAL_TARGET)
    evidence_ceiling: str = field(default=LLM_TURN_EVIDENCE_CEILING)
    parent_packet_id: PacketId | None = None
    conversation_root_id: PacketId | None = None
    family: str = field(default=LLM_TURN_FAMILY)
    schema_version: SchemaVersion = field(
        default_factory=lambda: SchemaVersion(LLM_TURN_SCHEMA)
    )
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    task_id: TaskId = field(default_factory=lambda: TaskId("llm_turn_task"))
    prompt_artifact_id: PromptArtifactId | None = None
    kill_conditions: tuple[Code, ...] = (Code("F-01_inherited_meaning"),)

    def __post_init__(self) -> None:
        auth_val = (
            self.authority_effect.value
            if isinstance(self.authority_effect, AuthorityEffect)
            else str(self.authority_effect)
        )
        if auth_val != "None":
            raise CanonicalizationError(
                "llm-turn payloads must carry AuthorityEffect None"
            )

        if not isinstance(self.objective, TaskObjective):
            object.__setattr__(
                self, "objective", TaskObjective.from_str(self.objective)
            )
        if not isinstance(self.role, TurnRole):
            object.__setattr__(self, "role", TurnRole.from_str(self.role))
        if not isinstance(self.turn_kind, TurnKind):
            object.__setattr__(self, "turn_kind", TurnKind.from_str(self.turn_kind))
        if not isinstance(self.content_sha256, ContentDigest):
            object.__setattr__(
                self, "content_sha256", ContentDigest.from_str(self.content_sha256)
            )
        if not isinstance(self.content_byte_count, ByteCount):
            object.__setattr__(
                self, "content_byte_count", ByteCount.from_int(self.content_byte_count)
            )
        if not isinstance(self.candidate_budget, CandidateBudget):
            object.__setattr__(
                self,
                "candidate_budget",
                CandidateBudget.from_int(self.candidate_budget),
            )
        if not isinstance(self.operation_budget, OperationBudget):
            object.__setattr__(
                self,
                "operation_budget",
                OperationBudget.from_int(self.operation_budget),
            )
        if not isinstance(self.required_reply_fields, RequiredReplyFields):
            object.__setattr__(
                self,
                "required_reply_fields",
                RequiredReplyFields.from_sequence(self.required_reply_fields),
            )
        if not isinstance(self.schema_version, SchemaVersion):
            object.__setattr__(
                self, "schema_version", SchemaVersion.from_str(self.schema_version)
            )
        if not isinstance(self.task_id, TaskId):
            object.__setattr__(self, "task_id", TaskId.from_str(self.task_id))
        if self.prompt_artifact_id is not None and not isinstance(
            self.prompt_artifact_id, PromptArtifactId
        ):
            object.__setattr__(
                self,
                "prompt_artifact_id",
                PromptArtifactId.from_str(self.prompt_artifact_id),
            )
        if self.parent_packet_id is not None and not isinstance(
            self.parent_packet_id, PacketId
        ):
            object.__setattr__(
                self, "parent_packet_id", PacketId.from_str(self.parent_packet_id)
            )
        if self.conversation_root_id is not None and not isinstance(
            self.conversation_root_id, PacketId
        ):
            object.__setattr__(
                self,
                "conversation_root_id",
                PacketId.from_str(self.conversation_root_id),
            )
        if not isinstance(self.authority_effect, AuthorityEffect):
            object.__setattr__(
                self, "authority_effect", AuthorityEffect(self.authority_effect)
            )

        if not isinstance(self.kill_conditions, (tuple, list)):
            raise CanonicalizationError("kill_conditions must be a sequence")
        norm_kill = tuple(
            sorted(
                {
                    k if isinstance(k, Code) else Code.from_str(k)
                    for k in self.kill_conditions
                },
                key=lambda x: x.value,
            )
        )
        object.__setattr__(self, "kill_conditions", norm_kill)

        if str(self.role) not in ALLOWED_ROLES:
            raise CanonicalizationError("role is unsupported for llm-turn payloads")
        turn_kind_str = str(self.turn_kind)
        if turn_kind_str not in ALLOWED_TURN_KINDS:
            raise CanonicalizationError("turn_kind is unsupported")
        if int(self.content_byte_count) > MAX_CONTENT_BYTES:
            raise CanonicalizationError(
                "content_byte_count exceeds the content resource limit"
            )
        if int(self.candidate_budget) > MAX_CANDIDATE_BUDGET:
            raise CanonicalizationError(
                "candidate_budget exceeds the llm-turn resource limit"
            )
        if int(self.operation_budget) > MAX_OPERATION_BUDGET:
            raise CanonicalizationError(
                "operation_budget exceeds the llm-turn resource limit"
            )

        reply_tuple = self.required_reply_fields.as_tuple()
        if (
            not reply_tuple
            or len(reply_tuple) > len(REQUIRED_REPLY_FIELD_IDS)
            or not set(reply_tuple).issubset(REQUIRED_REPLY_FIELD_IDS)
        ):
            raise CanonicalizationError(
                "required_reply_fields contains unsupported entries"
            )
        if (
            turn_kind_str in CONSEQUENTIAL_TURN_KINDS
            and reply_tuple != DEFAULT_REQUIRED_FIELDS
        ):
            raise CanonicalizationError(
                "consequential turns require the exact canonical required_reply_fields set"
            )
        if not norm_kill or len(norm_kill) > MAX_KILL_CONDITIONS:
            raise CanonicalizationError("kill_conditions must be nonempty and bounded")
        if (
            type(self.terminal_target) is not str
            or self.terminal_target != LLM_TURN_TERMINAL_TARGET
        ):
            raise CanonicalizationError("terminal_target is unsupported")
        if (
            type(self.evidence_ceiling) is not str
            or self.evidence_ceiling != LLM_TURN_EVIDENCE_CEILING
        ):
            raise CanonicalizationError("evidence_ceiling is unsupported")
        if type(self.family) is not str or self.family != LLM_TURN_FAMILY:
            raise CanonicalizationError("llm-turn family is unsupported")
        if str(self.schema_version) != LLM_TURN_SCHEMA:
            raise CanonicalizationError("llm-turn schema version is unsupported")
        encoded_size = len(
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if encoded_size > MAX_CANONICAL_PAYLOAD_BYTES:
            raise CanonicalizationError(
                "llm-turn payload exceeds the canonical resource limit"
            )

    @property
    def prompt_body_sha256(self) -> ContentDigest:
        return self.content_sha256

    @property
    def prompt_body_bytes_len(self) -> ByteCount:
        return self.content_byte_count

    @property
    def payload_id(self) -> str:
        raw = self.to_dict()
        encoded = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @property
    def turn_manifest_root(self) -> str:
        raw = {
            "content_sha256": str(self.content_sha256),
            "conversation_root_id": str(self.conversation_root_id)
            if self.conversation_root_id
            else None,
            "objective": str(self.objective),
            "parent_packet_id": str(self.parent_packet_id)
            if self.parent_packet_id
            else None,
            "role": str(self.role),
            "turn_kind": str(self.turn_kind),
        }
        encoded = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def create(
        cls,
        *,
        task_id: str | TaskId = "llm_turn_task",
        objective: str | TaskObjective,
        role: str | TurnRole = RoleKind.ASSISTANT.value,
        turn_kind: str | TurnKind = TurnModality.SYMBOL_GAME_TURN.value,
        candidate_budget: int | CandidateBudget = 4,
        operation_budget: int | OperationBudget = 16,
        prompt_artifact_id: str | PromptArtifactId | None = None,
        prompt_body_sha256: str | ContentDigest | None = None,
        content_sha256: str | ContentDigest | None = None,
        prompt_body_bytes_len: int | ByteCount | None = None,
        content_byte_count: int | ByteCount | None = None,
        parent_packet_id: str | PacketId | None = None,
        conversation_root_id: str | PacketId | None = None,
        required_reply_fields: Sequence[str]
        | RequiredReplyFields = DEFAULT_REQUIRED_FIELDS,
        kill_conditions: Sequence[str | Code] = ("F-01_inherited_meaning",),
        terminal_target: str = LLM_TURN_TERMINAL_TARGET,
        evidence_ceiling: str = LLM_TURN_EVIDENCE_CEILING,
        authority_effect: str | AuthorityEffect = AuthorityEffect.NONE,
    ) -> LlmTurnPayloadV1:
        resolved_sha = (
            prompt_body_sha256 if prompt_body_sha256 is not None else content_sha256
        )
        if not resolved_sha:
            resolved_sha = "0" * 64
        resolved_len = (
            prompt_body_bytes_len
            if prompt_body_bytes_len is not None
            else content_byte_count
        )
        if resolved_len is None:
            resolved_len = 0

        return cls(
            objective=TaskObjective.from_str(objective),
            role=TurnRole.from_str(role),
            turn_kind=TurnKind.from_str(turn_kind),
            content_sha256=ContentDigest.from_str(resolved_sha),
            content_byte_count=ByteCount.from_int(resolved_len),
            candidate_budget=CandidateBudget.from_int(candidate_budget),
            operation_budget=OperationBudget.from_int(operation_budget),
            required_reply_fields=RequiredReplyFields.from_sequence(
                required_reply_fields
            ),
            terminal_target=terminal_target,
            evidence_ceiling=evidence_ceiling,
            parent_packet_id=PacketId.from_str(parent_packet_id)
            if parent_packet_id
            else None,
            conversation_root_id=PacketId.from_str(conversation_root_id)
            if conversation_root_id
            else None,
            family=LLM_TURN_FAMILY,
            schema_version=SchemaVersion.from_str(LLM_TURN_SCHEMA),
            authority_effect=AuthorityEffect(authority_effect)
            if isinstance(authority_effect, str)
            else authority_effect,
            task_id=TaskId.from_str(task_id),
            prompt_artifact_id=PromptArtifactId.from_str(prompt_artifact_id)
            if prompt_artifact_id
            else None,
            kill_conditions=tuple(Code.from_str(k) for k in kill_conditions),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "schema_version": str(self.schema_version),
            "family": self.family,
            "objective": str(self.objective),
            "role": str(self.role),
            "turn_kind": str(self.turn_kind),
            "content_sha256": str(self.content_sha256),
            "content_byte_count": int(self.content_byte_count),
            "candidate_budget": int(self.candidate_budget),
            "operation_budget": int(self.operation_budget),
            "required_reply_fields": self.required_reply_fields.as_list(),
            "terminal_target": self.terminal_target,
            "evidence_ceiling": self.evidence_ceiling,
            "parent_packet_id": str(self.parent_packet_id)
            if self.parent_packet_id
            else None,
            "conversation_root_id": str(self.conversation_root_id)
            if self.conversation_root_id
            else None,
            "authority_effect": self.authority_effect.value
            if isinstance(self.authority_effect, AuthorityEffect)
            else str(self.authority_effect),
            "task_id": str(self.task_id),
            "prompt_artifact_id": str(self.prompt_artifact_id)
            if self.prompt_artifact_id
            else None,
            "kill_conditions": [str(code) for code in self.kill_conditions],
        }
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> LlmTurnPayloadV1:
        if type(data) is not dict or any(type(key) is not str for key in data):
            raise CanonicalizationError(
                "llm-turn payload must be an exact string-keyed object"
            )
        if "passed" in data or "promotion_eligible" in data or "verified" in data:
            raise CanonicalizationError(
                "llm-turn payload carries forbidden authority-bearing fields"
            )
        allowed_fields = frozenset(
            {
                "schema_version",
                "family",
                "objective",
                "role",
                "turn_kind",
                "content_sha256",
                "prompt_body_sha256",
                "content_byte_count",
                "prompt_body_bytes_len",
                "candidate_budget",
                "operation_budget",
                "required_reply_fields",
                "terminal_target",
                "evidence_ceiling",
                "parent_packet_id",
                "conversation_root_id",
                "authority_effect",
                "task_id",
                "prompt_artifact_id",
                "kill_conditions",
            }
        )
        unknown = frozenset(data) - allowed_fields
        if unknown:
            raise CanonicalizationError(
                "llm-turn payload has unknown fields: " + ", ".join(sorted(unknown))
            )
        required_fields = frozenset(
            {
                "schema_version",
                "family",
                "objective",
                "role",
                "turn_kind",
                "candidate_budget",
                "operation_budget",
                "required_reply_fields",
                "terminal_target",
                "evidence_ceiling",
                "parent_packet_id",
                "conversation_root_id",
                "authority_effect",
            }
        )
        missing = required_fields - frozenset(data)
        if missing:
            raise CanonicalizationError(
                "llm-turn payload is missing fields: " + ", ".join(sorted(missing))
            )
        if "content_sha256" not in data and "prompt_body_sha256" not in data:
            raise CanonicalizationError("content_sha256 is required")
        if "content_byte_count" not in data and "prompt_body_bytes_len" not in data:
            raise CanonicalizationError("content_byte_count is required")
        content_sha = _wire_string(
            data.get("content_sha256", data.get("prompt_body_sha256")),
            "content_sha256",
        )
        if "content_sha256" in data and "prompt_body_sha256" in data:
            alias_sha = _wire_string(data["prompt_body_sha256"], "prompt_body_sha256")
            if alias_sha != content_sha:
                raise CanonicalizationError("content SHA aliases disagree")
        content_byte_count = _wire_int(
            data.get("content_byte_count", data.get("prompt_body_bytes_len")),
            "content_byte_count",
        )
        if "content_byte_count" in data and "prompt_body_bytes_len" in data:
            alias_count = _wire_int(
                data["prompt_body_bytes_len"], "prompt_body_bytes_len"
            )
            if alias_count != content_byte_count:
                raise CanonicalizationError("content byte-count aliases disagree")

        auth_val = _wire_string(data["authority_effect"], "authority_effect")
        if auth_val != "None":
            raise CanonicalizationError(
                "llm-turn payloads must carry AuthorityEffect None"
            )
        schema_version = _wire_string(data["schema_version"], "schema_version")
        if schema_version != LLM_TURN_SCHEMA:
            raise CanonicalizationError("llm-turn schema version is unsupported")
        family = _wire_string(data["family"], "family")
        if family != LLM_TURN_FAMILY:
            raise CanonicalizationError("llm-turn family is unsupported")

        return cls.create(
            task_id=_wire_string(data.get("task_id", "llm_turn_task"), "task_id"),
            objective=_wire_string(data["objective"], "objective"),
            role=_wire_string(data["role"], "role"),
            turn_kind=_wire_string(data["turn_kind"], "turn_kind"),
            candidate_budget=_wire_int(data["candidate_budget"], "candidate_budget"),
            operation_budget=_wire_int(data["operation_budget"], "operation_budget"),
            prompt_artifact_id=_wire_optional_string(
                data.get("prompt_artifact_id"), "prompt_artifact_id"
            ),
            prompt_body_sha256=content_sha,
            prompt_body_bytes_len=content_byte_count,
            parent_packet_id=_wire_optional_string(
                data["parent_packet_id"], "parent_packet_id"
            ),
            conversation_root_id=_wire_optional_string(
                data["conversation_root_id"], "conversation_root_id"
            ),
            required_reply_fields=_wire_string_list(
                data["required_reply_fields"], "required_reply_fields"
            ),
            kill_conditions=_wire_string_list(
                data.get("kill_conditions", ["F-01_inherited_meaning"]),
                "kill_conditions",
            ),
            terminal_target=_wire_string(data["terminal_target"], "terminal_target"),
            evidence_ceiling=_wire_string(data["evidence_ceiling"], "evidence_ceiling"),
            authority_effect=auth_val,
        )


LlmPayloadV1 = LlmTurnPayloadV1
