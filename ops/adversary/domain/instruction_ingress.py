"""Request-bound evidence returned by an external instruction ingress verifier.

This receipt is a transport contract, not an admission policy or an authority
issuer. The verifier and its admission ledger remain unbound in v0.1.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass

from .models import AdversaryBoutRequestV1

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MAX_PLAN_PAYLOAD_BYTES = 131072
_PLAN_FIELDS = frozenset({
    "schema_version", "manifest_digest", "selection_digest", "plan_digest",
    "source_snapshot_digest", "ordered_bodies_digest", "ordered_operand_bodies",
    "source_digests", "operation_ids", "instruction_bytes", "authority_effect",
})


def instruction_request_digest(request: AdversaryBoutRequestV1) -> str:
    """Bind every request field, including the profile budget and carrier input.

    The canonical form is ASCII-escaped compact JSON with sorted keys, the same
    form every other digest on this seam uses, so an operator minting
    ``task_shape.request_digest`` reproduces exactly this.
    """
    if type(request) is not AdversaryBoutRequestV1:
        raise TypeError("instruction ingress requires an exact AdversaryBoutRequestV1")
    canonical = json.dumps(
        asdict(request), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class InstructionIngressReceiptV1:
    """A verifier's claim about one exact request and one compiled plan.

    A caller cannot make this authoritative by constructing the value object;
    the composition root must supply an independently trusted verifier.
    """

    request_digest: str
    plan_digest: str
    source_snapshot_digest: str
    admission_receipt_id: str
    verifier_id: str
    plan_payload: bytes | None = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        for name in (
            "request_digest", "plan_digest", "source_snapshot_digest",
            "admission_receipt_id",
        ):
            value = getattr(self, name)
            if type(value) is not str or _DIGEST.fullmatch(value) is None:
                raise ValueError(f"{name} must be a sha256:<lowercase hex> reference")
        if (
            type(self.verifier_id) is not str
            or not self.verifier_id.strip()
            or self.verifier_id.strip() != self.verifier_id
        ):
            raise ValueError("verifier_id must be a normalized nonempty string")
        if self.authority_effect != "None":
            raise ValueError("instruction ingress has AuthorityEffect None")
        self.native_instruction_plan()

    def native_instruction_plan(self) -> dict | None:
        """Parse immutable canonical transport bytes; native host checks body hashes."""
        raw = self.plan_payload
        if raw is None:
            return None
        if type(raw) is not bytes or not 0 < len(raw) <= _MAX_PLAN_PAYLOAD_BYTES:
            raise ValueError("instruction plan payload must be bounded exact bytes")
        try:
            value = json.loads(raw)
        except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
            raise ValueError("instruction plan payload is not JSON") from exc
        if type(value) is not dict or value.keys() != _PLAN_FIELDS:
            raise ValueError("instruction plan payload has an open shape")
        try:
            canonical = json.dumps(
                value, sort_keys=True, separators=(",", ":"),
                ensure_ascii=True, allow_nan=False,
            ).encode("ascii")
        except (ValueError, TypeError, RecursionError) as exc:
            raise ValueError("instruction plan payload cannot be canonicalized") from exc
        if canonical != raw:
            raise ValueError("instruction plan payload is not canonical")
        if (
            value["schema_version"] != "oewas.adversary.instruction_plan_transport.v0.1"
            or value["authority_effect"] != "None"
            or value["plan_digest"] != self.plan_digest
            or value["source_snapshot_digest"] != self.source_snapshot_digest
            or value["manifest_digest"] != self.admission_receipt_id
        ):
            raise ValueError("instruction plan payload differs from ingress receipt")
        return value
