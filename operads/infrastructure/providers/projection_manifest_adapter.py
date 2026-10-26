"""Projection manifest adapter."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from omega_engine_operations.domain.rop.result import Ok, Result
from ...application.ports.projection_manifest_port import ProjectionManifestPort
from ...domain.entities.catalog_v3 import EstateCatalogV3
from ...domain.errors.domain_errors import OeopDomainError


def projection_manifest(catalog: EstateCatalogV3, target_format: str) -> dict:
    from ...application.commands.compile_catalog import operation_content_digest

    owners = {str(op.operation_id): doc for doc in catalog.skills.values() for op in doc.operations}
    records = []
    for op_id, op in sorted(catalog.operations.items(), key=lambda row: str(row[0])):
        owner = owners.get(str(op_id))
        record = {
            "operation_id": str(op_id), "skill_id": str(owner.skill_id) if owner else "",
            "source_path": owner.source_relative_path if owner else "",
            "source_digest": str(owner.raw_digest) if owner else "",
            "content_digest": str(operation_content_digest(op)),
            "admission": op.lifecycle.admission.value,
        }
        if op.replacement_operation_id is not None:
            record["replacement_operation_id"] = str(op.replacement_operation_id)
        records.append(record)
    return {
        "schema_version": "oewas.projection.v3", "catalog_id": catalog.catalog_id,
        "catalog_digest": str(catalog.catalog_digest), "epoch": catalog.epoch,
        "target_format": target_format, "skills": sorted(map(str, catalog.skills)),
        "operations": sorted(map(str, catalog.operations)),
        "sources": [{
            "skill_id": str(doc.skill_id), "path": doc.source_relative_path,
            "raw_digest": str(doc.raw_digest), "semantic_digest": str(doc.semantic_digest),
            "operation_ids": sorted(str(op.operation_id) for op in doc.operations),
        } for doc in sorted(catalog.skills.values(), key=lambda item: str(item.skill_id))],
        "operation_records": records,
    }


def read_projection_documents(repo_root: Path, relative_path: str, operation_ids: set[str]):
    """Replay a stored projection against current canonical sources before selection."""
    from ...application.commands.compile_catalog import catalog_content_digest
    from ...application.woland_candidate_plan import PlanRefusal, _PROJECTION_PATH
    from ...domain.entities.catalog_v3 import EstateCatalogV3
    from ...domain.value_objects.identifier import EstateRef, SkillId
    from ..parser.markdown_parser_adapter import LosslessMarkdownParserAdapter
    from ..typed_contract_compiler import _read, compile_typed_contracts

    root = repo_root.absolute().resolve()
    if type(relative_path) is not str or _PROJECTION_PATH.fullmatch(relative_path) is None:
        raise PlanRefusal("PROJECTION_PATH_INVALID", str(relative_path))
    raw = _read(root, relative_path)
    try:
        manifest = json.loads(raw)
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
        if canonical != raw or manifest["schema_version"] != "oewas.projection.v3":
            raise ValueError("canonical projection required")
        documents = []
        typed_documents = None
        for source in manifest["sources"]:
            path = source["path"]
            if type(path) is not str or "\\" in path or ":" in path or any(
                part in {"", ".", ".."} for part in path.split("/")
            ):
                raise ValueError("canonical source path required")
            source_bytes = _read(root, path)
            if path.startswith("omega_engine_operads/catalog/contracts/v1/") and path.endswith(".json"):
                if typed_documents is None:
                    typed_documents = {doc.source_relative_path: doc for doc in compile_typed_contracts(root).all_documents}
                document = typed_documents[path]
            else:
                result = LosslessMarkdownParserAdapter().parse_document(SkillId(source["skill_id"]), path, source_bytes)
                if result.is_err:
                    raise ValueError(str(result.unwrap_err()))
                document = result.unwrap()
            documents.append(document)
        skills = {doc.skill_id: doc for doc in documents}
        operations = {op.operation_id: op for doc in documents for op in doc.operations}
        owners = {op.operation_id: doc.skill_id for doc in documents for op in doc.operations}
        if len(skills) != len(documents) or len(operations) != sum(len(doc.operations) for doc in documents):
            raise ValueError("duplicate source or operation")
        catalog = EstateCatalogV3(
            manifest["catalog_id"], EstateRef("projection"), manifest["epoch"], datetime.now(timezone.utc),
            skills, operations, {}, {}, catalog_content_digest(skills, operations, owners),
        )
        if projection_manifest(catalog, manifest["target_format"]) != manifest:
            raise ValueError("projection differs from current source declarations")
        by_operation = {str(op.operation_id): (doc, op) for doc in documents for op in doc.operations}
        for _doc, op in by_operation.values():
            if op.replacement_operation_id is not None:
                replacement = by_operation.get(str(op.replacement_operation_id))
                if replacement is None or replacement[1].lifecycle.admission.value == "Retired":
                    raise ValueError("replacement is missing or retired")
                if op.inputs != replacement[1].inputs or op.output != replacement[1].output:
                    raise ValueError("replacement ordered interface differs")
        selected = tuple(doc for doc in documents if any(str(op.operation_id) in operation_ids for op in doc.operations))
        if {str(op.operation_id) for doc in selected for op in doc.operations} != operation_ids:
            raise ValueError("selected operation is absent or has unselected siblings")
        return selected, manifest
    except (KeyError, TypeError, ValueError) as error:
        raise PlanRefusal("PROJECTION_REFUSED", str(error)) from error


class ProjectionManifestAdapter(ProjectionManifestPort):
    def emit_projection(
        self,
        catalog: EstateCatalogV3,
        target_format: str,
    ) -> Result[str, OeopDomainError]:
        return Ok(json.dumps(projection_manifest(catalog, target_format), sort_keys=True,
                             separators=(",", ":"), ensure_ascii=True, allow_nan=False))
