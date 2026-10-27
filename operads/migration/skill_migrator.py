"""OEWAS V3 Skill Migrator: Shadow dry-run and consolidation compiler."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Dict, List, Optional

from operations.domain.rop.result import Err, Ok, Result
from ..domain.entities.catalog_v3 import CapabilitySliceV3
from ..domain.entities.operation_v3 import OperationV3, PortSpecV3
from ..domain.errors.domain_errors import DomainInvariantError, OeopDomainError
from ..domain.value_objects.authority import AuthorityEffect
from ..domain.value_objects.content_digest import ContentDigest
from ..domain.value_objects.identifier import (
    ColourId,
    OperationId,
    SchemaRef,
    SkillId,
)
from ..domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)


class SkillMigratorV3:
    _MIRROR_HOSTS = (".agents", ".claude", ".codex", ".grok")

    def __init__(self, manifest_path: Optional[pathlib.Path] = None) -> None:
        if manifest_path is None:
            manifest_path = pathlib.Path(__file__).parent / "migration_manifest_v3.json"
        self._manifest_path = manifest_path
        self._manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    @property
    def manifest(self) -> dict:
        return self._manifest

    def verify_manifest_hashes(self, repo_root: pathlib.Path) -> Result[int, OeopDomainError]:
        mismatches: List[str] = []
        entries = self._manifest.get("entries")
        if type(entries) is not list:
            return Err(DomainInvariantError(
                code="MANIFEST_SCHEMA_INVALID",
                message="entries must be an exact list",
            ))
        if self._manifest.get("total_entries") != len(entries):
            return Err(DomainInvariantError(
                code="MANIFEST_SCHEMA_INVALID",
                message="total_entries does not equal entries length",
            ))
        if self._manifest.get("artifact_binding") != "SUCCESSOR_SKILL_BYTES":
            return Err(DomainInvariantError(
                code="MANIFEST_SCHEMA_INVALID",
                message="artifact_binding must be SUCCESSOR_SKILL_BYTES",
            ))
        if self._manifest.get("mapping_status") != "DECLARED_UNADMITTED":
            return Err(DomainInvariantError(
                code="MANIFEST_SCHEMA_INVALID",
                message="mapping_status must be DECLARED_UNADMITTED",
            ))
        seen_mappings: set[tuple[str, str]] = set()
        for entry in self._manifest["entries"]:
            legacy_id = entry["legacy_skill_id"]
            skill_id = entry["successor_skill_id"]
            mapping_key = (legacy_id, entry["operation_id"])
            if mapping_key in seen_mappings:
                mismatches.append(f"duplicate migration mapping: {mapping_key}")
                continue
            seen_mappings.add(mapping_key)
            expected_hash = entry["blob_sha256"]
            expected_size = entry.get("byte_count")
            if entry.get("residual_status") != "unknown":
                mismatches.append(f"{legacy_id}: residual_status must be unknown")
            hosts = entry.get("hosts")
            if not isinstance(hosts, dict):
                mismatches.append(f"{legacy_id}: missing or malformed host manifest")
                continue

            for host in self._MIRROR_HOSTS:
                if hosts.get(host) is not True:
                    mismatches.append(f"{host}/{skill_id}: host is not declared present")
                    continue

                target_file = repo_root / host / "skills" / skill_id / "SKILL.md"
                if not target_file.exists():
                    mismatches.append(f"{host}/{skill_id}: missing file on disk")
                    continue

                raw_bytes = target_file.read_bytes()
                actual_hash = hashlib.sha256(raw_bytes).hexdigest()
                if actual_hash != expected_hash:
                    mismatches.append(
                        f"{host}/{skill_id}: hash mismatch "
                        f"(exp {expected_hash[:8]} vs got {actual_hash[:8]})"
                    )
                if (
                    not isinstance(expected_size, int)
                    or isinstance(expected_size, bool)
                    or len(raw_bytes) != expected_size
                ):
                    mismatches.append(
                        f"{host}/{skill_id}: byte count mismatch "
                        f"(exp {expected_size} vs got {len(raw_bytes)})"
                    )
        if mismatches:
            return Err(DomainInvariantError(
                code="MANIFEST_HASH_MISMATCH",
                message=f"Found {len(mismatches)} hash mismatches: {mismatches}",
            ))
        return Ok(len(self._manifest["entries"]))

    def compile_migrated_capability_slices(
        self,
        repo_root: pathlib.Path,
    ) -> Result[Dict[SkillId, CapabilitySliceV3], OeopDomainError]:
        skills_dir = repo_root / ".agents" / "skills"
        slices: Dict[SkillId, List[OperationV3]] = {}

        verified = self.verify_manifest_hashes(repo_root)
        if verified.is_err:
            return Err(verified.unwrap_err())

        for entry in self._manifest["entries"]:
            succ_skill_id = SkillId(entry["successor_skill_id"])
            op_id = OperationId(entry["operation_id"])

            target_file = skills_dir / succ_skill_id.value / "SKILL.md"
            raw_bytes = target_file.read_bytes()
            digest = ContentDigest.sha256(hashlib.sha256(raw_bytes).hexdigest())

            port = PortSpecV3(
                name="in",
                colour_id=ColourId("Prompt"),
                schema_ref=SchemaRef("schema:skill:v3"),
                schema_digest=digest,
                validator_ref="",
                validator_digest=digest,
            )
            out_port = PortSpecV3(
                name="out",
                colour_id=ColourId("Audit"),
                schema_ref=SchemaRef("schema:audit:v3"),
                schema_digest=digest,
                validator_ref="",
                validator_digest=digest,
            )
            lifecycle = SkillLifecycleV3(
                declaration=DeclarationFacet.DECLARED,
                schema_binding=SchemaBindingFacet.UNBOUND,
                executor_binding=ExecutorBindingFacet.UNBOUND,
                validation=ValidationFacet.UNCHECKED,
                admission=AdmissionFacet.UNADMITTED,
                schema_digest=None,
                executor_digest=None,
            )
            op = OperationV3(
                operation_id=op_id,
                inputs=(port,),
                output=out_port,
                operand_refs=(),
                lifecycle=lifecycle,
                residual_status="unknown",
                authority_effect=AuthorityEffect.NONE,
                authority_ceiling=AuthorityEffect.NONE,
                description=(
                    f"Declared migration mapping from {entry['legacy_skill_id']}; "
                    "unbound, unchecked, and unadmitted"
                ),
            )
            if succ_skill_id not in slices:
                slices[succ_skill_id] = []
            slices[succ_skill_id].append(op)

        result_slices: Dict[SkillId, CapabilitySliceV3] = {}
        for s_id, ops in slices.items():
            result_slices[s_id] = CapabilitySliceV3(
                slice_id=f"slice_{s_id}",
                name=f"Capability slice for {s_id}",
                operation_ids=tuple(o.operation_id for o in ops),
                description=f"Consolidated slice containing {len(ops)} operations",
            )
        return Ok(result_slices)

    def migrate_document_to_v3(
        self,
        legacy_content: bytes,
        skill_id: str,
        successor_skill_id: str,
        op_id: str,
        description: str = "",
        input_colour: str = "Prompt",
        output_colour: str = "Receipt",
    ) -> bytes:
        """Migrate a v1/v2 legacy skill markdown document to v3 by appending an OEWAS v3 operation block."""
        text = legacy_content.decode("utf-8")
        raw_digest = hashlib.sha256(legacy_content).hexdigest()
        desc = description or f"Migrated operation for legacy skill {skill_id} under {successor_skill_id}"

        v3_block = f"""
```oewas.operation.v3
operation_id: "{op_id}"
inputs:
  - name: "input_packet"
    colour_id: "{input_colour}"
    schema_ref: "schema:legacy:{skill_id}:v1"
    schema_digest: "{raw_digest}"
output:
  name: "output_packet"
  colour_id: "{output_colour}"
  schema_ref: "schema:migrated:{successor_skill_id}:v3"
  schema_digest: "{raw_digest}"
declaration: "Declared"
schema_binding: "Unbound"
executor_binding: "Unbound"
validation: "Unchecked"
admission: "Unadmitted"
residual_status: "unknown"
authority_effect: "None"
authority_ceiling: "None"
invocation_grade: "entry"
description: "{desc}; declared migration mapping only, not admitted"
```
"""
        migrated_text = text.rstrip() + "\n\n" + v3_block.strip() + "\n"
        return migrated_text.encode("utf-8")
