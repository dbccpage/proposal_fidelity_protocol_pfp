"""Model matrix for C059: SQL Synthesis under Three-Valued-Logic Fences.

Sends the cases below to each declared model and scores the replies with both
judge checkers. This script makes live provider calls; run it only with an
explicit authorization of provider, budget and data handling, from the
repository root, as
``py -3.12 -m adversary.tests.pilots.c059_sql_null_total_query_synthesis.run_c059_matrix --output-dir <new directory> --max-estimated-cost-microusd 10000 --max-provider-calls 1 --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-output-tokens 2048``.
Shared behaviour (explicit configuration, opaque case tokens, full raw
responses, INFRA_ERROR and CHECKER_DEFECT outcomes, no overwriting) lives in
``pfp/infrastructure/synthesis_matrix.py``.

Correction, 2026-09-29: the earlier runner read a ``.env`` file, sent case IDs that name
the expected construct (for example ``c059_m06_anti_join_null_safe``), claimed
a canonical-JSON standard output it did not produce, and scored provider errors as failed cases. The hidden test
databases are still withheld from the prompt.
"""

from __future__ import annotations

import sys

from .judge_packet.exact_checker import (
    verify_candidate,
)
from .judge_packet.generate_cases import (
    create_sample_dbs,
)
from .judge_packet.independent_checker import (
    independent_check,
)
from pfp.infrastructure.synthesis_matrix import (
    MatrixSpec,
    main,
)

MODELS = [
    {
        "id": "stealth/space-bunny-alpha",
        "name": "Space Bunny Alpha",
        "tier": "undisclosed stealth model, exploratory only",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "LLaMA 3.3 70B Instruct",
        "tier": "70B Dense",
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "tier": "8B Dense",
    },
]

SYSTEM_PROMPT = """You are an expert database engine and compiler engineer participating in Challenge C059: SQL Synthesis under Three-Valued-Logic Fences under the Symbol Game protocol.

Given a case with parameters:
- "case_id": string identifier
- "schema": dictionary mapping table_name to {col_name: "INTEGER" | "TEXT"}
- "spec": relational algebra specification tree
- "protected": list of column names requiring totality preflight
- the judge runs your query on test databases that are not shown to you

Supported relational operators:
- "select": {"op": "select", "from": <rel>, "where": <pred>, "project": [<cols>]}
- "project": {"op": "project", "from": <rel>, "columns": [<cols>]}
- "rename": {"op": "rename", "from": <rel>, "map": {<old>: <new>}}
- "join": {"op": "join", "type": "inner"|"left", "left": <rel>, "right": <rel>, "on": <pred>}
- "anti_join": {"op": "anti_join", "match": "null_safe"|"sql_not_in", "left": <rel>, "right": <rel>, "on": <pred>}
- "semi_join": {"op": "semi_join", "left": <rel>, "right": <rel>, "on": <pred>}
- "group": {"op": "group", "from": <rel>, "by": [<cols>], "agg": {<out_col>: {"func": "count_star"|"count_col"|"sum"|"min"|"max", "arg": <col>}}}
- "union_all": {"op": "union_all", "left": <rel>, "right": <rel>}
- "distinct": {"op": "distinct", "from": <rel>}

Predicates under Kleene 3-Valued Logic:
- "distinct": emits `(a IS DISTINCT FROM b)` - NULL-safe inequality (never drops NULL vs non-NULL)
- "not_distinct": emits `(a IS NOT DISTINCT FROM b)` - NULL-safe equality
- "eq3": emits `(a = b)` - standard 3VL equality (UNKNOWN if either operand is NULL)
- "is_null": emits `(a IS NULL)`
- "is_not_null": emits `(a IS NOT NULL)`
- "and": emits `(p1 AND p2)`
- "or": emits `(p1 OR p2)`
- "not": emits `(NOT p)`
- "coalesce": emits `COALESCE(a1, a2, ...)`

Rules for SQL emission:
1. `anti_join`:
   - If match is "null_safe": emit `WHERE NOT EXISTS (SELECT 1 FROM <right> WHERE <pred>)`
   - If match is "sql_not_in": emit `WHERE <l_key> NOT IN (SELECT <r_key> FROM <right>)`
2. `preflight_sql`: For protected columns in the base table, emit query finding all rows with ANY protected column NULL:
   `SELECT * FROM <table_with_protected_cols> WHERE <col1> IS NULL OR <col2> IS NULL` (or `SELECT 1 WHERE 1=0` if no protected columns).
3. `null_ledger`: Record all 3VL constructs used in SQL (e.g. `[{"node": "where.distinct", "construct": "IS DISTINCT FROM"}]`).

Your response must be strictly valid JSON without Markdown fences:

1. If the specification is valid and supported (SOLVED):
{
  "case_id": "<case_id>",
  "status": "SOLVED",
  "sql": "SELECT ...",
  "preflight_sql": "SELECT ...",
  "null_ledger": [
    {"node": "where.distinct", "construct": "IS DISTINCT FROM"}
  ]
}

2. If the input case is MALFORMED or POISONED (e.g. unknown table, unknown column, unsupported op like 'cube', unsupported pred like 'regex_match') (OUT_OF_SCOPE):
{
  "case_id": "<case_id>",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "<REASON>"}
}

Reply with one JSON object only, without Markdown code fences."""

INSTRUCTION = "Case input:"

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


SPEC = MatrixSpec(
    challenge="C059: SQL Synthesis under Three-Valued-Logic Fences",
    system_prompt=SYSTEM_PROMPT,
    instruction=INSTRUCTION,
    cases=TEST_CASES,
    checkers=(("exact", verify_candidate), ("independent", independent_check)),
    models=MODELS,
    max_tokens=8192,
    hidden_keys=frozenset({"test_databases"}),
)


if __name__ == "__main__":
    sys.exit(main(SPEC))
