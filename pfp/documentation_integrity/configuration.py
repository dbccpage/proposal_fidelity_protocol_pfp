"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .domain import (
    ACTIVE_PATH_MAP_PATH,
    CONTRACT_PATH,
    DOC_ROOT,
    EXEMPTIONS_PATH,
    IntegrityError,
    is_document_relative_path,
)

MAX_CONTROL_BYTES = 16 * 1024 * 1024


def load_json(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_CONTROL_BYTES:
            raise IntegrityError(f"JSON control file exceeds {MAX_CONTROL_BYTES} bytes: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise IntegrityError(f"JSON object required in {path}")
    return value


def load_contract() -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    required = {
        "schema_version",
        "documentation_root",
        "source_roots",
        "generated_control_artifacts",
        "raw_archive_prefix",
        "education_copy_sets",
        "canonical_frontmatter",
        "allowed_dispositions",
        "allowed_claim_statuses",
        "source_drift_roots",
        "text_extensions",
    }
    missing = sorted(required - set(contract))
    if missing:
        raise IntegrityError(f"Documentation contract is missing: {', '.join(missing)}")
    return contract


def load_exemptions() -> dict[str, dict[str, Any]]:
    if not EXEMPTIONS_PATH.exists():
        return {}
    document = load_json(EXEMPTIONS_PATH)
    exemptions = document.get("exemptions", {})
    if not isinstance(exemptions, dict):
        raise IntegrityError("source-exemptions.json must contain an object named exemptions")
    normalized: dict[str, dict[str, Any]] = {}
    for path, value in exemptions.items():
        if not isinstance(path, str) or not isinstance(value, dict):
            raise IntegrityError("Each source exemption must map a source path to an object")
        reason = value.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise IntegrityError(f"Source exemption for {path} requires a non-empty reason")
        normalized[path] = value
    return normalized


def active_route_destinations() -> dict[str, str]:
    """Load moved active routes so deleted legacy paths retain a real destination."""

    if not ACTIVE_PATH_MAP_PATH.exists():
        return {}
    document = load_json(ACTIVE_PATH_MAP_PATH)
    routes = document.get("routes")
    if not isinstance(routes, list):
        raise IntegrityError("active-path-map.json must contain a routes list")
    destinations: dict[str, str] = {}
    for number, route in enumerate(routes, start=1):
        if not isinstance(route, dict):
            raise IntegrityError(f"active-path-map.json route {number} is not an object")
        source = route.get("from")
        destination = route.get("to")
        if not isinstance(source, str) or not is_document_relative_path(source):
            raise IntegrityError(f"active-path-map.json route {number} has an unsafe from path")
        if not isinstance(destination, str) or not is_document_relative_path(destination):
            raise IntegrityError(f"active-path-map.json route {number} has an unsafe to path")
        previous = destinations.setdefault(source, destination)
        if previous != destination:
            raise IntegrityError(f"active-path-map.json maps {source} to more than one destination")
    return destinations


def archive_record_destinations(contract: dict[str, Any]) -> dict[str, str]:
    """Read the archive builder's raw-to-record map when the rewrite estate exists."""

    manifest = DOC_ROOT / "archive" / "records" / "manifest.jsonl"
    if not manifest.exists():
        return {}
    documentation_root = contract["documentation_root"].rstrip("/")
    destinations: dict[str, str] = {}
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise IntegrityError(f"Cannot read archive record manifest {manifest}: {error}") from error
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise IntegrityError(
                f"Invalid archive record manifest line {number}: {error}"
            ) from error
        raw_path = record.get("raw_path") if isinstance(record, dict) else None
        record_path = record.get("record_path") if isinstance(record, dict) else None
        if not isinstance(raw_path, str) or not isinstance(record_path, str):
            raise IntegrityError(
                f"Archive record manifest line {number} lacks raw_path or record_path"
            )
        absolute_raw_path = f"{documentation_root}/{raw_path.lstrip('/')}"
        if absolute_raw_path in destinations and destinations[absolute_raw_path] != record_path:
            raise IntegrityError(f"Archive record manifest maps {raw_path} more than once")
        destinations[absolute_raw_path] = record_path
    return destinations


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise IntegrityError(f"Cannot read ledger {path}: {error}") from error
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise IntegrityError(f"Invalid JSONL in {path}:{number}: {error}") from error
        if not isinstance(value, dict):
            raise IntegrityError(f"Ledger row {number} is not an object")
        rows.append(value)
    return rows
