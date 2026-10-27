"""All schema sources, legacy totality, real reconstruction, and closed carriers."""

import sqlite3

import pytest

from pfp.infrastructure.normal_forms.schema_pipeline import ROOT
from pfp.infrastructure.normal_forms.schema_pipeline import SCHEMA_FILES
from pfp.infrastructure.normal_forms.schema_pipeline import (
    SchemaContractError,
)
from pfp.infrastructure.normal_forms.schema_pipeline import (
    assert_exhaustive_candidates,
)
from pfp.infrastructure.normal_forms.schema_pipeline import audit_all_schemas
from pfp.infrastructure.normal_forms.schema_pipeline import (
    install_totality_fences,
)
from pfp.infrastructure.normal_forms.schema_pipeline import table_contract


@pytest.mark.parametrize("owner", ["governance", "education"])
def test_runtime_evaluators_load_the_current_schema_and_enforce_totality(owner):
    if owner == "governance":
        from pfp.infrastructure.normal_forms.nf_evaluator import (
            NormalFormsEvaluator,
        )
    else:
        from pfp.infrastructure.normal_forms.evaluator import (
            NormalFormsEvaluator,
        )
    evaluator = NormalFormsEvaluator()
    try:
        flattened = evaluator.normalize_0nf_to_1nf([(1, "Ada", "alg,top")])
        assert [r["course_code"] for r in flattened] == ["alg", "top"]
        assert evaluator.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            evaluator.conn.execute(
                "INSERT INTO sales_cdc_log(op_type,sale_id,processed) VALUES ('INSERT',1,NULL)"
            )
    finally:
        evaluator.conn.close()


def test_inventory_exhausts_all_sources_and_every_table_has_a_total_key():
    report = audit_all_schemas()
    assert len(report["schemas"]) == len(SCHEMA_FILES) + 1
    # The five SQL sources already contain 84 tables at the migration base;
    # receipt_ledger_v1 adds its separately inventoried embedded table.
    assert sum(len(s["tables"]) for s in report["schemas"]) == 85
    for source in report["schemas"]:
        for table in source["tables"]:
            assert table["candidate_keys"]
            assert table["lossless_under_declared_fds"] is True
            assert table["dependencies_preserved"] is True
            assert table["authority_effect"] == "None"
            assert table["certified_implies_authorized"] is False


def test_optional_values_round_trip_through_key_based_projections():
    with sqlite3.connect(":memory:") as conn:
        conn.execute(
            "CREATE TABLE model (a TEXT NOT NULL, b INTEGER NOT NULL, x TEXT, y TEXT, PRIMARY KEY(a,b))"
        )
        conn.executemany(
            "INSERT INTO model VALUES (?,?,?,?)",
            [("alpha", 1, None, "p"), ("alpha", 2, "q", None), ("beta", 1, "q", "p")],
        )
        contract = table_contract(conn, "model")
        reconstructed = conn.execute(contract["reconstruction_sql"]).fetchall()
        assert set(reconstructed) == set(conn.execute("SELECT a,b,x,y FROM model"))
        assert len(reconstructed) == 3
        assert contract["optional_domains"] == ["x", "y"]
        assert contract["projections"] == [["a", "b", "x"], ["a", "b", "y"]]


def test_declared_education_dependencies_drive_the_actual_normalization_stages():
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(
            (
                ROOT / "pfp/infrastructure/yaml/normal_forms/normal_forms_schema.sql"
            ).read_text()
        )
        conn.executemany(
            "INSERT INTO student_enrollments_1nf VALUES (?,?,?,?,?,?)",
            [
                (1, "Ada", "alg", "Algebra", 7, "east"),
                (1, "Ada", "top", "Topology", 8, "west"),
                (2, "Emmy", "alg", "Algebra", 7, "east"),
            ],
        )
        stages = table_contract(conn, "student_enrollments_1nf")["semantic_pipeline"]
        assert stages["source_nf2"] is False
        assert stages["source_nf3"] is False
        assert stages["source_bcnf"] is False
        assert stages["nf3_lossless"] is True
        assert stages["nf3_dependency_preservation"] is True
        assert stages["nf6_lossless"] is True
        assert stages["nf6_dependency_preservation"] is True
        assert stages["instance_fd_violations"] == []
        conn.execute(
            "UPDATE student_enrollments_1nf SET instructor_office='wrong' WHERE student_id=2"
        )
        assert table_contract(conn, "student_enrollments_1nf")["semantic_pipeline"][
            "instance_fd_violations"
        ] == ["instructor_id->instructor_office"]


def test_nullable_unique_or_descending_integer_primary_key_is_not_a_total_key():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE bad (id INTEGER PRIMARY KEY DESC, payload TEXT)")
        with pytest.raises(SchemaContractError, match="no total candidate key"):
            table_contract(conn, "bad")


def test_legacy_text_primary_key_is_fenced_without_rewriting_valid_rows():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE model (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.execute("INSERT INTO model VALUES ('old', 'retained')")
        install_totality_fences(
            conn, "CREATE TABLE model (id TEXT PRIMARY KEY NOT NULL, payload TEXT NOT NULL)"
        )
        assert conn.execute("SELECT * FROM model").fetchall() == [("old", "retained")]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO model VALUES (NULL, 'bad')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE model SET id=NULL")
        install_totality_fences(
            conn, "CREATE TABLE model (id TEXT PRIMARY KEY NOT NULL, payload TEXT NOT NULL)"
        )


def test_legacy_null_fact_is_reported_and_not_coerced():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE model (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.execute("INSERT INTO model VALUES (NULL, 'retained')")
        with pytest.raises(SchemaContractError, match="legacy NULL"):
            install_totality_fences(
                conn, "CREATE TABLE model (id TEXT PRIMARY KEY NOT NULL, payload TEXT NOT NULL)"
            )
        assert conn.execute("SELECT * FROM model").fetchall() == [(None, "retained")]


def test_guard_refresh_protects_new_required_columns_atomically():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE model (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.execute("INSERT INTO model VALUES ('old', 'retained')")
        install_totality_fences(
            conn, "CREATE TABLE model (id TEXT PRIMARY KEY NOT NULL, payload TEXT NOT NULL)"
        )
        conn.execute("ALTER TABLE model ADD COLUMN added TEXT")
        conn.execute("UPDATE model SET added='required'")
        install_totality_fences(
            conn,
            "CREATE TABLE model (id TEXT PRIMARY KEY NOT NULL, payload TEXT NOT NULL, added TEXT NOT NULL)",
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE model SET added=NULL")
        conn.execute("CREATE TABLE zbad (id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO zbad VALUES (NULL)")
        before = conn.execute(
            "SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name"
        ).fetchall()
        with pytest.raises(SchemaContractError):
            install_totality_fences(
                conn,
                "CREATE TABLE model (id TEXT PRIMARY KEY NOT NULL, payload TEXT NOT NULL); CREATE TABLE zbad (id TEXT PRIMARY KEY NOT NULL)",
            )
        assert (
            conn.execute(
                "SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name"
            ).fetchall()
            == before
        )


@pytest.mark.parametrize(
    "expected, observed",
    [
        ([], []),
        (["a", "b"], ["a"]),
        (["a", "b"], ["a", "a"]),
        (["a", "b"], ["a", "c"]),
        (["a", "a"], ["a"]),
        (["a"], [True]),
        (["a"], [""]),
    ],
)
def test_exhaustiveness_refuses_vacuity_duplicates_and_foreign_candidates(expected, observed):
    with pytest.raises(SchemaContractError):
        assert_exhaustive_candidates(expected, observed)


def test_sql_coverage_checks_exact_carrier_and_input_binding():
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(
            (
                ROOT / "pfp/infrastructure/yaml/normal_forms/exhaustive_candidates.sql"
            ).read_text()
        )
        conn.execute("INSERT INTO nf_candidate_problems VALUES ('p', 'carrier', 2, 'None')")
        conn.executemany(
            "INSERT INTO nf_candidate_carrier VALUES ('p', ?, ?)",
            [("a", "input-a"), ("b", "input-b")],
        )
        conn.execute(
            "INSERT INTO nf_candidate_checks VALUES ('p', 'a', 'input-a', 'accept', 'evidence-a')"
        )
        assert conn.execute("SELECT exhaustive FROM nf_candidate_coverage").fetchone() == (0,)
        for values in [
            ("p", "c", "input-c", "accept", "e"),
            ("p", "b", "input-a", "accept", "e"),
            ("p", "b", "input-b", None, "e"),
            ("p", "a", "input-a", "accept", "e"),
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO nf_candidate_checks VALUES (?, ?, ?, ?, ?)", values)
        conn.execute(
            "INSERT INTO nf_candidate_checks VALUES ('p', 'b', 'input-b', 'reject', 'evidence-b')"
        )
        # Exhaustiveness includes checked negative outcomes; it does not mean every candidate passes.
        assert conn.execute(
            "SELECT exhaustive, authority_effect FROM nf_candidate_coverage"
        ).fetchone() == (1, "None")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE nf_candidate_problems SET declared_count=NULL")
        conn.commit()
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("UPDATE nf_candidate_checks SET input_digest='wrong' WHERE candidate_id='b'")
        assert conn.execute("SELECT exhaustive FROM nf_candidate_coverage").fetchone() == (0,)


def test_cdc_conditional_nulls_and_boolean_flags_are_sql_fenced():
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(
            (
                ROOT / "pfp/infrastructure/yaml/normal_forms/normal_forms_schema.sql"
            ).read_text()
        )
        conn.execute(
            "INSERT INTO sales_cdc_log(op_type,sale_id,new_region,new_amount) VALUES ('INSERT',1,'west',3)"
        )
        for statement in [
            "INSERT INTO sales_cdc_log(op_type,sale_id) VALUES ('INSERT',2)",
            "UPDATE sales_cdc_log SET processed=NULL",
            "UPDATE sales_cdc_log SET processed=2",
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(statement)


def test_legacy_cdc_variant_fields_and_binary_flag_are_fenced():
    ddl = "CREATE TABLE sales_cdc_log (cdc_id INTEGER PRIMARY KEY, op_type TEXT NOT NULL, sale_id INTEGER NOT NULL, old_region TEXT, new_region TEXT, old_amount REAL, new_amount REAL, processed INTEGER)"
    expected = ddl.replace("processed INTEGER)", "processed INTEGER NOT NULL)")
    with sqlite3.connect(":memory:") as conn:
        conn.execute(ddl)
        conn.execute("INSERT INTO sales_cdc_log VALUES(1,'INSERT',1,NULL,'west',NULL,3,0)")
        install_totality_fences(conn, expected)
        for statement in (
            "UPDATE sales_cdc_log SET new_region=NULL",
            "UPDATE sales_cdc_log SET processed=2",
            "INSERT INTO sales_cdc_log VALUES(2,'INSERT',2,NULL,NULL,NULL,NULL,0)",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(statement)


def test_failed_storage_initialization_cannot_be_bypassed_on_retry(tmp_path):
    from governance.infrastructure.storage.sqlite_governance_unit_of_work import (
        SqliteGovernanceUnitOfWork,
    )

    path = tmp_path / "legacy.db"
    ddl = (
        ROOT / "governance/infrastructure/storage/governance_schema.sql"
    ).read_text()
    with sqlite3.connect(path) as conn:
        conn.executescript(
            ddl.replace("event_id TEXT PRIMARY KEY NOT NULL", "event_id TEXT PRIMARY KEY")
        )
        conn.execute(
            "INSERT INTO governance_events VALUES(NULL,'a','kind','created','{}',1,'time')"
        )
    conn.close()
    owner = SqliteGovernanceUnitOfWork(str(path))
    for _ in range(2):
        with pytest.raises(SchemaContractError, match="legacy NULL"):
            _ = owner.connection
        assert owner._conn is None
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT event_id FROM governance_events").fetchall() == [(None,)]
