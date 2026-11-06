"""Generate and dual-verify 64 hidden evaluation cases for C059 SQL Synthesis under Three-Valued-Logic Fences."""

import json
from pathlib import Path

from .judge_packet.exact_checker import (
    verify_candidate,
)
from .judge_packet.independent_checker import (
    independent_check,
)
from .reference_solver import (
    solve,
)

cases_dir = Path(__file__).resolve().parent / "judge_packet" / "cases"


def create_sample_dbs():
    # DB 0: General nulls and non-nulls
    db0 = {
        "users": [
            {"id": 1, "name": "Alice", "role_id": 10, "status": "active"},
            {"id": 2, "name": "Bob", "role_id": None, "status": "pending"},
            {"id": 3, "name": "Charlie", "role_id": 20, "status": None},
            {"id": 4, "name": "David", "role_id": None, "status": None},
            {"id": 5, "name": "Eve", "role_id": 10, "status": "active"},
        ],
        "roles": [
            {"role_id": 10, "role_name": "Admin", "clearance": 5},
            {"role_id": 20, "role_name": "User", "clearance": 1},
            {"role_id": 30, "role_name": "Guest", "clearance": None},
        ],
        "facts": [
            {"id": 1, "f_val": 100, "g_verdict": 1, "l_prod": 1},
            {"id": 2, "f_val": None, "g_verdict": 0, "l_prod": 1},
            {"id": 3, "f_val": 200, "g_verdict": None, "l_prod": None},
            {"id": 4, "f_val": 300, "g_verdict": 1, "l_prod": None},
            {"id": 5, "f_val": None, "g_verdict": None, "l_prod": 0},
        ],
    }

    # DB 1: All-null values and empty sub-groups
    db1 = {
        "users": [
            {"id": 1, "name": None, "role_id": None, "status": None},
            {"id": 2, "name": None, "role_id": None, "status": None},
        ],
        "roles": [
            {"role_id": None, "role_name": None, "clearance": None},
        ],
        "facts": [
            {"id": 1, "f_val": None, "g_verdict": None, "l_prod": None},
            {"id": 2, "f_val": None, "g_verdict": None, "l_prod": None},
        ],
    }

    # DB 2: Empty tables
    db2 = {"users": [], "roles": [], "facts": []}

    return [db0, db1, db2]


def build_cases():
    test_dbs = create_sample_dbs()
    schema_std = {
        "users": {"id": "INTEGER", "name": "TEXT", "role_id": "INTEGER", "status": "TEXT"},
        "roles": {"role_id": "INTEGER", "role_name": "TEXT", "clearance": "INTEGER"},
        "facts": {"id": "INTEGER", "f_val": "INTEGER", "g_verdict": "INTEGER", "l_prod": "INTEGER"},
    }

    cases = []

    # =========================================================================
    # PART 1: 32 BASE CASES (b01 - b32)
    # =========================================================================

    # b01: Pointwise distinct comparison
    cases.append(
        {
            "case_id": "c059_b01_where_distinct",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "facts",
                "where": {"distinct": [{"col": "g_verdict"}, {"col": "l_prod"}]},
                "project": ["id", "f_val"],
            },
            "protected": ["f_val", "g_verdict"],
            "test_databases": test_dbs,
        }
    )

    # b02: eq3 with nulls (Kleene unknown drops row)
    cases.append(
        {
            "case_id": "c059_b02_where_eq3",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "facts",
                "where": {"eq3": [{"col": "g_verdict"}, {"col": "l_prod"}]},
                "project": ["id"],
            },
            "protected": ["g_verdict"],
            "test_databases": test_dbs,
        }
    )

    # b03: not_distinct (IS NOT DISTINCT FROM)
    cases.append(
        {
            "case_id": "c059_b03_not_distinct",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "facts",
                "where": {"not_distinct": [{"col": "g_verdict"}, {"col": "l_prod"}]},
                "project": ["id"],
            },
            "protected": ["g_verdict", "l_prod"],
            "test_databases": test_dbs,
        }
    )

    # b04: is_null check
    cases.append(
        {
            "case_id": "c059_b04_is_null",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {"is_null": {"col": "role_id"}},
                "project": ["id", "name"],
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b05: is_not_null check
    cases.append(
        {
            "case_id": "c059_b05_is_not_null",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {"is_not_null": {"col": "role_id"}},
                "project": ["id", "name"],
            },
            "protected": ["status"],
            "test_databases": test_dbs,
        }
    )

    # b06: and with null logic
    cases.append(
        {
            "case_id": "c059_b06_and_logic",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {
                    "and": [
                        {"is_not_null": {"col": "name"}},
                        {"eq3": [{"col": "role_id"}, {"val": 10}]},
                    ]
                },
                "project": ["id", "name"],
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b07: or with null logic
    cases.append(
        {
            "case_id": "c059_b07_or_logic",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {"or": [{"is_null": {"col": "role_id"}}, {"is_null": {"col": "status"}}]},
                "project": ["id", "name"],
            },
            "protected": ["role_id", "status"],
            "test_databases": test_dbs,
        }
    )

    # b08: not predicate
    cases.append(
        {
            "case_id": "c059_b08_not_predicate",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "roles",
                "where": {"not": {"is_null": {"col": "clearance"}}},
                "project": ["role_id", "role_name"],
            },
            "protected": ["clearance"],
            "test_databases": test_dbs,
        }
    )

    # b09: coalesce predicate
    cases.append(
        {
            "case_id": "c059_b09_coalesce",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "facts",
                "where": {"coalesce": [{"col": "g_verdict"}, {"col": "l_prod"}, {"val": 0}]},
                "project": ["id", "f_val"],
            },
            "protected": ["f_val"],
            "test_databases": test_dbs,
        }
    )

    # b10: inner join with null keys
    cases.append(
        {
            "case_id": "c059_b10_inner_join",
            "schema": schema_std,
            "spec": {
                "op": "join",
                "type": "inner",
                "left": "users",
                "right": "roles",
                "on": {"eq3": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b11: left join with null right rows
    cases.append(
        {
            "case_id": "c059_b11_left_join",
            "schema": schema_std,
            "spec": {
                "op": "join",
                "type": "left",
                "left": "users",
                "right": "roles",
                "on": {"eq3": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b12: anti_join null_safe (NOT EXISTS)
    cases.append(
        {
            "case_id": "c059_b12_anti_join_null_safe",
            "schema": schema_std,
            "spec": {
                "op": "anti_join",
                "match": "null_safe",
                "left": "users",
                "right": "roles",
                "on": {"not_distinct": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b13: anti_join sql_not_in
    cases.append(
        {
            "case_id": "c059_b13_anti_join_not_in",
            "schema": schema_std,
            "spec": {
                "op": "anti_join",
                "match": "sql_not_in",
                "left": "users",
                "right": "roles",
                "on": {"eq3": [{"col": "role_id"}, {"col": "role_id"}]},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b14: semi_join EXISTS
    cases.append(
        {
            "case_id": "c059_b14_semi_join",
            "schema": schema_std,
            "spec": {
                "op": "semi_join",
                "left": "users",
                "right": "roles",
                "on": {"not_distinct": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b15: group by with nulls
    cases.append(
        {
            "case_id": "c059_b15_group_by_nulls",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "users",
                "by": ["role_id"],
                "agg": {"user_count": {"func": "count_star"}},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b16: count_col ignores nulls
    cases.append(
        {
            "case_id": "c059_b16_count_col_nulls",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "users",
                "by": ["role_id"],
                "agg": {"named_count": {"func": "count_col", "arg": "name"}},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b17: sum on all-null groups
    cases.append(
        {
            "case_id": "c059_b17_sum_nulls",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "facts",
                "by": ["g_verdict"],
                "agg": {"total_f": {"func": "sum", "arg": "f_val"}},
            },
            "protected": ["g_verdict", "f_val"],
            "test_databases": test_dbs,
        }
    )

    # b18: min/max on nullable columns
    cases.append(
        {
            "case_id": "c059_b18_min_max_nulls",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "facts",
                "by": ["g_verdict"],
                "agg": {
                    "min_f": {"func": "min", "arg": "f_val"},
                    "max_f": {"func": "max", "arg": "f_val"},
                },
            },
            "protected": ["g_verdict"],
            "test_databases": test_dbs,
        }
    )

    # b19: distinct deduplication
    cases.append(
        {
            "case_id": "c059_b19_distinct_rows",
            "schema": schema_std,
            "spec": {
                "op": "distinct",
                "from": {"op": "project", "from": "users", "columns": ["role_id", "status"]},
            },
            "protected": ["role_id", "status"],
            "test_databases": test_dbs,
        }
    )

    # b20: union_all with null rows
    cases.append(
        {
            "case_id": "c059_b20_union_all",
            "schema": schema_std,
            "spec": {
                "op": "union_all",
                "left": {
                    "op": "select",
                    "from": "users",
                    "where": {"is_null": {"col": "role_id"}},
                    "project": ["id", "name"],
                },
                "right": {
                    "op": "select",
                    "from": "users",
                    "where": {"is_not_null": {"col": "role_id"}},
                    "project": ["id", "name"],
                },
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b21: rename columns
    cases.append(
        {
            "case_id": "c059_b21_rename",
            "schema": schema_std,
            "spec": {
                "op": "rename",
                "from": "users",
                "map": {"name": "user_name", "status": "user_status"},
            },
            "protected": ["status"],
            "test_databases": test_dbs,
        }
    )

    # b22: global aggregate (no by columns)
    cases.append(
        {
            "case_id": "c059_b22_global_aggregate",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "facts",
                "by": [],
                "agg": {
                    "grand_total": {"func": "sum", "arg": "f_val"},
                    "row_cnt": {"func": "count_star"},
                },
            },
            "protected": ["f_val"],
            "test_databases": test_dbs,
        }
    )

    # b23: nested filter in subquery
    cases.append(
        {
            "case_id": "c059_b23_nested_select",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": {
                    "op": "select",
                    "from": "facts",
                    "where": {"is_not_null": {"col": "f_val"}},
                    "project": ["id", "f_val", "g_verdict"],
                },
                "where": {"distinct": [{"col": "g_verdict"}, {"val": 1}]},
                "project": ["id", "f_val"],
            },
            "protected": ["f_val", "g_verdict"],
            "test_databases": test_dbs,
        }
    )

    # b24: composite join and filter
    cases.append(
        {
            "case_id": "c059_b24_join_and_filter",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": {
                    "op": "join",
                    "type": "inner",
                    "left": "users",
                    "right": "roles",
                    "on": {"eq3": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
                },
                "where": {"distinct": [{"col": "status"}, {"val": "active"}]},
                "project": ["id", "name", "role_name"],
            },
            "protected": ["role_id", "status"],
            "test_databases": test_dbs,
        }
    )

    # b25: multi-column grouping with nulls
    cases.append(
        {
            "case_id": "c059_b25_multi_col_group",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "facts",
                "by": ["g_verdict", "l_prod"],
                "agg": {"cnt": {"func": "count_star"}},
            },
            "protected": ["g_verdict", "l_prod"],
            "test_databases": test_dbs,
        }
    )

    # b26: join with null_safe on predicate
    cases.append(
        {
            "case_id": "c059_b26_join_null_safe_on",
            "schema": schema_std,
            "spec": {
                "op": "join",
                "type": "inner",
                "left": "users",
                "right": "roles",
                "on": {"not_distinct": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )

    # b27: select all from base table
    cases.append(
        {
            "case_id": "c059_b27_select_all",
            "schema": schema_std,
            "spec": {"op": "select", "from": "roles"},
            "protected": ["role_name"],
            "test_databases": test_dbs,
        }
    )

    # b28: project after rename
    cases.append(
        {
            "case_id": "c059_b28_project_after_rename",
            "schema": schema_std,
            "spec": {
                "op": "project",
                "from": {"op": "rename", "from": "users", "map": {"id": "uid", "name": "uname"}},
                "columns": ["uid", "uname"],
            },
            "protected": ["name"],
            "test_databases": test_dbs,
        }
    )

    # b29: distinct on single column
    cases.append(
        {
            "case_id": "c059_b29_distinct_single_col",
            "schema": schema_std,
            "spec": {
                "op": "distinct",
                "from": {"op": "project", "from": "facts", "columns": ["g_verdict"]},
            },
            "protected": ["g_verdict"],
            "test_databases": test_dbs,
        }
    )

    # b30: left join with right filter
    cases.append(
        {
            "case_id": "c059_b30_left_join_filter",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": {
                    "op": "join",
                    "type": "left",
                    "left": "users",
                    "right": "roles",
                    "on": {"eq3": [{"col": "users.role_id"}, {"col": "roles.role_id"}]},
                },
                "where": {"is_null": {"col": "clearance"}},
                "project": ["id", "name"],
            },
            "protected": ["clearance"],
            "test_databases": test_dbs,
        }
    )

    # b31: group by with max aggregation
    cases.append(
        {
            "case_id": "c059_b31_group_max",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "roles",
                "by": ["role_name"],
                "agg": {"max_clr": {"func": "max", "arg": "clearance"}},
            },
            "protected": ["clearance"],
            "test_databases": test_dbs,
        }
    )

    # b32: composite pipeline with union and distinct
    cases.append(
        {
            "case_id": "c059_b32_composite_pipeline",
            "schema": schema_std,
            "spec": {
                "op": "distinct",
                "from": {
                    "op": "union_all",
                    "left": {"op": "project", "from": "users", "columns": ["id"]},
                    "right": {"op": "project", "from": "facts", "columns": ["id"]},
                },
            },
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )

    # =========================================================================
    # PART 2: 16 RELABEL / GAUGE CONTROLS (g01 - g16)
    # =========================================================================
    for idx in range(1, 17):
        base_c = cases[idx - 1]
        gid = f"c059_g{idx:02d}_relabel_control"
        # Duplicate with different protected order or alias
        g_case = {
            "case_id": gid,
            "schema": base_c["schema"],
            "spec": base_c["spec"],
            "protected": list(reversed(base_c["protected"])),
            "test_databases": base_c["test_databases"],
        }
        cases.append(g_case)

    # =========================================================================
    # PART 3: 16 POISONED CASES (p01 - p16)
    # =========================================================================
    # p01: Unknown base table
    cases.append(
        {
            "case_id": "c059_p01_unknown_table",
            "schema": schema_std,
            "spec": {"op": "select", "from": "ghost_table", "project": ["id"]},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p02: Unknown column in project
    cases.append(
        {
            "case_id": "c059_p02_unknown_column_proj",
            "schema": schema_std,
            "spec": {"op": "select", "from": "users", "project": ["ghost_col"]},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p03: Unknown column in where predicate
    cases.append(
        {
            "case_id": "c059_p03_unknown_col_pred",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {"eq3": [{"col": "ghost_col"}, {"val": 1}]},
            },
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p04: Unsupported operator "cube"
    cases.append(
        {
            "case_id": "c059_p04_unsupported_op",
            "schema": schema_std,
            "spec": {"op": "cube", "from": "users"},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p05: Unsupported predicate operator "regex_match"
    cases.append(
        {
            "case_id": "c059_p05_unsupported_pred_op",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {"regex_match": [{"col": "name"}, {"val": ".*"}]},
            },
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p06: Missing from clause
    cases.append(
        {
            "case_id": "c059_p06_missing_from",
            "schema": schema_std,
            "spec": {"op": "select", "where": {"is_null": {"col": "id"}}},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p07: Missing join operands
    cases.append(
        {
            "case_id": "c059_p07_missing_join_operands",
            "schema": schema_std,
            "spec": {"op": "join", "left": "users"},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p08: Unsupported aggregate function "median"
    cases.append(
        {
            "case_id": "c059_p08_unsupported_agg_func",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "facts",
                "by": ["g_verdict"],
                "agg": {"med": {"func": "median", "arg": "f_val"}},
            },
            "protected": ["g_verdict"],
            "test_databases": test_dbs,
        }
    )
    # p09: Empty schema dict
    cases.append(
        {
            "case_id": "c059_p09_empty_schema",
            "schema": {},
            "spec": {"op": "select", "from": "users"},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p10: Project not a list
    cases.append(
        {
            "case_id": "c059_p10_project_not_list",
            "schema": schema_std,
            "spec": {"op": "select", "from": "users", "project": "id, name"},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p11: Rename with unknown old column
    cases.append(
        {
            "case_id": "c059_p11_rename_unknown_col",
            "schema": schema_std,
            "spec": {"op": "rename", "from": "users", "map": {"nonexistent_col": "new_name"}},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p12: Binary predicate arity violation (3 args for eq3)
    cases.append(
        {
            "case_id": "c059_p12_pred_arity_violation",
            "schema": schema_std,
            "spec": {
                "op": "select",
                "from": "users",
                "where": {"eq3": [{"col": "id"}, {"val": 1}, {"val": 2}]},
            },
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p13: Aggregate arg missing on count_col
    cases.append(
        {
            "case_id": "c059_p13_agg_arg_missing",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "users",
                "by": ["role_id"],
                "agg": {"c": {"func": "count_col"}},
            },
            "protected": ["role_id"],
            "test_databases": test_dbs,
        }
    )
    # p14: Spec is not a dict
    cases.append(
        {
            "case_id": "c059_p14_spec_not_dict",
            "schema": schema_std,
            "spec": "SELECT * FROM users",
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p15: Column def is not string
    cases.append(
        {
            "case_id": "c059_p15_invalid_col_def",
            "schema": {"users": {"id": 123}},
            "spec": {"op": "select", "from": "users"},
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )
    # p16: Unknown column in group by
    cases.append(
        {
            "case_id": "c059_p16_unknown_by_column",
            "schema": schema_std,
            "spec": {
                "op": "group",
                "from": "users",
                "by": ["unknown_group_key"],
                "agg": {"cnt": {"func": "count_star"}},
            },
            "protected": ["id"],
            "test_databases": test_dbs,
        }
    )

    return cases


def main():
    cases_dir.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    print(f"Total cases generated: {len(cases)}")
    assert len(cases) == 64, f"Expected exactly 64 cases, got {len(cases)}"

    for c in cases:
        cid = c["case_id"]
        # Save case JSON
        with open(cases_dir / f"{cid}.json", "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2)

        # Verify with reference solver and dual checkers
        sol = solve(c)
        ok1, msg1 = verify_candidate(c, sol)
        assert ok1, f"Exact checker failed on {cid}: {msg1}"

        ok2, msg2 = independent_check(c, sol)
        assert ok2, f"Independent checker failed on {cid}: {msg2}"

    print("Generated 64/64 hidden cases dual-verified successfully!")


if __name__ == "__main__":
    main()
