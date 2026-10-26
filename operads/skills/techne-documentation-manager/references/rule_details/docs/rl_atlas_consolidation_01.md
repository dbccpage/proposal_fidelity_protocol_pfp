# Detailed definition: Atlas Consolidation & EADC Addressing (1)

**AuthorityEffect:** None.

Parent: [Atlas Consolidation & EADC Addressing](../../../../../rules/docs/rl_atlas_consolidation.md). Load for the matching predicate, not every task.

---
paths:
- "omega_engine_atlas/**"
---

# Rule: Encyclopedia Anomalanica (EADC) & Atlas Consolidation Invariants

**AuthorityEffect:** None.

All agent operations within `omega_engine_atlas/coda_atlas/` and source consolidation passes must strictly comply with the following invariants. Detailed multi-step integration procedures reside in [`governance-wdp`](../../../../governance-wdp/references/eadc_consolidation_protocol.md).

---

## 1. EADC Decimal Addressing & Identifier Separation

- All catalog coordinates must follow the EADC standard: `EA:FFF.SSS.BBB` (Floor.Shelf.Book).
- Empty shelves and floors (`EA:002.000`) are valid addressable catalog entities.
- Strictly separate:
  - **EADC Address**: Library coordinate in `atlas_catalog.yaml` (`EA:FFF.SSS.BBB`).
  - **L1 Component Code**: Mathematical system identifier (e.g. `CODA_FOC`).
  - **Source ID (`SRC-*`)**: Raw internal manuscript in `source_disposition.yaml`.
  - **Library ID (`LIB-*`)**: External literature in `coda_library/markdown/`.
  - **Claim ID**: Atomic claim key (`BXXX:CYYY`).

---

## 2. Structural Chapter & Gap Register Invariants

- Every book chapter under `book/` must implement the mandatory 6-section structure (Entry Structure, Admitted Constructions, Surviving Invariants, Exit Structure, Explicit Nonclaims, Primary Distillation Sources) with clean markdown headers.
- Gaps belong **only** to root `gap_register.yaml` at floor, shelf, or inter-book boundaries. No gap is owned by an individual book.

---

## 3. Scope & Naming Discipline

- External Genesis references are strictly pinned to `dbccpage/19L57G1@sealed-derivation-v1` (`3100c4e`). Never copy `prompt/`, `paper/`, `code/derivation/`, `lean4/Derivation/`, or `artifacts/` from `19L57G1`.
- Jupyter companion notebooks under `jupyter_notebooks/` must use canonical `<paper_num>_<slug>.ipynb` naming. The prefixes `reviewer_` and `qm` are forbidden.
- Lowercase Filename Invariant: All files in the atlas estate must strictly use lowercase letters in filenames (e.g. `atlas.md`, `coda_and_lggr_repo_wide_foundation.md`, `repo_wide_coda_lggr_audit_report.md`). The only permitted exception is `README.md`.
- Claim ledgers in self-contained paper directories must bind directly to local Lean 4 declarations (`lean4/`); legacy `ENC-*` codes and dead external links are prohibited.

---

## 4. Test Harness & Contract Path Portability

- Test suites, verification harnesses, and contract parsers that resolve documentation chapters (e.g. `omega_engine_education/documentation/`) must resolve 3-digit EADC numbering conventions (`014_normal_forms`, `003_minimal_symbol_system_n_mssn`).
- Hardcoding legacy unpadded 2-digit prefixes (`13_normal_forms`, `15_normal_forms`) is prohibited in test harnesses. Test path resolvers must use canonical 3-digit paths with dynamic discovery fallbacks (`path.glob("*_normal_forms/contracts_normal_forms")`) to remain resilient across atlas re-indexing passes.
