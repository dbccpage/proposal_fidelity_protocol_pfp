"""CDC application and the extremum and quantile cochains.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import sqlite3
from typing import Optional


def cochain_add(conn: sqlite3.Connection, region: str, amount: float) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT frequency FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
        (region, amount),
    )
    if cursor.fetchone():
        cursor.execute(
            "UPDATE region_extremum_cochain SET frequency = frequency + 1 "
            "WHERE region = ? AND amount = ?;",
            (region, amount),
        )
        return
    cursor.execute(
        "INSERT INTO region_extremum_cochain (region, amount, frequency) VALUES (?, ?, 1);",
        (region, amount),
    )


def cochain_remove(conn: sqlite3.Connection, region: str, amount: float) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT frequency FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
        (region, amount),
    )
    row = cursor.fetchone()
    if row is None:
        return
    if row["frequency"] <= 1:
        cursor.execute(
            "DELETE FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
            (region, amount),
        )
        return
    cursor.execute(
        "UPDATE region_extremum_cochain SET frequency = frequency - 1 "
        "WHERE region = ? AND amount = ?;",
        (region, amount),
    )


def quantile_cochain_add(
    conn: sqlite3.Connection,
    region: str,
    amount: float,
    bucket_width: float = 10.0,
) -> None:
    cursor = conn.cursor()
    bucket_id = int(math.floor(amount / bucket_width))
    lower = bucket_id * bucket_width
    upper = (bucket_id + 1) * bucket_width
    cursor.execute(
        "SELECT count FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
        (region, bucket_id),
    )
    if cursor.fetchone():
        cursor.execute(
            "UPDATE region_quantile_cochain SET count = count + 1 "
            "WHERE region = ? AND bucket_id = ?;",
            (region, bucket_id),
        )
        return
    cursor.execute(
        "INSERT INTO region_quantile_cochain "
        "(region, bucket_id, lower_bound, upper_bound, count) VALUES (?, ?, ?, ?, 1);",
        (region, bucket_id, lower, upper),
    )


def quantile_cochain_remove(
    conn: sqlite3.Connection,
    region: str,
    amount: float,
    bucket_width: float = 10.0,
) -> None:
    cursor = conn.cursor()
    bucket_id = int(math.floor(amount / bucket_width))
    cursor.execute(
        "SELECT count FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
        (region, bucket_id),
    )
    row = cursor.fetchone()
    if row is None:
        return
    if row["count"] <= 1:
        cursor.execute(
            "DELETE FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
            (region, bucket_id),
        )
        return
    cursor.execute(
        "UPDATE region_quantile_cochain SET count = count - 1 WHERE region = ? AND bucket_id = ?;",
        (region, bucket_id),
    )


def estimate_quantile(
    conn: sqlite3.Connection,
    region: str,
    q: float = 0.5,
) -> Optional[float]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT bucket_id, lower_bound, upper_bound, count
        FROM region_quantile_cochain
        WHERE region = ? AND count > 0
        ORDER BY bucket_id ASC;
        """,
        (region,),
    )
    buckets = cursor.fetchall()
    if not buckets:
        return None
    total_count = sum(bucket["count"] for bucket in buckets)
    if total_count == 0:
        return None
    target_rank = q * total_count
    cumulative = 0
    for bucket in buckets:
        count = bucket["count"]
        if cumulative + count >= target_rank:
            fraction = (target_rank - cumulative) / count if count > 0 else 0.0
            return bucket["lower_bound"] + fraction * (
                bucket["upper_bound"] - bucket["lower_bound"]
            )
        cumulative += count
    return buckets[-1]["upper_bound"]


def compute_true_median(conn: sqlite3.Connection, region: str) -> Optional[float]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT amount FROM base_sales WHERE region = ? ORDER BY amount ASC;",
        (region,),
    )
    rows = cursor.fetchall()
    if not rows:
        return None
    count = len(rows)
    if count % 2 == 1:
        return float(rows[count // 2]["amount"])
    return float(rows[count // 2 - 1]["amount"] + rows[count // 2]["amount"]) / 2.0


def apply_sales_cdc(
    conn: sqlite3.Connection,
    op_type: str,
    sale_id: int,
    old_region: Optional[str] = None,
    new_region: Optional[str] = None,
    old_amount: Optional[float] = None,
    new_amount: Optional[float] = None,
    maintain_cochain: bool = True,
) -> None:
    cursor = conn.cursor()
    if op_type in ("UPDATE", "DELETE") and (old_region is None or old_amount is None):
        cursor.execute("SELECT region, amount FROM base_sales WHERE sale_id = ?;", (sale_id,))
        row = cursor.fetchone()
        if row:
            if old_region is None:
                old_region = row["region"]
            if old_amount is None:
                old_amount = row["amount"]
    if op_type == "INSERT":
        cursor.execute(
            "INSERT INTO base_sales VALUES (?, ?, ?);",
            (sale_id, new_region, new_amount),
        )
        if maintain_cochain and new_region is not None and new_amount is not None:
            cochain_add(conn, new_region, new_amount)
            quantile_cochain_add(conn, new_region, new_amount)
    elif op_type == "DELETE":
        cursor.execute("DELETE FROM base_sales WHERE sale_id = ?;", (sale_id,))
        if maintain_cochain and old_region is not None and old_amount is not None:
            cochain_remove(conn, old_region, old_amount)
            quantile_cochain_remove(conn, old_region, old_amount)
    elif op_type == "UPDATE":
        cursor.execute(
            "UPDATE base_sales SET region = ?, amount = ? WHERE sale_id = ?;",
            (new_region, new_amount, sale_id),
        )
        if maintain_cochain:
            if old_region is not None and old_amount is not None:
                cochain_remove(conn, old_region, old_amount)
                quantile_cochain_remove(conn, old_region, old_amount)
            if new_region is not None and new_amount is not None:
                cochain_add(conn, new_region, new_amount)
                quantile_cochain_add(conn, new_region, new_amount)
    cursor.execute(
        """
        INSERT INTO sales_cdc_log (
            op_type, sale_id, old_region, new_region, old_amount, new_amount, processed
        ) VALUES (?, ?, ?, ?, ?, ?, 0);
        """,
        (op_type, sale_id, old_region, new_region, old_amount, new_amount),
    )
    conn.commit()
