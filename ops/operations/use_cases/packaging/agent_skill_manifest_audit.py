#!/usr/bin/env python3
"""Schema and capability audit for the canonical agent and skill manifests.

This module intentionally uses only the Python standard library. A missing YAML
package must not disable governance checks. It supports the flat frontmatter
subset used by the canonical manifests and rejects unsupported nested syntax.
AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_SKILL_FIELDS = (
    "name",
    "description",
    "operad_source_colours",
    "operad_target_colour",
    "operad_arity",
    "operad_residual",
)
REQUIRED_AGENT_FIELDS = (
    "name",
    "description",
    "model",
    "authority_effect",
    "tools",
    "standalone",
    "licensed_skills",
    "licensed_colours",
)
PLACEHOLDER_PREFIXES = (
    "canonical skill package for ",
    "operadic capability slice for ",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    locus: str
    code: str
    detail: str

    def render(self) -> str:
        return f"[{self.severity}] {self.locus}: {self.code}: {self.detail}"


def _parse_value(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return None
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if value[0:1] in {'"', "'", "[", "{"}:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                return ast.literal_eval(value)
        except (SyntaxError, ValueError) as err:
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                return (
                    []
                    if not inner
                    else [item.strip().strip('"\'') for item in inner.split(",")]
                )
            raise ValueError(f"unsupported frontmatter value {value!r}: {err}") from err
    try:
        return int(value)
    except ValueError:
        return value


def _unquote_item(item_val: str) -> str:
    quoted = item_val.startswith(('"', "'")) and item_val.endswith(('"', "'"))
    if quoted and len(item_val) >= 2:
        return item_val[1:-1]
    return item_val


def _append_frontmatter_item(data: dict[str, Any], key: str, stripped: str) -> None:
    item_val = _unquote_item(stripped[2:].strip())
    if not isinstance(data[key], list):
        data[key] = []
    data[key].append(item_val)


def _assign_frontmatter_key(data: dict[str, Any], line: str, line_no: int) -> str | None:
    if line[:1].isspace() or ":" not in line:
        raise ValueError(f"unsupported nested or malformed frontmatter at line {line_no}")
    key, raw = line.split(":", 1)
    key = key.strip()
    if not key or key in data:
        raise ValueError(f"empty or duplicate frontmatter key at line {line_no}")
    val = _parse_value(raw)
    if val is None and not raw.strip():
        data[key] = []
        return key
    data[key] = val
    return None


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as err:
        raise ValueError("missing closing frontmatter delimiter") from err
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for line_no, line in enumerate(lines[1:end], start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key is not None:
            _append_frontmatter_item(data, current_list_key, stripped)
            continue
        current_list_key = _assign_frontmatter_key(data, line, line_no)
    return data, "\n".join(lines[end + 1 :])


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def load_operad(repo_root: Path) -> tuple[set[str], dict[str, set[str]]]:
    sig_path = repo_root / ".agents/skill_operads/operad_signature.json"
    if not sig_path.exists():
        sig_path = repo_root / ".agents/operad/json/operad_signature.json"
    if not sig_path.exists():
        sig_path = repo_root / ".agents/operad/operad_signature.json"
    if not sig_path.exists():
        sig_path = repo_root / "operads/skill_operad/json/operad_signature.json"
    signature = _read_json(sig_path)
    colours = set(signature.get("colours", {}))
    operations: dict[str, set[str]] = {}
    for row in signature.get("operations", []):
        if not isinstance(row, dict) or not row.get("skill_id"):
            continue
        used = set(row.get("source_colours") or [])
        target = row.get("target_colour")
        if target:
            used.add(str(target))
        operations[str(row["skill_id"])] = used
    return colours, operations


def _tracked_entrypoints(repo_root: Path, kind: str) -> tuple[Path, ...]:
    """Use the Git index in a repository; fixtures fall back to direct files."""

    if kind not in {"agents", "skills"}:
        raise ValueError(f"unknown estate kind: {kind}")
    git_marker = repo_root / ".git"
    if git_marker.exists():
        environment = os.environ.copy()
        environment["GIT_CONFIG_GLOBAL"] = os.devnull
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z", "--", f".agents/{kind}"],
            check=False,
            capture_output=True,
            env=environment,
        )
        if completed.returncode != 0:
            raise ValueError("Git-tracked estate inventory is unavailable")
        relative = tuple(
            sorted(
                item.decode("utf-8", errors="strict")
                for item in completed.stdout.split(b"\0")
                if item
            )
        )
        if kind == "skills":
            selected = tuple(
                item
                for item in relative
                if len(item.split("/")) == 4
                and item.endswith("/SKILL.md")
                and not item.split("/")[2].startswith(("_", "."))
            )
        else:
            selected = tuple(
                item
                for item in relative
                if len(item.split("/")) == 3
                and item.endswith(".md")
                and not Path(item).name.startswith(("_", "."))
            )
        return tuple(repo_root / Path(*item.split("/")) for item in selected)
    pattern = "*/SKILL.md" if kind == "skills" else "*.md"
    return tuple(sorted((repo_root / ".agents" / kind).glob(pattern)))


def _audit_skill_description(data: dict[str, Any], locus: str, findings: list[Finding]) -> None:
    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        findings.append(
            Finding("ERROR", locus, "EMPTY_DESCRIPTION", "description must be non-empty")
        )
        return
    if description.strip().lower().startswith(PLACEHOLDER_PREFIXES):
        findings.append(Finding("WARN", locus, "PLACEHOLDER_DESCRIPTION", description.strip()))


def _audit_source_colours(
    data: dict[str, Any], colours: set[str], locus: str, findings: list[Finding]
) -> None:
    source = data.get("operad_source_colours")
    arity = data.get("operad_arity")
    if not isinstance(source, list) or not all(isinstance(item, str) for item in source):
        findings.append(Finding("ERROR", locus, "INVALID_SOURCE_COLOURS", "must be a list of strings"))
        return
    if not isinstance(arity, int) or arity < 0 or len(source) != arity:
        findings.append(
            Finding("ERROR", locus, "ARITY_MISMATCH", f"arity={arity!r}, source_count={len(source)}")
        )
        return
    unknown = sorted(set(source) - colours)
    if unknown:
        findings.append(Finding("ERROR", locus, "UNKNOWN_COLOUR", ", ".join(unknown)))


def _audit_skill_registry(
    directory: Path,
    data: dict[str, Any],
    operations: dict[str, set[str]],
    counts: dict[str, int],
    locus: str,
    findings: list[Finding],
) -> None:
    if directory.name not in operations:
        return
    counts["registered"] += 1
    source = data.get("operad_source_colours")
    target = data.get("operad_target_colour")
    declared = set(source or []) | ({target} if isinstance(target, str) else set())
    if declared != operations[directory.name]:
        findings.append(
            Finding(
                "ERROR",
                locus,
                "REGISTRY_SIGNATURE_DRIFT",
                f"manifest={sorted(declared)}, registry={sorted(operations[directory.name])}",
            )
        )


def _heading_present(body: str) -> bool:
    return any(line.startswith("## ") and line[3:].strip() for line in body.splitlines())


def _audit_one_skill(
    repo_root: Path,
    manifest_path: Path,
    colours: set[str],
    operations: dict[str, set[str]],
    findings: list[Finding],
    counts: dict[str, int],
) -> None:
    directory = manifest_path.parent
    counts["inventory"] += 1
    locus = manifest_path.relative_to(repo_root).as_posix()
    if not manifest_path.is_file():
        findings.append(Finding("ERROR", locus, "MISSING_SKILL_MD", "package has no SKILL.md"))
        return
    try:
        data, body = parse_frontmatter(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as err:
        findings.append(Finding("ERROR", locus, "INVALID_FRONTMATTER", str(err)))
        return
    missing = [field for field in REQUIRED_SKILL_FIELDS if field not in data]
    if missing:
        findings.append(Finding("ERROR", locus, "MISSING_FIELDS", ", ".join(missing)))
        return
    if data["name"] != directory.name:
        findings.append(
            Finding(
                "ERROR",
                locus,
                "NAME_PATH_MISMATCH",
                f"name={data['name']!r}, directory={directory.name!r}",
            )
        )
    _audit_skill_description(data, locus, findings)
    _audit_source_colours(data, colours, locus, findings)
    target = data.get("operad_target_colour")
    if not isinstance(target, str) or target not in colours:
        findings.append(Finding("ERROR", locus, "INVALID_TARGET_COLOUR", repr(target)))
    else:
        counts["typed"] += 1
    _audit_skill_registry(directory, data, operations, counts, locus, findings)
    if (directory / "scripts").is_dir():
        counts["scripts"] += 1
    if (directory / "tests").is_dir():
        counts["tests"] += 1
    if not _heading_present(body):
        findings.append(
            Finding("WARN", locus, "NO_ACTIONABLE_SECTIONS", "body has no non-empty H2 section")
        )


def audit_skills(repo_root: Path) -> tuple[list[Finding], dict[str, int]]:
    colours, operations = load_operad(repo_root)
    findings: list[Finding] = []
    counts = {"inventory": 0, "typed": 0, "registered": 0, "scripts": 0, "tests": 0}
    for manifest_path in _tracked_entrypoints(repo_root, "skills"):
        _audit_one_skill(repo_root, manifest_path, colours, operations, findings, counts)
    return findings, counts


def _present_text(item: object) -> bool:
    return type(item) is str and bool(item)


def _unique_nonempty_strings(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not all(_present_text(item) for item in value):
        return False
    return value == sorted(set(value))


def _capability_slice_path(repo_root: Path) -> Path:
    relatives = (
        ".agents/skill_operads/agent_capability_slices.json",
        ".agents/operad/json/agent_capability_slices.json",
        ".agents/operad/agent_capability_slices.json",
        "operads/skill_operad/json/agent_capability_slices.json",
    )
    for relative in relatives:
        path = repo_root / relative
        if path.exists():
            return path
    return repo_root / relatives[-1]


def _note_agent_shape(data: dict[str, Any], path: Path, locus: str, findings: list[Finding]) -> None:
    if data["name"] != path.stem:
        findings.append(Finding("ERROR", locus, "NAME_PATH_MISMATCH", repr(data["name"])))
    if not isinstance(data.get("tools"), list):
        findings.append(Finding("ERROR", locus, "INVALID_TOOLS", "tools must be a list"))
    if data.get("authority_effect") != "none":
        findings.append(
            Finding("ERROR", locus, "AUTHORITY_NOT_NONE", repr(data.get("authority_effect")))
        )
    if "skills" in data:
        findings.append(Finding("ERROR", locus, "LEGACY_LICENSE_KEY", "use licensed_skills"))


def _note_capability_slice(
    path: Path,
    slices: object,
    licensed: list,
    allowed_raw: list,
    locus: str,
    findings: list[Finding],
) -> None:
    spec = slices.get(path.stem) if isinstance(slices, dict) else None
    if not isinstance(spec, dict):
        findings.append(Finding("ERROR", locus, "MISSING_CAPABILITY_SLICE", path.stem))
        return
    if spec.get("licensed_skills") != licensed or spec.get("sub_operad") != allowed_raw:
        findings.append(Finding("ERROR", locus, "CAPABILITY_PROJECTION_DRIFT", path.stem))


def _note_licensed_skills(
    licensed: list,
    allowed: set,
    operations: dict[str, set[str]],
    locus: str,
    findings: list[Finding],
) -> None:
    for skill_id in licensed:
        used = operations.get(skill_id)
        if used is None:
            findings.append(Finding("ERROR", locus, "UNREGISTERED_SKILL", skill_id))
            continue
        escaped = sorted(used - allowed)
        if escaped:
            findings.append(
                Finding(
                    "ERROR",
                    locus,
                    "CAPABILITY_ESCAPE",
                    f"{skill_id} uses {escaped} outside {sorted(allowed)}",
                )
            )


def _audit_one_agent(
    repo_root: Path,
    path: Path,
    operations: dict[str, set[str]],
    slices: object,
    findings: list[Finding],
    counts: dict[str, int],
) -> None:
    counts["inventory"] += 1
    locus = path.relative_to(repo_root).as_posix()
    try:
        data, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as err:
        findings.append(Finding("ERROR", locus, "INVALID_FRONTMATTER", str(err)))
        return
    missing = [field for field in REQUIRED_AGENT_FIELDS if field not in data]
    if missing:
        findings.append(Finding("ERROR", locus, "MISSING_FIELDS", ", ".join(missing)))
        return
    _note_agent_shape(data, path, locus, findings)
    licensed = data.get("licensed_skills")
    allowed_raw = data.get("licensed_colours")
    if not _unique_nonempty_strings(licensed):
        findings.append(Finding("ERROR", locus, "INVALID_LICENSE_LIST", repr(licensed)))
        return
    if not _unique_nonempty_strings(allowed_raw):
        findings.append(Finding("ERROR", locus, "INVALID_LICENSE_COLOURS", repr(allowed_raw)))
        return
    _meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if re.search(r"(?m)^\s*licensed_skills\s*(?:=|:)", body):
        findings.append(
            Finding(
                "WARN",
                locus,
                "IGNORED_BODY_LICENSE_DECLARATION",
                "body licence-like text is non-authoritative",
            )
        )
    allowed = set(allowed_raw)
    counts["licensed_edges"] += len(licensed)
    _note_capability_slice(path, slices, licensed, allowed_raw, locus, findings)
    _note_licensed_skills(licensed, allowed, operations, locus, findings)


def _append_orphan_slices(findings: list[Finding], slices: object, agent_paths: tuple[Path, ...]) -> None:
    extra_slices = sorted(set(slices) - {path.stem for path in agent_paths})
    for name in extra_slices:
        findings.append(
            Finding("ERROR", ".agents/operad/agent_capability_slices.json", "ORPHAN_SLICE", name)
        )


def audit_agents(repo_root: Path) -> tuple[list[Finding], dict[str, int]]:
    _, operations = load_operad(repo_root)
    slice_path = _capability_slice_path(repo_root)
    slices = _read_json(slice_path).get("agents", {})
    findings: list[Finding] = []
    counts = {"inventory": 0, "licensed_edges": 0, "empty_licenses": 0}
    agent_paths = _tracked_entrypoints(repo_root, "agents")
    for path in agent_paths:
        _audit_one_agent(repo_root, path, operations, slices, findings, counts)
    _append_orphan_slices(findings, slices, agent_paths)
    return findings, counts


def errors(findings: Iterable[Finding]) -> int:
    return sum(1 for finding in findings if finding.severity == "ERROR")
