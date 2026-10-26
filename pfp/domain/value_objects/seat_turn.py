"""The Symbol Game seat-turn request and reply.

A seat transport receives a ``SeatTurnRequestV1`` and returns a
``SeatTurnReplyV1``. PFP owns the transports, so it owns these two types; the
Woland stage runtime imports them from here. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SeatTurnRequestV1:
    """Request to execute a model/agent turn for a specific scene and seat."""

    scene_id: str
    seat_id: str
    prompt_text: str
    cognitive_operator: str = ""
    role_kind: str = "prose"
    candidate_id: str = ""
    round_index: int = 0
    context_bytes: bytes = b""

    def request_digest(self) -> str:
        """Content digest of this request for provenance tracking."""
        material = {
            "candidate_id": self.candidate_id,
            "cognitive_operator": self.cognitive_operator,
            "context_sha256": hashlib.sha256(self.context_bytes).hexdigest(),
            "prompt_text": self.prompt_text,
            "role_kind": self.role_kind,
            "round_index": self.round_index,
            "scene_id": self.scene_id,
            "seat_id": self.seat_id,
        }
        encoded = json.dumps(
            material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _optional_text(value: Any, name: str) -> None:
    if value is not None and (type(value) is not str or not value.strip()):
        raise TypeError(f"{name} must be None or a nonempty string")


@dataclass(frozen=True)
class SeatTurnReplyV1:
    """Parsed model reply from a seat turn."""

    reply_text: str
    machine_fields: dict[str, str]
    residual_colour: str = "Open"
    authority_effect: str = "None"
    raw_bytes: bytes = b""
    model: str | None = None
    provider: str | None = None
    parameters: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    request_digest: str | None = None

    def __post_init__(self) -> None:
        _optional_text(self.model, "model")
        _optional_text(self.provider, "provider")
        _optional_text(self.request_digest, "request_digest")
        if self.parameters is not None and (
            type(self.parameters) is not dict
            or any(type(key) is not str for key in self.parameters)
        ):
            raise TypeError("parameters must be None or a string-keyed dict")
        if self.usage is not None:
            if type(self.usage) is not dict:
                raise TypeError("usage must be None or a dict of exact integers")
            for key, count in self.usage.items():
                if type(key) is not str or type(count) is not int or count < 0:
                    raise TypeError(
                        "usage must map string keys to non-negative exact integers"
                    )

    def provenance(self) -> dict[str, Any]:
        """The reported provenance fields, with None kept for unreported ones."""
        return {
            "model": self.model,
            "parameters": None if self.parameters is None else dict(self.parameters),
            "provider": self.provider,
            "request_digest": self.request_digest,
            "usage": None if self.usage is None else dict(self.usage),
        }


__all__ = ["SeatTurnReplyV1", "SeatTurnRequestV1"]
