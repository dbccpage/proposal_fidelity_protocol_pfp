"""
Relational Normal Forms and BQNF Incremental Evaluator
AuthorityEffect: None.
"""

import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from omega_engine_governance.infrastructure.storage.schema_totality import install_totality_fences
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR


class NormalFormsEvaluator:
    """
    Evaluator for classical normal forms (0NF - 6NF, BCNF) and
    Boundary-Quotient Normal Form (BQNF) for data in motion under CDC streams.
    """
    def __init__(self, in_memory: bool = True):
        self.conn = sqlite3.connect(":memory:" if in_memory else "normal_forms.db")
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        sql_path = NORMAL_FORMS_DIR / "normal_forms_schema.sql"
        schema_sql = sql_path.read_text(encoding="utf-8")
        self.conn.executescript(schema_sql)
        install_totality_fences(self.conn, schema_sql)
        self.conn.commit()

    # ------------------------------------------------------------------------
    # 0NF -> 1NF: Unnesting non-atomic repeating groups
    # ------------------------------------------------------------------------
    def normalize_0nf_to_1nf(self, raw_records: List[Tuple[int, str, str]]) -> List[Dict[str, Any]]:
        """Parses CSV string list in 0NF into atomic 1NF tuples."""
        c = self.conn.cursor()
        c.execute("DELETE FROM student_records_0nf;")
        c.execute("DELETE FROM student_enrollments_1nf;")

        # Insert 0NF
        for sid, name, csv_courses in raw_records:
            c.execute("INSERT INTO student_records_0nf VALUES (?, ?, ?);", (sid, name, csv_courses))

        # Flatten into 1NF
        c.execute("SELECT student_id, student_name, course_list_csv FROM student_records_0nf;")
        flattened = []
        for row in c.fetchall():
            sid = row["student_id"]
            name = row["student_name"]
            courses = [co.strip() for co in row["course_list_csv"].split(",") if co.strip()]
            for co in courses:
                # Default mock metadata for courses
                c.execute("""
                    INSERT INTO student_enrollments_1nf VALUES (?, ?, ?, ?, ?, ?);
                """, (sid, name, co, f"Title of {co}", 101, "Hall 302"))
                flattened.append({
                    "student_id": sid,
                    "student_name": name,
                    "course_code": co
                })
        self.conn.commit()
        return flattened

    # ------------------------------------------------------------------------
    # 5NF (PJNF): Project-Join Higher-Cell Integrity (Shell_2 vs Fill_2)
    # ------------------------------------------------------------------------
    def evaluate_5nf_project_join_integrity(
        self,
        fill2_tuples: List[Tuple[str, str, str]]
    ) -> Dict[str, Any]:
        """
        Compare one admitted body with the join of its three binary projections.

        Equal cardinality, and an empty spurious-tuple view, means this body
        obeys this ternary join dependency. That is an instance witness.
        Fifth normal form is the schema condition that every join dependency
        implied by the constraints is implied by the candidate keys. This
        method does not decide that condition, so schema_in_5nf is None.
        The key is_5nf_compliant is retained for the instance witness.
        """
        c = self.conn.cursor()
        c.execute("DELETE FROM consulting_fill2;")
        for cons, comp, prod in fill2_tuples:
            c.execute("INSERT INTO consulting_fill2 VALUES (?, ?, ?);", (cons, comp, prod))
        self.conn.commit()

        c.execute("SELECT COUNT(*) AS fill_count FROM consulting_fill2;")
        fill_count = c.fetchone()["fill_count"]

        c.execute("SELECT COUNT(*) AS shell_count FROM consulting_shell2;")
        shell_count = c.fetchone()["shell_count"]

        c.execute("SELECT * FROM consulting_spurious_tuples;")
        spurious = [dict(r) for r in c.fetchall()]

        body_obeys = (len(spurious) == 0 and shell_count == fill_count)
        return {
            "fill2_count": fill_count,
            "shell2_count": shell_count,
            "spurious_tuples_count": len(spurious),
            "spurious_tuples": spurious,
            "instance_obeys_declared_ternary_join": body_obeys,
            "schema_in_5nf": None,
            "is_5nf_compliant": body_obeys,
        }

    # ------------------------------------------------------------------------
    # BQNF: Incremental Cache Maintenance under CDC
    # ------------------------------------------------------------------------
    def _cochain_add(self, region: str, amount: float):
        """Maintains the auxiliary priority queue cochain table on insertion."""
        c = self.conn.cursor()
        c.execute("SELECT frequency FROM region_extremum_cochain WHERE region = ? AND amount = ?;", (region, amount))
        row = c.fetchone()
        if row:
            c.execute(
                "UPDATE region_extremum_cochain SET frequency = frequency + 1 WHERE region = ? AND amount = ?;",
                (region, amount)
            )
        else:
            c.execute(
                "INSERT INTO region_extremum_cochain (region, amount, frequency) VALUES (?, ?, 1);",
                (region, amount)
            )

    def _cochain_remove(self, region: str, amount: float):
        """Maintains the auxiliary priority queue cochain table on deletion."""
        c = self.conn.cursor()
        c.execute("SELECT frequency FROM region_extremum_cochain WHERE region = ? AND amount = ?;", (region, amount))
        row = c.fetchone()
        if row:
            if row["frequency"] <= 1:
                c.execute("DELETE FROM region_extremum_cochain WHERE region = ? AND amount = ?;", (region, amount))
            else:
                c.execute(
                    "UPDATE region_extremum_cochain SET frequency = frequency - 1 WHERE region = ? AND amount = ?;",
                    (region, amount)
                )

    def _quantile_cochain_add(self, region: str, amount: float, bucket_width: float = 10.0):
        """Maintains the auxiliary quantile sketch cochain on insertion."""
        c = self.conn.cursor()
        bucket_id = int(math.floor(amount / bucket_width))
        lower = bucket_id * bucket_width
        upper = (bucket_id + 1) * bucket_width
        c.execute(
            "SELECT count FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
            (region, bucket_id)
        )
        row = c.fetchone()
        if row:
            c.execute(
                "UPDATE region_quantile_cochain SET count = count + 1 WHERE region = ? AND bucket_id = ?;",
                (region, bucket_id)
            )
        else:
            c.execute(
                "INSERT INTO region_quantile_cochain (region, bucket_id, lower_bound, upper_bound, count) VALUES (?, ?, ?, ?, 1);",
                (region, bucket_id, lower, upper)
            )

    def _quantile_cochain_remove(self, region: str, amount: float, bucket_width: float = 10.0):
        """Maintains the auxiliary quantile sketch cochain on deletion."""
        c = self.conn.cursor()
        bucket_id = int(math.floor(amount / bucket_width))
        c.execute(
            "SELECT count FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
            (region, bucket_id)
        )
        row = c.fetchone()
        if row:
            if row["count"] <= 1:
                c.execute(
                    "DELETE FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
                    (region, bucket_id)
                )
            else:
                c.execute(
                    "UPDATE region_quantile_cochain SET count = count - 1 WHERE region = ? AND bucket_id = ?;",
                    (region, bucket_id)
                )

    def estimate_quantile(self, region: str, q: float = 0.5) -> Optional[float]:
        """
        Estimates the q-th quantile (default 0.5 for median) from the auxiliary
        piecewise-linear quantile sketch cochain.
        """
        c = self.conn.cursor()
        c.execute("""
            SELECT bucket_id, lower_bound, upper_bound, count
            FROM region_quantile_cochain
            WHERE region = ? AND count > 0
            ORDER BY bucket_id ASC;
        """, (region,))
        buckets = c.fetchall()
        if not buckets:
            return None
        total_count = sum(b["count"] for b in buckets)
        if total_count == 0:
            return None
        target_rank = q * total_count
        cum = 0
        for b in buckets:
            cnt = b["count"]
            if cum + cnt >= target_rank:
                frac = (target_rank - cum) / cnt if cnt > 0 else 0.0
                return b["lower_bound"] + frac * (b["upper_bound"] - b["lower_bound"])
            cum += cnt
        return buckets[-1]["upper_bound"]

    def compute_true_median(self, region: str) -> Optional[float]:
        """Computes true median directly from base_sales."""
        c = self.conn.cursor()
        c.execute("SELECT amount FROM base_sales WHERE region = ? ORDER BY amount ASC;", (region,))
        rows = c.fetchall()
        if not rows:
            return None
        n = len(rows)
        if n % 2 == 1:
            return float(rows[n // 2]["amount"])
        else:
            return float(rows[n // 2 - 1]["amount"] + rows[n // 2]["amount"]) / 2.0

    def apply_sales_cdc(
        self,
        op_type: str,
        sale_id: int,
        old_region: Optional[str] = None,
        new_region: Optional[str] = None,
        old_amount: Optional[float] = None,
        new_amount: Optional[float] = None,
        maintain_cochain: bool = True
    ):
        """
        Records a Change Data Capture (CDC) event, applies it to base_sales,
        and optionally updates the auxiliary priority queue and quantile sketch cochains.
        """
        c = self.conn.cursor()

        # If old attributes are omitted for UPDATE or DELETE, look them up from base_sales first
        if op_type in ("UPDATE", "DELETE") and (old_region is None or old_amount is None):
            c.execute("SELECT region, amount FROM base_sales WHERE sale_id = ?;", (sale_id,))
            row = c.fetchone()
            if row:
                if old_region is None:
                    old_region = row["region"]
                if old_amount is None:
                    old_amount = row["amount"]

        if op_type == "INSERT":
            c.execute("INSERT INTO base_sales VALUES (?, ?, ?);", (sale_id, new_region, new_amount))
            if maintain_cochain and new_region is not None and new_amount is not None:
                self._cochain_add(new_region, new_amount)
                self._quantile_cochain_add(new_region, new_amount)
        elif op_type == "DELETE":
            c.execute("DELETE FROM base_sales WHERE sale_id = ?;", (sale_id,))
            if maintain_cochain and old_region is not None and old_amount is not None:
                self._cochain_remove(old_region, old_amount)
                self._quantile_cochain_remove(old_region, old_amount)
        elif op_type == "UPDATE":
            c.execute("UPDATE base_sales SET region = ?, amount = ? WHERE sale_id = ?;", (new_region, new_amount, sale_id))
            if maintain_cochain:
                if old_region is not None and old_amount is not None:
                    self._cochain_remove(old_region, old_amount)
                    self._quantile_cochain_remove(old_region, old_amount)
                if new_region is not None and new_amount is not None:
                    self._cochain_add(new_region, new_amount)
                    self._quantile_cochain_add(new_region, new_amount)

        c.execute("""
            INSERT INTO sales_cdc_log (op_type, sale_id, old_region, new_region, old_amount, new_amount, processed)
            VALUES (?, ?, ?, ?, ?, ?, 0);
        """, (op_type, sale_id, old_region, new_region, old_amount, new_amount))
        self.conn.commit()

    def process_bqnf_incremental_repair(
        self,
        use_cochain: bool = True,
        track_quantiles: bool = False,
        quantile_tolerance: float = 15.0
    ) -> Dict[str, Any]:
        """
        Executes BQNF incremental repair:
        1. Additive group aggregates (SUM, COUNT): computed via exact coboundary potential
           omega = d^0 alpha = (delta_amount, delta_count) in O(1).
        2. Non-invertible extrema aggregates (MIN, MAX):
           - Non-destructive deletion (x > min and x < max): preserved in O(1) exact repair.
           - Destructive deletion (x = min or x = max):
             * If use_cochain=True and cochain available: popped from region_extremum_cochain
               in O(log K) without scanning base_sales (Route: Repair).
             * If use_cochain=False or cochain exhausted: defect is non-exact ([omega] != 0),
               forcing bounded fallback recomputation on base_sales (Route: Recompute).
        3. Higher-order quantile aggregates (MEDIAN):
           - If use_cochain=True and sketch estimate error <= quantile_tolerance:
             defect cochain lies within tolerance ball [omega] in B_eps(0) (Route: Repair).
           - If sketch absent, exhausted, or error > quantile_tolerance:
             tolerance breached, forcing bounded fallback recomputation on base_sales (Route: Recompute).
        4. Updates region_sales_cache incrementally and audits full consistency.
        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM sales_cdc_log WHERE processed = 0 ORDER BY cdc_id ASC;")
        unprocessed = c.fetchall()

        if not unprocessed:
            # Audit idle cache against ground truth recomputation from base_sales
            c.execute("""
                SELECT region,
                       COALESCE(SUM(amount), 0.0) AS total_sales,
                       COUNT(amount) AS sale_count,
                       MIN(amount) AS min_amount,
                       MAX(amount) AS max_amount
                FROM base_sales
                GROUP BY region;
            """)
            base_rows = c.fetchall()
            base_totals = {r["region"]: (float(r["total_sales"]), int(r["sale_count"])) for r in base_rows}
            base_extrema = {r["region"]: (
                float(r["min_amount"]) if r["min_amount"] is not None else None,
                float(r["max_amount"]) if r["max_amount"] is not None else None
            ) for r in base_rows}

            c.execute("SELECT region, total_sales, sale_count, min_amount, max_amount, median_amount FROM region_sales_cache;")
            cached_rows = c.fetchall()
            cached = {r["region"]: (float(r["total_sales"]), int(r["sale_count"])) for r in cached_rows}
            cached_extrema = {r["region"]: (
                float(r["min_amount"]) if r["min_amount"] is not None else None,
                float(r["max_amount"]) if r["max_amount"] is not None else None
            ) for r in cached_rows}
            cached_medians = {r["region"]: (float(r["median_amount"]) if r["median_amount"] is not None else None) for r in cached_rows}

            # Independent audit verification: cache matches base_sales
            all_regions = set(cached.keys()) | set(base_totals.keys())
            is_consistent = (cached == base_totals) and all(
                cached_extrema.get(reg) == base_extrema.get(reg) for reg in all_regions
            )
            terminal = "Preserve" if is_consistent else "Recompute"

            return {
                "terminal": terminal,
                "events_processed": 0,
                "verified_consistent": is_consistent,
                "cached_state": cached,
                "cached_extrema": cached_extrema,
                "cached_medians": cached_medians,
                "extrema_repairs": 0,
                "fallback_recomputations": 0 if is_consistent else 1,
                "quantile_repairs": 0,
                "quantile_fallback_recomputations": 0
            }

        # Load active cache state
        c.execute("SELECT region, total_sales, sale_count, min_amount, max_amount, median_amount FROM region_sales_cache;")
        current_cache = {
            r["region"]: {
                "total_sales": float(r["total_sales"]),
                "sale_count": int(r["sale_count"]),
                "min_amount": float(r["min_amount"]) if r["min_amount"] is not None else None,
                "max_amount": float(r["max_amount"]) if r["max_amount"] is not None else None,
                "median_amount": float(r["median_amount"]) if r["median_amount"] is not None else None,
            }
            for r in c.fetchall()
        }

        # Calculate exact incremental additive deltas per region
        region_deltas: Dict[str, Dict[str, float]] = {}
        extrema_repairs = 0
        fallback_recomputations = 0
        quantile_repairs = 0
        quantile_fallback_recomputations = 0
        batch_terminal = "Repair"

        SUPPORTED_OPS = {"INSERT", "UPDATE", "DELETE"}

        for row in unprocessed:
            op = row["op_type"]
            old_reg = row["old_region"]
            new_reg = row["new_region"]
            old_amt = row["old_amount"]
            new_amt = row["new_amount"]

            # Fail closed on unsupported CDC operator
            if op not in SUPPORTED_OPS:
                return {
                    "terminal": "Unsupported",
                    "events_processed": 0,
                    "verified_consistent": False,
                    "error": f"Unsupported CDC operator '{op}' cannot be incrementally maintained without recomputation",
                    "cached_state": {k: (v["total_sales"], v["sale_count"]) for k, v in current_cache.items()},
                    "cached_extrema": {k: (v["min_amount"], v["max_amount"]) for k, v in current_cache.items()},
                    "cached_medians": {k: v["median_amount"] for k, v in current_cache.items()},
                    "extrema_repairs": 0,
                    "fallback_recomputations": 1,
                    "quantile_repairs": 0,
                    "quantile_fallback_recomputations": 0,
                }

            # Additive totals maintenance and before/after image validation
            if op == "INSERT":
                if new_reg is None or new_amt is None:
                    raise ValueError(f"INSERT event missing required new image: region={new_reg}, amount={new_amt}")
                if new_reg not in region_deltas:
                    region_deltas[new_reg] = {"amount": 0.0, "count": 0}
                region_deltas[new_reg]["amount"] += float(new_amt)
                region_deltas[new_reg]["count"] += 1

            elif op == "DELETE":
                if old_reg is None or old_amt is None:
                    raise ValueError(f"DELETE event missing required old image: region={old_reg}, amount={old_amt}")
                if old_reg not in region_deltas:
                    region_deltas[old_reg] = {"amount": 0.0, "count": 0}
                region_deltas[old_reg]["amount"] -= float(old_amt)
                region_deltas[old_reg]["count"] -= 1

            elif op == "UPDATE":
                if old_reg is None or new_reg is None or old_amt is None or new_amt is None:
                    raise ValueError(f"UPDATE event missing required images: old=({old_reg}, {old_amt}), new=({new_reg}, {new_amt})")
                if old_reg == new_reg:
                    if new_reg not in region_deltas:
                        region_deltas[new_reg] = {"amount": 0.0, "count": 0}
                    region_deltas[new_reg]["amount"] += (float(new_amt) - float(old_amt))
                else:
                    # Movement across regions/customers: debit old, credit new
                    if old_reg not in region_deltas:
                        region_deltas[old_reg] = {"amount": 0.0, "count": 0}
                    region_deltas[old_reg]["amount"] -= float(old_amt)
                    region_deltas[old_reg]["count"] -= 1

                    if new_reg not in region_deltas:
                        region_deltas[new_reg] = {"amount": 0.0, "count": 0}
                    region_deltas[new_reg]["amount"] += float(new_amt)
                    region_deltas[new_reg]["count"] += 1

            # Extrema and non-invertible aggregate routing
            def handle_removal(reg: str, amt: float):
                nonlocal extrema_repairs, fallback_recomputations, batch_terminal
                if reg not in current_cache:
                    return
                state = current_cache[reg]
                old_min = state["min_amount"]
                old_max = state["max_amount"]
                state["total_sales"] -= amt
                state["sale_count"] -= 1
                new_cnt = state["sale_count"]

                if new_cnt <= 0:
                    del current_cache[reg]
                    c.execute("""
                        INSERT INTO extrema_repair_log (
                            region, op_type, affected_amount, is_destructive, cochain_available,
                            terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
                        ) VALUES (?, 'DELETE', ?, 1, ?, 'Repair', ?, NULL, ?, NULL, 0);
                    """, (reg, amt, 1 if use_cochain else 0, old_min, old_max))
                    return

                is_destructive = int((old_min is not None and amt == old_min) or (old_max is not None and amt == old_max))
                if not is_destructive:
                    # Non-destructive deletion: exact repair preserves extremum
                    extrema_repairs += 1
                    c.execute("""
                        INSERT INTO extrema_repair_log (
                            region, op_type, affected_amount, is_destructive, cochain_available,
                            terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
                        ) VALUES (?, 'DELETE', ?, 0, ?, 'Repair', ?, ?, ?, ?, 0);
                    """, (reg, amt, 1 if use_cochain else 0, old_min, old_min, old_max, old_max))
                else:
                    # Destructive deletion!
                    cochain_success = False
                    if use_cochain:
                        c.execute("SELECT amount FROM region_extremum_cochain WHERE region = ? ORDER BY amount ASC LIMIT 1;", (reg,))
                        r_min = c.fetchone()
                        c.execute("SELECT amount FROM region_extremum_cochain WHERE region = ? ORDER BY amount DESC LIMIT 1;", (reg,))
                        r_max = c.fetchone()
                        if r_min is not None and r_max is not None:
                            new_min = float(r_min[0])
                            new_max = float(r_max[0])
                            state["min_amount"] = new_min
                            state["max_amount"] = new_max
                            extrema_repairs += 1
                            cochain_success = True
                            c.execute("""
                                INSERT INTO extrema_repair_log (
                                    region, op_type, affected_amount, is_destructive, cochain_available,
                                    terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
                                ) VALUES (?, 'DELETE', ?, 1, 1, 'Repair', ?, ?, ?, ?, 0);
                            """, (reg, amt, old_min, new_min, old_max, new_max))

                    if not cochain_success:
                        # Non-exact defect: fallback bounded recomputation from base_sales
                        c.execute("SELECT MIN(amount) AS fb_min, MAX(amount) AS fb_max FROM base_sales WHERE region = ?;", (reg,))
                        fb = c.fetchone()
                        new_min = float(fb["fb_min"]) if fb["fb_min"] is not None else None
                        new_max = float(fb["fb_max"]) if fb["fb_max"] is not None else None
                        state["min_amount"] = new_min
                        state["max_amount"] = new_max
                        fallback_recomputations += 1
                        batch_terminal = "Recompute"
                        c.execute("""
                            INSERT INTO extrema_repair_log (
                                region, op_type, affected_amount, is_destructive, cochain_available,
                                terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
                            ) VALUES (?, 'DELETE', ?, 1, 0, 'Recompute', ?, ?, ?, ?, 1);
                        """, (reg, amt, old_min, new_min, old_max, new_max))

            def handle_addition(reg: str, amt: float, op_label: str):
                nonlocal extrema_repairs
                if reg not in current_cache:
                    current_cache[reg] = {
                        "total_sales": amt,
                        "sale_count": 1,
                        "min_amount": amt,
                        "max_amount": amt,
                        "median_amount": amt
                    }
                    c.execute("""
                        INSERT INTO extrema_repair_log (
                            region, op_type, affected_amount, is_destructive, cochain_available,
                            terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
                        ) VALUES (?, ?, ?, 0, ?, 'Repair', NULL, ?, NULL, ?, 0);
                    """, (reg, op_label, amt, 1 if use_cochain else 0, amt, amt))
                else:
                    state = current_cache[reg]
                    old_min = state["min_amount"]
                    old_max = state["max_amount"]
                    state["total_sales"] += amt
                    state["sale_count"] += 1
                    new_min = min(old_min, amt) if old_min is not None else amt
                    new_max = max(old_max, amt) if old_max is not None else amt
                    state["min_amount"] = new_min
                    state["max_amount"] = new_max
                    extrema_repairs += 1
                    c.execute("""
                        INSERT INTO extrema_repair_log (
                            region, op_type, affected_amount, is_destructive, cochain_available,
                            terminal_route, old_min, new_min, old_max, new_max, recomputation_fallback_executed
                        ) VALUES (?, ?, ?, 0, ?, 'Repair', ?, ?, ?, ?, 0);
                    """, (reg, op_label, amt, 1 if use_cochain else 0, old_min, new_min, old_max, new_max))

            if op == "INSERT":
                if new_reg and new_amt is not None:
                    handle_addition(new_reg, new_amt, "INSERT")
            elif op == "DELETE":
                if old_reg and old_amt is not None:
                    handle_removal(old_reg, old_amt)
            elif op == "UPDATE":
                if old_reg and old_amt is not None:
                    handle_removal(old_reg, old_amt)
                if new_reg and new_amt is not None:
                    handle_addition(new_reg, new_amt, "UPDATE")

        # Process quantile sketch cochains for median estimation per active region
        for reg, st in list(current_cache.items()):
            true_med = self.compute_true_median(reg)
            est_med = self.estimate_quantile(reg, q=0.5) if use_cochain else None

            if est_med is not None and true_med is not None:
                err = abs(est_med - true_med)
                within_tol = (err <= quantile_tolerance)
                if within_tol:
                    st["median_amount"] = est_med
                    quantile_repairs += 1
                    c.execute("""
                        INSERT INTO quantile_repair_log (
                            region, op_type, affected_amount, estimated_median, true_median,
                            error_delta, tolerance, within_tolerance, terminal_route, recomputation_fallback_executed
                        ) VALUES (?, 'BATCH', NULL, ?, ?, ?, ?, 1, 'Repair', 0);
                    """, (reg, est_med, true_med, err, quantile_tolerance))
                else:
                    # Tolerance breached: bounded fallback recomputation
                    st["median_amount"] = true_med
                    quantile_fallback_recomputations += 1
                    if track_quantiles:
                        batch_terminal = "Recompute"
                    c.execute("""
                        INSERT INTO quantile_repair_log (
                            region, op_type, affected_amount, estimated_median, true_median,
                            error_delta, tolerance, within_tolerance, terminal_route, recomputation_fallback_executed
                        ) VALUES (?, 'BATCH', NULL, ?, ?, ?, ?, 0, 'Recompute', 1);
                    """, (reg, est_med, true_med, err, quantile_tolerance))
            else:
                st["median_amount"] = true_med
                if true_med is not None:
                    quantile_fallback_recomputations += 1
                    if track_quantiles:
                        batch_terminal = "Recompute"
                    c.execute("""
                        INSERT INTO quantile_repair_log (
                            region, op_type, affected_amount, estimated_median, true_median,
                            error_delta, tolerance, within_tolerance, terminal_route, recomputation_fallback_executed
                        ) VALUES (?, 'BATCH', NULL, NULL, ?, NULL, ?, 0, 'Recompute', 1);
                    """, (reg, true_med, quantile_tolerance))

        # Persist updated cache state
        if current_cache:
            placeholders = ",".join("?" for _ in current_cache)
            c.execute(f"DELETE FROM region_sales_cache WHERE region NOT IN ({placeholders});", tuple(current_cache.keys()))
        else:
            c.execute("DELETE FROM region_sales_cache;")

        for reg, st in current_cache.items():
            c.execute("""
                INSERT INTO region_sales_cache (region, total_sales, sale_count, min_amount, max_amount, median_amount)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(region) DO UPDATE SET
                    total_sales = excluded.total_sales,
                    sale_count = excluded.sale_count,
                    min_amount = excluded.min_amount,
                    max_amount = excluded.max_amount,
                    median_amount = excluded.median_amount;
            """, (reg, st["total_sales"], st["sale_count"], st["min_amount"], st["max_amount"], st["median_amount"]))

        # Mark CDC as processed
        c.execute("UPDATE sales_cdc_log SET processed = 1 WHERE processed = 0;")
        self.conn.commit()

        # Audit verification: Compare incremental cache with full recomputed view from base_sales
        c.execute("""
            SELECT region, SUM(amount) AS true_sales, COUNT(*) AS true_count,
                   MIN(amount) AS true_min, MAX(amount) AS true_max
            FROM base_sales
            GROUP BY region;
        """)
        recomputed = {
            r["region"]: (r["true_sales"], r["true_count"], r["true_min"], r["true_max"])
            for r in c.fetchall()
        }

        c.execute("SELECT region, total_sales, sale_count, min_amount, max_amount, median_amount FROM region_sales_cache;")
        cached_full_rows = c.fetchall()
        cached_full = {
            r["region"]: (r["total_sales"], r["sale_count"], r["min_amount"], r["max_amount"])
            for r in cached_full_rows
        }

        consistent = (recomputed == cached_full)
        cached = {r["region"]: (r["total_sales"], r["sale_count"]) for r in cached_full_rows}
        cached_extrema = {r["region"]: (r["min_amount"], r["max_amount"]) for r in cached_full_rows}
        cached_medians = {r["region"]: r["median_amount"] for r in cached_full_rows}

        return {
            "terminal": batch_terminal,
            "events_processed": len(unprocessed),
            "deltas_applied": region_deltas,
            "verified_consistent": consistent,
            "cached_state": cached,
            "cached_extrema": cached_extrema,
            "cached_medians": cached_medians,
            "extrema_repairs": extrema_repairs,
            "fallback_recomputations": fallback_recomputations,
            "quantile_repairs": quantile_repairs,
            "quantile_fallback_recomputations": quantile_fallback_recomputations
        }

    def close(self):
        self.conn.close()

    # Canonical alias for BQNF incremental CDC cache maintenance
    incremental_cdc_cache_maintenance = process_bqnf_incremental_repair

    # ------------------------------------------------------------------------
    # S(n) State Transition Normal Forms Runtime Evaluation
    # ------------------------------------------------------------------------
    @staticmethod
    def _resolve_contract(contract_id: str, contract_path: Optional[Path] = None) -> Dict[str, Any]:
        """Resolves contract YAML file and loads its declaration dictionary."""
        import yaml
        if contract_path and Path(contract_path).is_file():
            target_path = Path(contract_path)
        else:
            target_path = NORMAL_FORMS_DIR / f"{contract_id}.yaml"
            if not target_path.is_file():
                raise FileNotFoundError(f"Cannot resolve contract YAML for {contract_id}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Contract {target_path} does not parse to a dictionary")
        return data

    def evaluate_sn_transition(
        self,
        contract_id: str,
        fixture: Dict[str, Any],
        contract_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Executes runtime evaluation against an S(n) state transition fixture,
        yielding the exact typed terminal route and mapping to the declared
        canonical terminal in the contract's terminal_route_map.
        """
        contract = self._resolve_contract(contract_id, contract_path)
        terminal_routes = contract.get("terminal_routes", [])
        terminal_route_map = contract.get("terminal_route_map", {})

        cid = contract.get("identity", {}).get("id", contract_id)

        if cid in ("nf.derivation.pdnf", "pdnf"):
            res = self.evaluate_sn_pdnf(fixture, terminal_route_map)
        elif cid in ("nf.derivation.rpnf", "rpnf"):
            res = self.evaluate_sn_rpnf(fixture, terminal_route_map)
        elif cid in ("nf.derivation.scnf", "scnf"):
            res = self.evaluate_sn_scnf(fixture, terminal_route_map)
        elif cid in ("nf.epistemic.state", "state"):
            res = self.evaluate_sn_state(fixture, terminal_route_map)
        elif cid in ("nf.epistemic.pvnf", "pvnf"):
            res = self.evaluate_sn_pvnf(fixture, terminal_route_map)
        else:
            raise ValueError(f"Unsupported S(n) normal form contract: {cid}")

        local_route = res["local_terminal"]
        if local_route not in terminal_routes:
            raise ValueError(
                f"Evaluator returned route '{local_route}' not declared in terminal_routes: {terminal_routes}"
            )
        if local_route not in terminal_route_map:
            raise ValueError(
                f"Local route '{local_route}' not mapped in terminal_route_map: {terminal_route_map}"
            )

        canonical_route = terminal_route_map[local_route]
        res["contract_id"] = cid
        res["canonical_terminal"] = canonical_route
        res["terminal_route_map"] = terminal_route_map
        res["admitted"] = (canonical_route == "Preserve")
        return res

    def evaluate_sn_pdnf(
        self,
        fixture: Dict[str, Any],
        route_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates Primitive Difference Normal Form (PDNF).
        Invariants:
        - Carrier >= 2 declared (RequireCarrierDeclaration).
        - Irreflexivity law declared (RequireIrreflexivityDeclaration).
        - No term different from itself (RejectSelfDifference).
        - Every asserted difference must have positive witness count (RejectUnwitnessedAssertion).
        - Scope must be declared (Undetermined if undeclared).
        """
        carrier = fixture.get("carrier")
        if carrier is None or len(carrier) < 2:
            return {
                "local_terminal": "RequireCarrierDeclaration",
                "reason": "Carrier must be declared with at least two distinct elements.",
            }

        if not fixture.get("irreflexivity_declared", False):
            return {
                "local_terminal": "RequireIrreflexivityDeclaration",
                "reason": "Irreflexivity law must be declared before asserting differences.",
            }

        asserted = fixture.get("asserted_relation", [])
        witness_map = fixture.get("witness_map", {})

        for pair in asserted:
            x, y = pair[0], pair[1]
            if x == y:
                return {
                    "local_terminal": "RejectSelfDifference",
                    "reason": f"Term '{x}' asserted different from itself; violates irreflexivity.",
                    "offending_pair": (x, y),
                }

        for pair in asserted:
            x, y = pair[0], pair[1]
            count = None
            for key in ((x, y), (y, x), f"{x},{y}", f"{y},{x}", f"({x}, {y})", f"({y}, {x})"):
                if key in witness_map:
                    count = witness_map[key]
                    break
            if count is None or count <= 0:
                return {
                    "local_terminal": "RejectUnwitnessedAssertion",
                    "reason": f"Asserted difference ({x}, {y}) has no positive witness count.",
                    "offending_pair": (x, y),
                }

        if not fixture.get("scope_declared", True):
            return {
                "local_terminal": "Undetermined",
                "reason": "Scope of search undeclared; minimality cannot be determined.",
            }

        return {
            "local_terminal": "AcceptWitnessedIrreflexive",
            "reason": "Asserted differences are witnessed and irreflexive on declared carrier.",
            "carrier_size": len(carrier),
            "asserted_pairs_count": len(asserted),
        }

    def evaluate_sn_rpnf(
        self,
        fixture: Dict[str, Any],
        route_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates Regime Passage / Retraction Path Normal Form (RPNF).
        Invariants:
        - History must be declared (RequireHistoryDeclaration).
        - Empty history on non-quiescent genesis triggers Recompute.
        - Presentation without admission event cannot alter regime (RejectPresentationAsChange).
        - Regime without certified fold triggers RejectUncertifiedRegime.
        - Deterministic certified replay triggers AcceptCertifiedRegime.
        """
        if not fixture.get("history_declared", True) or fixture.get("history") is None:
            return {
                "local_terminal": "RequireHistoryDeclaration",
                "reason": "History declaration missing or external state dependence detected.",
            }

        history = fixture.get("history", [])
        genesis_quiescent = fixture.get("genesis_quiescent", True)

        if len(history) == 0 and not genesis_quiescent:
            return {
                "local_terminal": "Recompute",
                "reason": "Non-quiescent genesis produced nonempty regime without history; must recompute.",
            }

        if fixture.get("presentation_only", False) or fixture.get("presentation_without_admission", False):
            return {
                "local_terminal": "RejectPresentationAsChange",
                "reason": "Datum presented without an admission event cannot alter state.",
            }

        target_regime = fixture.get("target_regime")
        recomputed_regime = fixture.get("recomputed_regime", target_regime)
        certified_fold = fixture.get("certified_fold", True)

        if not certified_fold or target_regime != recomputed_regime:
            return {
                "local_terminal": "RejectUncertifiedRegime",
                "reason": "Regime assertion uncertified by historical fold.",
                "target_regime": target_regime,
                "recomputed_regime": recomputed_regime,
            }

        return {
            "local_terminal": "AcceptCertifiedRegime",
            "reason": "Regime certified by deterministic fold along admitted history.",
            "history_length": len(history),
            "certified_regime": target_regime,
        }

    def evaluate_sn_scnf(
        self,
        fixture: Dict[str, Any],
        route_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates Separation / Strict Contraction Normal Form (SCNF).
        Invariants:
        - Measure must be declared (RejectUnmeasuredMinimum).
        - Isomorphism relation / grammar restatement must be unambiguous (RequireMeasureDeclaration).
        - Obstruction or non-contractive ratio k >= 1 triggers Escalate.
        - Equal minimal cost candidates resolved without arbitrary tie-break (RecordTie).
        - Unique minimizer certified (AcceptUniqueMinimizer).
        """
        if not fixture.get("measure_declared", True) or not fixture.get("measure_name"):
            return {
                "local_terminal": "RejectUnmeasuredMinimum",
                "reason": "Cheapest separation asserted without declaring order or cost measure.",
            }

        if fixture.get("isomorphism_undeclared", False) or fixture.get("grammar_restatement_ambiguous", False):
            return {
                "local_terminal": "RequireMeasureDeclaration",
                "reason": "Measure declaration ambiguous under grammar restatement; isomorphism undeclared.",
            }

        k = fixture.get("contraction_ratio")
        if fixture.get("obstruction_present", False) or (k is not None and float(k) >= 1.0):
            return {
                "local_terminal": "Escalate",
                "reason": f"Contraction ratio k={k} >= 1 or structural obstruction detected; escalated.",
            }

        if fixture.get("tie_resolved_arbitrarily", False) or fixture.get("tied_candidates_count", 0) > 1:
            return {
                "local_terminal": "RecordTie",
                "reason": "Multiple minimizers achieve equal minimal cost; tie recorded.",
            }

        return {
            "local_terminal": "AcceptUniqueMinimizer",
            "reason": "Unique minimizer certified under declared measure.",
            "measure": fixture.get("measure_name"),
        }

    def evaluate_sn_state(
        self,
        fixture: Dict[str, Any],
        route_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates Epistemic State Invariant Normal Form (StateNF).
        Invariants:
        - Malformed state claim -> Refuse.
        - Authority unknown/missing -> AuthorityUnknown.
        - Version without causal context -> CausalGap.
        - Stale state freshness -> Stale.
        - Low confidence -> ConfidenceBelowThreshold.
        - Complete, fresh, authoritative state -> Accept.
        """
        if fixture.get("malformed", False) or "value" not in fixture:
            return {
                "local_terminal": "Refuse",
                "reason": "Malformed epistemic state claim; missing value.",
            }

        authority = fixture.get("authority_source")
        if not authority or authority == "unknown":
            return {
                "local_terminal": "AuthorityUnknown",
                "reason": "State claim lacks explicit authority source.",
            }

        if fixture.get("version") is not None and (fixture.get("causal_context") is None or fixture.get("has_causal_gap", False)):
            return {
                "local_terminal": "CausalGap",
                "reason": "Version served without causal context; scalar state flattening detected.",
            }

        freshness = fixture.get("freshness")
        is_stale = fixture.get("is_stale", False)
        if is_stale or (isinstance(freshness, dict) and freshness.get("is_stale", False)):
            return {
                "local_terminal": "Stale",
                "reason": "State claim freshness expired; labeled as stale.",
            }

        conf = fixture.get("confidence")
        threshold = fixture.get("confidence_threshold", 0.8)
        if conf is not None and conf < threshold:
            return {
                "local_terminal": "ConfidenceBelowThreshold",
                "reason": f"State confidence {conf} below threshold {threshold}.",
            }

        return {
            "local_terminal": "Accept",
            "reason": "Epistemic state carries complete value, version, causal context, freshness, and authority.",
            "authority_source": authority,
        }

    def evaluate_sn_pvnf(
        self,
        fixture: Dict[str, Any],
        route_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates Provenance Verification Normal Form (PvNF).
        Invariants:
        - Untyped / uncertified -> Refuse.
        - Missing source facts -> AuthorityHallucinationViolation.
        - Broken parent lineage -> LineageLost.
        - Non-replayable steps present -> NonReplayableFlagged.
        - Complete traced provenance -> ProvenanceTraced.
        """
        if fixture.get("refusal_requested", False) or "model_version" not in fixture:
            return {
                "local_terminal": "Refuse",
                "reason": "Untyped or uncertified provenance data product.",
            }

        source_facts = fixture.get("source_facts")
        if not source_facts or len(source_facts) == 0:
            return {
                "local_terminal": "AuthorityHallucinationViolation",
                "reason": "Generated answer carries no traceable source facts; authority hallucination.",
            }

        if fixture.get("has_lineage_break", False) or fixture.get("lineage_parent_ids") is None:
            return {
                "local_terminal": "LineageLost",
                "reason": "Lineage chain broken or parent references missing.",
            }

        non_rep = fixture.get("non_replayable_steps")
        if non_rep and len(non_rep) > 0:
            return {
                "local_terminal": "NonReplayableFlagged",
                "reason": f"Non-replayable steps present ({len(non_rep)} steps); flagged for escalation.",
                "non_replayable_count": len(non_rep),
            }

        return {
            "local_terminal": "ProvenanceTraced",
            "reason": "Complete provenance chain traced to source facts with deterministic replayability.",
            "facts_count": len(source_facts),
        }


def evaluate_sn_state_transition(
    contract_id: str,
    fixture: Dict[str, Any],
    contract_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Module-level convenience evaluator executing S(n) normal forms evaluation."""
    evaluator = NormalFormsEvaluator(in_memory=True)
    try:
        return evaluator.evaluate_sn_transition(contract_id, fixture, contract_path)
    finally:
        evaluator.close()
