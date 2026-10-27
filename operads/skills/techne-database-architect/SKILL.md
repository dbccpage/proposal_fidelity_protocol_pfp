---
name: techne-database-architect
description: "Use for database schema design, query tuning, indexing and migrations across SQL, NoSQL, graph and vector stores."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# techne-database-architect

## 7. Analytical & Vector Engines (DuckDB & Lakehouses)

## 6. Neo4j & Graph Databases (Property Graph & Cypher)

## 5. MongoDB (Document-Oriented NoSQL)

## 4. Redis (In-Memory Key-Value & Data Structures)

## 3. SQL Server (Enterprise Relational & T-SQL)

## 2. SQLite (Embedded Relational & Local Engines)

## 1. PostgreSQL (Relational & Hybrid Object-Relational)

## Multi-Paradigm Database Foundations

## status: canonical-candidate

## Operational Directives

1. **Schema Design First:** Ensure all table/collection definitions have explicit primary keys, indices, and integrity constraints before code generation.
2. **Query Performance Law:** Every complex query MUST include execution plan analysis (`EXPLAIN ANALYZE` or Cypher `PROFILE`) to verify index usage.
3. **No Unindexed Scans:** Prohibit sequential scans on large tables ($>10,000$ rows) without explicit justification.

---

## Detailed PostgreSQL Architecture & Optimization Patterns

### PostgreSQL 18 Project Conventions

- **Version Enforcement:** ALL PostgreSQL commands MUST target PostgreSQL 18 (`"/mnt/c/Program Files/PostgreSQL/18/bin/psql.exe"`).
- **Naming Conventions:** Lowercase `snake_case` for tables/columns, singular table names (`user`, `order`), foreign keys formatted as `{referenced_table}_id`.
- **Environment & Credentials:** Use `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD` via environment or `.pgpass`. Never hardcode secrets.

### Data Type & Indexing Rules

- **IDs & Primary Keys:** Use `BIGINT GENERATED ALWAYS AS IDENTITY` or `UUID` (`gen_random_uuid()`).
- **Timestamps & Text:** Use `TIMESTAMPTZ` (timezone-aware) and `TEXT` over `VARCHAR(n)`.
- **JSON & Vectors:** Use `JSONB` for unstructured data; use `vector(n)` with HNSW (`vector_cosine_ops`) for embeddings (`pgvector`).
- **Index Types:** B-Tree (default), GIN (JSONB / FTS), GiST (range/trigram), HNSW (pgvector). Always create indexes on Foreign Key columns!

### High-Performance Query & Concurrency Patterns

- **UPSERT (Insert / On Conflict):** Use `ON CONFLICT (cols) DO UPDATE SET ... EXCLUDED.val`.
- **Cursor Pagination:** Use `WHERE id > $last_id ORDER BY id LIMIT N` (O(1) cost, avoiding `OFFSET`).
- **Locking & Queues:** Use `FOR UPDATE SKIP LOCKED` for atomic background task polling.
- **RLS Policy Optimization:** Wrap auth lookups in scalar subqueries `((SELECT auth.uid()) = user_id)` to avoid per-row function evaluation.

### Alembic Migration Conventions

- Keep migration revision IDs $\le 32$ characters (`alembic_version.version_num` limit).
- Execute migrations per schema target: `alembic -c alembic_sdlc.ini upgrade head`.

### Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever `techne-database-architect` encounters database connection failures, unindexed sequential scans (>10,000 rows), or schema corruption:

1. Automatically create a formal investigation report under:
   `engine/sentinel_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_db_architect_{defect_id}.md`
2. Include error traces, query execution plans (`EXPLAIN ANALYZE`), root cause analysis, and remediation plan for Blackrod review.

---

**AuthorityEffect:** None.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
