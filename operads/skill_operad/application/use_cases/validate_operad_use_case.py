"""ValidateOperadUseCase: Orchestrates multi-coloured operad validation,
two-layer grading laws, agent capability slices, and residual honesty audits.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from domain.colours import ADMITTED_FINITE_COLOURS, Colour
    from domain.errors import (
        ArityMismatchError,
        Err,
        IllTypedCompositionError,
        InvalidColourError,
        MissingUnitError,
        Ok,
        Result,
    )
    from operads.domain.operad.operad import AgentSlice, ColouredOperad
    from operads.domain.operad.operation import OperationId, OperationSignature
    from domain.ports import OperadRepositoryPort
    from application.dto.operad_dto import ValidationReportDTO
except (ImportError, ValueError):
    from ...domain.colours import ADMITTED_FINITE_COLOURS, Colour
    from ...domain.errors import (
        ArityMismatchError,
        Err,
        IllTypedCompositionError,
        InvalidColourError,
        MissingUnitError,
        Ok,
        Result,
    )
    from operads.domain.operad.operad import AgentSlice, ColouredOperad
    from operads.domain.operad.operation import OperationId, OperationSignature
    from ...domain.ports import OperadRepositoryPort
    from ..dto.operad_dto import ValidationReportDTO

from operads.domain.operad.errors import DomainError, SliceViolationError


def load_entry_skills(skills_root: Path) -> Set[str]:
    entries: Set[str] = set()
    if not skills_root.exists():
        return entries
    for skill_path in sorted(skills_root.glob("*/SKILL.md")):
        try:
            text = skill_path.read_text(encoding="utf-8-sig")
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            frontmatter = parts[1]
            if not re.search(r"(?m)^invocation:\s*entry\s*$", frontmatter):
                continue
            name = re.search(r"(?m)^name:\s*[\"']?([^\r\n\"']+)", frontmatter)
            entries.add(name.group(1).strip() if name else skill_path.parent.name)
        except Exception:
            continue
    return entries


def validate_composition_grading(
    compositions: List[Dict[str, Any]], entry_skills: Set[str]
) -> tuple[List[str], Set[str]]:
    """Refuse any operation composed above a terminal entry operation.

    A composite whose outer operation is entry-graded remains terminal.  Compute
    that closure before checking edges so a reordered matrix cannot hide an
    indirect discipline-over-entry composition.
    """
    terminal_entries = set(entry_skills)
    changed = True
    while changed:
        changed = False
        for composition in compositions:
            outer = composition.get("outer")
            result = composition.get("composite_id", composition.get("result"))
            if outer in terminal_entries and result and result not in terminal_entries:
                terminal_entries.add(str(result))
                changed = True

    errors: List[str] = []
    for composition in compositions:
        outer = composition.get("outer")
        inner = composition.get("inner")
        if inner in terminal_entries:
            errors.append(
                "Two-Layer Grading Violation: nothing may compose above "
                f"terminal entry operation '{inner}' (outer='{outer}')"
            )
    return errors, terminal_entries


class ValidateOperadUseCase:
    """Application use case for validating the multi-coloured operad and all governance boundaries."""

    def __init__(self, repository: OperadRepositoryPort) -> None:
        self.repository = repository
        self.root_dir = repository.root_dir

    def execute(self) -> Result[ValidationReportDTO, List[str]]:
        errors: List[str] = []
        warnings: List[str] = []

        try:
            operad = self.repository.load_operad()
        except Exception as exc:
            return Err([f"Failed to load operad signatures: {exc}"])

        try:
            added_units = operad.ensure_units()
        except DomainError as exc:
            return Err([f"Unit validation error: {exc}"])

        try:
            operad.validate_types()
        except DomainError as exc:
            errors.append(f"Type validation error: {exc}")

        comp_data = self.repository.load_composition_matrix()
        skills_root = self.root_dir.parent / "skills"
        entry_skills = load_entry_skills(skills_root)
        grading_errors, _terminal_entries = validate_composition_grading(
            comp_data.get("compositions", []), entry_skills
        )
        errors.extend(grading_errors)

        assoc_laws = comp_data.get("associativity_laws", [])
        unverified_laws = []
        for law in assoc_laws:
            witness = law.get("verified_equal_id")
            if not (witness and witness in operad.operations):
                unverified_laws.append(
                    f"Declared: {law.get('left_composite')} == {law.get('right_composite')}"
                )

        slice_data = self.repository.load_agent_capability_slices()
        agents = slice_data.get("agents", {})
        slices_verified = 0

        for agent_id, data in agents.items():
            try:
                operad.slice(agent_id, data.get("licensed_skills", []))
                slices_verified += 1
            except SliceViolationError as exc:
                errors.append(f"Agent slice strict validation failed for '{agent_id}': {exc}")

        meta_skills = comp_data.get("synthesized_meta_skills", [])
        provisional_meta = {}
        for ms in meta_skills:
            ms_id = ms.get("id", "unknown")
            if ms.get("status") != "provisional":
                errors.append(f"Meta-skill '{ms_id}' is not provisional")
            else:
                provisional_meta[ms_id] = 1

        report = ValidationReportDTO(
            colour_count=len(operad.colours),
            operation_count=len(operad.operations),
            unit_count=len(added_units),
            admitted_entry_skills=sorted(list(entry_skills)),
            slices_verified=slices_verified,
            provisional_meta_skills=provisional_meta,
            unverified_laws=unverified_laws,
            is_valid=(len(errors) == 0),
            warnings=warnings,
            errors=errors,
        )

        if errors:
            return Err(errors)
        return Ok(report)
