"""Pure Python in-memory relational algebra engine implementing Kleene 3VL and bag semantics.
Owned by the second judge, separate from proposer SQL compilation.
"""

from typing import Any, Dict, List, Optional, Tuple


def kleene_and(p1: Optional[bool], p2: Optional[bool]) -> Optional[bool]:
    if p1 is False or p2 is False:
        return False
    if p1 is True and p2 is True:
        return True
    return None


def kleene_or(p1: Optional[bool], p2: Optional[bool]) -> Optional[bool]:
    if p1 is True or p2 is True:
        return True
    if p1 is False and p2 is False:
        return False
    return None


def kleene_not(p: Optional[bool]) -> Optional[bool]:
    if p is None:
        return None
    return not p


def eval_arg_val(arg: Any, row: Dict[str, Any]) -> Any:
    if isinstance(arg, dict):
        if "col" in arg:
            col_name = arg["col"]
            # Might be table.col or just col
            if col_name in row:
                return row[col_name]
            simple = col_name.split(".")[-1]
            return row.get(simple)
        elif "val" in arg:
            return arg["val"]
    elif isinstance(arg, str):
        if arg in row:
            return row[arg]
        return row.get(arg.split(".")[-1])
    return arg


def eval_predicate(pred: Dict[str, Any], row: Dict[str, Any]) -> Optional[bool]:
    """Evaluates predicate under Kleene 3-valued logic."""
    if not pred:
        return True

    results = []
    for k, v in pred.items():
        if k == "eq3":
            a1 = eval_arg_val(v[0], row)
            a2 = eval_arg_val(v[1], row)
            if a1 is None or a2 is None:
                results.append(None)
            else:
                results.append(a1 == a2)
        elif k == "distinct":
            a1 = eval_arg_val(v[0], row)
            a2 = eval_arg_val(v[1], row)
            if a1 is None and a2 is None:
                results.append(False)
            elif a1 is None or a2 is None:
                results.append(True)
            else:
                results.append(a1 != a2)
        elif k == "not_distinct":
            a1 = eval_arg_val(v[0], row)
            a2 = eval_arg_val(v[1], row)
            if a1 is None and a2 is None:
                results.append(True)
            elif a1 is None or a2 is None:
                results.append(False)
            else:
                results.append(a1 == a2)
        elif k == "is_null":
            a = eval_arg_val(v, row)
            results.append(a is None)
        elif k == "is_not_null":
            a = eval_arg_val(v, row)
            results.append(a is not None)
        elif k == "and":
            cur = True
            for p in v:
                sub = eval_predicate(p, row)
                cur = kleene_and(cur, sub)
            results.append(cur)
        elif k == "or":
            cur = False
            for p in v:
                sub = eval_predicate(p, row)
                cur = kleene_or(cur, sub)
            results.append(cur)
        elif k == "not":
            sub = eval_predicate(v, row)
            results.append(kleene_not(sub))
        elif k == "coalesce":
            val = None
            for a in v:
                av = eval_arg_val(a, row)
                if av is not None:
                    val = av
                    break
            results.append(None if val is None else bool(val))

    final_res = True
    for r in results:
        final_res = kleene_and(final_res, r)
    return final_res


def get_node_table_name(node: Any) -> Optional[str]:
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if "from" in node:
            return get_node_table_name(node["from"])
    return None


def relation_heading(spec: Any, schema: Dict[str, Any]) -> Tuple[str, ...]:
    """Derive ordered row-dictionary labels from the schema, never observed rows.

    Duplicate names retain the existing first-label-wins carrier limitation.
    This metadata routine calls neither SQL nor either proposer implementation.
    """
    if isinstance(spec, str):
        return tuple(schema[spec])
    op = spec["op"]
    if op in {"join", "anti_join", "semi_join", "union_all"}:
        left = relation_heading(spec["left"], schema)
        if op in {"anti_join", "semi_join"}:
            return left
        right = relation_heading(spec["right"], schema)
        if op == "union_all":
            if len(left) != len(right):
                raise ValueError("UNION_HEADING_ARITY_MISMATCH")
            return left
        return tuple(dict.fromkeys(left + right))
    source = relation_heading(spec["from"], schema)
    if op == "select":
        columns = spec.get("project") or source
    elif op == "project":
        columns = spec["columns"]
    elif op == "rename":
        columns = [spec["map"].get(column, column) for column in source]
    elif op == "group":
        columns = [*spec.get("by", []), *spec.get("agg", {})]
    elif op == "distinct":
        columns = source
    else:
        raise ValueError(f"UNSUPPORTED_HEADING_OPERATOR: {op}")
    return tuple(dict.fromkeys(columns))


def execute_relational_spec(
    spec: Dict[str, Any], database: Dict[str, List[Dict[str, Any]]],
    schema: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Evaluates the relational algebra tree over the given database."""
    if schema is None:
        # Legacy direct callers can infer only labels present in their rows.
        # Judges MUST supply the declared schema, especially for empty tables.
        schema = {table: dict.fromkeys(key for row in rows for key in row)
                  for table, rows in database.items()}
    if isinstance(spec, str):
        # Base table
        return [{column: row.get(column) for column in schema[spec]}
                for row in database.get(spec, [])]

    op = spec.get("op")

    if op == "select":
        from_rows = execute_relational_spec(spec["from"], database, schema)
        where_pred = spec.get("where")
        proj_cols = spec.get("project")

        filtered = []
        for r in from_rows:
            if where_pred:
                # SQL WHERE clause accepts only TRUE (drops False and NULL)
                if eval_predicate(where_pred, r) is True:
                    filtered.append(r)
            else:
                filtered.append(r)

        if proj_cols:
            return [{c: r.get(c) for c in proj_cols} for r in filtered]
        return filtered

    elif op == "project":
        from_rows = execute_relational_spec(spec["from"], database, schema)
        cols = spec["columns"]
        return [{c: r.get(c) for c in cols} for r in from_rows]

    elif op == "rename":
        from_rows = execute_relational_spec(spec["from"], database, schema)
        mapping = spec["map"]
        res = []
        for r in from_rows:
            new_r = {}
            for k, v in r.items():
                new_k = mapping.get(k, k)
                new_r[new_k] = v
            res.append(new_r)
        return res

    elif op == "join":
        left_rows = execute_relational_spec(spec["left"], database, schema)
        right_rows = execute_relational_spec(spec["right"], database, schema)
        join_type = spec.get("type", "inner")
        on_pred = spec.get("on")
        tbl_l = get_node_table_name(spec["left"])
        tbl_r = get_node_table_name(spec["right"])

        res = []
        for lr in left_rows:
            matched = False
            for rr in right_rows:
                combined_eval = {}
                for k, v in lr.items():
                    combined_eval[k] = v
                    if tbl_l:
                        combined_eval[f"{tbl_l}.{k}"] = v
                for k, v in rr.items():
                    if tbl_r:
                        combined_eval[f"{tbl_r}.{k}"] = v
                    if k not in combined_eval:
                        combined_eval[k] = v

                if on_pred is None or eval_predicate(on_pred, combined_eval) is True:
                    matched = True
                    # Left table keys take precedence in case of duplicate names
                    combined_out = dict(lr)
                    for key, value in rr.items():
                        combined_out.setdefault(key, value)
                    res.append(combined_out)
            if not matched and join_type == "left":
                # produce NULL-extended right row
                combined_out = dict(lr)
                for key in relation_heading(spec["right"], schema):
                    combined_out.setdefault(key, None)
                res.append(combined_out)
        return res

    elif op == "anti_join":
        left_rows = execute_relational_spec(spec["left"], database, schema)
        right_rows = execute_relational_spec(spec["right"], database, schema)
        match_mode = spec.get("match", "null_safe")
        on_pred = spec.get("on", {})
        tbl_l = get_node_table_name(spec["left"])
        tbl_r = get_node_table_name(spec["right"])

        res = []
        if match_mode == "null_safe":
            for lr in left_rows:
                has_match = False
                for rr in right_rows:
                    combined_eval = {}
                    for k, v in lr.items():
                        combined_eval[k] = v
                        if tbl_l:
                            combined_eval[f"{tbl_l}.{k}"] = v
                    for k, v in rr.items():
                        if tbl_r:
                            combined_eval[f"{tbl_r}.{k}"] = v
                        if k not in combined_eval:
                            combined_eval[k] = v

                    if eval_predicate(on_pred, combined_eval) is True:
                        has_match = True
                        break
                if not has_match:
                    res.append(dict(lr))
        else:  # sql_not_in
            # Extract right comparison column
            eq_spec = on_pred.get("eq3") or on_pred.get("not_distinct")
            if eq_spec:
                l_arg, r_arg = eq_spec[0], eq_spec[1]
                right_vals = [eval_arg_val(r_arg, rr) for rr in right_rows]
                has_null_in_subquery = any(v is None for v in right_vals)
                for lr in left_rows:
                    if not right_vals:
                        # Even a NULL left operand is outside an empty set.
                        res.append(dict(lr))
                        continue
                    lv = eval_arg_val(l_arg, lr)
                    if lv is None:
                        # NULL NOT IN (...) is UNKNOWN -> dropped
                        continue
                    if has_null_in_subquery:
                        # If right subquery contains NULL and lv is not found in non-nulls:
                        # lv = v_i is UNKNOWN for NULL -> NOT UNKNOWN is UNKNOWN -> dropped!
                        if lv in right_vals:
                            continue
                        else:
                            continue  # dropped by SQL 3VL!
                    else:
                        if lv not in right_vals:
                            res.append(dict(lr))
            else:
                pass
        return res

    elif op == "semi_join":
        left_rows = execute_relational_spec(spec["left"], database, schema)
        right_rows = execute_relational_spec(spec["right"], database, schema)
        on_pred = spec.get("on", {})
        tbl_l = get_node_table_name(spec["left"])
        tbl_r = get_node_table_name(spec["right"])
        res = []
        for lr in left_rows:
            has_match = False
            for rr in right_rows:
                combined_eval = {}
                for k, v in lr.items():
                    combined_eval[k] = v
                    if tbl_l:
                        combined_eval[f"{tbl_l}.{k}"] = v
                for k, v in rr.items():
                    if tbl_r:
                        combined_eval[f"{tbl_r}.{k}"] = v
                    if k not in combined_eval:
                        combined_eval[k] = v
                if eval_predicate(on_pred, combined_eval) is True:
                    has_match = True
                    break
            if has_match:
                res.append(dict(lr))
        return res

    elif op == "group":
        from_rows = execute_relational_spec(spec["from"], database, schema)
        by_cols = spec.get("by", [])
        aggs = spec.get("agg", {})

        # Partition into groups with null-safe key comparison
        groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
        for r in from_rows:
            key = tuple(r.get(c) for c in by_cols)
            groups.setdefault(key, []).append(r)

        if not groups and not by_cols:
            # Single group over empty table
            groups[()] = []

        res = []
        for key, group_rows in groups.items():
            out_row = {by_cols[i]: key[i] for i in range(len(by_cols))}
            for out_name, agg_spec in aggs.items():
                func = agg_spec["func"]
                arg = agg_spec.get("arg")
                if func == "count_star":
                    out_row[out_name] = len(group_rows)
                elif func == "count_col":
                    out_row[out_name] = sum(1 for gr in group_rows if gr.get(arg) is not None)
                elif func == "sum":
                    vals = [gr.get(arg) for gr in group_rows if gr.get(arg) is not None]
                    out_row[out_name] = sum(vals) if vals else None
                elif func == "min":
                    vals = [gr.get(arg) for gr in group_rows if gr.get(arg) is not None]
                    out_row[out_name] = min(vals) if vals else None
                elif func == "max":
                    vals = [gr.get(arg) for gr in group_rows if gr.get(arg) is not None]
                    out_row[out_name] = max(vals) if vals else None
            res.append(out_row)
        return res

    elif op == "union_all":
        left_rows = execute_relational_spec(spec["left"], database, schema)
        right_rows = execute_relational_spec(spec["right"], database, schema)
        left_columns = relation_heading(spec["left"], schema)
        right_columns = relation_heading(spec["right"], schema)
        if len(left_columns) != len(right_columns):
            raise ValueError("UNION_HEADING_ARITY_MISMATCH")
        return [dict(r) for r in left_rows] + [
            dict(zip(left_columns, (row.get(column) for column in right_columns)))
            for row in right_rows
        ]

    elif op == "distinct":
        from_rows = execute_relational_spec(spec["from"], database, schema)
        seen = set()
        res = []
        for r in from_rows:
            # Hashable representation of row
            key = tuple(sorted(r.items()))
            if key not in seen:
                seen.add(key)
                res.append(dict(r))
        return res

    return []
