"""Generate and verify 48 Hostile Mutations for C059 Judge Packet.

Verifies that BOTH exact_checker and independent_checker REJECT (kill) 100% of mutations.
"""

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
mutations_dir = Path(__file__).resolve().parent / "judge_packet" / "hostile_mutations"


def load_case(case_id: str) -> dict:
    with open(cases_dir / f"{case_id}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_mutations() -> list[dict]:
    MUTATIONS = []

    # Base solved cases
    c_b01 = load_case("c059_b01_where_distinct")
    sol_b01 = solve(c_b01)

    c_b03 = load_case("c059_b03_not_distinct")
    sol_b03 = solve(c_b03)

    c_b04 = load_case("c059_b04_is_null")
    sol_b04 = solve(c_b04)

    c_b05 = load_case("c059_b05_is_not_null")
    sol_b05 = solve(c_b05)

    c_b06 = load_case("c059_b06_and_logic")
    sol_b06 = solve(c_b06)

    c_b07 = load_case("c059_b07_or_logic")
    sol_b07 = solve(c_b07)

    c_b08 = load_case("c059_b08_not_predicate")
    sol_b08 = solve(c_b08)

    c_b10 = load_case("c059_b10_inner_join")
    sol_b10 = solve(c_b10)

    c_b11 = load_case("c059_b11_left_join")
    sol_b11 = solve(c_b11)

    c_b12 = load_case("c059_b12_anti_join_null_safe")
    sol_b12 = solve(c_b12)

    c_b13 = load_case("c059_b13_anti_join_not_in")
    sol_b13 = solve(c_b13)

    c_b14 = load_case("c059_b14_semi_join")
    sol_b14 = solve(c_b14)

    c_b15 = load_case("c059_b15_group_by_nulls")
    sol_b15 = solve(c_b15)

    c_b16 = load_case("c059_b16_count_col_nulls")
    sol_b16 = solve(c_b16)

    c_b17 = load_case("c059_b17_sum_nulls")
    sol_b17 = solve(c_b17)

    # Poisoned cases
    c_p01 = load_case("c059_p01_unknown_table")
    c_p04 = load_case("c059_p04_unsupported_op")
    c_p05 = load_case("c059_p05_unsupported_pred_op")

    # =============================================================================
    # 1-8: Three-Valued Logic Predicate Corruptions
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_01_neq_instead_of_distinct",
            c_b01,
            {**sol_b01, "sql": "SELECT id, f_val FROM facts WHERE (g_verdict <> l_prod)"},
            "Uses <> instead of IS DISTINCT FROM, silently dropping rows where either column is NULL",
        )
    )
    MUTATIONS.append(
        (
            "mut_02_eq_instead_of_not_distinct",
            c_b03,
            {**sol_b03, "sql": "SELECT id FROM facts WHERE (g_verdict = l_prod)"},
            "Uses = instead of IS NOT DISTINCT FROM, dropping rows where both are NULL",
        )
    )
    MUTATIONS.append(
        (
            "mut_03_is_null_inverted",
            c_b04,
            {**sol_b04, "sql": "SELECT id, name FROM users WHERE (role_id IS NOT NULL)"},
            "Uses IS NOT NULL when IS NULL was requested",
        )
    )
    MUTATIONS.append(
        (
            "mut_04_is_not_null_inverted",
            c_b05,
            {**sol_b05, "sql": "SELECT id, name FROM users WHERE (role_id IS NULL)"},
            "Uses IS NULL when IS NOT NULL was requested",
        )
    )
    MUTATIONS.append(
        (
            "mut_05_and_corrupted_to_or",
            c_b06,
            {
                **sol_b06,
                "sql": "SELECT id, name FROM users WHERE ((name IS NOT NULL) OR (role_id = 10))",
            },
            "Substitutes OR for AND in compound predicate",
        )
    )
    MUTATIONS.append(
        (
            "mut_06_or_corrupted_to_and",
            c_b07,
            {
                **sol_b07,
                "sql": "SELECT id, name FROM users WHERE ((role_id IS NULL) AND (status IS NULL))",
            },
            "Substitutes AND for OR in compound predicate",
        )
    )
    MUTATIONS.append(
        (
            "mut_07_not_predicate_omitted",
            c_b08,
            {**sol_b08, "sql": "SELECT role_id, role_name FROM roles WHERE (clearance IS NULL)"},
            "Omitted NOT operator in predicate",
        )
    )
    MUTATIONS.append(
        (
            "mut_08_where_clause_dropped",
            c_b01,
            {**sol_b01, "sql": "SELECT id, f_val FROM facts"},
            "Omitted WHERE clause entirely",
        )
    )

    # =============================================================================
    # 9-16: Anti-Join and Join Semantic Corruptions
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_09_not_in_used_for_null_safe_anti_join",
            c_b12,
            {**sol_b12, "sql": "SELECT * FROM users WHERE role_id NOT IN (SELECT role_id FROM roles)"},
            "Uses NOT IN instead of NOT EXISTS for null_safe anti-join when right table has NULLs",
        )
    )
    MUTATIONS.append(
        (
            "mut_10_not_exists_used_for_sql_not_in",
            c_b13,
            {
                **sol_b13,
                "sql": "SELECT * FROM users WHERE NOT EXISTS (SELECT 1 FROM roles WHERE (users.role_id = roles.role_id))",
            },
            "Uses NOT EXISTS when sql_not_in was requested (which should return 0 rows on NULLs)",
        )
    )
    MUTATIONS.append(
        (
            "mut_11_anti_join_converted_to_inner",
            c_b12,
            {
                **sol_b12,
                "sql": "SELECT users.* FROM users INNER JOIN roles ON (users.role_id = roles.role_id)",
            },
            "Substitutes inner join for anti-join",
        )
    )
    MUTATIONS.append(
        (
            "mut_12_semi_join_converted_to_anti",
            c_b14,
            {
                **sol_b14,
                "sql": "SELECT * FROM users WHERE NOT EXISTS (SELECT 1 FROM roles WHERE (users.role_id IS NOT DISTINCT FROM roles.role_id))",
            },
            "Substitutes NOT EXISTS for EXISTS in semi-join",
        )
    )
    MUTATIONS.append(
        (
            "mut_13_left_join_converted_to_inner",
            c_b11,
            {
                **sol_b11,
                "sql": "SELECT * FROM users INNER JOIN roles ON (users.role_id = roles.role_id)",
            },
            "Converts LEFT JOIN to INNER JOIN, dropping users with NULL or unmatched role_id",
        )
    )
    MUTATIONS.append(
        (
            "mut_14_inner_join_converted_to_cross",
            c_b10,
            {**sol_b10, "sql": "SELECT * FROM users CROSS JOIN roles"},
            "Drops ON clause converting inner join to cross join",
        )
    )
    MUTATIONS.append(
        (
            "mut_15_semi_join_pred_reversed",
            c_b14,
            {
                **sol_b14,
                "sql": "SELECT * FROM users WHERE EXISTS (SELECT 1 FROM roles WHERE (users.role_id IS DISTINCT FROM roles.role_id))",
            },
            "Inverts match predicate in semi-join",
        )
    )
    MUTATIONS.append(
        (
            "mut_16_join_pred_corrupted_to_false",
            c_b10,
            {**sol_b10, "sql": "SELECT * FROM users INNER JOIN roles ON 1=0"},
            "Forces join ON predicate to 1=0",
        )
    )

    # =============================================================================
    # 17-24: Aggregation and Grouping Corruptions
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_17_count_col_for_count_star",
            c_b15,
            {
                **sol_b15,
                "sql": "SELECT role_id, COUNT(role_id) AS user_count FROM users GROUP BY role_id",
            },
            "Uses COUNT(role_id) instead of COUNT(*), ignoring NULL role rows in count",
        )
    )
    MUTATIONS.append(
        (
            "mut_18_count_star_for_count_col",
            c_b16,
            {**sol_b16, "sql": "SELECT role_id, COUNT(*) AS named_count FROM users GROUP BY role_id"},
            "Uses COUNT(*) instead of COUNT(name), falsely counting NULL names",
        )
    )
    MUTATIONS.append(
        (
            "mut_19_sum_null_replaced_by_zero",
            c_b17,
            {
                **sol_b17,
                "sql": "SELECT g_verdict, COALESCE(SUM(f_val), 0) AS total_f FROM facts GROUP BY g_verdict",
            },
            "Coalesces SUM to 0 on all-NULL groups when SQL specification demands NULL",
        )
    )
    MUTATIONS.append(
        (
            "mut_20_group_by_omitted_in_aggregation",
            c_b15,
            {**sol_b15, "sql": "SELECT role_id, COUNT(*) AS user_count FROM users"},
            "Omitted GROUP BY clause, collapsing rows into single aggregate",
        )
    )
    MUTATIONS.append(
        (
            "mut_21_group_by_wrong_column",
            c_b15,
            {**sol_b15, "sql": "SELECT role_id, COUNT(*) AS user_count FROM users GROUP BY id"},
            "Grouped by primary key id instead of role_id",
        )
    )
    MUTATIONS.append(
        (
            "mut_22_group_by_drops_null_group",
            c_b15,
            {
                **sol_b15,
                "sql": "SELECT role_id, COUNT(*) AS user_count FROM users WHERE role_id IS NOT NULL GROUP BY role_id",
            },
            "Filtered out NULL grouping values before GROUP BY",
        )
    )
    MUTATIONS.append(
        (
            "mut_23_min_aggregate_corrupted",
            c_b17,
            {**sol_b17, "sql": "SELECT g_verdict, MAX(f_val) AS total_f FROM facts GROUP BY g_verdict"},
            "Uses MAX instead of SUM",
        )
    )
    MUTATIONS.append(
        (
            "mut_24_global_agg_returns_empty_on_empty_db",
            c_b15,
            {
                **sol_b15,
                "sql": "SELECT role_id, COUNT(*) AS user_count FROM users WHERE 1=0 GROUP BY role_id",
            },
            "Forces empty result on group query",
        )
    )

    # =============================================================================
    # 25-30: Preflight SQL Corruptions
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_25_missing_preflight_sql",
            c_b01,
            {**sol_b01, "preflight_sql": ""},
            "Empty preflight_sql string",
        )
    )
    MUTATIONS.append(
        (
            "mut_26_preflight_omits_protected_column",
            c_b01,  # protected: ["f_val", "g_verdict"]
            {**sol_b01, "preflight_sql": "SELECT * FROM facts WHERE f_val IS NULL"},
            "Preflight checks only f_val, omitting protected column g_verdict",
        )
    )
    MUTATIONS.append(
        (
            "mut_27_preflight_checks_not_null",
            c_b01,
            {
                **sol_b01,
                "preflight_sql": "SELECT * FROM facts WHERE f_val IS NOT NULL OR g_verdict IS NOT NULL",
            },
            "Preflight checks IS NOT NULL instead of IS NULL",
        )
    )
    MUTATIONS.append(
        (
            "mut_28_preflight_uses_and_instead_of_or",
            c_b01,
            {
                **sol_b01,
                "preflight_sql": "SELECT * FROM facts WHERE f_val IS NULL AND g_verdict IS NULL",
            },
            "Preflight requires all protected columns to be NULL simultaneously",
        )
    )
    MUTATIONS.append(
        (
            "mut_29_preflight_dummy_false_condition",
            c_b01,
            {**sol_b01, "preflight_sql": "SELECT 1 WHERE 1 = 0"},
            "Preflight dummy query returning 0 rows when protected columns are declared",
        )
    )
    MUTATIONS.append(
        (
            "mut_30_preflight_queries_wrong_table",
            c_b01,
            {**sol_b01, "preflight_sql": "SELECT * FROM users WHERE id IS NULL"},
            "Preflight queries users table instead of facts",
        )
    )

    # =============================================================================
    # 31-36: Malformed SQL Syntax and Schema Violations
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_31_sql_syntax_error",
            c_b01,
            {**sol_b01, "sql": "SELECCT id, f_val FROM facts"},
            "Syntax error in SQL text",
        )
    )
    MUTATIONS.append(
        (
            "mut_32_sql_unknown_table",
            c_b01,
            {**sol_b01, "sql": "SELECT id, f_val FROM non_existent_table"},
            "SQL references non-existent table",
        )
    )
    MUTATIONS.append(
        (
            "mut_33_sql_unknown_column",
            c_b01,
            {**sol_b01, "sql": "SELECT id, ghost_column FROM facts"},
            "SQL references non-existent column",
        )
    )
    MUTATIONS.append(
        (
            "mut_34_preflight_syntax_error",
            c_b01,
            {**sol_b01, "preflight_sql": "SELECT FROM facts WHERE f_val IS NULL"},
            "Syntax error in preflight SQL",
        )
    )
    MUTATIONS.append(
        (
            "mut_35_preflight_unknown_column",
            c_b01,
            {**sol_b01, "preflight_sql": "SELECT * FROM facts WHERE ghost_col IS NULL"},
            "Preflight references non-existent column",
        )
    )
    MUTATIONS.append(
        ("mut_36_empty_sql_string", c_b01, {**sol_b01, "sql": ""}, "Candidate SQL is empty string")
    )

    # =============================================================================
    # 37-42: Guardrail / Poisoned Case Exploits
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_37_solved_claimed_on_unknown_table",
            c_p01,
            {
                "case_id": c_p01["case_id"],
                "status": "SOLVED",
                "sql": "SELECT id FROM ghost_table",
                "preflight_sql": "SELECT 1 WHERE 1=0",
                "null_ledger": [],
            },
            "Claims SOLVED on poisoned case with non-existent table",
        )
    )
    MUTATIONS.append(
        (
            "mut_38_solved_claimed_on_unsupported_op",
            c_p04,
            {
                "case_id": c_p04["case_id"],
                "status": "SOLVED",
                "sql": "SELECT * FROM users",
                "preflight_sql": "SELECT 1 WHERE 1=0",
                "null_ledger": [],
            },
            "Claims SOLVED on poisoned case with unsupported op cube",
        )
    )
    MUTATIONS.append(
        (
            "mut_39_solved_claimed_on_unsupported_pred",
            c_p05,
            {
                "case_id": c_p05["case_id"],
                "status": "SOLVED",
                "sql": "SELECT * FROM users",
                "preflight_sql": "SELECT 1 WHERE 1=0",
                "null_ledger": [],
            },
            "Claims SOLVED on poisoned case with unsupported regex_match predicate",
        )
    )
    MUTATIONS.append(
        (
            "mut_40_false_unknown_on_valid_case",
            c_b01,
            {"case_id": c_b01["case_id"], "status": "UNKNOWN"},
            "Claims UNKNOWN on perfectly valid case B01",
        )
    )
    MUTATIONS.append(
        (
            "mut_41_false_out_of_scope_on_valid_case",
            c_b01,
            {
                "case_id": c_b01["case_id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "claims invalid"},
            },
            "Claims OUT_OF_SCOPE on perfectly valid case B01",
        )
    )
    MUTATIONS.append(
        (
            "mut_42_false_out_of_scope_on_valid_join",
            c_b10,
            {
                "case_id": c_b10["case_id"],
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "claims invalid"},
            },
            "Claims OUT_OF_SCOPE on perfectly valid inner join case B10",
        )
    )

    # =============================================================================
    # 43-48: Protocol, Null-Ledger and Canonical Format Violations
    # =============================================================================
    MUTATIONS.append(
        (
            "mut_43_case_id_mismatch",
            c_b01,
            {**sol_b01, "case_id": "c059_b02_where_eq3"},
            "Mismatched case_id in certificate response",
        )
    )
    MUTATIONS.append(
        (
            "mut_44_missing_case_id_field",
            c_b01,
            {
                "status": "SOLVED",
                "sql": sol_b01["sql"],
                "preflight_sql": sol_b01["preflight_sql"],
                "null_ledger": sol_b01["null_ledger"],
            },
            "Missing case_id field in candidate response",
        )
    )
    MUTATIONS.append(
        (
            "mut_45_invalid_status_string",
            c_b01,
            {**sol_b01, "status": "SUCCEEDED"},
            "Invalid status string SUCCEEDED",
        )
    )
    MUTATIONS.append(
        (
            "mut_46_candidate_not_a_dict",
            c_b01,
            '{"case_id": "c059_b01_where_distinct", "status": "SOLVED"}',
            "Candidate response passed as unparsed JSON string instead of dict",
        )
    )
    MUTATIONS.append(
        (
            "mut_47_null_ledger_not_a_list",
            c_b01,
            {**sol_b01, "null_ledger": "IS DISTINCT FROM"},
            "null_ledger is string instead of list",
        )
    )
    MUTATIONS.append(
        (
            "mut_48_null_ledger_construct_absent_in_sql",
            c_b01,
            {**sol_b01, "null_ledger": [{"node": "where.coalesce", "construct": "COALESCE"}]},
            "null_ledger claims COALESCE but COALESCE is not present in SQL text",
        )
    )
    return MUTATIONS


def main():
    MUTATIONS = build_mutations()
    mutations_dir.mkdir(parents=True, exist_ok=True)
    print(f"Total mutations defined: {len(MUTATIONS)}")
    assert len(MUTATIONS) == 48, f"Expected exactly 48 mutations, got {len(MUTATIONS)}"

    exact_kills = 0
    indep_kills = 0
    escapes = 0

    for idx, (m_id, case, cand, desc) in enumerate(MUTATIONS, 1):
        mut_path = mutations_dir / f"{m_id}.json"
        with open(mut_path, "w", encoding="utf-8") as f:
            json.dump(
                {"mutation_id": m_id, "description": desc, "case": case, "candidate": cand},
                f,
                indent=2,
            )

        ok_exact, msg_exact = verify_candidate(case, cand)
        ok_indep, msg_indep = independent_check(case, cand)

        if not ok_exact:
            exact_kills += 1
        if not ok_indep:
            indep_kills += 1

        if ok_exact or ok_indep:
            escapes += 1
            print(
                f"ESCAPE on {m_id}: exact={ok_exact} ({msg_exact}), indep={ok_indep} ({msg_indep})"
            )

    print(
        f"Exact checker kills:       {exact_kills} / {len(MUTATIONS)} ({exact_kills / len(MUTATIONS) * 100:.1f}%)"
    )
    print(
        f"Independent checker kills: {indep_kills} / {len(MUTATIONS)} ({indep_kills / len(MUTATIONS) * 100:.1f}%)"
    )
    print(f"Total escapes:             {escapes}")

    assert escapes == 0, f"{escapes} mutations escaped detection!"
    print("All 48 hostile mutations killed successfully with ZERO escapes!")


if __name__ == "__main__":
    main()
