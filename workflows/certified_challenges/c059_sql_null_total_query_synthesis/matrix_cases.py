"""Small fixed case set for C059, used by the replay-custody test.

These cases were the model-matrix inputs in the original suite; only the
case data is kept here.
"""

from .generate_cases import create_sample_dbs

test_dbs = create_sample_dbs()

schema_std = {
    "users": {"id": "INTEGER", "name": "TEXT", "role_id": "INTEGER", "status": "TEXT"},
    "roles": {"role_id": "INTEGER", "role_name": "TEXT", "clearance": "INTEGER"},
    "facts": {"id": "INTEGER", "f_val": "INTEGER", "g_verdict": "INTEGER", "l_prod": "INTEGER"},
}

TEST_CASES = [
    # 1. Pointwise distinct comparison
    {
        "case_id": "c059_m01_where_distinct",
        "schema": schema_std,
        "spec": {
            "op": "select",
            "from": "facts",
            "where": {"distinct": [{"col": "g_verdict"}, {"col": "l_prod"}]},
            "project": ["id", "f_val"],
        },
        "protected": ["f_val", "g_verdict"],
        "test_databases": test_dbs,
    },
    # 2. eq3 with nulls
    {
        "case_id": "c059_m02_where_eq3",
        "schema": schema_std,
        "spec": {
            "op": "select",
            "from": "facts",
            "where": {"eq3": [{"col": "g_verdict"}, {"col": "l_prod"}]},
            "project": ["id"],
        },
        "protected": ["g_verdict"],
        "test_databases": test_dbs,
    },
    # 3. is_null check
    {
        "case_id": "c059_m03_is_null",
        "schema": schema_std,
        "spec": {
            "op": "select",
            "from": "users",
            "where": {"is_null": {"col": "role_id"}},
            "project": ["id", "name"],
        },
        "protected": ["role_id"],
        "test_databases": test_dbs,
    },
    # 4. inner join with null keys
    {
        "case_id": "c059_m04_inner_join",
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
    },
    # 5. left join
    {
        "case_id": "c059_m05_left_join",
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
    },
    # 6. anti_join null_safe (NOT EXISTS)
    {
        "case_id": "c059_m06_anti_join_null_safe",
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
    },
    # 7. anti_join sql_not_in (NOT IN)
    {
        "case_id": "c059_m07_anti_join_not_in",
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
    },
    # 8. group by with nulls
    {
        "case_id": "c059_m08_group_by_nulls",
        "schema": schema_std,
        "spec": {
            "op": "group",
            "from": "users",
            "by": ["role_id"],
            "agg": {"user_count": {"func": "count_star"}},
        },
        "protected": ["role_id"],
        "test_databases": test_dbs,
    },
    # 9. Poisoned case: unknown base table -> OUT_OF_SCOPE
    {
        "case_id": "c059_m09_poison_unknown_table",
        "schema": schema_std,
        "spec": {"op": "select", "from": "ghost_table", "project": ["id"]},
        "protected": ["id"],
        "test_databases": test_dbs,
    },
    # 10. Poisoned case: unsupported operator "cube" -> OUT_OF_SCOPE
    {
        "case_id": "c059_m10_poison_unsupported_op",
        "schema": schema_std,
        "spec": {"op": "cube", "from": "users"},
        "protected": ["id"],
        "test_databases": test_dbs,
    },
]
