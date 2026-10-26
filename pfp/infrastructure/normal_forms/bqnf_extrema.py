"""Extremum repair steps for one CDC removal or addition.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RepairTally:
    extrema_repairs: int = 0
    fallback_recomputations: int = 0
    quantile_repairs: int = 0
    quantile_fallback_recomputations: int = 0
    batch_terminal: str = "Repair"


_LOG = """
INSERT INTO extrema_repair_log (
    region, op_type, affected_amount, is_destructive, cochain_available,
    terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def _log(
    cursor: sqlite3.Cursor,
    region: str,
    op_type: str,
    amount: float,
    destructive: int,
    cochain_available: int,
    route: str,
    old_min: Optional[float],
    new_min: Optional[float],
    old_max: Optional[float],
    new_max: Optional[float],
    recomputed: int,
) -> None:
    cursor.execute(
        _LOG,
        (
            region,
            op_type,
            amount,
            destructive,
            cochain_available,
            route,
            old_min,
            new_min,
            old_max,
            new_max,
            recomputed,
        ),
    )


def accumulate_delta(
    region_deltas: dict[str, dict[str, float]],
    op: str,
    old_region: Any,
    new_region: Any,
    old_amount: Any,
    new_amount: Any,
) -> None:
    if op == "INSERT":
        if new_region is None or new_amount is None:
            raise ValueError(
                f"INSERT event missing required new image: region={new_region}, amount={new_amount}"
            )
        bucket = region_deltas.setdefault(new_region, {"amount": 0.0, "count": 0})
        bucket["amount"] += float(new_amount)
        bucket["count"] += 1
        return
    if op == "DELETE":
        if old_region is None or old_amount is None:
            raise ValueError(
                f"DELETE event missing required old image: region={old_region}, amount={old_amount}"
            )
        bucket = region_deltas.setdefault(old_region, {"amount": 0.0, "count": 0})
        bucket["amount"] -= float(old_amount)
        bucket["count"] -= 1
        return
    if old_region is None or new_region is None or old_amount is None or new_amount is None:
        raise ValueError(
            "UPDATE event missing required images: "
            f"old=({old_region}, {old_amount}), new=({new_region}, {new_amount})"
        )
    if old_region == new_region:
        bucket = region_deltas.setdefault(new_region, {"amount": 0.0, "count": 0})
        bucket["amount"] += float(new_amount) - float(old_amount)
        return
    old_bucket = region_deltas.setdefault(old_region, {"amount": 0.0, "count": 0})
    old_bucket["amount"] -= float(old_amount)
    old_bucket["count"] -= 1
    new_bucket = region_deltas.setdefault(new_region, {"amount": 0.0, "count": 0})
    new_bucket["amount"] += float(new_amount)
    new_bucket["count"] += 1


def apply_removal(
    cursor: sqlite3.Cursor,
    current_cache: dict[str, dict[str, Any]],
    region: str,
    amount: float,
    use_cochain: bool,
    tally: RepairTally,
) -> None:
    if region not in current_cache:
        return
    state = current_cache[region]
    old_min = state["min_amount"]
    old_max = state["max_amount"]
    state["total_sales"] -= amount
    state["sale_count"] -= 1
    if state["sale_count"] <= 0:
        del current_cache[region]
        _log(
            cursor,
            region,
            "DELETE",
            amount,
            1,
            1 if use_cochain else 0,
            "Repair",
            old_min,
            None,
            old_max,
            None,
            0,
        )
        return
    destructive = int(
        (old_min is not None and amount == old_min) or (old_max is not None and amount == old_max)
    )
    if not destructive:
        tally.extrema_repairs += 1
        _log(
            cursor,
            region,
            "DELETE",
            amount,
            0,
            1 if use_cochain else 0,
            "Repair",
            old_min,
            old_min,
            old_max,
            old_max,
            0,
        )
        return
    if use_cochain:
        cursor.execute(
            "SELECT amount FROM region_extremum_cochain WHERE region = ? ORDER BY amount ASC LIMIT 1;",
            (region,),
        )
        row_min = cursor.fetchone()
        cursor.execute(
            "SELECT amount FROM region_extremum_cochain WHERE region = ? ORDER BY amount DESC LIMIT 1;",
            (region,),
        )
        row_max = cursor.fetchone()
        if row_min is not None and row_max is not None:
            new_min = float(row_min[0])
            new_max = float(row_max[0])
            state["min_amount"] = new_min
            state["max_amount"] = new_max
            tally.extrema_repairs += 1
            _log(
                cursor,
                region,
                "DELETE",
                amount,
                1,
                1,
                "Repair",
                old_min,
                new_min,
                old_max,
                new_max,
                0,
            )
            return
    cursor.execute(
        "SELECT MIN(amount) AS fb_min, MAX(amount) AS fb_max FROM base_sales WHERE region = ?;",
        (region,),
    )
    fallback = cursor.fetchone()
    new_min = float(fallback["fb_min"]) if fallback["fb_min"] is not None else None
    new_max = float(fallback["fb_max"]) if fallback["fb_max"] is not None else None
    state["min_amount"] = new_min
    state["max_amount"] = new_max
    tally.fallback_recomputations += 1
    tally.batch_terminal = "Recompute"
    _log(cursor, region, "DELETE", amount, 1, 0, "Recompute", old_min, new_min, old_max, new_max, 1)


def apply_addition(
    cursor: sqlite3.Cursor,
    current_cache: dict[str, dict[str, Any]],
    region: str,
    amount: float,
    op_label: str,
    use_cochain: bool,
    tally: RepairTally,
) -> None:
    if region not in current_cache:
        current_cache[region] = {
            "total_sales": amount,
            "sale_count": 1,
            "min_amount": amount,
            "max_amount": amount,
            "median_amount": amount,
        }
        _log(
            cursor,
            region,
            op_label,
            amount,
            0,
            1 if use_cochain else 0,
            "Repair",
            None,
            amount,
            None,
            amount,
            0,
        )
        return
    state = current_cache[region]
    old_min = state["min_amount"]
    old_max = state["max_amount"]
    state["total_sales"] += amount
    state["sale_count"] += 1
    new_min = min(old_min, amount) if old_min is not None else amount
    new_max = max(old_max, amount) if old_max is not None else amount
    state["min_amount"] = new_min
    state["max_amount"] = new_max
    tally.extrema_repairs += 1
    _log(
        cursor,
        region,
        op_label,
        amount,
        0,
        1 if use_cochain else 0,
        "Repair",
        old_min,
        new_min,
        old_max,
        new_max,
        0,
    )
