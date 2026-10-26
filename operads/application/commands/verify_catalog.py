"""Command Handler: Verify Catalog."""

from __future__ import annotations

from omega_engine_operations.domain.rop.result import Err, Ok, Result
from ..dtos.api_error_dto import ApiErrorDTO
from ..dtos.command_dtos import VerifyCatalogCommand
from ..dtos.success_dtos import VerifyCatalogResultDTO
from ..ports.strict_operad_port import StrictOperadPort
from ..ports.unit_of_work_port import OeopUnitOfWorkPort


class VerifyCatalogHandler:
    def __init__(
        self,
        uow: OeopUnitOfWorkPort,
        operad_port: StrictOperadPort,
    ) -> None:
        self._uow = uow
        self._operad_port = operad_port

    def handle(self, command: VerifyCatalogCommand) -> Result[VerifyCatalogResultDTO, ApiErrorDTO]:
        cat_res = self._uow.get_catalog(command.catalog_id)
        if cat_res.is_err:
            return Err(ApiErrorDTO(
                code="CATALOG_LOOKUP_FAILED",
                message=str(cat_res.unwrap_err()),
                status_code=500,
            ))
        catalog = cat_res.unwrap()
        if catalog is None:
            return Err(ApiErrorDTO(
                code="CATALOG_NOT_FOUND",
                message=f"Catalog {command.catalog_id} not found",
                status_code=404,
            ))

        errors = []
        # Verify operations
        for op in catalog.operations.values():
            if not op.operation_id:
                errors.append("Empty operation_id detected")

        # Verify compositions in skill documents
        for doc in catalog.skills.values():
            for comp in doc.compositions:
                root_op = catalog.operations.get(comp.root_operation_id)
                if not root_op:
                    errors.append(f"Composition root operation {comp.root_operation_id} not found in catalog")
                    continue
                resolved_slots = []
                for slot_idx, child_id in comp.slot_bindings:
                    child_op = catalog.operations.get(child_id)
                    if not child_op:
                        errors.append(f"Composition child operation {child_id} not found in catalog")
                        continue
                    resolved_slots.append((slot_idx, child_op))
                if resolved_slots:
                    v_res = self._operad_port.verify_composition(root_op, (), tuple(resolved_slots))
                    if v_res.is_err:
                        errors.append(f"Composition {comp.composition_id} failed verification: {v_res.unwrap_err()}")

        is_valid = len(errors) == 0
        return Ok(VerifyCatalogResultDTO(
            catalog_id=catalog.catalog_id,
            is_valid=is_valid,
            total_operations_verified=len(catalog.operations),
            errors=tuple(errors),
        ))
