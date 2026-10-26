"""Incremental BQNF repair of the region sales cache.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from omega_engine_pfp.infrastructure.normal_forms.bqnf_extrema import RepairTally
from omega_engine_pfp.infrastructure.normal_forms.bqnf_extrema import accumulate_delta
from omega_engine_pfp.infrastructure.normal_forms.bqnf_extrema import apply_addition
from omega_engine_pfp.infrastructure.normal_forms.bqnf_extrema import apply_removal
from omega_engine_pfp.infrastructure.normal_forms.sales_cochain import compute_true_median
from omega_engine_pfp.infrastructure.normal_forms.sales_cochain import estimate_quantile

_SUPPORTED = {"INSERT", "UPDATE", "DELETE"}


def _cache_view(current_cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "cached_state": {
            key: (value["total_sales"], value["sale_count"]) for key, value in current_cache.items()
        },
        "cached_extrema": {
            key: (value["min_amount"], value["max_amount"]) for key, value in current_cache.items()
        },
        "cached_medians": {key: value["median_amount"] for key, value in current_cache.items()},
    }


def _unsupported(op: str, current_cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "terminal": "Unsupported",
        "events_processed": 0,
        "verified_consistent": False,
        "error": (
            f"Unsupported CDC operator '{op}' cannot be incrementally maintained "
            "without recomputation"
        ),
        "extrema_repairs": 0,
        "fallback_recomputations": 1,
        "quantile_repairs": 0,
        "quantile_fallback_recomputations": 0,
        **_cache_view(current_cache),
    }


def _idle(cursor: sqlite3.Cursor) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT region,
               COALESCE(SUM(amount), 0.0) AS total_sales,
               COUNT(amount) AS sale_count,
               MIN(amount) AS min_amount,
               MAX(amount) AS max_amount
        FROM base_sales
        GROUP BY region;
        """
    )
    base_rows = cursor.fetchall()
    base_totals = {
        row["region"]: (float(row["total_sales"]), int(row["sale_count"])) for row in base_rows
    }
    base_extrema = {
        row["region"]: (
            float(row["min_amount"]) if row["min_amount"] is not None else None,
            float(row["max_amount"]) if row["max_amount"] is not None else None,
        )
        for row in base_rows
    }
    cursor.execute(
        "SELECT region, total_sales, sale_count, min_amount, max_amount, median_amount "
        "FROM region_sales_cache;"
    )
    cached_rows = cursor.fetchall()
    cached = {
        row["region"]: (float(row["total_sales"]), int(row["sale_count"])) for row in cached_rows
    }
    cached_extrema = {
        row["region"]: (
            float(row["min_amount"]) if row["min_amount"] is not None else None,
            float(row["max_amount"]) if row["max_amount"] is not None else None,
        )
        for row in cached_rows
    }
    cached_medians = {
        row["region"]: float(row["median_amount"]) if row["median_amount"] is not None else None
        for row in cached_rows
    }
    regions = set(cached) | set(base_totals)
    consistent = cached == base_totals and all(
        cached_extrema.get(region) == base_extrema.get(region) for region in regions
    )
    return {
        "terminal": "Preserve" if consistent else "Recompute",
        "events_processed": 0,
        "verified_consistent": consistent,
        "cached_state": cached,
        "cached_extrema": cached_extrema,
        "cached_medians": cached_medians,
        "extrema_repairs": 0,
        "fallback_recomputations": 0 if consistent else 1,
        "quantile_repairs": 0,
        "quantile_fallback_recomputations": 0,
    }


def _load_cache(cursor: sqlite3.Cursor) -> dict[str, dict[str, Any]]:
    cursor.execute(
        "SELECT region, total_sales, sale_count, min_amount, max_amount, median_amount "
        "FROM region_sales_cache;"
    )
    return {
        row["region"]: {
            "total_sales": float(row["total_sales"]),
            "sale_count": int(row["sale_count"]),
            "min_amount": float(row["min_amount"]) if row["min_amount"] is not None else None,
            "max_amount": float(row["max_amount"]) if row["max_amount"] is not None else None,
            "median_amount": float(row["median_amount"])
            if row["median_amount"] is not None
            else None,
        }
        for row in cursor.fetchall()
    }


def _quantiles(
    conn: sqlite3.Connection,
    cursor: sqlite3.Cursor,
    current_cache: dict[str, dict[str, Any]],
    use_cochain: bool,
    track_quantiles: bool,
    quantile_tolerance: float,
    tally: RepairTally,
) -> None:
    for region, state in list(current_cache.items()):
        true_median = compute_true_median(conn, region)
        estimated = estimate_quantile(conn, region, q=0.5) if use_cochain else None
        if estimated is not None and true_median is not None:
            error = abs(estimated - true_median)
            within = error <= quantile_tolerance
            state["median_amount"] = estimated if within else true_median
            if within:
                tally.quantile_repairs += 1
            else:
                tally.quantile_fallback_recomputations += 1
                if track_quantiles:
                    tally.batch_terminal = "Recompute"
            cursor.execute(
                """
                INSERT INTO quantile_repair_log (
                    region, op_type, affected_amount, estimated_median, true_median,
                    error_delta, tolerance, within_tolerance, terminal_route,
                    recomputation_fallback_executed
                ) VALUES (?, 'BATCH', NULL, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    region,
                    estimated,
                    true_median,
                    error,
                    quantile_tolerance,
                    1 if within else 0,
                    "Repair" if within else "Recompute",
                    0 if within else 1,
                ),
            )
            continue
        state["median_amount"] = true_median
        if true_median is None:
            continue
        tally.quantile_fallback_recomputations += 1
        if track_quantiles:
            tally.batch_terminal = "Recompute"
        cursor.execute(
            """
            INSERT INTO quantile_repair_log (
                region, op_type, affected_amount, estimated_median, true_median,
                error_delta, tolerance, within_tolerance, terminal_route,
                recomputation_fallback_executed
            ) VALUES (?, 'BATCH', NULL, NULL, ?, NULL, ?, 0, 'Recompute', 1);
            """,
            (region, true_median, quantile_tolerance),
        )


def _persist(cursor: sqlite3.Cursor, current_cache: dict[str, dict[str, Any]]) -> None:
    if current_cache:
        cursor.execute("SELECT region FROM region_sales_cache;")
        stale = [row["region"] for row in cursor.fetchall() if row["region"] not in current_cache]
        if stale:
            cursor.executemany(
                "DELETE FROM region_sales_cache WHERE region = ?;",
                [(region,) for region in stale],
            )
    else:
        cursor.execute("DELETE FROM region_sales_cache;")
    for region, state in current_cache.items():
        cursor.execute(
            """
            INSERT INTO region_sales_cache (
                region, total_sales, sale_count, min_amount, max_amount, median_amount
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(region) DO UPDATE SET
                total_sales = excluded.total_sales,
                sale_count = excluded.sale_count,
                min_amount = excluded.min_amount,
                max_amount = excluded.max_amount,
                median_amount = excluded.median_amount;
            """,
            (
                region,
                state["total_sales"],
                state["sale_count"],
                state["min_amount"],
                state["max_amount"],
                state["median_amount"],
            ),
        )


def _audit(cursor: sqlite3.Cursor, tally: RepairTally, events: int, deltas: dict) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT region, SUM(amount) AS true_sales, COUNT(*) AS true_count,
               MIN(amount) AS true_min, MAX(amount) AS true_max
        FROM base_sales
        GROUP BY region;
        """
    )
    recomputed = {
        row["region"]: (row["true_sales"], row["true_count"], row["true_min"], row["true_max"])
        for row in cursor.fetchall()
    }
    cursor.execute(
        "SELECT region, total_sales, sale_count, min_amount, max_amount, median_amount "
        "FROM region_sales_cache;"
    )
    rows = cursor.fetchall()
    cached_full = {
        row["region"]: (row["total_sales"], row["sale_count"], row["min_amount"], row["max_amount"])
        for row in rows
    }
    return {
        "terminal": tally.batch_terminal,
        "events_processed": events,
        "deltas_applied": deltas,
        "verified_consistent": recomputed == cached_full,
        "cached_state": {row["region"]: (row["total_sales"], row["sale_count"]) for row in rows},
        "cached_extrema": {row["region"]: (row["min_amount"], row["max_amount"]) for row in rows},
        "cached_medians": {row["region"]: row["median_amount"] for row in rows},
        "extrema_repairs": tally.extrema_repairs,
        "fallback_recomputations": tally.fallback_recomputations,
        "quantile_repairs": tally.quantile_repairs,
        "quantile_fallback_recomputations": tally.quantile_fallback_recomputations,
    }


def process_bqnf_incremental_repair(
    conn: sqlite3.Connection,
    use_cochain: bool = True,
    track_quantiles: bool = False,
    quantile_tolerance: float = 15.0,
) -> dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_cdc_log WHERE processed = 0 ORDER BY cdc_id ASC;")
    pending = cursor.fetchall()
    if not pending:
        return _idle(cursor)
    current_cache = _load_cache(cursor)
    deltas: dict[str, dict[str, float]] = {}
    tally = RepairTally()
    for row in pending:
        op = row["op_type"]
        if op not in _SUPPORTED:
            return _unsupported(op, current_cache)
        accumulate_delta(
            deltas, op, row["old_region"], row["new_region"], row["old_amount"], row["new_amount"]
        )
        if op == "INSERT" and row["new_region"] and row["new_amount"] is not None:
            apply_addition(
                cursor,
                current_cache,
                row["new_region"],
                row["new_amount"],
                "INSERT",
                use_cochain,
                tally,
            )
        elif op == "DELETE" and row["old_region"] and row["old_amount"] is not None:
            apply_removal(
                cursor, current_cache, row["old_region"], row["old_amount"], use_cochain, tally
            )
        elif op == "UPDATE":
            if row["old_region"] and row["old_amount"] is not None:
                apply_removal(
                    cursor, current_cache, row["old_region"], row["old_amount"], use_cochain, tally
                )
            if row["new_region"] and row["new_amount"] is not None:
                apply_addition(
                    cursor,
                    current_cache,
                    row["new_region"],
                    row["new_amount"],
                    "UPDATE",
                    use_cochain,
                    tally,
                )
    _quantiles(conn, cursor, current_cache, use_cochain, track_quantiles, quantile_tolerance, tally)
    _persist(cursor, current_cache)
    cursor.execute("UPDATE sales_cdc_log SET processed = 1 WHERE processed = 0;")
    conn.commit()
    return _audit(cursor, tally, len(pending), deltas)
