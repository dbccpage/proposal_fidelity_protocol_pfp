"""Infrastructure workflow and skills garden loader.

Reads skill frontmatter YAML from disk and loads workflow JSON files
to evaluate planar operad substitution and workflow DAG validity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from ..domain.planar_substitution import (
    OperadOperation,
    SubstitutionError,
)
from ..domain.workflow_graph import (
    WorkflowError,
    WorkflowFinding,
    WorkflowReport,
    unknown_operations,
    validate_workflow,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT_DIR / "operads" / "skills"
WORKFLOWS_DIR = ROOT_DIR / "operads" / "workflows"

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def load_garden(skills_dir: Path | str | None = None) -> tuple[OperadOperation, ...]:
    """Read every skill's declared operation from its frontmatter."""
    directory = Path(skills_dir) if skills_dir is not None else SKILLS_DIR
    if not directory.is_dir():
        raise SubstitutionError(
            "GARDEN_MISSING", f"skill directory is missing: {directory}"
        )
    operations: list[OperadOperation] = []
    for path in sorted(directory.glob("*/SKILL.md")):
        match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            raise SubstitutionError(
                "NO_FRONTMATTER", f"{path.parent.name} declares no frontmatter"
            )
        data = yaml.safe_load(match.group(1)) or {}
        sources = data.get("operad_source_colours")
        target = data.get("operad_target_colour")
        declared_arity = data.get("operad_arity")
        if sources is None or target is None or declared_arity is None:
            raise SubstitutionError(
                "INCOMPLETE_OPERAD",
                f"{path.parent.name} does not declare the operad triple",
            )
        if not isinstance(sources, list):
            raise SubstitutionError(
                "BAD_SOURCES", f"{path.parent.name} source colours are not a list"
            )
        if len(sources) != declared_arity:
            raise SubstitutionError(
                "ARITY_DISAGREES",
                f"{path.parent.name} declares arity {declared_arity} beside "
                f"{len(sources)} source colours",
            )
        operations.append(
            OperadOperation(
                name=path.parent.name,
                source_colours=tuple(sources),
                target_colour=target,
            )
        )
    if not operations:
        raise SubstitutionError("GARDEN_EMPTY", f"no skills found in {directory}")
    return tuple(operations)


def _read_workflow(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WorkflowError("MISSING", f"workflow is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError("MALFORMED_JSON", f"{path.name}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise WorkflowError("NOT_AN_OBJECT", f"{path.name} is not a JSON object")
    return data


def validate_all(
    workflows_dir: Path | str | None = None,
    garden: dict[str, OperadOperation] | None = None,
) -> tuple[WorkflowReport, ...]:
    """Validate all workflow JSON files in workflows_dir against the skill garden."""
    directory = Path(workflows_dir) if workflows_dir is not None else WORKFLOWS_DIR
    if not directory.is_dir():
        raise WorkflowError(
            "WORKFLOWS_MISSING", f"workflow directory is missing: {directory}"
        )
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise WorkflowError(
            "NO_WORKFLOWS",
            f"no JSON workflows in {directory}; an empty sweep is not a clean one",
        )
    known = garden if garden is not None else {op.name: op for op in load_garden()}
    return tuple(validate_workflow(_read_workflow(path), known) for path in paths)


__all__ = [
    "ROOT_DIR",
    "SKILLS_DIR",
    "WORKFLOWS_DIR",
    "WorkflowError",
    "WorkflowFinding",
    "WorkflowReport",
    "load_garden",
    "unknown_operations",
    "validate_all",
    "validate_workflow",
]
