"""Common types, schemas, and serialization utilities for prompt representations.

Governing Standard: Proposal Fidelity Protocol (PFP).
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Annotated, Any, Dict, Literal, Mapping, Tuple

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

MAX_PROMPT_BYTES = 65536
MAX_SEGMENTS = 256
ROLE_REGEX = re.compile(r"^(task|constraint|context|output|unresolved)$")
SLOT_REGEX = re.compile(r"^s[0-9]+$")
SHA256_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$")

Role = Literal["task", "constraint", "context", "output", "unresolved"]
RepresentationKind = Literal[
    "raw",
    "structured",
    "relational",
    "symbolic",
    "operadic",
    "egraph",
    "diagram",
    "cochain",
]

ROLE_TO_SYMBOLIC: Mapping[Role, str] = {
    "task": "q",
    "constraint": "c",
    "context": "d",
    "output": "o",
    "unresolved": "u",
}

SYMBOLIC_TO_ROLE: Mapping[str, Role] = {
    "q": "task",
    "c": "constraint",
    "d": "context",
    "o": "output",
    "u": "unresolved",
}

Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


def sha256_digest(data: bytes | str) -> str:
    """Calculates lowercase hexadecimal SHA-256 digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic python-sorted-json-v1 bytes (not RFC 8785/JCS)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_str(obj: Any) -> str:
    """Deterministic python-sorted-json-v1 string."""
    return canonical_json_bytes(obj).decode("utf-8")


class BaseRepresentationRecord(BaseModel):
    """Immutable base model forbidding extra fields and enforcing strict typing."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        revalidate_instances="always",
    )
