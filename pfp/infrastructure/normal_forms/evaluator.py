"""SQLite session that delegates normal-form evaluation.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

from omega_engine_pfp.infrastructure.normal_forms.bqnf_repair import (
    process_bqnf_incremental_repair as repair_bqnf,
)
from omega_engine_pfp.infrastructure.normal_forms.db_context import NormalFormsDbContext
from omega_engine_pfp.infrastructure.normal_forms.relational_eval import (
    evaluate_5nf_project_join_integrity as witness_5nf,
)
from omega_engine_pfp.infrastructure.normal_forms.relational_eval import (
    normalize_0nf_to_1nf as flatten_0nf,
)
from omega_engine_pfp.infrastructure.normal_forms.sales_cochain import (
    apply_sales_cdc as record_sales_cdc,
)
from omega_engine_pfp.infrastructure.normal_forms.sales_cochain import (
    compute_true_median as median_of,
)
from omega_engine_pfp.infrastructure.normal_forms.sales_cochain import (
    estimate_quantile as quantile_of,
)
from omega_engine_pfp.infrastructure.normal_forms.schema_sql import install_schema
from omega_engine_pfp.infrastructure.normal_forms.sn_dispatch import (
    evaluate_sn_transition as dispatch_sn,
)
from omega_engine_pfp.infrastructure.normal_forms.sn_dispatch import resolve_contract
from omega_engine_pfp.infrastructure.normal_forms.sn_forms import (
    evaluate_sn_pdnf as form_pdnf,
)
from omega_engine_pfp.infrastructure.normal_forms.sn_forms import (
    evaluate_sn_pvnf as form_pvnf,
)
from omega_engine_pfp.infrastructure.normal_forms.sn_forms import (
    evaluate_sn_rpnf as form_rpnf,
)
from omega_engine_pfp.infrastructure.normal_forms.sn_forms import (
    evaluate_sn_scnf as form_scnf,
)
from omega_engine_pfp.infrastructure.normal_forms.sn_forms import (
    evaluate_sn_state as form_state,
)


class NormalFormsEvaluator:
    """Own one normal-forms database session."""

    def __init__(
        self,
        in_memory: bool = True,
        conn: Optional[sqlite3.Connection] = None,
        db_context: Optional[NormalFormsDbContext] = None,
    ) -> None:
        if db_context is not None:
            self.db_context = db_context
        else:
            self.db_context = NormalFormsDbContext(in_memory=in_memory, conn=conn)
        self.conn = self.db_context.connection
        install_schema(self.conn)

    def __enter__(self) -> NormalFormsEvaluator:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def transaction(self):
        return self.db_context.transaction()

    def close(self) -> None:
        if self.db_context is not None:
            self.db_context.close()

    @staticmethod
    def _resolve_contract(
        contract_id: str,
        contract_path: Optional[Path] = None,
    ) -> dict[str, Any]:
        return resolve_contract(contract_id, contract_path)

    def normalize_0nf_to_1nf(self, raw_records: list[tuple[int, str, str]]) -> list[dict[str, Any]]:
        return flatten_0nf(self.conn, raw_records)

    def evaluate_5nf_project_join_integrity(
        self,
        fill2_tuples: list[tuple[str, str, str]],
    ) -> dict[str, Any]:
        return witness_5nf(self.conn, fill2_tuples)

    def apply_sales_cdc(
        self,
        op_type: str,
        sale_id: int,
        old_region: Optional[str] = None,
        new_region: Optional[str] = None,
        old_amount: Optional[float] = None,
        new_amount: Optional[float] = None,
        maintain_cochain: bool = True,
    ):
        return record_sales_cdc(
            self.conn,
            op_type,
            sale_id,
            old_region,
            new_region,
            old_amount,
            new_amount,
            maintain_cochain,
        )

    def estimate_quantile(self, region: str, q: float = 0.5) -> Optional[float]:
        return quantile_of(self.conn, region, q)

    def compute_true_median(self, region: str) -> Optional[float]:
        return median_of(self.conn, region)

    def process_bqnf_incremental_repair(
        self,
        use_cochain: bool = True,
        track_quantiles: bool = False,
        quantile_tolerance: float = 15.0,
    ) -> dict[str, Any]:
        return repair_bqnf(self.conn, use_cochain, track_quantiles, quantile_tolerance)

    incremental_cdc_cache_maintenance = process_bqnf_incremental_repair

    def evaluate_sn_transition(
        self,
        contract_id: str,
        fixture: dict[str, Any],
        contract_path: Optional[Path] = None,
    ) -> dict[str, Any]:
        return dispatch_sn(contract_id, fixture, contract_path)

    def evaluate_sn_pdnf(
        self,
        fixture: dict[str, Any],
        route_map: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        return form_pdnf(fixture, route_map)

    def evaluate_sn_rpnf(
        self,
        fixture: dict[str, Any],
        route_map: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        return form_rpnf(fixture, route_map)

    def evaluate_sn_scnf(
        self,
        fixture: dict[str, Any],
        route_map: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        return form_scnf(fixture, route_map)

    def evaluate_sn_state(
        self,
        fixture: dict[str, Any],
        route_map: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        return form_state(fixture, route_map)

    def evaluate_sn_pvnf(
        self,
        fixture: dict[str, Any],
        route_map: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        return form_pvnf(fixture, route_map)
