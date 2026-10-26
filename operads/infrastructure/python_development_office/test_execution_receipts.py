"""Filesystem receipt loader and system clock for Python quality evidence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omega_engine_operads.domain.python_development_office.test_execution_receipt import (
    TestExecutionReceipt,
)


class FileSystemTestExecutionReceiptRepository:
    """Load versioned JSON receipts without executing their recorded commands."""

    def load(self, receipt_directory: str) -> tuple[TestExecutionReceipt, ...]:
        root = Path(receipt_directory)
        if not root.exists():
            return ()
        if root.is_symlink() or not root.is_dir():
            raise ValueError(f"test receipt path must be a real directory: {root}")
        receipts: list[TestExecutionReceipt] = []
        for path in sorted(root.iterdir()):
            if path.suffix != ".json":
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"test receipt must be a regular JSON file: {path}")
            receipts.append(_parse_receipt(path))
        return tuple(receipts)


class SystemUtcClock:
    """Production UTC clock adapter."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def _parse_receipt(path: Path) -> TestExecutionReceipt:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("receipt root must be an object")
        allowed = {
            "schema",
            "receipt_id",
            "tier",
            "execution_kind",
            "command",
            "python_version",
            "exit_code",
            "test_count",
            "target_paths",
            "source_sha256",
            "policy_sha256",
            "completed_at",
            "asserted_status",
            "mutation_score",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(f"unknown receipt fields: {', '.join(unknown)}")
        return TestExecutionReceipt(
            schema=_string(payload, "schema"),
            receipt_id=_string(payload, "receipt_id"),
            tier=_string(payload, "tier"),
            execution_kind=_string(payload, "execution_kind"),
            command=_string_tuple(payload, "command"),
            python_version=_string(payload, "python_version"),
            exit_code=_integer(payload, "exit_code"),
            test_count=_integer(payload, "test_count"),
            target_paths=_string_tuple(payload, "target_paths"),
            source_sha256=_string(payload, "source_sha256"),
            policy_sha256=_string(payload, "policy_sha256"),
            completed_at=_timestamp(payload, "completed_at"),
            asserted_status=_string(payload, "asserted_status"),
            mutation_score=_optional_number(payload, "mutation_score"),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid test execution receipt {path}: {exc}") from exc


def _string(payload: dict[str, Any], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _string_tuple(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be an array of strings")
    return tuple(value)


def _integer(payload: dict[str, Any], key: str) -> int:
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _timestamp(payload: dict[str, Any], key: str) -> datetime:
    value = _string(payload, key)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{key} must include a timezone")
    return parsed


def _optional_number(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric or null")
    return float(value)
