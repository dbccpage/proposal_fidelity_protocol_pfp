"""Command Handler: Compile Catalog."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping, Optional

from operations.domain.rop.result import Err, Ok, Result

from ...domain.entities.catalog_v3 import CapabilitySliceV3, EstateCatalogV3
from ...domain.entities.operation_v3 import OperationV3, PortSpecV3
from ...domain.entities.skill_document_v3 import SkillDocumentV3
from ...domain.events.domain_events import CatalogCompiledV3, EstateCapturedV3
from ...domain.value_objects.content_digest import ContentDigest
from ...domain.value_objects.identifier import OperationId, SkillId
from ..dtos.api_error_dto import ApiErrorDTO
from ..dtos.command_dtos import CompileCatalogCommand
from ..dtos.success_dtos import CompileCatalogResultDTO
from ..ports.clock_port import ClockPort
from ..ports.estate_source_port import EstateSourcePort
from ..ports.id_generator_port import IdGeneratorPort
from ..ports.legacy_catalog_reader_port import LegacyCatalogReaderPort
from ..ports.skill_document_parser_port import SkillDocumentParserPort
from ..ports.unit_of_work_port import OeopUnitOfWorkPort

CATALOG_DIGEST_SCHEMA = "oewas.catalog_digest.v2"


def _canonical_json_bytes(value: Any) -> bytes:
    """Sorted keys, no whitespace, ASCII only, NaN refused.

    JSON arrays and strings are self-delimiting, so no two different payloads
    share an encoding -- unlike the concatenation of bare ids this replaces,
    under which ``["ab", "c"]`` and ``["a", "bc"]`` hashed identically.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _optional_digest(digest: Optional[ContentDigest]) -> Optional[str]:
    return None if digest is None else str(digest)


def _port_record(port: PortSpecV3) -> Dict[str, Any]:
    return {
        "colour_id": str(port.colour_id),
        "name": port.name,
        "schema_digest": str(port.schema_digest),
        "schema_ref": str(port.schema_ref),
        "validator_digest": str(port.validator_digest),
        "validator_ref": port.validator_ref,
    }


def _operation_record(op: OperationV3) -> Dict[str, Any]:
    lifecycle = op.lifecycle
    record = {
        "authority_ceiling": op.authority_ceiling.value,
        "authority_effect": op.authority_effect.value,
        "description": op.description,
        "effects": list(op.effects),
        "inputs": [_port_record(port) for port in op.inputs],
        "invocation_grade": op.invocation_grade,
        "lifecycle": {
            "admission": lifecycle.admission.value,
            "declaration": lifecycle.declaration.value,
            "executor_binding": lifecycle.executor_binding.value,
            "executor_digest": _optional_digest(lifecycle.executor_digest),
            "schema_binding": lifecycle.schema_binding.value,
            "schema_digest": _optional_digest(lifecycle.schema_digest),
            "validation": lifecycle.validation.value,
        },
        "operand_refs": [str(ref) for ref in op.operand_refs],
        "operation_id": str(op.operation_id),
        "output": _port_record(op.output),
        "residual_status": op.residual_status,
        "tool_refs": list(op.tool_refs),
    }
    if op.replacement_operation_id is not None:
        record["replacement_operation_id"] = str(op.replacement_operation_id)
    return record


def operation_content_bytes(op: OperationV3) -> bytes:
    """Exact existing digest profile consumed by the native typed graph port."""
    return _canonical_json_bytes(_operation_record(op))


def operation_content_digest(op: OperationV3) -> ContentDigest:
    """Digest of everything an operation declares, not only its id."""
    return ContentDigest.sha256(
        hashlib.sha256(operation_content_bytes(op)).hexdigest()
    )


def _ordinal(key: Any) -> bytes:
    return str(key).encode("utf-8")


def catalog_content_digest(
    skills: Mapping[SkillId, SkillDocumentV3],
    operations: Mapping[OperationId, OperationV3],
    operation_owners: Mapping[OperationId, SkillId],
) -> ContentDigest:
    """Content-addressed digest of a compiled catalog.

    Covers every skill document (its identity and the raw and semantic digests
    of its bytes) and every operation (its id, its owning skill and the digest
    of its declared content), in ordinal UTF-8 order of their ids.
    """
    payload = {
        "operations": [
            {
                "content_digest": str(operation_content_digest(operations[op_id])),
                "operation_id": str(op_id),
                "skill_id": str(operation_owners[op_id]),
            }
            for op_id in sorted(operations, key=_ordinal)
        ],
        "schema": CATALOG_DIGEST_SCHEMA,
        "skills": [
            {
                "document_id": str(skills[skill_id].document_id),
                "raw_digest": str(skills[skill_id].raw_digest),
                "semantic_digest": str(skills[skill_id].semantic_digest),
                "skill_id": str(skill_id),
                "source_relative_path": skills[skill_id].source_relative_path,
            }
            for skill_id in sorted(skills, key=_ordinal)
        ],
    }
    return ContentDigest.sha256(hashlib.sha256(_canonical_json_bytes(payload)).hexdigest())


class CompileCatalogHandler:
    def __init__(
        self,
        estate_source: EstateSourcePort,
        parser: SkillDocumentParserPort,
        legacy_reader: LegacyCatalogReaderPort,
        uow: OeopUnitOfWorkPort,
        clock: ClockPort,
        id_gen: IdGeneratorPort,
    ) -> None:
        self._estate_source = estate_source
        self._parser = parser
        self._legacy_reader = legacy_reader
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    def handle(self, command: CompileCatalogCommand) -> Result[CompileCatalogResultDTO, ApiErrorDTO]:
        # 1. Check idempotency if key provided
        request_fields: Dict[str, Any] = {
            "estate_ref": str(command.estate_ref),
            "expected_version": command.expected_version,
        }
        # Encoded only when set, so requests that do not use the flag keep the
        # digest they had before it existed.
        if command.allow_empty_estate:
            request_fields["allow_empty_estate"] = True
        req_digest = hashlib.sha256(
            json.dumps(
                request_fields,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if command.idempotency_key:
            idem_res = self._uow.check_idempotency(command.idempotency_key, req_digest)
            if idem_res.is_ok and idem_res.unwrap() is not None:
                cached = idem_res.unwrap()
                return Ok(CompileCatalogResultDTO(
                    catalog_id=cached.get("catalog_id", ""),
                    estate_ref=cached.get("estate_ref", str(command.estate_ref)),
                    epoch=cached.get("epoch", 1),
                    total_skills=cached.get("total_skills", 0),
                    total_operations=cached.get("total_operations", 0),
                    catalog_digest=cached.get("catalog_digest", ""),
                ))
            elif idem_res.is_err:
                err = idem_res.unwrap_err()
                return Err(ApiErrorDTO(
                    code=err.code,
                    message=err.message,
                    status_code=409,
                ))

        latest_res = self._uow.get_latest_catalog(str(command.estate_ref))
        if latest_res.is_err:
            return Err(ApiErrorDTO(
                code="CATALOG_VERSION_LOOKUP_FAILED",
                message=str(latest_res.unwrap_err()),
                status_code=500,
            ))
        latest_catalog = latest_res.unwrap()
        current_version = latest_catalog.epoch if latest_catalog is not None else 0
        if (
            command.expected_version is not None
            and command.expected_version != current_version
        ):
            return Err(ApiErrorDTO(
                code="CONCURRENCY_CONFLICT",
                message=(
                    f"Estate {command.estate_ref} is at version {current_version}, "
                    f"not expected version {command.expected_version}"
                ),
                status_code=409,
            ))

        # 2. List skills
        paths_res = self._estate_source.list_skill_paths(command.estate_ref)
        if paths_res.is_err:
            return Err(ApiErrorDTO(
                code="ESTATE_LIST_FAILED",
                message=str(paths_res.unwrap_err()),
                status_code=500,
            ))
        paths = paths_res.unwrap()

        skills: Dict[SkillId, SkillDocumentV3] = {}
        operations: Dict[OperationId, OperationV3] = {}
        operation_owners: Dict[OperationId, SkillId] = {}
        capability_slices: Dict[str, CapabilitySliceV3] = {}
        aliases: Dict[str, OperationId] = {}
        documents: list[SkillDocumentV3] = []

        if not paths:
            # No tracked skill paths: read the legacy estate instead. A failed
            # read is refused. It used to fall through with nothing read and
            # persist an empty epoch as if the estate had no skills.
            legacy_res = self._legacy_reader.read_legacy_estate(command.estate_ref)
            if legacy_res.is_err:
                return Err(ApiErrorDTO(
                    code="LEGACY_READ_FAILED",
                    message=str(legacy_res.unwrap_err()),
                    status_code=500,
                ))
            documents.extend(legacy_res.unwrap())
        else:
            for p in paths:
                compiled_res = self._estate_source.read_compiled_skill_document(p)
                if compiled_res.is_err:
                    return Err(ApiErrorDTO(
                        code="DOCUMENT_COMPILE_ERROR", message=str(compiled_res.unwrap_err()),
                        status_code=400, locus=p,
                    ))
                if compiled_res.unwrap() is not None:
                    documents.append(compiled_res.unwrap())
                    continue
                bytes_res = self._estate_source.read_skill_bytes(p)
                if bytes_res.is_err:
                    err = bytes_res.unwrap_err()
                    return Err(ApiErrorDTO(
                        code="DOCUMENT_READ_ERROR",
                        message=str(err),
                        status_code=500,
                        locus=p,
                    ))
                content = bytes_res.unwrap()
                # Derive skill id from path
                name = p.replace("\\", "/").split("/")[-2] if "/" in p else "skill"
                skill_id = SkillId(name)
                parse_res = self._parser.parse_document(skill_id, p, content)
                if parse_res.is_err:
                    err = parse_res.unwrap_err()
                    locus = getattr(err, "locus", "")
                    return Err(ApiErrorDTO(
                        code="DOCUMENT_PARSE_ERROR",
                        message=str(err),
                        status_code=400,
                        locus=locus,
                    ))
                documents.append(parse_res.unwrap())

        # Keyed maps would let a second document with the same skill id, or a
        # second operation with the same id, silently replace the first and
        # drop it from the catalog and its digest.
        for doc in documents:
            if doc.skill_id in skills:
                return Err(ApiErrorDTO(
                    code="DUPLICATE_SKILL_ID",
                    message=f"skill {doc.skill_id} is declared by more than one document",
                    status_code=400,
                    locus=doc.source_relative_path,
                ))
            skills[doc.skill_id] = doc
            for op in doc.operations:
                if op.operation_id in operations:
                    return Err(ApiErrorDTO(
                        code="DUPLICATE_OPERATION_ID",
                        message=(
                            f"operation {op.operation_id} is declared by both "
                            f"{operation_owners[op.operation_id]} and {doc.skill_id}"
                        ),
                        status_code=400,
                        locus=doc.source_relative_path,
                    ))
                operations[op.operation_id] = op
                operation_owners[op.operation_id] = doc.skill_id

        if not skills and not command.allow_empty_estate:
            return Err(ApiErrorDTO(
                code="EMPTY_ESTATE",
                message=(
                    f"estate {command.estate_ref} yielded no skill documents; an "
                    "empty catalog epoch is only compiled when the command sets "
                    "allow_empty_estate"
                ),
                status_code=422,
            ))

        # Compute catalog digest
        cat_id = self._id_gen.generate_id("cat")
        cat_digest = catalog_content_digest(skills, operations, operation_owners)

        catalog = EstateCatalogV3(
            catalog_id=cat_id,
            estate_ref=command.estate_ref,
            epoch=current_version + 1,
            compiled_at=self._clock.now_utc(),
            skills=skills,
            operations=operations,
            capability_slices=capability_slices,
            aliases=aliases,
            catalog_digest=cat_digest,
        )

        events = (
            EstateCapturedV3.create(
                event_id=self._id_gen.generate_id("evt"),
                correlation_id=str(command.correlation_id),
                causation_id=str(command.causation_id),
                estate_ref=command.estate_ref,
                document_count=len(skills),
                raw_digest=cat_digest,
            ),
            CatalogCompiledV3.create(
                event_id=self._id_gen.generate_id("evt"),
                correlation_id=str(command.correlation_id),
                causation_id=str(command.causation_id),
                catalog_id=cat_id,
                epoch=current_version + 1,
                total_skills=len(skills),
                total_operations=len(operations),
                catalog_digest=cat_digest,
            ),
        )

        dto = CompileCatalogResultDTO(
            catalog_id=cat_id,
            estate_ref=str(command.estate_ref),
            epoch=current_version + 1,
            total_skills=len(skills),
            total_operations=len(operations),
            catalog_digest=str(cat_digest),
        )

        save_res = self._uow.save_catalog(
            catalog=catalog,
            events=events,
            idempotency_key=command.idempotency_key,
            request_digest=req_digest,
            response_data={
                "catalog_id": cat_id,
                "estate_ref": str(command.estate_ref),
                "epoch": current_version + 1,
                "total_skills": len(skills),
                "total_operations": len(operations),
                "catalog_digest": str(cat_digest),
            },
            expected_version=command.expected_version,
        )
        if save_res.is_err:
            err = save_res.unwrap_err()
            if err.code == "CONCURRENCY_CONFLICT":
                return Err(ApiErrorDTO(
                    code=err.code,
                    message=err.message,
                    status_code=409,
                ))
            return Err(ApiErrorDTO(
                code="CATALOG_PERSIST_FAILED",
                message=str(err),
                status_code=500,
            ))

        if command.idempotency_key:
            idem_res = self._uow.check_idempotency(command.idempotency_key, req_digest)
            if idem_res.is_ok and idem_res.unwrap() is not None:
                cached = idem_res.unwrap()
                return Ok(CompileCatalogResultDTO(
                    catalog_id=cached.get("catalog_id", cat_id),
                    estate_ref=cached.get("estate_ref", str(command.estate_ref)),
                    epoch=cached.get("epoch", 1),
                    total_skills=cached.get("total_skills", len(skills)),
                    total_operations=cached.get("total_operations", len(operations)),
                    catalog_digest=cached.get("catalog_digest", str(cat_digest)),
                ))

        return Ok(dto)
