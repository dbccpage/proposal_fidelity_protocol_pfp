---
name: lib-master-librarian
description: "Navigate and search the whole repo (FTS5 plus TF-IDF), govern publication skeletons, claim ledgers and archives."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# Master Librarian of the Anomalon Research Estate

The `lib-master-librarian` skill is the **Single Point of Entry (SPOE)** for searching, navigating, auditing, structuring, and verifying all documents, historical archives, mathematical frameworks, Lean 4 obligations, and code loci across the entire Anomalon monorepo. It operates under **$O(1)$ Filter–Select–Read (FSR) discipline** to prevent context window thrashing.

---

## 1. Unified FTS5 & Semantic Estate Search Engine

When searching for research, proofs, concepts, or literature across the entire estate:

```text
                           [QUERY / SEARCH REQUEST]
                                      │
                                      ▼
    ┌───────────────────────────────────────────────────────────────────────────┐
    │ STAGE 1: FILTER via Hybrid FTS5 & Concept Search Engine (< 15ms)          │
    │ python -m omega_engine_operations.entrypoints.cli search "<query>"        │
    │        --estate all|published|library|encyclopedia|crates|lean4|python    │
    │ Target DB: omega_engine_databases/ (master SQLite FTS5 + TF-IDF)          │
    └───────────────────────────────────────────────────────────────────────────┘
                                      │ Target Document IDs & File Paths
                                      ▼
    ┌───────────────────────────────────────────────────────────────────────────┐
    │ STAGE 2: SELECT via Frontmatter YAML (~500 tokens)                        │
    │ - Inspect ONLY lines 1–30 of target `.md` files (`view_file`)             │
    │ - Verify `summary`, `key_concepts`, `prerequisites`, `omega_relevance`    │
    └───────────────────────────────────────────────────────────────────────────┘
                                      │ Verified Target Line Range
                                      ▼
    ┌───────────────────────────────────────────────────────────────────────────┐
    │ STAGE 3: READ Target Line Range                                           │
    │ - Read ONLY the specific file line range required for proof/code          │
    └───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Whole-Repo Estate Navigation & Routing Table

Navigate the monorepo without dumping file trees into context:

| Estate / Query Class | Preferred Index / Entry Point | Domain Scope & Rules |
| :--- | :--- | :--- |
| **All Monorepo Estates** | `omega_engine_operations/entrypoints/cli.py` | Full-text & TF-IDF cross-estate query router |
| **Published CODA Papers** | `omega_engine/research/published/_indexes/published_master_index.yaml` | 13-section identical skeletons, 7-class claim ledgers |
| **Live Literature (`LIB-*`)** | `omega_engine_library/library_master_index.yaml` | Raw and parsed literature monographs |
| **Historical Archive (`ARC-*`)** | `omega_engine/research/library/_archive/archive_master_index.yaml` | Pre-consolidated research, DTOs, and legacy notes |
| **Encyclopedia Finite Graph** | `omega_engine/research/encyclopedia/library/objects.ndjson` | Finite Library graph, ENC bindings, and typed objects |
| **Lean 4 Proof Kernels** | `omega_engine/lean4/lakefile.lean` | Formal proof obligations & sorry audits |
| **Domain Prompt Custody** | `omega_engine_library/prompts/` | Domain campaigns & looping goal prompt manifests |
| **Rust Crates & Solvers** | `omega_engine/crates/` | Rust PROD implementations & solver crates |
| **Python Operations Suite** | `omega_engine_operations/` | Controllers, domain models, infrastructure, use cases |

---

## 3. CODA Publication Estate & Paper Skeleton Governance

Every paper across every research program MUST adhere strictly to the **MUB & OE-034 Standard**:

### A. Folder & File Naming Rules

1. **Research Program Syntax**: `omega_engine/research/published/NNN_<lowercase_slug>/` (`NNN` from `000` to `899` with **one single underscore**).
2. **Dedicated Paper Directory Structure**:

   ```text
   omega_engine/research/published/NNN_<programme_slug>/<paper_slug>/
   ├── <paper_slug>.md                       # Monograph Paper (13-section skeleton; NO inlined changelog/ledger)
   ├── <paper_slug>_change_log.md            # Version Change Log (Mandatory companion)
   ├── <paper_slug>_claim_ledger.md          # 7-Class Typed Claim Ledger (Mandatory companion)
   ├── <paper_slug>_math_spine.md            # Extended Prose Proofs (Optional 4th monograph file)
   ├── docs/                                 # update_packet.md, red_team_dialogue_raw.md, provenance.md
   ├── code/                                 # <claim_id>_test.py executable property tests & artifact bundles
   ├── evidence/                             # SHA256SUMS, manifest.json, replay_receipt.json
   └── public_export/                        # Self-contained public export package (README.md, Makefile)
   ```

### B. Mandatory 13-Section Paper Skeleton

1. **Header / Metadata Block** (Canonical ID, Title, Version `v1.0`, CC-BY-4.0, `AuthorityEffect: None`)
2. **Omega Engine Primitives Table** (11 Primitive slots)
3. **Core Dependency Topology Diagram**
4. **Refusal Box / Anti-Kernel** ($\boxed{\text{No automatic upgrade to [Non-Claims].}}$)
5. **Abstract & Why a Researcher Should Care**
6. **Section 1: Introduction & Related Work**
7. **Section 2: Mathematical Foundation & Primitive Differences**
8. **Section 3: Core Theorems & Structural Results**
9. **Section 4: Worked Example & Falsifiability**
10. **Section 5: Code / Lean4 Mechanization & Verification**
11. **Section 6: Discussion & Non-Claims**
12. **References**
13. **Claim-ID Body Index Table**

### C. 7-Class Claim Ledger Breakdown

Every claim in `{stem}_claim_ledger.md` MUST be assigned one of the 7 canonical types:

- `LEAN4_PROOF`: Formalized in `omega_engine/lean4/`.
- `PROSE_PROOF`: Inline markdown or `{stem}_math_spine.md`.
- `CODE_DEMO_PYTHON`: Executable Python test or Pydantic model in `code/`.
- `CODE_DEMO_RUST`: Unit/integration test in `omega_engine/crates/`.
- `CODE_DEMO_JS_TS`: Web UI component.
- `WORKED_EXAMPLE`: Step-by-step numerical or symbolic instance.
- `THEOREM_DEFINITION`: Formal theorem, axiom, or definition statement.

---

## 4. Encyclopedia Finite Library Graph & ENC Bindings

1. **Graph Invariant Audits**: Scans `objects.ndjson` and per-paper ENC bindings for:
   - Missing typed objects or missing morphism endpoints.
   - Duplicate claims without distinct witness hashes.
   - Projection loss and raw uncontracted nulls.
2. **Paper $\leftrightarrow$ ENC Identity Synchronization**:
   - Synchronizes `omega_engine/lean4/research_programs/index.yaml` and `claim_index.yaml`.
   - Preserves Borges persona internally: reports structural defects, never invents un-witnessed mathematical entities.

---

## 5. Lean 4 Lake Binding, Path Resolution & Proof Hygiene

1. **Resolution of Proof References**:
   - Maps paper claims to formal modules under `omega_engine/lean4/research_programs/`.
   - Audits `lakefile.lean` target resolution: ensures roots match leaf module names and `srcDir` paths.
2. **LGGR Research Program Home Invariants**:
   - LGGR Papers 019, 020, 021 map strictly to `008_engine_runtime/` (`core_l020_*`, `core_l023_*`, `core_l025_*`).
3. **Triad Independence & Ceiling Enforcement**:
   - Preserves three independent verification gates: `LEAN_PATH_BOUND`, `LEAN_LAKE_BUILDS`, `LEAN_SORRY_FREE`.
   - Prohibits vacuous premise exploitation (`VACUOUS_PREMISE_THEOREM`) and enforces `MECHANIZED_CORE_ONLY` status ceilings.

---

## 6. Domain Campaign & Goal Prompt Custody

1. **Prompt Repository Locus**:
   - Maintains active and looping goal prompts under `omega_engine_library/prompts/` and `coda_university/coda_library/prompts/` (e.g. `qm_looping_goal_prompt.md`, `q_looping_goal_prompt.md`, `fable_gtla_prompt.md`, `coda_codaq_solver_of_solvers_looping_goal_prompt.md`).
2. **Custody Protocol**:
   - Every goal prompt must explicitly declare `AuthorityEffect: None`.
   - Maintains hypothesis ledgers and points strictly to canonical contracts without speculative claim inflation.

---

## 7. Historical Archive Governance & Mining (`_archive/`)

Governs historical research assets under `omega_engine/research/library/_archive/`:

1. **Four-Axis Mining Protocol**:
   - `DELETE`: True scratch/build junk (`__pycache__`, `.pyc`, empty `.log`). Never delete historical paper monographs.
   - `ZIP_BACKUP`: Compress large obsolete raw trees to a dated root `.zip`.
   - `BUILD_SCHEMA`: Extract legacy DTOs/solvers into active crate or operational domain packages.
   - `PUSH_TO_LIBRARY`: Promote verified historical literature into live `omega_engine_library/markdown/`.

---

## 8. Session Verification & Quality Gates Checklist

Execute the standard verification gates prior to completing turns or submitting PRs:

| Phase | Gate / Objective | Verification Command |
| :--- | :--- | :--- |
| **Phase 0: Smoke Test** | Python import integrity | `python -c "import omega_engine_operations"` |
| **Phase 1: Local CI** | Deterministic gate verification | `python -m omega_engine_operations.entrypoints.cli` |
| **Phase 2: Type Check** | Static typing & type bounds | `pyright .` / `cargo check` |
| **Phase 3: Lint & Encoding** | Markdown & UTF-8 delinting | `RULE_MARKDOWN_DELINTING_001` (0 warnings/errors) |
| **Phase 4: Test Suites** | Full test execution & coverage | `pytest` / `cargo test` |
| **Phase 5: Security** | Secret & API key leak scan | `grep -rn "sk-" .` (0 matches) |
| **Phase 6: Diff Audit** | Clean Architecture boundary audit | `python -m omega_engine_operads.frontend.cli.python_dev_cli` |
| **Phase 7: Operad Gate** | Operad structural registry check | `python .agents/operad/validate_operad.py` |
