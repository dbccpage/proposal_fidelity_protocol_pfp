"""
pipeline_contract.py - Validation of the digest pins in the C001 ``pipeline.json``.

A digest pin is either a lowercase 64-hex SHA-256 value or explicitly unset
(``null`` together with ``"<field>_status": "UNSET"``). A pin whose value is the
SHA-256 of an empty input (for example empty bytes or the two bytes ``[]``) is a
placeholder, not a pin, and is refused with ``PIN_UNSET_SENTINEL_DIGEST``.

Report status:
- ``READY``: every digest pin is a well-formed, non-sentinel SHA-256 value.
- ``NOT_READY``: no refusal, but at least one pin is explicitly unset.
- ``REFUSED``: at least one pin is a sentinel digest, malformed, or inconsistent
  with its status field, or the schema/challenge header is wrong.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_SCHEMA = "omega.symbol-game.pipeline.v1"
PIPELINE_PATH = Path(__file__).resolve().parent / "pipeline.json"

DIGEST_PIN_FIELDS: tuple[str, ...] = (
    "tokenizer_json_sha256",
    "prompt_template_digest",
    "host_digest",
    "public_selection_table_sha256",
)
UNSET = "UNSET"

# SHA-256 digests of empty or trivially empty inputs. None of them can pin a
# tokenizer file, a prompt template, a host build or a selection table.
SENTINEL_PREIMAGES: tuple[bytes, ...] = (b"", b"[]", b"{}", b"null", b'""', b"\n")
SENTINEL_DIGESTS: dict[str, bytes] = {
    hashlib.sha256(preimage).hexdigest(): preimage for preimage in SENTINEL_PREIMAGES
}

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")

REFUSAL_CODES: frozenset[str] = frozenset(
    {
        "PIPELINE_NOT_OBJECT",
        "PIPELINE_SCHEMA_MISMATCH",
        "PIPELINE_CHALLENGE_MISMATCH",
        "PIN_UNSET_SENTINEL_DIGEST",
        "PIN_MALFORMED_DIGEST",
        "PIN_MISSING",
        "PIN_STATUS_INCONSISTENT",
    }
)
NOT_READY_CODES: frozenset[str] = frozenset({"PIN_UNSET"})


@dataclass(frozen=True)
class PinFinding:
    field: str
    code: str
    detail: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return (self.field, self.code, self.detail) == (other.field, other.code, other.detail)

    def __hash__(self) -> int:
        return hash((type(self), self.field, self.code, self.detail))


@dataclass(frozen=True)
class PipelinePinReport:
    status: str
    findings: tuple[PinFinding, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return (self.status, self.findings) == (other.status, other.findings)

    def __hash__(self) -> int:
        return hash((type(self), self.status, self.findings))

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)

    @property
    def is_ready(self) -> bool:
        return self.status == "READY"


class PipelinePinError(ValueError):
    """Typed refusal raised by :func:`require_ready_pipeline`."""

    def __init__(self, report: PipelinePinReport) -> None:
        self.report = report
        self.code = report.findings[0].code if report.findings else report.status
        super().__init__(f"C001 pipeline pins {report.status}: {', '.join(report.codes)}")


def _check_pin(data: dict[str, Any], field: str) -> PinFinding | None:
    status_key = f"{field}_status"
    status = data.get(status_key)
    if field not in data:
        return PinFinding(field, "PIN_MISSING", "field absent from pipeline.json")
    value = data[field]
    if value is None:
        if status == UNSET:
            return PinFinding(field, "PIN_UNSET", f"{status_key} is UNSET")
        return PinFinding(
            field, "PIN_STATUS_INCONSISTENT", f"null value requires {status_key} == 'UNSET'"
        )
    if status is not None:
        return PinFinding(
            field, "PIN_STATUS_INCONSISTENT", f"{status_key} must be absent when a digest is set"
        )
    if type(value) is not str or _SHA256_HEX.fullmatch(value) is None:
        return PinFinding(field, "PIN_MALFORMED_DIGEST", "expected 64 lowercase hex characters")
    if value in SENTINEL_DIGESTS:
        return PinFinding(
            field,
            "PIN_UNSET_SENTINEL_DIGEST",
            f"SHA-256 of the empty input {SENTINEL_DIGESTS[value]!r}",
        )
    return None


def validate_pipeline_pins(data: object) -> PipelinePinReport:
    """Classify the digest pins of a parsed ``pipeline.json`` as READY, NOT_READY or REFUSED."""
    if type(data) is not dict:
        finding = PinFinding(
            "pipeline", "PIPELINE_NOT_OBJECT", "pipeline.json must hold a JSON object"
        )
        return PipelinePinReport("REFUSED", (finding,))
    findings: list[PinFinding] = []
    if data.get("schema") != PIPELINE_SCHEMA:
        findings.append(
            PinFinding("schema", "PIPELINE_SCHEMA_MISMATCH", f"expected {PIPELINE_SCHEMA}")
        )
    if data.get("challenge_id") != "C001":
        findings.append(PinFinding("challenge_id", "PIPELINE_CHALLENGE_MISMATCH", "expected C001"))
    for field in DIGEST_PIN_FIELDS:
        finding = _check_pin(data, field)
        if finding is not None:
            findings.append(finding)
    codes = {finding.code for finding in findings}
    if codes & REFUSAL_CODES:
        status = "REFUSED"
    elif codes & NOT_READY_CODES:
        status = "NOT_READY"
    else:
        status = "READY"
    return PipelinePinReport(status, tuple(findings))


def load_pipeline(path: Path = PIPELINE_PATH) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def require_ready_pipeline(data: object) -> PipelinePinReport:
    """Return the report if every pin is set; otherwise raise :class:`PipelinePinError`."""
    report = validate_pipeline_pins(data)
    if not report.is_ready:
        raise PipelinePinError(report)
    return report
