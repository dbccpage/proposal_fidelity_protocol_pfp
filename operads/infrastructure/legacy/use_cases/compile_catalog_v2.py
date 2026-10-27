"""Compile and verify the V2 derived estate catalog."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

import yaml  # type: ignore[import-untyped]

from operations.domain.rop.result import Err, Ok, Result

from ..catalog_v2 import (
    EstateCatalogV2,
    InstructionAtomBindingV1,
    MetaSkillBindingV1,
    NodeAssignmentV1,
    SkillFamilyBindingV1,
    SkillLifecycleBindingV1,
    SourceSpanV1,
)
from ..models import (
    CatalogAntiSkillRefV1,
    EstateCatalogSnapshotV1,
    EstateDiagnosticFindingV1,
    EstateDiagnosticsV1,
    LegacyEstateSnapshotV1,
    SkillOperationV1,
    normalize_estate_path,
)
from ...fs_reader import ReadOnlyEstateFSReader, parse_skill_operation

SECTION_RE = re.compile(rb"(?m)^##[ \t]+([^\r\n]+)[\r]?$")


def _compile_shadow_catalog(
    snapshot: LegacyEstateSnapshotV1,
) -> Result[EstateCatalogSnapshotV1, EstateDiagnosticsV1]:
    """Parse the isolated legacy snapshot without depending on the V3 application."""

    if not isinstance(snapshot, LegacyEstateSnapshotV1):
        return Err(
            _diagnostic(
                "INVALID_SNAPSHOT_TYPE",
                getattr(snapshot, "snapshot_id", "unknown"),
                "snapshot must be an instance of LegacyEstateSnapshotV1",
            )
        )
    try:
        skills, agents, workflows = ReadOnlyEstateFSReader().read_snapshot(snapshot)
        if not skills and not agents and not workflows:
            raise ValueError("snapshot contains no canonical WAS catalog entries")
        return Ok(
            EstateCatalogSnapshotV1(
                snapshot_id=snapshot.snapshot_id,
                skills=skills,
                agents=agents,
                workflows=workflows,
                anti_skills={},
                authority_effect="None",
            )
        )
    except (
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        return Err(_diagnostic("SNAPSHOT_PARSE_FAILURE", snapshot.snapshot_id, str(exc)))


def _diagnostic(kind: str, subject: str, message: str) -> EstateDiagnosticsV1:
    return EstateDiagnosticsV1(
        status="REFUSAL",
        findings=(
            EstateDiagnosticFindingV1(
                finding_kind=kind,
                subject_id=subject,
                message=message,
            ),
        ),
        authority_effect="None",
    )


def _snapshot_bytes(snapshot: LegacyEstateSnapshotV1, source_path: str) -> bytes:
    selected = normalize_estate_path(source_path)
    for raw_path, raw in snapshot.raw_files.items():
        if normalize_estate_path(raw_path) == selected:
            return raw
    raise ValueError(f"snapshot omits selected source path: {source_path}")


def _section_atoms(
    skill_id: str, source_path: str, raw: bytes
) -> tuple[InstructionAtomBindingV1, ...]:
    raw.decode("utf-8")
    source_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    matches = tuple(SECTION_RE.finditer(raw))
    spans: tuple[tuple[int, int, str], ...]
    if not matches:
        spans = ((0, len(raw), "document"),)
    else:
        spans = tuple(
            (
                match.start(),
                matches[index + 1].start() if index + 1 < len(matches) else len(raw),
                bytes(match.group(1)).decode("utf-8").strip(),
            )
            for index, match in enumerate(matches)
        )
    atoms: list[InstructionAtomBindingV1] = []
    for ordinal, (start, end, section) in enumerate(spans):
        content = raw[start:end]
        content_digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        atoms.append(
            InstructionAtomBindingV1(
                atom_id=f"{skill_id}:{ordinal:03d}",
                skill_id=skill_id,
                section=section,
                ordinal=ordinal,
                span=SourceSpanV1(
                    source_path=source_path,
                    start_byte=start,
                    end_byte=end,
                    source_digest=source_digest,
                    content_digest=content_digest,
                ),
                authority_effect="None",
            )
        )
    return tuple(atoms)


def _selected_skill_source(
    snapshot: LegacyEstateSnapshotV1, skill_id: str
) -> tuple[str, bytes] | None:
    suffix = f"skills/{skill_id}/SKILL.md"
    for path, raw in snapshot.raw_files.items():
        if normalize_estate_path(path) == suffix:
            return suffix, raw
    return None


def _preflight_selected_operations(
    snapshot: LegacyEstateSnapshotV1,
    selected: Sequence[str],
) -> Result[dict[str, SkillOperationV1], EstateDiagnosticsV1]:
    findings: list[EstateDiagnosticFindingV1] = []
    operations: dict[str, SkillOperationV1] = {}
    for skill_id in selected:
        if type(skill_id) is not str or not skill_id:
            findings.append(
                EstateDiagnosticFindingV1(
                    finding_kind="DISHONEST_SELECTED_OPERATION",
                    subject_id=str(skill_id),
                    message="selected skill id must be a nonempty str",
                )
            )
            continue
        source = _selected_skill_source(snapshot, skill_id)
        if source is None:
            findings.append(
                EstateDiagnosticFindingV1(
                    finding_kind="DISHONEST_SELECTED_OPERATION",
                    subject_id=skill_id,
                    message="selected skill source is absent from the snapshot",
                )
            )
            continue
        _, raw = source
        try:
            operations[skill_id] = parse_skill_operation(
                raw.decode("utf-8"),
                operation_id=skill_id,
                require_explicit=True,
            )
        except (TypeError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
            findings.append(
                EstateDiagnosticFindingV1(
                    finding_kind="DISHONEST_SELECTED_OPERATION",
                    subject_id=skill_id,
                    message=str(exc),
                )
            )
    if findings:
        return Err(
            EstateDiagnosticsV1(
                status="REFUSAL",
                findings=tuple(findings),
                authority_effect="None",
            )
        )
    return Ok(operations)


def compile_estate_catalog_v2(
    snapshot: LegacyEstateSnapshotV1,
    *,
    selected_skill_ids: Sequence[str],
    anti_skills: Mapping[str, CatalogAntiSkillRefV1] | None = None,
    family_members: Mapping[str, Sequence[str]] | None = None,
    family_anti_skills: Mapping[str, Sequence[str]] | None = None,
    meta_skill_operations: Mapping[str, Sequence[str]] | None = None,
    node_assignments: Sequence[NodeAssignmentV1] = (),
    catalog_id: str = "adversary_engineering_shadow_v2",
) -> Result[EstateCatalogV2, EstateDiagnosticsV1]:
    """Compile selected legacy-current skill bytes into an immutable V2 binding."""

    if type(selected_skill_ids) not in (tuple, list):
        return Err(
            _diagnostic(
                "INVALID_SELECTED_SKILLS",
                catalog_id,
                "selected_skill_ids must be an exact tuple or list",
            )
        )
    selected = tuple(selected_skill_ids)
    if len(set(selected)) != len(selected):
        return Err(
            _diagnostic("DUPLICATE_SELECTED_SKILL", catalog_id, "duplicate skill id")
        )

    preflight = _preflight_selected_operations(snapshot, selected)
    if isinstance(preflight, Err):
        return preflight

    compiled = _compile_shadow_catalog(snapshot)
    if isinstance(compiled, Err):
        return compiled
    base_catalog = compiled.value
    for skill_id, expected in preflight.value.items():
        actual = base_catalog.skills.get(skill_id)
        if actual is None:
            return Err(
                _diagnostic(
                    "PREFLIGHT_OPERATION_MISMATCH",
                    skill_id,
                    "selected skill is absent from the compatibility catalog",
                )
            )
        if actual.operation != expected:
            return Err(
                _diagnostic(
                    "PREFLIGHT_OPERATION_MISMATCH",
                    skill_id,
                    "strict selected operation does not equal the compatibility catalog operation",
                )
            )

    try:
        atoms: list[InstructionAtomBindingV1] = []
        lifecycles: list[SkillLifecycleBindingV1] = []
        for skill_id in selected:
            if type(skill_id) is not str or skill_id not in base_catalog.skills:
                raise ValueError(
                    f"selected skill is absent from typed catalog: {skill_id}"
                )
            skill = base_catalog.skills[skill_id]
            raw = _snapshot_bytes(snapshot, skill.file_path)
            atoms.extend(_section_atoms(skill_id, skill.file_path, raw))
            lifecycles.append(
                SkillLifecycleBindingV1(
                    skill_id=skill_id,
                    lifecycle_status="BOUND",
                    source_role="LEGACY_CURRENT",
                    evaluation_receipt_refs=(),
                    authority_effect="None",
                )
            )

        anti_map = dict(anti_skills or {})
        anti_by_family = dict(family_anti_skills or {})
        families = tuple(
            SkillFamilyBindingV1(
                family_id=family_id,
                skill_ids=tuple(members),
                anti_skill_ids=tuple(anti_by_family.get(family_id, ())),
                authority_effect="None",
            )
            for family_id, members in sorted((family_members or {}).items())
        )
        metas = tuple(
            MetaSkillBindingV1(
                meta_skill_id=meta_id,
                selectable_operation_ids=tuple(operations),
                path2_evidence_refs=(),
                authority_effect="None",
            )
            for meta_id, operations in sorted((meta_skill_operations or {}).items())
        )
        catalog = EstateCatalogV2(
            catalog_id=catalog_id,
            base_catalog=base_catalog,
            instruction_atoms=tuple(atoms),
            lifecycles=tuple(lifecycles),
            families=families,
            meta_skills=metas,
            node_assignments=tuple(node_assignments),
            anti_skills=anti_map,
            authority_effect="None",
        )
        for atom in catalog.instruction_atoms:
            atom.span.verify(_snapshot_bytes(snapshot, atom.span.source_path))
        return Ok(catalog)
    except (TypeError, UnicodeDecodeError, ValueError) as exc:
        return Err(_diagnostic("CATALOG_V2_COMPILE_FAILURE", catalog_id, str(exc)))


def _strict_json_loads(raw: bytes) -> Any:
    if type(raw) is not bytes:
        raise TypeError("catalog bytes must be exact bytes")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON number: {value}")
        ),
    )


def verify_estate_catalog_v2(
    catalog_bytes: bytes,
    snapshot: LegacyEstateSnapshotV1,
    **compile_kwargs: Any,
) -> Result[EstateCatalogV2, EstateDiagnosticsV1]:
    """Recompile from source bytes and require byte-exact canonical agreement."""

    try:
        _strict_json_loads(catalog_bytes)
    except (TypeError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        return Err(_diagnostic("CATALOG_V2_MALFORMED", "catalog_bytes", str(exc)))
    compiled = compile_estate_catalog_v2(snapshot, **compile_kwargs)
    if isinstance(compiled, Err):
        return compiled
    if catalog_bytes != compiled.value.canonical_bytes():
        return Err(
            _diagnostic(
                "CATALOG_V2_BYTES_MISMATCH",
                compiled.value.catalog_id,
                "supplied bytes are not the canonical source-derived V2 catalog",
            )
        )
    return Ok(compiled.value)


__all__ = ["compile_estate_catalog_v2", "verify_estate_catalog_v2"]
