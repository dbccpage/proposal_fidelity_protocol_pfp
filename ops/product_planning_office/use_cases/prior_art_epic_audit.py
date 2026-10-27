"""Check source/navigation custody for proposed epics. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

from product_planning_office.domain.contracts.historical_sources import (
    HistoricalSourceResolver,
)

MAP_PATH = "product_planning_office/receipts/prior_art_epic_map_20261016_pfp_consolidation_successor.json"
PREDECESSOR_PATH = "product_planning_office/receipts/prior_art_epic_map_20261010.json"
PREDECESSOR_SHA256 = "992e17ba3a197e726d40d19b38e749c2fabbbbf551c182c51f77068a4756a2f3"
INDEX_PATH = "product_planning_office/plans/epics/README.md"
_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_CONTRACT_MARKERS = ("INVARIANT", "BREAK", "WITNESS", "MUTATION")
_SUCCESSOR_SCHEMA = "core.product_planning.prior-art-epic-map-successor.v1"
_EPIC_ROW_FIELDS = {
    "epic_id",
    "epic_path",
    "system_path",
    "registry_relationship",
    "direct_registry_rows",
    "sources",
}
_SUCCESSOR_FIELDS = {
    "schema",
    "authority_effect",
    "completion_boundary",
    "predecessor",
    "registry",
    "replacements",
}
_REPLACEMENT_FIELDS = {"previous", "current", "reason", "review_provenance"}
_CONSOLIDATION_FIELDS = {
    "previous_epic_paths",
    "current",
    "reason",
    "review_provenance",
}
_CONSOLIDATED_CURRENT_FIELDS = {"epic_id", "epic_path"}


def _path(
    root: Path,
    value: str,
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> Path:
    resolved = (root / value).resolve()
    if root.resolve() not in resolved.parents:
        raise ValueError(f"Path escapes repository: {value}")
    if not resolved.exists():
        origin = resolved.relative_to(root.resolve()).as_posix()
        if historical_source_resolver is not None and origin.startswith("_intelligence/"):
            selected = historical_source_resolver(root.resolve(), origin).resolve(strict=True)
            if root.resolve() not in selected.parents or not selected.is_file():
                raise ValueError(f"Historical source escapes repository or is not a file: {value}")
            return selected
        raise ValueError(f"Missing path: {value}")
    return resolved


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(
    root: Path,
    path: Path,
    historical_source_resolver: HistoricalSourceResolver | None = None,
    seen: set[Path] | None = None,
) -> tuple[dict, tuple[tuple[dict, dict], ...]]:
    """Load a full custody map or a pinned replacement/consolidation successor."""
    resolved = path.resolve()
    if seen is None:
        seen = set()
    if resolved in seen:
        raise ValueError(f"Cyclic prior-art successor: {path}")
    seen.add(resolved)
    mapping = json.loads(resolved.read_text(encoding="utf-8"))
    if mapping.get("schema") != _SUCCESSOR_SCHEMA:
        return mapping, ()

    replacements, consolidations = _successor_overlays(mapping)
    predecessor = _successor_predecessor(mapping)
    predecessor_path = _path(root, predecessor["path"], historical_source_resolver)
    if _digest(predecessor_path) != predecessor["sha256"]:
        raise ValueError("Prior-art successor predecessor digest mismatch")
    parent, inherited = _load_mapping(
        root, predecessor_path, historical_source_resolver, seen
    )
    if parent.get("authority_effect") != mapping["authority_effect"]:
        raise ValueError("Prior-art successor authority mismatch")

    registry = _successor_registry(mapping)

    rows = [dict(row) for row in parent["epics"]]
    transitions = list(inherited)
    for replacement in replacements:
        transitions.append(_apply_replacement(rows, replacement))
    for consolidation in consolidations:
        transitions.extend(_apply_consolidation(rows, consolidation))

    effective = dict(parent)
    effective.update(registry)
    effective["epics"] = rows
    return effective, tuple(transitions)


def _successor_overlays(mapping: dict) -> tuple[list[object], list[object]]:
    allowed = _SUCCESSOR_FIELDS | {"consolidations"}
    if set(mapping) != _SUCCESSOR_FIELDS and set(mapping) != allowed:
        raise ValueError("Prior-art successor schema mismatch")
    if mapping["authority_effect"] != "None" or not isinstance(
        mapping["completion_boundary"], str
    ):
        raise ValueError("Prior-art successor authority or boundary mismatch")
    replacements = mapping["replacements"]
    consolidations = mapping.get("consolidations", [])
    if not isinstance(replacements, list) or not isinstance(consolidations, list):
        raise ValueError("Prior-art successor overlays must be lists")
    if not replacements and not consolidations:
        raise ValueError("Prior-art successor requires a replacement or consolidation")
    return replacements, consolidations


def _successor_predecessor(mapping: dict) -> dict:
    predecessor = mapping["predecessor"]
    if not isinstance(predecessor, dict) or set(predecessor) != {"path", "sha256"}:
        raise ValueError("Prior-art successor predecessor binding is malformed")
    return predecessor


def _successor_registry(mapping: dict) -> dict:
    required_registry = {
        "registry_path",
        "registry_sha256",
        "registry_file_rows",
        "direct_system_count",
        "declared_system_paths",
    }
    registry = mapping["registry"]
    if not isinstance(registry, dict) or set(registry) != required_registry:
        raise ValueError("Prior-art successor registry schema mismatch")
    return registry


def _apply_replacement(rows: list[dict], replacement: object) -> tuple[dict, dict]:
    if not isinstance(replacement, dict) or set(replacement) != _REPLACEMENT_FIELDS:
        raise ValueError("Prior-art successor replacement schema mismatch")
    previous = replacement["previous"]
    current = replacement["current"]
    if (
        not isinstance(previous, dict)
        or not isinstance(current, dict)
        or set(previous) != _EPIC_ROW_FIELDS
        or set(current) != _EPIC_ROW_FIELDS
        or not isinstance(replacement["reason"], str)
        or not isinstance(replacement["review_provenance"], str)
    ):
        raise ValueError("Prior-art successor replacement contents are malformed")
    try:
        index = next(index for index, row in enumerate(rows) if row == previous)
    except StopIteration as error:
        raise ValueError("Prior-art successor parent row mismatch") from error
    if (current["epic_id"], current["epic_path"]) == (
        previous["epic_id"],
        previous["epic_path"],
    ):
        raise ValueError("Prior-art successor replacement identity mismatch")
    rows[index] = current
    return previous, current


def _apply_consolidation(
    rows: list[dict], consolidation: object
) -> list[tuple[dict, dict]]:
    if not isinstance(consolidation, dict) or set(consolidation) != _CONSOLIDATION_FIELDS:
        raise ValueError("Prior-art successor consolidation schema mismatch")
    previous_paths = consolidation["previous_epic_paths"]
    current = consolidation["current"]
    if (
        not isinstance(previous_paths, list)
        or not previous_paths
        or any(not isinstance(path, str) for path in previous_paths)
        or len(set(previous_paths)) != len(previous_paths)
        or not isinstance(current, dict)
        or set(current) != _CONSOLIDATED_CURRENT_FIELDS
        or not isinstance(consolidation["reason"], str)
        or not isinstance(consolidation["review_provenance"], str)
    ):
        raise ValueError("Prior-art successor consolidation contents are malformed")
    transitions: list[tuple[dict, dict]] = []
    for previous_path in previous_paths:
        matches = [row for row in rows if row["epic_path"] == previous_path]
        if len(matches) != 1:
            raise ValueError("Prior-art successor consolidation parent mismatch")
        previous = matches[0]
        current_row = dict(previous)
        current_row.update(current)
        if (current_row["epic_id"], current_row["epic_path"]) == (
            previous["epic_id"],
            previous["epic_path"],
        ):
            raise ValueError("Prior-art successor consolidation identity mismatch")
        rows[rows.index(previous)] = current_row
        transitions.append((previous, current_row))
    return transitions


def load_mapping(
    root: Path,
    path: Path | None = None,
    *,
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> dict:
    """Return the current effective map while retaining pinned predecessor bytes."""
    mapping, _ = _load_mapping(
        root, path or root / MAP_PATH, historical_source_resolver
    )
    return mapping


def _links(
    root: Path, document: Path, historical_source_resolver: HistoricalSourceResolver | None = None
) -> set[Path]:
    """Resolve local Markdown links in the newly authored plans/index."""
    targets = set()
    for value in _LINK.findall(document.read_text(encoding="utf-8")):
        url = urlsplit(value.strip().strip("<>"))
        if url.scheme or url.netloc or not url.path:
            continue
        relative = document.parent / unquote(url.path)
        targets.add(_path(root, str(relative), historical_source_resolver))
    return targets


def _required_link(
    root: Path,
    document: Path,
    target: Path,
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> None:
    if target.resolve() not in _links(root, document, historical_source_resolver):
        raise ValueError(f"Missing local link to {target}: {document}")


def _check_inventory(
    root: Path, mapping: dict, historical_source_resolver: HistoricalSourceResolver | None = None
) -> None:
    inventory = mapping["prior_epic_inventory"]
    if not inventory or len({row["path"] for row in inventory}) != len(inventory):
        raise ValueError("Missing or duplicate prior-epic inventory")
    for row in inventory:
        if _digest(_path(root, row["path"], historical_source_resolver)) != row["sha256"]:
            raise ValueError(f"Prior epic digest mismatch: {row['path']}")


def _check_predecessor(
    root: Path,
    mapping: dict,
    replacements: tuple[tuple[dict, dict], ...],
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> None:
    reference = mapping["predecessor"]
    if reference["path"] != PREDECESSOR_PATH or reference["sha256"] != PREDECESSOR_SHA256:
        raise ValueError("Unexpected predecessor custody pin")
    path = _path(root, PREDECESSOR_PATH, historical_source_resolver)
    if _digest(path) != PREDECESSOR_SHA256:
        raise ValueError("Predecessor digest mismatch")
    predecessor = json.loads(path.read_text(encoding="utf-8"))
    expected = {(row["epic_id"], row["epic_path"]) for row in predecessor["epics"]}
    for previous, current in replacements:
        previous_pair = (previous["epic_id"], previous["epic_path"])
        current_pair = (current["epic_id"], current["epic_path"])
        if previous_pair not in expected or current_pair == previous_pair:
            raise ValueError("Successor replacement violates historical epic identity")
        expected.remove(previous_pair)
        expected.add(current_pair)
    actual = {(row["epic_id"], row["epic_path"]) for row in mapping["epics"]}
    if actual != expected:
        raise ValueError("Successor epic identity/path coverage mismatch")
    if mapping["original_inventory_base_revision"] != predecessor["base_revision"]:
        raise ValueError("Original inventory base revision mismatch")
    expected_inventory = {
        row["path"]: row["base_sha256"] for row in predecessor["prior_epic_inventory"]
    }
    actual_inventory = {row["path"]: row["base_sha256"] for row in mapping["prior_epic_inventory"]}
    if actual_inventory != expected_inventory:
        raise ValueError("Original inventory custody mismatch")


def audit(
    root: Path,
    map_path: Path | None = None,
    *,
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> dict:
    mapping, replacements = _load_mapping(
        root, map_path or root / MAP_PATH, historical_source_resolver
    )
    if mapping["authority_effect"] != "None":
        raise ValueError("Unexpected authority effect")
    registry_path = _path(root, mapping["registry_path"], historical_source_resolver)
    if _digest(registry_path) != mapping["registry_sha256"]:
        raise ValueError("Registry digest mismatch")
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    files = registry["files"]
    assignments = Counter(row["folder"] for row in files)
    paths = {row["file_location"]: row["folder"] for row in files}
    for path in paths:
        _path(root, path, historical_source_resolver)
    declared_list = registry["summary"]["folders_covered"]
    declared = set(declared_list)
    if (
        mapping["registry_file_rows"] != len(files)
        or mapping["direct_system_count"] != len(assignments)
        or mapping["declared_system_paths"] != sorted(declared)
        or len(declared_list) != len(declared)
    ):
        raise ValueError("Registry summary mismatch")
    epics = mapping["epics"]
    systems = [row["system_path"] for row in epics]
    # An architecture plan can carry several system rows, but never with a
    # conflicting id/path pairing or duplicate custody of the same system row.
    if set(systems) != declared:
        raise ValueError("Epic system coverage mismatch")
    _check_epic_identity_paths(epics)
    _check_predecessor(root, mapping, replacements, historical_source_resolver)
    _check_inventory(root, mapping, historical_source_resolver)
    index = _path(root, INDEX_PATH, historical_source_resolver)
    for row in epics:
        _check_epic(root, row, assignments, paths, historical_source_resolver)
        _required_link(
            root,
            index,
            _path(root, row["epic_path"], historical_source_resolver),
            historical_source_resolver,
        )
        _required_link(
            root,
            index,
            _path(root, row["system_path"], historical_source_resolver),
            historical_source_resolver,
        )
    return {
        "status": "PASS",
        "authority_effect": "None",
        "scope": "source and navigation custody only",
        "registry_rows": len(files),
        "direct_systems": len(assignments),
        "epics": len(epics),
    }


def _check_epic_identity_paths(epics: list[dict]) -> None:
    ids_to_paths: dict[str, str] = {}
    paths_to_ids: dict[str, str] = {}
    system_custody: set[tuple[str, str, str]] = set()
    for row in epics:
        epic_id = row["epic_id"]
        epic_path = row["epic_path"]
        if epic_id in ids_to_paths and ids_to_paths[epic_id] != epic_path:
            raise ValueError("Duplicate epic identity")
        if epic_path in paths_to_ids and paths_to_ids[epic_path] != epic_id:
            raise ValueError("Duplicate epic path")
        custody = (row["system_path"], epic_id, epic_path)
        if custody in system_custody:
            raise ValueError("Duplicate system custody")
        ids_to_paths[epic_id] = epic_path
        paths_to_ids[epic_path] = epic_id
        system_custody.add(custody)


def _check_epic(
    root: Path,
    row: dict,
    assignments: Counter,
    paths: dict[str, str],
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> None:
    system = row["system_path"]
    epic = _path(root, row["epic_path"], historical_source_resolver)
    text = epic.read_text(encoding="utf-8")
    expected = "DIRECT_REGISTRY_ASSIGNMENT" if assignments[system] else "INTEGRATION_HYPOTHESIS"
    if (
        row["direct_registry_rows"] != assignments[system]
        or row["registry_relationship"] != expected
    ):
        raise ValueError(f"Assignment mismatch: {system}")
    for marker in (row["epic_id"], "AuthorityEffect:** None", "RESEARCH_HOLD"):
        if marker not in text:
            raise ValueError(f"Missing plan contract {marker}: {epic}")
    for marker in _CONTRACT_MARKERS:
        if re.search(rf"\b{marker}\b", text) is None:
            raise ValueError(f"Missing plan contract {marker}: {epic}")
    _required_link(
        root, epic, _path(root, system, historical_source_resolver), historical_source_resolver
    )
    suite_index = epic.parent / "README.md"
    if (
        not suite_index.exists()
        and epic.parent.parent == (root / INDEX_PATH).parent
        and tuple(epic.parent.glob("*.md")) == (epic,)
    ):
        # A consolidated single-file suite uses the declared parent register.
        suite_index = _path(root, INDEX_PATH, historical_source_resolver)
    _required_link(root, suite_index, epic, historical_source_resolver)
    if not row["sources"]:
        raise ValueError(f"No source links: {system}")
    for source in row["sources"]:
        _check_source(root, source, system, paths, historical_source_resolver)
        _required_link(
            root,
            epic,
            _path(root, source["path"], historical_source_resolver),
            historical_source_resolver,
        )


def _check_source(
    root: Path,
    source: dict,
    system: str,
    paths: dict[str, str],
    historical_source_resolver: HistoricalSourceResolver | None = None,
) -> None:
    if source["path"] not in paths:
        raise ValueError(f"Source absent from registry: {source['path']}")
    if source["registry_system"] != paths[source["path"]]:
        raise ValueError(f"Source registry assignment mismatch: {source['path']}")
    if _digest(_path(root, source["path"], historical_source_resolver)) != source["sha256"]:
        raise ValueError(f"Source digest mismatch: {source['path']}")
    expected = "direct" if source["registry_system"] == system else "integration_hypothesis"
    if source["transfer"] != expected:
        raise ValueError(f"Source transfer mismatch: {source['path']}")


def main(*, historical_source_resolver: HistoricalSourceResolver | None = None) -> int:
    root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
    try:
        print(
            json.dumps(
                audit(root, historical_source_resolver=historical_source_resolver), sort_keys=True
            )
        )
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
