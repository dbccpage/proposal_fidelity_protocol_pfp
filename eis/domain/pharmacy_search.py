"""Search DTOs and the explicit pharmacy rule-content serialization profile.

This profile is sorted-key UTF-8 JSON over string/list metadata, not RFC 8785.
Observation identity, timestamps, admission and ranking are not rule identity.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

RULE_CONTENT_KEYS = (
    "failure_class", "target_pattern", "constraint_type", "operatorizability",
    "action", "severity", "negative_fixture", "positive_fixture", "scope", "guidance_text",
)


def rule_content_bytes(record: Mapping[str, Any]) -> bytes:
    return json.dumps(
        {key: record[key] for key in RULE_CONTENT_KEYS},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def rule_content_sha256(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(rule_content_bytes(record)).hexdigest()


@dataclass(frozen=True)
class PharmacyQuery:
    domain: str
    tags: tuple[str, ...]
    stage: str
    prompt_field: str
    scope: str
    limit: int = 3
    suspended_ids: tuple[str, ...] = ()


class PharmacyMatch(TypedDict):
    antibody_id: str
    rule_digest: str
    guidance_text: str
    target_pattern: str
    scope: dict[str, Any]
    admission_reference: dict[str, Any]


class PharmacyExclusion(TypedDict):
    antibody_id: str
    reason: str


class PharmacySearchResult(TypedDict):
    catalog_digest: str
    request_digest: str
    selected: list[PharmacyMatch]
    exclusions: list[PharmacyExclusion]
    authority_effect: str
    hits: NotRequired[list[dict[str, Any]]]
    subject_digest: NotRequired[str]
