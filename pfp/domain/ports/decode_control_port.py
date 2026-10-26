"""Domain port and value objects for decode controls and logit-level attention interventions.

AuthorityEffect: None.
Clean Architecture Layer: Domain Port
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol


class ControlKind(str, Enum):
    """The 5 canonical decode control intervention kinds."""

    NONE = "NONE"
    CARRIER_MASK = "CARRIER_MASK"
    LOGIT_BIAS = "LOGIT_BIAS"
    JSON_SCHEMA = "JSON_SCHEMA"
    GBNF = "GBNF"


@dataclass(frozen=True)
class CarrierMask:
    """Exact token set and character spans defining the carrier restriction."""

    allowed_tokens: tuple[int, ...]
    span_character_offsets: tuple[tuple[int, int], ...] = field(default_factory=tuple)

    def is_token_allowed(self, token_id: int) -> bool:
        return token_id in self.allowed_tokens


@dataclass(frozen=True)
class LogitBias:
    """Bounded integer logit steering vector."""

    biases: Mapping[int, int] = field(default_factory=dict)
    description: str = ""

    def get_bias(self, token_id: int) -> int:
        return self.biases.get(token_id, 0)


@dataclass(frozen=True)
class GrammarMask:
    """Deterministic structured output constraint (JSON schema or GBNF grammar)."""

    grammar_text: str
    grammar_type: str = "json_schema"  # "json_schema" or "gbnf"
    grammar_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.grammar_sha256 and self.grammar_text:
            digest = hashlib.sha256(self.grammar_text.encode("utf-8")).hexdigest()
            object.__setattr__(self, "grammar_sha256", digest)


@dataclass(frozen=True)
class DecodeControlSpec:
    """Specification of decoding interventions for a model turn."""

    control_kind: ControlKind = ControlKind.NONE
    carrier_mask: CarrierMask | None = None
    grammar_mask: GrammarMask | None = None
    logit_bias: LogitBias | None = None
    temperature: str = "0"
    max_tokens: int = 64


DECODE_RECEIPT_SCHEMA = "omega.symbol_game.decode_receipt.v1"


@dataclass(frozen=True)
class DecodeControlReceipt:
    """Immutable execution receipt recording the applied decode control and outcome."""

    receipt_id: str
    case_id: str
    control_kind: str
    output_tokens: tuple[int, ...]
    allowed_tokens: tuple[int, ...] = field(default_factory=tuple)
    logit_biases: tuple[tuple[int, int], ...] = field(default_factory=tuple)
    grammar_sha256: str | None = None
    honored: bool = True
    authority_effect: str = "None"
    schema_version: str = DECODE_RECEIPT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "case_id": self.case_id,
            "control_kind": self.control_kind,
            "allowed_tokens": list(self.allowed_tokens),
            "output_tokens": list(self.output_tokens),
            "logit_biases": [list(pair) for pair in self.logit_biases],
            "grammar_sha256": self.grammar_sha256,
            "authority_effect": self.authority_effect,
        }

    def digest_sha256(self) -> str:
        data = self.to_dict()
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


class DecodeControlPort(Protocol):
    """Protocol for applying and verifying decode controls across local and hosted models."""

    def apply_decode_control(
        self,
        spec: DecodeControlSpec,
        prompt: str,
        case_id: str = "case_unknown",
    ) -> tuple[str, DecodeControlReceipt]:
        """Apply the specified decoding control, generating text and emitting a receipt."""
        ...

    def verify_decode_receipt(self, receipt: DecodeControlReceipt) -> dict[str, Any]:
        """Verify V1 token and control metadata outside the model."""
        ...


@dataclass(frozen=True, slots=True)
class DecodeControlReceiptV2:
    """Actual bytes and a declared validator, never an assertion of correctness.

    V1 retains its token/hash metadata interpretation. V2 must be replayed
    against the caller's independently retained request and language.
    """

    request_bytes: bytes
    output_bytes: bytes
    language_bytes: bytes
    validation_outcome: str
    enforcement: str = "POST_VALIDATION"
    tokenizer_profile: str | None = None
    validation_method: str = "finite-utf8.v1"

    def __post_init__(self) -> None:
        for name, limit in (
            ("request_bytes", 16384),
            ("output_bytes", 16384),
            ("language_bytes", 32768),
        ):
            value = getattr(self, name)
            if type(value) is not bytes or len(value) > limit:
                raise ValueError(f"{name} requires exact bounded bytes")
        if not self.request_bytes or not self.language_bytes:
            raise ValueError("request and language bytes are required")
        if self.validation_outcome not in {"VALID", "INVALID", "NOT_MEASURED"}:
            raise ValueError("invalid validation outcome")
        if self.enforcement not in {"POST_VALIDATION", "PROVIDER_REQUESTED", "FIXTURE"}:
            raise ValueError("unattested generation enforcement cannot be claimed")

    def to_dict(self) -> dict[str, Any]:
        def ref(raw: bytes) -> str:
            return "sha256:" + hashlib.sha256(raw).hexdigest()

        return {
            "schema_version": "omega.symbol_game.decode_receipt.v2",
            "request_hex": self.request_bytes.hex(),
            "request_sha256": ref(self.request_bytes),
            "output_hex": self.output_bytes.hex(),
            "output_sha256": ref(self.output_bytes),
            "language_hex": self.language_bytes.hex(),
            "language_sha256": ref(self.language_bytes),
            "tokenizer_profile": self.tokenizer_profile,
            "enforcement": self.enforcement,
            "validation_method": self.validation_method,
            "validation_outcome": self.validation_outcome,
            "authority_effect": "None",
        }
