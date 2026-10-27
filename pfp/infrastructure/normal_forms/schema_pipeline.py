"""SQL inventory, null-totality fences, and declared-key normal-form projections.

This is an operational schema contract, relative to SQL's declared key FDs. It
does not infer semantic dependencies inside JSON/CSV or invent MVD/JD declarations.
Nullable payload values are explicit optional domains; candidate identity is total.
AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from governance.infrastructure.storage.schema_totality import (
    SchemaContractError,
    columns,
    install_totality_fences,
    quote,
    tables,
    total_columns,
)
from pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_2nf,
    check_3nf,
    check_bcnf,
    check_dependency_preservation,
    check_lossless_decomposition,
)
from pfp.domain.normal_forms.relational_advanced import (
    decompose_bcnf_tree,
    synthesize_3nf_bernstein,
)
from pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "governance").is_dir() and (
            parent / "education"
        ).is_dir():
            return parent
    raise SchemaContractError("repository schema anchors were not found")


ROOT = _repository_root()
SCHEMA_FILES = (
    "governance/infrastructure/storage/governance_schema.sql",
    "pfp/infrastructure/yaml/normal_forms/normal_forms_schema.sql",
    "pfp/infrastructure/yaml/normal_forms/exhaustive_candidates.sql",
    "education/documentation/014_normal_forms/demos/normal_forms_schema.sql",
    "pfp/infrastructure/yaml/normal_forms/_golden_nfs/normal_forms_schema.sql"
    if (
        ROOT
        / "pfp/infrastructure/yaml/normal_forms/_golden_nfs/normal_forms_schema.sql"
    ).is_file()
    else "pfp/infrastructure/yaml/normal_forms/normal_forms_schema.sql",
)
LEDGER_FILE = "governance/infrastructure/storage/receipt_ledger_v1.py"


def assert_exhaustive_candidates(expected: Sequence[str], observed: Sequence[str]) -> None:
    """Check exact set AND cardinality with unique, nonempty, stable string IDs."""
    for label, values in (("expected", expected), ("observed", observed)):
        if (
            isinstance(values, (str, bytes))
            or not values
            or any(type(v) is not str or not v.strip() for v in values)
        ):
            raise SchemaContractError(f"{label} candidate carrier is empty or untyped")
        if len(set(values)) != len(values):
            raise SchemaContractError(f"duplicate {label} candidate ID")
    if len(expected) != len(observed) or set(expected) != set(observed):
        raise SchemaContractError("candidate IDs do not exhaust the exact declared carrier")


def declared_keys(conn: sqlite3.Connection, table: str) -> list[frozenset[str]]:
    info = columns(conn, table)
    rowid_aliases = {r[1] for r in info if r[5] and r[2].upper() == "INTEGER"}
    if any(index[3] == "pk" for index in conn.execute(f"PRAGMA index_list({quote(table)})")):
        rowid_aliases = set()
    total = {r[1] for r in info if r[3]} | rowid_aliases
    primary = frozenset(r[1] for r in info if r[5])
    keys = [primary] if primary and primary.issubset(total) else []
    for index in conn.execute(f"PRAGMA index_list({quote(table)})"):
        if index[2] and not index[4]:  # Only unconditional UNIQUE indexes.
            names = [r[2] for r in conn.execute(f"PRAGMA index_info({quote(index[1])})")]
            if names and all(type(n) is str and n in total for n in names):
                keys.append(frozenset(names))
    # With key->heading FDs only, minimal declared keys exhaust the candidate keys.
    return sorted(
        {k for k in keys if k and not any(j < k for j in keys)}, key=lambda k: (len(k), sorted(k))
    )


def semantic_stages(
    conn: sqlite3.Connection, table: str, key_schema: RelationalSchema
) -> dict[str, Any]:
    """Use the education schemas' explicitly stated partial/transitive dependencies.

    Other tables retain the key-FD scope. CSV unnesting is a declared education
    operation; JSON payload semantics and undeclared MVD/JDs remain open.
    """
    extra = {
        "student_enrollments_1nf": (
            ("student_id", "student_name"),
            ("course_code", "course_title"),
            ("instructor_id", "instructor_office"),
        ),
        "student_registrations_2nf": (("instructor_id", "instructor_office"),),
    }.get(table, ())
    if not extra:
        return {
            "dependency_scope": "SQL key FDs only",
            "semantic_dependencies_complete": False,
            "zero_to_one": "declared CSV unnesting required"
            if table == "student_records_0nf"
            else "scalar storage; semantic domain interpretation required",
        }
    if any(a not in key_schema.attributes or b not in key_schema.attributes for a, b in extra):
        raise SchemaContractError(f"{table}: declared education FD escapes its heading")
    dependencies = key_schema.dependencies | frozenset(
        FunctionalDependency.from_str(a, b) for a, b in extra
    )
    schema = RelationalSchema(key_schema.attributes, dependencies)
    violations = []
    for a, b in extra:
        disagreement = conn.execute(
            f"SELECT 1 FROM {quote(table)} p JOIN {quote(table)} q "
            f"ON p.{quote(a)} IS NOT DISTINCT FROM q.{quote(a)} "
            f"WHERE p.{quote(b)} IS DISTINCT FROM q.{quote(b)} LIMIT 1"
        ).fetchone()
        if disagreement:
            violations.append(f"{a}->{b}")
    synthesis = synthesize_3nf_bernstein(schema)
    bcnf = decompose_bcnf_tree(schema)
    terminal = []
    for component in bcnf:
        key = sorted(component.candidate_keys(), key=lambda k: (len(k), sorted(k)))[0]
        terminal.extend([key | {a} for a in sorted(component.attributes - key)] or [key])
    return {
        "dependency_scope": "SQL keys plus stated education partial/transitive FDs",
        "declared_extra_fds": [f"{a}->{b}" for a, b in extra],
        "instance_fd_violations": violations,
        "semantic_dependencies_complete": False,
        "candidate_keys": [sorted(k) for k in schema.candidate_keys()],
        "source_nf2": check_2nf(schema)[0],
        "source_nf3": check_3nf(schema)[0],
        "source_bcnf": check_bcnf(schema)[0],
        "nf3_synthesis": [sorted(p) for p in synthesis],
        "nf3_lossless": check_lossless_decomposition(schema, synthesis)[0],
        "nf3_dependency_preservation": check_dependency_preservation(schema, synthesis)[0],
        "bcnf_decomposition": [sorted(p.attributes) for p in bcnf],
        "nf6_key_profile": [sorted(p) for p in terminal],
        "nf6_lossless": check_lossless_decomposition(schema, terminal)[0],
        "nf6_dependency_preservation": check_dependency_preservation(schema, terminal)[0],
        "nf4_nf5_nf6_semantics": "requires complete MVD/JD declarations",
        "reconstruction_precondition": "input instance satisfies every declared FD",
    }


def table_contract(conn: sqlite3.Connection, table: str) -> dict[str, Any]:
    info = columns(conn, table)
    heading = frozenset(r[1] for r in info)
    keys = declared_keys(conn, table)
    if not keys:
        raise SchemaContractError(f"{table}: no total candidate key")
    dependencies = frozenset(FunctionalDependency(key, heading) for key in keys)
    schema = RelationalSchema(heading, dependencies)
    key = keys[0]
    pieces = [key | {a} for a in sorted(heading - key)] or [key]
    if frozenset().union(*pieces) != heading:
        raise SchemaContractError(f"{table}: projection cover is incomplete")
    lossless, reason = check_lossless_decomposition(schema, pieces)
    preserved, preservation_reason = check_dependency_preservation(schema, pieces)
    if not lossless:
        raise SchemaContractError(f"{table}: {reason}")
    bcnf, _ = check_bcnf(schema)
    nullable = sorted(heading - set(total_columns(info)) - {r[1] for r in info if r[5]})
    projection_sql = [
        f"SELECT {', '.join(map(quote, sorted(p)))} FROM {quote(table)}" for p in pieces
    ]
    key_names = ", ".join(map(quote, sorted(key)))
    projected = [f"({sql}) AS p{i}" for i, sql in enumerate(projection_sql)]
    reconstruction = projected[0] + "".join(f" JOIN {p} USING ({key_names})" for p in projected[1:])
    selected = ", ".join(
        f"p{next(i for i, p in enumerate(pieces) if a in p)}.{quote(a)}" for a in sorted(heading)
    )
    return {
        "table": table,
        "heading": sorted(heading),
        "candidate_keys": [sorted(k) for k in keys],
        "candidate_exhaustiveness_scope": "minimal keys under declared SQL key-to-heading FDs",
        "required_facts": sorted(total_columns(info)),
        "optional_domains": nullable,
        "storage_1nf": True,
        "semantic_1nf": "requires declared interpretation of JSON/CSV payloads",
        "nf2_nf3_bcnf_under_key_fds": bcnf,
        "nf4_nf5": "conditional on complete MVD/JD declarations; no semantic certification",
        "nf6_target": "key plus at most one nonkey attribute; closed key-FD profile",
        "projections": [sorted(p) for p in pieces],
        "projection_sql": projection_sql,
        "reconstruction_sql": f"SELECT {selected} FROM {reconstruction}",
        "lossless_under_declared_fds": lossless,
        "dependencies_preserved": preserved,
        "dependency_preservation_gap": preservation_reason,
        "authority_effect": "None",
        "certified_implies_authorized": False,
        "semantic_pipeline": semantic_stages(conn, table, schema),
    }


def schema_sources() -> list[tuple[str, str]]:
    discovered = sorted(
        p.relative_to(ROOT).as_posix()
        for directory in (
            ROOT / "governance",
            ROOT / "education" / "documentation" / "014_normal_forms",
            NORMAL_FORMS_DIR,
        )
        for p in directory.rglob("*.sql")
    )
    assert_exhaustive_candidates(SCHEMA_FILES, discovered)
    sources = [(path, (ROOT / path).read_text(encoding="utf-8")) for path in SCHEMA_FILES]
    tree = ast.parse((ROOT / LEDGER_FILE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_SCHEMA" for t in node.targets
        ):
            sources.append((LEDGER_FILE + "::_SCHEMA", ast.literal_eval(node.value)))
            break
    else:
        raise SchemaContractError("receipt ledger embedded schema was not found")
    return sources


def audit_all_schemas() -> dict[str, Any]:
    inventory = []
    for path, sql in schema_sources():
        with sqlite3.connect(":memory:") as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript(sql)
            install_totality_fences(conn, sql)
            inventory.append(
                {"source": path, "tables": [table_contract(conn, t) for t in tables(conn)]}
            )
    return {
        "schema_version": "core.nf.schema-inventory.v1",
        "schemas": inventory,
        "authority_effect": "None",
        "dependency_scope": "declared SQL keys only",
    }


if __name__ == "__main__":
    print(json.dumps(audit_all_schemas(), indent=2, sort_keys=True))
