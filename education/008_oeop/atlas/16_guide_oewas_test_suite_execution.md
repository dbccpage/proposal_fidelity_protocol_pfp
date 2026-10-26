# OEWAS V3 Comprehensive Test Suite & Execution Guide

This document catalogs all test suites, fixtures, benchmarks, and edge-case fuzz tests implemented for the **OEWAS V3 (Omega Engine Workflows, Agents & Skills)** subsystem under Clean Architecture and Operadic Domain-Driven Design.

---

## 1. Test Architecture & Execution Invariants

> [!IMPORTANT]
> **Strict Test Execution Directive**: Local environments cannot sustain whole-suite sweeps (`pytest .`). Always execute tests in targeted files or small batches (1–3 files max) using the explicit commands documented below.

### Test Directory Layout

```text
omega_engine_operads/
├── _docs/
│   └── oewas_test_suite_execution_guide.md   <-- (This Document)
├── _img/
│   └── oewas_operad_model_guide.md           <-- (Visual Diagrams & Mathematical Models)
├── frontend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py
│   └── cli/
│       ├── __init__.py
│       ├── __main__.py
│       └── main.py
└── tests/
    ├── architecture/
    │   └── test_clean_architecture_ast_boundaries.py
    ├── contract/
    │   ├── test_fastapi_router_contracts.py
    │   └── test_oewas_python_facade.py
    ├── integration/
    │   ├── test_agent_to_agent_dag_compilation.py
    │   ├── test_asgi_multi_tenant_compile_catalog.py
    │   ├── test_benchmark_burst_load.py
    │   ├── test_cli_frontend_encoding_and_exit_codes.py
    │   ├── test_concurrent_multi_worker_idempotency.py
    │   ├── test_dual_read_legacy_catalog.py
    │   ├── test_e2e_full_lifecycle_roundtrip.py
    │   ├── test_e2e_multi_stage_agentic_terms.py
    │   ├── test_e2e_schema_migration_lossless.py
    │   ├── test_goo_migration_manifest_parity.py
    │   ├── test_higher_operad_adapter.py
    │   ├── test_higher_operad_laws_and_cyclic_graphs.py
    │   ├── test_legacy_woland_projection.py
    │   ├── test_manifest_signature_adversarial_matrix.py
    │   ├── test_openapi_schema_and_swagger_docs.py
    │   ├── test_outbox_message_dispatcher.py
    │   ├── test_outbox_transaction_atomicity.py
    │   ├── test_projection_manifest_signature_verification.py
    │   ├── test_sql_constraint_rejection_matrix.py
    │   └── test_sqlite_journal_unit_of_work.py
    └── unit/
        ├── test_application_railway_handlers.py
        ├── test_domain_value_objects.py
        ├── test_domain_value_objects_boundary_and_fuzz.py
        ├── test_lossless_markdown_parser.py
        ├── test_markdown_parser_edge_case_fuzz.py
        ├── test_markdown_parser_property_laws.py
        ├── test_operad_clean_arch.py
        ├── test_operad_compiler_service.py
        ├── test_prompt_civilization_oewas.py
        └── test_skill_document_v3_aggregate.py
```

---

## 2. Complete Inventory of Test Suites

### A. Integration & End-to-End Suites

#### 1. End-to-End Multi-Stage Agentic Pipeline

- **File**: [`tests/integration/test_e2e_multi_stage_agentic_terms.py`](../tests/integration/test_e2e_multi_stage_agentic_terms.py)
- **What it tests**: Full 7-stage lifecycle:
  1. Compiling estate catalog into SQLite WAL engine.
  2. Multi-operation operadic tree composition ($\gamma(\text{op}_A; \text{op}_B)$).
  3. Generating and signing Projection Manifests.
  4. Refusing unbound licensed-term requests with `LICENSE_WITNESS_REQUIRED`.
  5. Workflow DAG validation and topological cycle detection.
  6. Direct SQL inspection of `catalogs_v3`, `events_v3`, `outbox_v3`.
  7. Query handler roundtrip via `GetCatalogHandler`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_e2e_multi_stage_agentic_terms.py -p no:cacheprovider
  ```

#### 2. Lossless Multi-Document Schema Migration (v1/v2 $\to$ v3)

- **File**: [`tests/integration/test_e2e_schema_migration_lossless.py`](../tests/integration/test_e2e_schema_migration_lossless.py)
- **What it tests**: Upgrading legacy v1 (YAML frontmatter + markdown tables) and v2 markdown files into OEWAS v3 code fences (` ```oewas.operation.v3 `). Verifies **100% byte-exact slice reconstruction** from AST leaf node spans, compiles the migrated estate catalog, and persists into SQLite with full event sourcing.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_e2e_schema_migration_lossless.py -p no:cacheprovider
  ```

#### 3. Outbox Transaction Atomicity & Rollback

- **File**: [`tests/integration/test_outbox_transaction_atomicity.py`](../tests/integration/test_outbox_transaction_atomicity.py)
- **What it tests**:
  1. Mid-transaction simulated crashes during event outbox emission $\to$ validates complete SQLite `ROLLBACK` with 0 leaked rows in `catalogs_v3`, `events_v3`, `outbox_v3`, `idempotency_v3`.
  2. Pre-commit aggregate errors (e.g. malformed skill syntax) $\to$ fails fast with typed domain errors, touching 0 database records.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_outbox_transaction_atomicity.py -p no:cacheprovider
  ```

#### 4. Outbox Message Dispatcher & At-Least-Once Delivery

- **File**: [`tests/integration/test_outbox_message_dispatcher.py`](../tests/integration/test_outbox_message_dispatcher.py)
- **What it tests**:
  1. Polling pending outbox messages and routing to topic subscribers.
  2. Subscriber failure recovery: leaves failed messages in `outbox_v3` for at-least-once retry until successful.
  3. Consumer-side idempotency deduplication preventing double-execution of side effects on redelivery.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_outbox_message_dispatcher.py -p no:cacheprovider
  ```

#### 5. Concurrent Multi-Worker Idempotency Harness

- **File**: [`tests/integration/test_concurrent_multi_worker_idempotency.py`](../tests/integration/test_concurrent_multi_worker_idempotency.py)
- **What it tests**: 10-worker multi-threaded concurrent execution:
  - 10 workers writing distinct catalogs in parallel.
  - 10 racing workers submitting the exact same `IdempotencyKey` simultaneously $\to$ exactly one winner computes and all 10 receive the identical canonical payload.
  - Rejection and error reporting for duplicate keys with mismatched request digests (`IDEMPOTENCY_CONFLICT`).
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_concurrent_multi_worker_idempotency.py -p no:cacheprovider
  ```

#### 6. Asynchronous HTTP ASGI Multi-Tenant Stress Test

- **File**: [`tests/integration/test_asgi_multi_tenant_compile_catalog.py`](../tests/integration/test_asgi_multi_tenant_compile_catalog.py)
- **What it tests**: Dispatches 10 concurrent HTTP POST requests via `httpx.AsyncClient` + `httpx.ASGITransport` against `/api/oewas/v3/compile_catalog`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_asgi_multi_tenant_compile_catalog.py -p no:cacheprovider
  ```

#### 7. Sustained 120-Request Parallel Burst Load Benchmark

- **File**: [`tests/integration/test_benchmark_burst_load.py`](../tests/integration/test_benchmark_burst_load.py)
- **What it tests**: 120 concurrent asynchronous requests in 30-worker bursts across catalog compile, term evaluation, and DAG validation. Measures throughput ($> 50$ req/s), latency percentiles ($p50$, $p95$, $p99$), and peak memory delta ($< 5\text{MB}$) via `tracemalloc`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_benchmark_burst_load.py -s -p no:cacheprovider
  ```

#### 8. SQLite WAL Unit of Work & Journal

- **File**: [`tests/integration/test_sqlite_journal_unit_of_work.py`](../tests/integration/test_sqlite_journal_unit_of_work.py)
- **What it tests**: Direct SQLite WAL storage operations, multi-process lock safety, and event sourcing.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_sqlite_journal_unit_of_work.py -p no:cacheprovider
  ```

#### 9. Higher Operad Adapter

- **File**: [`tests/integration/test_higher_operad_adapter.py`](../tests/integration/test_higher_operad_adapter.py)
- **What it tests**: Strict operadic boundary composition, colour signature compatibility, and invalid slot binding rejection.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_higher_operad_adapter.py -p no:cacheprovider
  ```

#### 10. Goo-Type Skill Migration Manifest Parity

- **File**: [`tests/integration/test_goo_migration_manifest_parity.py`](../tests/integration/test_goo_migration_manifest_parity.py)
- **What it tests**: Audits all 41 legacy `goo-*` skills against `migration_manifest_v3.json`, asserting SHA-256 disk blob agreement.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_goo_migration_manifest_parity.py -p no:cacheprovider
  ```

#### 11. Agent-to-Agent Workflow DAG Compilation & Validation

- **File**: [`tests/integration/test_agent_to_agent_dag_compilation.py`](../tests/integration/test_agent_to_agent_dag_compilation.py)
- **What it tests**:
  1. Multi-agent parallel collaborative workflows (diamond joins across author, unit-tester, linter, Blackrod audit, and release agents) with Kahn's topological sort and parallel execution stages.
  2. Circular feedback cycle detection between agents ($A \to B \to C \to A$).
  3. Port and colour type mismatch detection (e.g. `Code` $\to$ `Receipt`).
  4. Orphaned edge reference detection (edges pointing to non-existent agent steps).
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_agent_to_agent_dag_compilation.py -p no:cacheprovider
  ```

#### 12. Projection Manifest Cryptographic Signature & Verification

- **File**: [`tests/integration/test_projection_manifest_signature_verification.py`](../tests/integration/test_projection_manifest_signature_verification.py)
- **What it tests**:
  1. End-to-end projection manifest compilation, cryptographic envelope signing (`HMAC-SHA256`), and constant-time signature verification.
  2. Rejection of payload tampering (1-byte modifications to exported skill catalogs fail verification with `PAYLOAD_DIGEST_MISMATCH`).
  3. Rejection of corrupt or forged cryptographic signatures (`SIGNATURE_VERIFICATION_FAILED`).
  4. Rejection of unauthorized keys or signer ID mismatches.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_projection_manifest_signature_verification.py -p no:cacheprovider
  ```

#### 13. CLI Frontend Exit Codes, JSON Output & CP1252 Terminal Safety

- **File**: [`tests/integration/test_cli_frontend_encoding_and_exit_codes.py`](../tests/integration/test_cli_frontend_encoding_and_exit_codes.py)
- **What it tests**:
  1. `compile-catalog --json`: returns exit code 0 and valid JSON output payload.
  2. Failure handling: returns exit code 1 on compilation syntax failure.
  3. Invalid CLI flags: returns exit code 2 on unknown arguments.
  4. Windows CP1252 console encoding guard: UTF-8 stdout reconfiguration ensuring multi-byte unicode math symbols (Φ₁, 🚀, ⊗) output cleanly without crashes.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_cli_frontend_encoding_and_exit_codes.py -p no:cacheprovider
  ```

#### 14. OpenAPI Schema Reflection, Swagger UI & ReDoc Accessibility

- **File**: [`tests/integration/test_openapi_schema_and_swagger_docs.py`](../tests/integration/test_openapi_schema_and_swagger_docs.py)
- **What it tests**:
  1. OpenAPI 3.1 schema generation at `/openapi.json` without runtime reflection errors.
  2. Swagger UI documentation page accessibility at `/docs`.
  3. ReDoc documentation page accessibility at `/redoc`.
  4. Lightweight health-check probe at `/healthz`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_openapi_schema_and_swagger_docs.py -p no:cacheprovider
  ```

#### 15. Full End-to-End Multi-Agent Lifecycle Roundtrip

- **File**: [`tests/integration/test_e2e_full_lifecycle_roundtrip.py`](../tests/integration/test_e2e_full_lifecycle_roundtrip.py)
- **What it tests**:
  1. Full estate compilation across authored skill documents into SQLite WAL database.
  2. Multi-agent workflow DAG validation with Kahn's topological sort and parallel execution stages.
  3. Projection manifest export and cryptographic signing (`HMAC-SHA256`) with constant-time verification.
  4. Outbox event message dispatching to subscriber topics.
  5. CLI query inspection (`verify-catalog`, structured JSON output).
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_e2e_full_lifecycle_roundtrip.py -p no:cacheprovider
  ```

#### 16. SQL Constraint Rejection Matrix & Primary Key Isolation (Landau Class 2)

- **File**: [`tests/integration/test_sql_constraint_rejection_matrix.py`](../tests/integration/test_sql_constraint_rejection_matrix.py)
- **What it tests**:
  1. Duplicate `catalog_id` PRIMARY KEY violation fails transaction with `UOW_COMMIT_FAILED` and preserves epoch conservation.
  2. Duplicate `event_id` PRIMARY KEY violation rolls back domain event persistence.
  3. Idempotency collision on differing request digests triggers `IDEMPOTENCY_CONFLICT` / `UOW_COMMIT_FAILED`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_sql_constraint_rejection_matrix.py -p no:cacheprovider
  ```

#### 17. Higher Operad Laws & Arbitrary N-Node Cyclic Graph Rejection (Landau Class 1 & 2)

- **File**: [`tests/integration/test_higher_operad_laws_and_cyclic_graphs.py`](../tests/integration/test_higher_operad_laws_and_cyclic_graphs.py)
- **What it tests**:
  1. Arbitrary $N$-agent circular workflow loops ($N \in [2, 8]$) are rejected with `is_valid=False`, empty topological sorts, and populated cycle paths.
  2. Out-of-bounds slot index bindings ($s \ge k$) fail composition with `SLOT_INDEX_OUT_OF_BOUNDS`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_higher_operad_laws_and_cyclic_graphs.py -p no:cacheprovider
  ```

#### 18. Cryptographic Manifest Signature Adversarial Attack Matrix (Landau Class 2)

- **File**: [`tests/integration/test_manifest_signature_adversarial_matrix.py`](../tests/integration/test_manifest_signature_adversarial_matrix.py)
- **What it tests**:
  1. Rejects verification with attacker forged secret keys (`SIGNATURE_VERIFICATION_FAILED`).
  2. Rejects metadata tampering on epoch or signer ID fields.
  3. Rejects truncated or partial signature hex strings.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/integration/test_manifest_signature_adversarial_matrix.py -p no:cacheprovider
  ```

---

### B. Unit & Boundary Fuzzing Suites

#### 1. Domain Value Objects Boundary & Type Fuzz

- **File**: [`tests/unit/test_domain_value_objects_boundary_and_fuzz.py`](../tests/unit/test_domain_value_objects_boundary_and_fuzz.py)
- **What it tests**:
  - Rejects non-string types (`int`, `float`, `bool`, `None`, `dict`) passed to `_BaseId` subclasses.
  - Rejects giant strings (> 512 characters) and whitespace-only identifiers.
  - Rejects non-integer types (floats, bools), negative indices, and inverted coordinates in `SourceByteSpan`.
  - Rejects malformed or non-hex digests in `ContentDigest`.
  - Verifies abstract `DomainEventV3` base interface, property accessors, and `to_dict()` serialization.
  - Verifies `OewasDomainError` exception hierarchy formatting with source locus.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_domain_value_objects_boundary_and_fuzz.py -p no:cacheprovider
  ```

#### 2. Markdown Parser Edge-Case Fuzz & AST Recovery

- **File**: [`tests/unit/test_markdown_parser_edge_case_fuzz.py`](../tests/unit/test_markdown_parser_edge_case_fuzz.py)
- **What it tests**:
  - Unclosed / unterminated code fences $\to$ preserves document losslessly as prose leaf nodes without parser crash.
  - Malformed YAML syntax $\to$ returns typed `MALFORMED_OEWAS_DECLARATION` with line locus.
  - Scalar / list YAML payloads $\to$ returns typed `MALFORMED_OPERATION_BLOCK`.
  - Invalid enum facets $\to$ returns typed error with invalid literal.
  - Corrupt binary / non-UTF-8 bytes $\to$ returns typed `ENCODING_ERROR`.
  - Interleaved multi-language fences (`python`, `bash`, `oewas.*`) $\to$ exact byte span slice preservation.
  - **Unicode Multi-Byte Span Accuracy (Soviet Patch 1)**: asserts that multi-byte UTF-8 symbols (Φ₁, 🚀, ∇²ψ) do not shift subsequent byte spans.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_markdown_parser_edge_case_fuzz.py -p no:cacheprovider
  ```

#### 3. Core Domain Value Objects

- **File**: [`tests/unit/test_domain_value_objects.py`](../tests/unit/test_domain_value_objects.py)
- **What it tests**: Strongly typed value object equality, immutability, and hashing.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_domain_value_objects.py -p no:cacheprovider
  ```

#### 4. Lossless Markdown Parser

- **File**: [`tests/unit/test_lossless_markdown_parser.py`](../tests/unit/test_lossless_markdown_parser.py)
- **What it tests**: Exact byte-span extraction across markdown headings, prose, and OEWAS code blocks.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_lossless_markdown_parser.py -p no:cacheprovider
  ```

#### 5. Application Railway Handlers

- **File**: [`tests/unit/test_application_railway_handlers.py`](../tests/unit/test_application_railway_handlers.py)
- **What it tests**: Railway Oriented Programming (ROP) command and query execution.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_application_railway_handlers.py -p no:cacheprovider
  ```

#### 6. SkillDocumentV3 Aggregate

- **File**: [`tests/unit/test_skill_document_v3_aggregate.py`](../tests/unit/test_skill_document_v3_aggregate.py)
- **What it tests**: Aggregate state transitions and operation indexing.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_skill_document_v3_aggregate.py -p no:cacheprovider
  ```

#### 7. Lossless Markdown Parser Property & Conservation Laws (Landau Class 1)

- **File**: [`tests/unit/test_markdown_parser_property_laws.py`](../tests/unit/test_markdown_parser_property_laws.py)
- **What it tests**:
  1. Gap-Free Span Contiguity: `node[i+1].start == node[i].end` across 10 generated document templates.
  2. Algebraic Byte Conservation: `b"".join(node.span_bytes) == raw_bytes`.
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/unit/test_markdown_parser_property_laws.py -p no:cacheprovider
  ```

---

### C. Clean Architecture Guard Suite

#### Clean Architecture AST Boundaries

- **File**: [`tests/architecture/test_clean_architecture_ast_boundaries.py`](../tests/architecture/test_clean_architecture_ast_boundaries.py)
- **What it tests**: AST-level import analysis enforcing that `domain/` and `application/` directories have **0 forbidden imports** (no `fastapi`, `sqlite3`, `httpx`, `yaml`, or `starlette` leaks inside domain).
- **Run command**:

  ```powershell
  python -m pytest omega_engine_operads/tests/architecture/test_clean_architecture_ast_boundaries.py -p no:cacheprovider
  ```

---

## 3. Quick-Run Discipline

Run the per-file commands above one at a time. Do not pass a test directory or a long list of files to one `pytest` invocation. For example:

```powershell
python -m pytest omega_engine_operads/tests/unit/test_application_railway_handlers.py -p no:cacheprovider
python -m pytest omega_engine_operads/tests/integration/test_outbox_transaction_atomicity.py -p no:cacheprovider
python -m pytest omega_engine_operads/tests/architecture/test_clean_architecture_ast_boundaries.py -p no:cacheprovider
```

---

## 4. Techne Code Soviet Builder Hardening & Mutation Verification Report

### Theoretical Minimum Matrix

| # | Invariant | Break Mode | Witness Assertion | Production Mutation |
| --- | --- | --- | --- | --- |
| 1 | SQLite PRIMARY KEY & unique constraints abort transactional catalog/event writes upon collision. | Silent overwrite or corrupted journal. | `res.is_err` with `UOW_COMMIT_FAILED` / `IDEMPOTENCY_CONFLICT`. | In `sqlite_unit_of_work.py`, replace `INSERT INTO catalogs_v3` with `INSERT OR REPLACE`. |
| 2 | Out-of-bounds operad slot index $s \ge k$ is strictly rejected by the composition adapter. | Silent execution on unindexed slots. | `res.is_err` with `SLOT_INDEX_OUT_OF_BOUNDS`. | In `higher_operad_adapter.py`, omit `if slot_idx >= len(root_op.inputs)` check. |
| 3 | Cryptographic HMAC manifest signatures must reject forged keys and altered metadata in constant time. | Forged envelopes accepted or timing leaked. | `res.is_err` with `SIGNATURE_VERIFICATION_FAILED`. | In `manifest_signature_provider.py`, replace `hmac.compare_digest` with `return Ok(True)`. |
| 4 | Markdown parser spans form a gap-free partition with strict byte conservation $\bigoplus_i \text{node}_i = \text{raw}$. | Dropped trailing prose or multi-byte drift. | `reconstructed == raw_bytes` and `span[i+1].start == span[i].end`. | In `markdown_parser_adapter.py`, omit trailing prose leaf node append. |

### Mutation Verification Evidence (Mandatory Lev Landau Discipline)

| Test | Mutation Applied | Red Under Mutation? | Failure Message Observed | Green After Revert? |
| --- | --- | --- | --- | --- |
| `test_duplicate_catalog_id_primary_key_rejection` | `INSERT INTO` $\to$ `INSERT OR REPLACE` in `sqlite_unit_of_work.py` | **YES** (Exit 1) | `AssertionError: False is not true : Duplicate catalog_id MUST trigger a storage transaction failure` | **YES** (Exit 0) |
| `test_out_of_bounds_slot_binding_rejection` | Omitted slot index bounds check in `higher_operad_adapter.py` | **YES** (Exit 1) | `AssertionError: False is not true` | **YES** (Exit 0) |
| `test_wrong_key_rejection` | Bypassed HMAC check in `manifest_signature_provider.py` | **YES** (Exit 1) | `AssertionError: False is not true` | **YES** (Exit 0) |
| `test_property_gap_free_partition_over_generated_corpus` | Omitted trailing prose append in `markdown_parser_adapter.py` | **YES** (Exit 1) | `AssertionError: 0 != 70 : Template 0 total parsed bytes 0 != raw length 70` | **YES** (Exit 0) |
