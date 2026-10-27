"""Query Handler: Get Catalog."""

from __future__ import annotations

from operations.domain.rop.result import Err, Ok, Result
from ...domain.entities.catalog_v3 import EstateCatalogV3
from ..dtos.api_error_dto import ApiErrorDTO
from ..dtos.query_dtos import GetCatalogQuery
from ..ports.unit_of_work_port import OeopUnitOfWorkPort


class GetCatalogHandler:
    def __init__(self, uow: OeopUnitOfWorkPort) -> None:
        self._uow = uow

    def handle(self, query: GetCatalogQuery) -> Result[EstateCatalogV3, ApiErrorDTO]:
        if query.catalog_id == "latest":
            res = self._uow.get_latest_catalog()
        else:
            res = self._uow.get_catalog(query.catalog_id)

        if res.is_err:
            return Err(ApiErrorDTO(code="CATALOG_LOOKUP_FAILED", message=str(res.unwrap_err()), status_code=500))
        catalog = res.unwrap()
        if catalog is None:
            return Err(ApiErrorDTO(code="CATALOG_NOT_FOUND", message=f"Catalog {query.catalog_id} not found", status_code=404))
        return Ok(catalog)
