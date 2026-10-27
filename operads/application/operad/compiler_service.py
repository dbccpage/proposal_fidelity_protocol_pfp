"""
Operad Compiler Service.
========================

Extracts YAML frontmatter operad signatures from SKILL.md documents,
constructs the ColouredOperad aggregate, validates type-safe compositions,
and emits immutable EvidenceReceipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from operads.domain.operad import (
    ADMITTED_FINITE_COLOURS,
    ColouredOperad,
    ColourSignature,
    Err,
    EvidenceObservation,
    EvidenceReceipt,
    EvidenceType,
    Ok,
    OperadDomainError,
    OperationId,
    OperationSignature,
    Result,
    SkillSignatureRefusal,
)


class OperadCompilerService:
    """Application service for compiling skill packages into a ColouredOperad."""

    def __init__(self, skills_root: Optional[Path] = None) -> None:
        self.skills_root = skills_root
        self.operad = ColouredOperad()
        # Skills refused during parsing, with the reason. A caller that cares
        # about coverage must inspect this; an empty parse result and a refused
        # one are otherwise indistinguishable.
        self.refusals: List[str] = []

    def _refuse(
        self, code: str, skill_path: Path, detail: str
    ) -> Result[OperationSignature, SkillSignatureRefusal]:
        refusal = SkillSignatureRefusal(code, str(skill_path), detail)
        self.refusals.append(refusal.message)
        return Err(refusal)

    def parse_skill_md(
        self, skill_path: Path
    ) -> Result[OperationSignature, SkillSignatureRefusal]:
        """Extract the operad signature from a SKILL.md, or a typed refusal.

        Every refusal is also appended to ``self.refusals``. An unreadable
        file, a missing frontmatter block and a YAML error used to return
        ``None`` without a record, so ``compile_skills_garden`` dropped the
        skill and could still report PASSED.
        """
        try:
            content = skill_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            return self._refuse("UNREADABLE_SKILL_FILE", skill_path, str(error))

        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not frontmatter_match:
            return self._refuse(
                "MISSING_FRONTMATTER", skill_path, "no '---' delimited frontmatter block"
            )

        try:
            meta = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError as error:
            return self._refuse("FRONTMATTER_YAML_ERROR", skill_path, str(error))
        if meta is None:
            meta = {}
        if not isinstance(meta, dict):
            return self._refuse(
                "FRONTMATTER_NOT_A_MAPPING",
                skill_path,
                f"frontmatter parses to {type(meta).__name__}, not a mapping",
            )

        name = meta.get("name") or skill_path.parent.name
        source_colours = meta.get("operad_source_colours", [])
        target_colour = meta.get("operad_target_colour")
        if not isinstance(source_colours, list):
            return self._refuse(
                "SOURCE_COLOURS_NOT_A_LIST",
                skill_path,
                f"operad_source_colours is {type(source_colours).__name__}, not a list",
            )

        # An unadmitted colour is refused, not repaired.
        #
        # This previously defaulted an unrecognised target to "Receipt" and
        # dropped unrecognised sources from the list. Both are silent
        # corruptions: dropping a source changes the operation's arity, and
        # rewriting the target changes what the operation produces, while the
        # compile still reports success. Refusing the skill instead surfaces the
        # problem at its cause -- either the frontmatter is wrong or the colour
        # belongs in ADMITTED_FINITE_COLOURS.
        if not target_colour or target_colour not in ADMITTED_FINITE_COLOURS:
            return self._refuse(
                "UNADMITTED_TARGET_COLOUR",
                skill_path,
                f"target colour {target_colour!r} is not admitted",
            )

        unadmitted = [s for s in source_colours if s not in ADMITTED_FINITE_COLOURS]
        if unadmitted:
            return self._refuse(
                "UNADMITTED_SOURCE_COLOUR",
                skill_path,
                f"source colours {unadmitted!r} are not admitted",
            )
        valid_sources = list(source_colours)

        op_id = OperationId(name)
        sig = ColourSignature(source=valid_sources, target=target_colour)
        return Ok(
            OperationSignature(
                op_id=op_id,
                signature=sig,
                equivariant=meta.get("operad_equivariant", False),
                residual_effect=str(meta.get("operad_residual", "unknown")),
            )
        )

    def compile_skills_garden(self, root_dir: Optional[Path] = None) -> EvidenceReceipt:
        """Discovers and compiles all SKILL.md files in the skill garden."""
        target_dir = root_dir or self.skills_root
        if not target_dir or not target_dir.exists():
            return EvidenceReceipt(
                receipt_id="compilation_err_no_dir",
                evidence_type=EvidenceType.COMPILATION,
                passed=False,
                observations=(EvidenceObservation("error", f"Directory {target_dir} does not exist"),),
            )

        compiled_count = 0
        self.operad = ColouredOperad()
        # Reset alongside the operad. Carrying refusals across runs would report
        # the previous root's problems as belonging to this one.
        self.refusals = []
        observations: List[EvidenceObservation] = []

        # Sorted so refusal indices in the receipt do not depend on directory
        # enumeration order.
        sources: Dict[str, Path] = {}
        for skill_file in sorted(target_dir.rglob("SKILL.md")):
            parsed = self.parse_skill_md(skill_file)
            if parsed.is_err:
                continue
            op_sig = parsed.unwrap()
            op_name = op_sig.op_id.value
            # add_operation overwrites by id, so a second skill declaring the
            # same name would silently replace the first.
            if op_name in sources:
                self._refuse(
                    "DUPLICATE_OPERATION_ID",
                    skill_file,
                    f"operation {op_name!r} is already declared by {sources[op_name]}",
                )
                continue
            try:
                self.operad.add_operation(op_sig)
            except OperadDomainError as error:
                self._refuse("OPERATION_NOT_ADMITTED", skill_file, error.message)
                continue
            sources[op_name] = skill_file
            compiled_count += 1

        unit_ops = self.operad.ensure_units()
        observations.append(EvidenceObservation("total_skills_compiled", compiled_count))
        observations.append(EvidenceObservation("total_unit_identities", len(unit_ops)))
        observations.append(EvidenceObservation("total_operad_operations", len(self.operad.operations)))

        # Refusals must reach the receipt, or the new refuse-don't-repair path
        # would merely trade a silent repair for a silent drop: the skill leaves
        # the operad and nothing in the receipt, the CLI output, or the exit code
        # says so. A refused skill fails the compile.
        observations.append(EvidenceObservation("total_skills_refused", len(self.refusals)))
        for index, reason in enumerate(self.refusals):
            observations.append(EvidenceObservation(f"refusal_{index}", reason))

        receipt = EvidenceReceipt(
            receipt_id=f"receipt_compilation_{compiled_count}_ops",
            evidence_type=EvidenceType.COMPILATION,
            passed=(compiled_count > 0 and not self.refusals),
            observations=tuple(observations),
            metadata={"skills_root": str(target_dir)},
        )
        return receipt
