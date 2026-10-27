"""core.work_packet.v1 schema validation (SWARM-L2/L4/L5).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .authority_effect_v1 import AuthorityEffectV1
from .work_packet_validation_error import WorkPacketValidationError

REQUIRED_FIELDS = (
    "packet_id",
    "base_epoch_sha",
    "branch",
    "worktree_id",
    "read_paths",
    "write_paths",
    "exclusive_resources",
    "forbidden_paths",
    "residual_slots",
)


def _canonical_authority_effect(value: object) -> AuthorityEffectV1:
    if type(value) is AuthorityEffectV1:
        return value
    if value is None or (type(value) is str and value == "None"):
        return AuthorityEffectV1.NONE
    raise WorkPacketValidationError(f"INVALID_AUTHORITY_EFFECT:{value!r}")


def _as_str_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        raise WorkPacketValidationError(f"MISSING_FIELD:{field_name}")
    if not isinstance(value, (list, tuple)):
        raise WorkPacketValidationError(f"INVALID_TYPE:{field_name}")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise WorkPacketValidationError(f"INVALID_ITEM:{field_name}")
        out.append(item)
    return tuple(out)


@dataclass(frozen=True)
class WorkPacketV1:
    packet_id: str
    base_epoch_sha: str
    branch: str
    worktree_id: str
    read_paths: tuple[str, ...]
    write_paths: tuple[str, ...]
    exclusive_resources: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    residual_slots: tuple[str, ...]
    authority_effect: AuthorityEffectV1 = AuthorityEffectV1.NONE
    schema: str = "core.work_packet.v1"
    extras: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self) is not WorkPacketV1:
            raise WorkPacketValidationError("WORK_PACKET_SUBCLASS_REFUSED")
        authority_effect = _canonical_authority_effect(self.authority_effect)
        if authority_effect is not self.authority_effect:
            object.__setattr__(self, "authority_effect", authority_effect)


def validate_work_packet(raw: Mapping[str, Any]) -> WorkPacketV1:
    if not isinstance(raw, Mapping):
        raise WorkPacketValidationError("INVALID_ROOT")

    for key in REQUIRED_FIELDS:
        if key not in raw:
            raise WorkPacketValidationError(f"MISSING_FIELD:{key}")

    packet_id = raw["packet_id"]
    if not isinstance(packet_id, str) or not packet_id.strip():
        raise WorkPacketValidationError("EMPTY_PACKET_ID")

    base = raw["base_epoch_sha"]
    if not isinstance(base, str) or not base.strip():
        raise WorkPacketValidationError("MISSING_BASE_EPOCH")

    branch = raw["branch"]
    worktree_id = raw["worktree_id"]
    if not isinstance(branch, str) or not branch.strip():
        raise WorkPacketValidationError("MISSING_BRANCH")
    if not isinstance(worktree_id, str) or not worktree_id.strip():
        raise WorkPacketValidationError("MISSING_WORKTREE_ID")

    write_paths = _as_str_tuple(raw["write_paths"], "write_paths")
    if len(write_paths) == 0:
        raise WorkPacketValidationError("EMPTY_WRITE_PATHS")

    auth = _canonical_authority_effect(raw.get("authority_effect", "None"))

    return WorkPacketV1(
        packet_id=packet_id.strip(),
        base_epoch_sha=base.strip(),
        branch=branch.strip(),
        worktree_id=worktree_id.strip(),
        read_paths=_as_str_tuple(raw["read_paths"], "read_paths"),
        write_paths=write_paths,
        exclusive_resources=_as_str_tuple(
            raw["exclusive_resources"], "exclusive_resources"
        ),
        forbidden_paths=_as_str_tuple(raw["forbidden_paths"], "forbidden_paths"),
        residual_slots=_as_str_tuple(raw["residual_slots"], "residual_slots"),
        authority_effect=auth,
    )
