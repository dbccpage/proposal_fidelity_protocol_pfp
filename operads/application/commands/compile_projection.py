"""Command Handler: Compile Projection."""

from __future__ import annotations

import hashlib

from omega_engine_operations.domain.rop.result import Err, Ok, Result
from ..dtos.api_error_dto import ApiErrorDTO
from ..dtos.command_dtos import CompileProjectionCommand
from ..dtos.success_dtos import ProjectionResultDTO
from ..ports.id_generator_port import IdGeneratorPort
from ..ports.projection_manifest_port import ProjectionManifestPort
from ..ports.unit_of_work_port import OeopUnitOfWorkPort


class CompileProjectionHandler:
    def __init__(
        self,
        uow: OeopUnitOfWorkPort,
        projection_port: ProjectionManifestPort,
        id_gen: IdGeneratorPort,
    ) -> None:
        self._uow = uow
        self._projection_port = projection_port
        self._id_gen = id_gen

    def handle(self, command: CompileProjectionCommand) -> Result[ProjectionResultDTO, ApiErrorDTO]:
        cat_res = self._uow.get_catalog(command.catalog_id)
        if cat_res.is_err:
            return Err(ApiErrorDTO(code="LOOKUP_ERROR", message=str(cat_res.unwrap_err()), status_code=500))
        catalog = cat_res.unwrap()
        if catalog is None:
            return Err(ApiErrorDTO(code="CATALOG_NOT_FOUND", message=f"Catalog {command.catalog_id} not found", status_code=404))

        emit_res = self._projection_port.emit_projection(catalog, command.target_format)
        if emit_res.is_err:
            return Err(ApiErrorDTO(code="PROJECTION_FAILED", message=str(emit_res.unwrap_err()), status_code=422))

        payload = emit_res.unwrap()
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        proj_id = self._id_gen.generate_id("proj")

        return Ok(ProjectionResultDTO(
            projection_id=proj_id,
            catalog_id=command.catalog_id,
            target_format=command.target_format,
            manifest_digest=digest,
            payload=payload,
        ))
