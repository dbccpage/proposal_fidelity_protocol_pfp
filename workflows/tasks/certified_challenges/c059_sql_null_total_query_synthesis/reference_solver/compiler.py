"""SQL compiler from JSON relational-algebra trees with Kleene 3VL and null-totality discipline."""

from typing import Any, Dict, List, Optional, Tuple


class SQLCompiler:
    """Compiles JSON relational algebra AST to dialect-neutral SQL."""

    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.subquery_count = 0
        self.null_ledger: List[Dict[str, str]] = []

    def _next_alias(self) -> str:
        self.subquery_count += 1
        return f"sq_{self.subquery_count}"

    def compile(
        self, spec: Dict[str, Any], protected: Optional[List[str]] = None
    ) -> Tuple[str, str, List[Dict[str, str]]]:
        self.null_ledger = []
        sql = self._compile_node(spec)

        # Preflight SQL for protected columns
        preflight_sql = self._compile_preflight(spec, protected or [])
        return sql, preflight_sql, self.null_ledger

    def _compile_preflight(self, spec: Dict[str, Any], protected: List[str]) -> str:
        if not protected:
            return "SELECT 1 WHERE 1 = 0"

        target_table = None
        applicable_cols = []
        # A nested AST node is not a hashable table name. Inspect actual source
        # tables first, not unrelated tables that merely appear earlier in schema.
        tables_to_check = self._extract_tables(spec) or list(self.schema.keys())
        for tbl in tables_to_check:
            tbl_cols = set(self.schema.get(tbl, {}).keys())
            applicable = [c for c in protected if c in tbl_cols]
            if applicable:
                target_table = tbl
                applicable_cols = applicable
                break

        if not target_table or not applicable_cols:
            return "SELECT 1 WHERE 1 = 0"

        conditions = [f"{col} IS NULL" for col in applicable_cols]
        return f"SELECT * FROM {target_table} WHERE {' OR '.join(conditions)}"

    def _extract_tables(self, node: Any) -> List[str]:
        if isinstance(node, str):
            return [node]
        if not isinstance(node, dict):
            return []
        res = []
        if "from" in node:
            res.extend(self._extract_tables(node["from"]))
        if "left" in node:
            res.extend(self._extract_tables(node["left"]))
        if "right" in node:
            res.extend(self._extract_tables(node["right"]))
        return res

    def _compile_arg(self, arg: Any) -> str:
        if isinstance(arg, dict):
            if "col" in arg:
                return str(arg["col"])
            elif "val" in arg:
                v = arg["val"]
                if v is None:
                    return "NULL"
                if isinstance(v, str):
                    escaped = v.replace("'", "''")
                    return f"'{escaped}'"
                return str(v)
        if isinstance(arg, str):
            return arg
        return str(arg)

    def _compile_predicate(self, pred: Dict[str, Any], path: str = "where") -> str:
        parts = []
        for k, v in pred.items():
            if k == "eq3":
                a1 = self._compile_arg(v[0])
                a2 = self._compile_arg(v[1])
                parts.append(f"({a1} = {a2})")
            elif k == "distinct":
                a1 = self._compile_arg(v[0])
                a2 = self._compile_arg(v[1])
                self.null_ledger.append(
                    {"node": f"{path}.distinct", "construct": "IS DISTINCT FROM"}
                )
                parts.append(f"({a1} IS DISTINCT FROM {a2})")
            elif k == "not_distinct":
                a1 = self._compile_arg(v[0])
                a2 = self._compile_arg(v[1])
                self.null_ledger.append(
                    {"node": f"{path}.not_distinct", "construct": "IS NOT DISTINCT FROM"}
                )
                parts.append(f"({a1} IS NOT DISTINCT FROM {a2})")
            elif k == "is_null":
                a = self._compile_arg(v)
                self.null_ledger.append({"node": f"{path}.is_null", "construct": "IS NULL"})
                parts.append(f"({a} IS NULL)")
            elif k == "is_not_null":
                a = self._compile_arg(v)
                self.null_ledger.append({"node": f"{path}.is_not_null", "construct": "IS NOT NULL"})
                parts.append(f"({a} IS NOT NULL)")
            elif k == "and":
                sub_parts = [self._compile_predicate(p, f"{path}.and") for p in v]
                parts.append(f"({' AND '.join(sub_parts)})")
            elif k == "or":
                sub_parts = [self._compile_predicate(p, f"{path}.or") for p in v]
                parts.append(f"({' OR '.join(sub_parts)})")
            elif k == "not":
                sub = self._compile_predicate(v, f"{path}.not")
                parts.append(f"(NOT {sub})")
            elif k == "coalesce":
                args = [self._compile_arg(a) for a in v]
                self.null_ledger.append({"node": f"{path}.coalesce", "construct": "COALESCE"})
                parts.append(f"COALESCE({', '.join(args)})")
        return " AND ".join(parts)

    def _compile_node(self, node: Any) -> str:
        if isinstance(node, str):
            return f"SELECT * FROM {node}"

        op = node.get("op")

        if op == "select":
            from_node = node["from"]
            from_sql, from_alias = self._get_from_clause(from_node)
            where_pred = node.get("where")
            proj_cols = node.get("project")

            select_str = ", ".join(proj_cols) if proj_cols else "*"
            where_str = (
                f" WHERE {self._compile_predicate(where_pred, 'where')}" if where_pred else ""
            )
            return f"SELECT {select_str} FROM {from_sql}{where_str}"

        elif op == "project":
            from_sql, _ = self._get_from_clause(node["from"])
            cols = ", ".join(node["columns"])
            return f"SELECT {cols} FROM {from_sql}"

        elif op == "rename":
            from_sql, _ = self._get_from_clause(node["from"])
            mapping = node["map"]
            # To preserve other columns, fetch available columns if base table
            base_tbl = node["from"] if isinstance(node["from"], str) else None
            all_cols = (
                list(self.schema[base_tbl].keys())
                if base_tbl in self.schema
                else list(mapping.keys())
            )
            renamed_exprs = []
            for c in all_cols:
                if c in mapping:
                    renamed_exprs.append(f"{c} AS {mapping[c]}")
                else:
                    renamed_exprs.append(c)
            return f"SELECT {', '.join(renamed_exprs)} FROM {from_sql}"

        elif op == "join":
            left_sql, left_alias = self._get_from_clause(node["left"])
            right_sql, right_alias = self._get_from_clause(node["right"])
            join_type = node.get("type", "inner").upper()
            on_pred = node.get("on")
            on_str = f" ON {self._compile_predicate(on_pred, 'on')}" if on_pred else " ON 1=1"
            return f"SELECT * FROM {left_sql} {join_type} JOIN {right_sql}{on_str}"

        elif op == "anti_join":
            left_sql, left_alias = self._get_from_clause(node["left"])
            right_node = node["right"]
            match_mode = node.get("match", "null_safe")
            on_pred = node.get("on", {})

            if match_mode == "null_safe":
                self.null_ledger.append({"node": "anti_join", "construct": "NOT EXISTS null_safe"})
                right_sql, _ = self._get_from_clause(right_node)
                pred_str = self._compile_predicate(on_pred, "anti_join.on")
                return f"SELECT * FROM {left_sql} WHERE NOT EXISTS (SELECT 1 FROM {right_sql} WHERE {pred_str})"
            else:  # sql_not_in
                self.null_ledger.append({"node": "anti_join", "construct": "NOT IN"})
                # For NOT IN, extract left and right comparison keys
                eq_spec = on_pred.get("eq3") or on_pred.get("not_distinct")
                if eq_spec:
                    l_key = self._compile_arg(eq_spec[0])
                    r_key = self._compile_arg(eq_spec[1])
                    right_tbl = (
                        right_node
                        if isinstance(right_node, str)
                        else self._compile_node(right_node)
                    )
                    right_target = right_tbl if isinstance(right_node, str) else f"({right_tbl})"
                    return f"SELECT * FROM {left_sql} WHERE {l_key} NOT IN (SELECT {r_key} FROM {right_target})"
                else:
                    return f"SELECT * FROM {left_sql} WHERE 1=0"

        elif op == "semi_join":
            left_sql, left_alias = self._get_from_clause(node["left"])
            right_node = node["right"]
            right_sql, _ = self._get_from_clause(right_node)
            on_pred = node.get("on", {})
            pred_str = self._compile_predicate(on_pred, "semi_join.on")
            self.null_ledger.append({"node": "semi_join", "construct": "EXISTS"})
            return f"SELECT * FROM {left_sql} WHERE EXISTS (SELECT 1 FROM {right_sql} WHERE {pred_str})"

        elif op == "group":
            from_sql, _ = self._get_from_clause(node["from"])
            by_cols = node.get("by", [])
            aggs = node.get("agg", {})

            select_items = list(by_cols)
            for out_name, agg_spec in aggs.items():
                func = agg_spec["func"]
                arg = agg_spec.get("arg")
                if func == "count_star":
                    select_items.append(f"COUNT(*) AS {out_name}")
                elif func == "count_col":
                    select_items.append(f"COUNT({arg}) AS {out_name}")
                elif func == "sum":
                    select_items.append(f"SUM({arg}) AS {out_name}")
                elif func == "min":
                    select_items.append(f"MIN({arg}) AS {out_name}")
                elif func == "max":
                    select_items.append(f"MAX({arg}) AS {out_name}")

            by_str = f" GROUP BY {', '.join(by_cols)}" if by_cols else ""
            return f"SELECT {', '.join(select_items)} FROM {from_sql}{by_str}"

        elif op == "union_all":
            left_node = node["left"]
            right_node = node["right"]
            l_sql = self._compile_node(left_node)
            r_sql = self._compile_node(right_node)
            return f"{l_sql} UNION ALL {r_sql}"

        elif op == "distinct":
            from_node = node["from"]
            inner_sql = self._compile_node(from_node)
            return f"SELECT DISTINCT * FROM ({inner_sql}) AS {self._next_alias()}"

        return "SELECT 1 WHERE 1=0"

    def _get_from_clause(self, node: Any) -> Tuple[str, str]:
        if isinstance(node, str):
            return node, node
        inner_sql = self._compile_node(node)
        alias = self._next_alias()
        return f"({inner_sql}) AS {alias}", alias
