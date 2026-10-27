"""Pure C059 input and row-carrier contracts; no search or query execution.

AuthorityEffect: None. Validation and row comparison are shared contracts,
not a shared relational evaluation algorithm.
"""

from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

VALID_OPS = {
    "select",
    "project",
    "rename",
    "join",
    "anti_join",
    "semi_join",
    "group",
    "union_all",
    "distinct",
}


VALID_PRED_OPS = {
    "eq3",
    "distinct",
    "not_distinct",
    "is_null",
    "is_not_null",
    "and",
    "or",
    "not",
    "coalesce",
}


VALID_AGG_FUNCS = {"count_star", "count_col", "sum", "min", "max"}


def validate_schema_and_spec(
    schema: Dict[str, Any], spec: Dict[str, Any]
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates schema structure and relational algebra specification tree.

    Returns:
        (is_valid, error_code, witness)
    """
    if not isinstance(schema, dict) or len(schema) == 0:
        return False, "INVALID_SCHEMA", {"reason": "schema must be non-empty dictionary"}

    for tbl, cols in schema.items():
        if not isinstance(cols, dict) or len(cols) == 0:
            return False, "INVALID_TABLE_SCHEMA", {"table": tbl}
        for cname, ctype in cols.items():
            if not isinstance(cname, str) or not isinstance(ctype, str):
                return False, "INVALID_COLUMN_DEF", {"table": tbl, "col": cname}

    if not isinstance(spec, dict):
        return False, "INVALID_SPEC_TYPE", {"reason": "spec must be dictionary"}

    # Recursive validation of spec nodes and column references
    def get_node_columns(
        node: Any, path: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Set[str]]:
        if isinstance(node, str):
            # Base table reference
            if node not in schema:
                return False, "UNKNOWN_TABLE", {"table": node, "path": path}, set()
            return True, None, None, set(schema[node].keys())

        if not isinstance(node, dict):
            return False, "MALFORMED_NODE", {"path": path, "node": node}, set()

        op = node.get("op")
        if op not in VALID_OPS:
            return False, "UNSUPPORTED_OPERATOR", {"op": op, "path": path}, set()

        if op == "select":
            from_node = node.get("from")
            if not from_node:
                return False, "MISSING_FROM", {"path": f"{path}.from"}, set()
            ok, err, wit, in_cols = get_node_columns(from_node, f"{path}.from")
            if not ok:
                return False, err, wit, set()

            # check where predicate if present
            where = node.get("where")
            if where:
                pok, perr, pwit = validate_predicate(where, in_cols, f"{path}.where")
                if not pok:
                    return False, perr, pwit, set()

            proj = node.get("project")
            if proj is not None:
                if not isinstance(proj, list):
                    return False, "PROJECT_NOT_LIST", {"path": f"{path}.project"}, set()
                for col in proj:
                    if col not in in_cols:
                        return (
                            False,
                            "UNKNOWN_COLUMN",
                            {"col": col, "path": f"{path}.project"},
                            set(),
                        )
                return True, None, None, set(proj)
            return True, None, None, in_cols

        elif op == "project":
            from_node = node.get("from")
            cols = node.get("columns")
            if not from_node or not isinstance(cols, list):
                return False, "MALFORMED_PROJECT", {"path": path}, set()
            ok, err, wit, in_cols = get_node_columns(from_node, f"{path}.from")
            if not ok:
                return False, err, wit, set()
            for c in cols:
                if c not in in_cols:
                    return False, "UNKNOWN_COLUMN", {"col": c, "path": f"{path}.columns"}, set()
            return True, None, None, set(cols)

        elif op == "rename":
            from_node = node.get("from")
            mapping = node.get("map")
            if not from_node or not isinstance(mapping, dict):
                return False, "MALFORMED_RENAME", {"path": path}, set()
            ok, err, wit, in_cols = get_node_columns(from_node, f"{path}.from")
            if not ok:
                return False, err, wit, set()
            out_cols = set(in_cols)
            for old_c, new_c in mapping.items():
                if old_c not in in_cols:
                    return False, "UNKNOWN_COLUMN", {"col": old_c, "path": f"{path}.map"}, set()
                out_cols.remove(old_c)
                out_cols.add(new_c)
            return True, None, None, out_cols

        elif op in {"join", "anti_join", "semi_join"}:
            left = node.get("left")
            right = node.get("right")
            if not left or not right:
                return False, "MISSING_JOIN_OPERANDS", {"path": path}, set()
            ok_l, err_l, wit_l, left_cols = get_node_columns(left, f"{path}.left")
            if not ok_l:
                return False, err_l, wit_l, set()
            ok_r, err_r, wit_r, right_cols = get_node_columns(right, f"{path}.right")
            if not ok_r:
                return False, err_r, wit_r, set()

            # Check on predicate
            on_pred = node.get("on")
            combined_cols = left_cols | right_cols
            if on_pred:
                pok, perr, pwit = validate_predicate(on_pred, combined_cols, f"{path}.on")
                if not pok:
                    return False, perr, pwit, set()

            if op == "anti_join" or op == "semi_join":
                return True, None, None, left_cols
            return True, None, None, combined_cols

        elif op == "group":
            from_node = node.get("from")
            by_cols = node.get("by", [])
            aggs = node.get("agg", {})
            if not from_node or not isinstance(by_cols, list) or not isinstance(aggs, dict):
                return False, "MALFORMED_GROUP", {"path": path}, set()
            ok, err, wit, in_cols = get_node_columns(from_node, f"{path}.from")
            if not ok:
                return False, err, wit, set()
            for b in by_cols:
                if b not in in_cols:
                    return False, "UNKNOWN_COLUMN", {"col": b, "path": f"{path}.by"}, set()
            out_cols = set(by_cols)
            for out_name, agg_spec in aggs.items():
                if not isinstance(agg_spec, dict):
                    return False, "MALFORMED_AGG_SPEC", {"path": f"{path}.agg.{out_name}"}, set()
                func = agg_spec.get("func")
                if func not in VALID_AGG_FUNCS:
                    return (
                        False,
                        "UNKNOWN_AGG_FUNC",
                        {"func": func, "path": f"{path}.agg.{out_name}"},
                        set(),
                    )
                arg = agg_spec.get("arg")
                if func != "count_star":
                    if not arg or arg not in in_cols:
                        return (
                            False,
                            "UNKNOWN_COLUMN",
                            {"col": arg, "path": f"{path}.agg.{out_name}.arg"},
                            set(),
                        )
                out_cols.add(out_name)
            return True, None, None, out_cols

        elif op == "union_all":
            left = node.get("left")
            right = node.get("right")
            if not left or not right:
                return False, "MISSING_UNION_OPERANDS", {"path": path}, set()
            ok_l, err_l, wit_l, left_cols = get_node_columns(left, f"{path}.left")
            if not ok_l:
                return False, err_l, wit_l, set()
            ok_r, err_r, wit_r, right_cols = get_node_columns(right, f"{path}.right")
            if not ok_r:
                return False, err_r, wit_r, set()
            return True, None, None, left_cols

        elif op == "distinct":
            from_node = node.get("from")
            if not from_node:
                return False, "MISSING_FROM", {"path": path}, set()
            return get_node_columns(from_node, f"{path}.from")

        return False, "UNHANDLED_OP", {"op": op, "path": path}, set()

    def validate_predicate(
        pred: Any, available_cols: Set[str], path: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        if not isinstance(pred, dict):
            return False, "PRED_NOT_DICT", {"path": path}

        for k, v in pred.items():
            if k not in VALID_PRED_OPS:
                return False, "UNKNOWN_PRED_OP", {"op": k, "path": path}
            if k in {"eq3", "distinct", "not_distinct"}:
                if not isinstance(v, list) or len(v) != 2:
                    return False, "BINARY_PRED_ARITY", {"op": k, "path": path}
                for i, arg in enumerate(v):
                    aok, aerr, awit = validate_arg(arg, available_cols, f"{path}.{k}[{i}]")
                    if not aok:
                        return False, aerr, awit
            elif k in {"is_null", "is_not_null"}:
                aok, aerr, awit = validate_arg(v, available_cols, f"{path}.{k}")
                if not aok:
                    return False, aerr, awit
            elif k in {"and", "or"}:
                if not isinstance(v, list) or len(v) == 0:
                    return False, "LOGICAL_OP_EMPTY", {"op": k, "path": path}
                for i, subpred in enumerate(v):
                    sok, serr, swit = validate_predicate(
                        subpred, available_cols, f"{path}.{k}[{i}]"
                    )
                    if not sok:
                        return False, serr, swit
            elif k == "not":
                sok, serr, swit = validate_predicate(v, available_cols, f"{path}.not")
                if not sok:
                    return False, serr, swit
            elif k == "coalesce":
                if not isinstance(v, list) or len(v) == 0:
                    return False, "COALESCE_EMPTY", {"path": path}
                for i, arg in enumerate(v):
                    aok, aerr, awit = validate_arg(arg, available_cols, f"{path}.coalesce[{i}]")
                    if not aok:
                        return False, aerr, awit
        return True, None, None

    def validate_arg(
        arg: Any, available_cols: Set[str], path: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        if isinstance(arg, dict):
            if "col" in arg:
                cname = arg["col"]
                # Col might be table.col or just col
                simple_name = cname.split(".")[-1]
                if cname not in available_cols and simple_name not in available_cols:
                    return False, "UNKNOWN_COLUMN", {"col": cname, "path": path}
                return True, None, None
            elif "val" in arg:
                return True, None, None
            return False, "INVALID_ARG_SPEC", {"arg": arg, "path": path}
        elif isinstance(arg, str):
            simple_name = arg.split(".")[-1]
            if arg not in available_cols and simple_name not in available_cols:
                return False, "UNKNOWN_COLUMN", {"col": arg, "path": path}
            return True, None, None
        return False, "INVALID_ARG_TYPE", {"arg": arg, "path": path}

    ok, err, wit, _ = get_node_columns(spec, "spec")
    return ok, err, wit


def row_to_canonical_tuple(
    row: Dict[str, Any], col_order: Optional[List[str]] = None
) -> Tuple[Any, ...]:
    """Converts row dict to hashable tuple with sorted keys."""
    if col_order:
        return tuple(row.get(c) for c in col_order)
    return tuple(sorted((k, v) for k, v in row.items()))


def compare_bags(bag1: List[Dict[str, Any]], bag2: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Compares two bags of rows with null-safe value matching."""
    if len(bag1) != len(bag2):
        return False, f"BAG_SIZE_MISMATCH: {len(bag1)} != {len(bag2)}"

    if not bag1 and not bag2:
        return True, "EMPTY_BAGS_EQUAL"

    # Missing fields are not SQL NULL, and extra fields cannot be discarded.
    # Every row in either bag must have the same complete heading.
    heading = set(bag1[0])
    if any(set(row) != heading for row in bag1) or any(set(row) != heading for row in bag2):
        return False, "BAG_HEADING_MISMATCH"
    cols = sorted(heading)

    c1 = Counter(row_to_canonical_tuple(r, cols) for r in bag1)
    c2 = Counter(row_to_canonical_tuple(r, cols) for r in bag2)

    if c1 != c2:
        diff_1 = c1 - c2
        diff_2 = c2 - c1
        return (
            False,
            f"BAG_ELEMENT_MISMATCH: excess_in_1={dict(diff_1)}, excess_in_2={dict(diff_2)}",
        )

    return True, "BAGS_EQUAL"
