"""Strict JSON policy loader for the Python quality inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from operads.domain.python_development_office.quality_errors import (
    QualityPolicyLoadError,
)
from operads.domain.python_development_office.quality_inventory import (
    ClassificationRule,
    PythonQualityPolicy,
    PythonSourceClass,
    QualityThresholds,
    TestTierRule,
)

DEFAULT_POLICY_PATH = Path(__file__).with_name("python_quality_policy.v1.json")


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def _strings(value: object, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context} must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{context} entries must be non-empty strings")
    return tuple(value)


def load_quality_policy(path: Path | None = None) -> tuple[PythonQualityPolicy, bytes]:
    """Load an exact v1 policy or raise a typed refusal."""

    policy_path = path or DEFAULT_POLICY_PATH
    try:
        raw = policy_path.read_bytes()
        payload = _mapping(json.loads(raw.decode("utf-8")), "policy")
        policy = _parse_policy(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise QualityPolicyLoadError(f"{policy_path}: {exc}") from exc
    return policy, raw


def _parse_policy(payload: dict[str, Any]) -> PythonQualityPolicy:
    return PythonQualityPolicy(
        schema=str(payload["schema"]),
        version=str(payload["version"]),
        classifications=_parse_classifications(payload["classifications"]),
        thresholds=_parse_thresholds(payload["thresholds"]),
        test_tiers=_parse_test_tiers(payload["test_tiers"]),
        excluded_directories=_strings(payload["excluded_directories"], "excluded_directories"),
        receipt_directory=str(payload["receipt_directory"]),
        receipt_max_age_hours=_integer(payload, "receipt_max_age_hours"),
    )


def _parse_classifications(value: object) -> tuple[ClassificationRule, ...]:
    if not isinstance(value, list):
        raise ValueError("classifications must be an array")
    return tuple(_parse_classification(item) for item in value)


def _parse_classification(value: object) -> ClassificationRule:
    item = _mapping(value, "classification")
    return ClassificationRule(
        source_class=PythonSourceClass(item["class"]),
        patterns=_strings(item["patterns"], "classification.patterns"),
        rationale=str(item["rationale"]),
        enforce_metrics=(
            item["enforce_metrics"] if isinstance(item["enforce_metrics"], bool) else _raise_bool()
        ),
    )


def _parse_test_tiers(value: object) -> tuple[TestTierRule, ...]:
    if not isinstance(value, list):
        raise ValueError("test_tiers must be an array")
    return tuple(_parse_test_tier(item) for item in value)


def _parse_test_tier(value: object) -> TestTierRule:
    item = _mapping(value, "test tier")
    return TestTierRule(
        name=str(item["name"]),
        patterns=_strings(item["patterns"], "test_tier.patterns"),
        execution_kind=str(item["execution_kind"]),
        minimum_mutation_score=_optional_number(item, "minimum_mutation_score"),
    )


def _parse_thresholds(value: object) -> QualityThresholds:
    thresholds = _mapping(value, "thresholds")
    return QualityThresholds(
        physical_loc=_integer(thresholds, "physical_loc"),
        cyclomatic_complexity=_integer(thresholds, "cyclomatic_complexity"),
        nesting_depth=_integer(thresholds, "nesting_depth"),
        function_span=_integer(thresholds, "function_span"),
        arguments=_integer(thresholds, "arguments"),
    )


def _raise_bool() -> bool:
    raise ValueError("classification.enforce_metrics must be a boolean")


def _optional_number(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric or null")
    return float(value)


def _integer(payload: dict[str, Any], key: str) -> int:
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value
