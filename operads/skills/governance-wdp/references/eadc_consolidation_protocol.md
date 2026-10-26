# Encyclopedia Anomalanica (EADC) & Atlas Consolidation Protocol

**AuthorityEffect:** None.

This reference documents the procedural workflow and structural standards for consolidating materials within `omega_engine_atlas/coda_atlas/`.

---

## 1. EADC Decimal Classification & Addressing

- **Library Coordinates**: All coordinates must follow the EADC standard:
  `EA:FFF.SSS.BBB` (Floor.Shelf.Book).
- **Empty Entities**: Empty shelves and floors (e.g. `EA:002.000`, `EA:003.000`) are valid, addressable catalog entities with declared admission and exit contracts.
- **Lifecycle Model**: The 5-state lifecycle model (`planned`, `scaffold`, `active`, `consolidated`, `certified`) must be explicitly declared for all book entries.

---

## 2. Decoupled Identifier Separation

Strictly separate:

- **EADC Address**: Library coordinate in `atlas_catalog.yaml` (`EA:FFF.SSS.BBB`).
- **L1 Component Code**: Mathematical system identifier (e.g. `CODA_FOC`).
- **Source ID (`SRC-*`)**: Raw internal manuscript in `source_disposition.yaml`.
- **Library ID (`LIB-*`)**: External literature in `coda_library/markdown/`.
- **Claim ID**: Atomic claim key (`BXXX:CYYY`).

---

## 3. Mandatory 6-Section Chapter Structure

Every book chapter file under `book/` must implement:

1. `## 1. Entry Structure`
2. `## 2. Admitted Constructions`
3. `## 3. Surviving Invariants & Key Results`
4. `## 4. Exit Structure`
5. `## 5. Explicit Nonclaims`
6. `## 6. Primary Distillation Sources`

Ensure blank lines follow all markdown headers to satisfy clean linting with 0 warnings.

---

## 4. Centralized Gap & Source Disposition Integrity

- **Root Gap Register**: Gaps belong **only** to root `gap_register.yaml` at floor, shelf, or inter-book boundaries. No gap is owned by an individual book.
- **Source Hashes**: Sources in `source_disposition.yaml` require verified SHA-256 hashes and exact repository or bibliographic witnesses. Never mark sources deletable during active consolidation.

---

## 5. Genesis Citation & Scope Discipline

- External Genesis reference is strictly pinned to `dbccpage/19L57G1@sealed-derivation-v1` (`3100c4e`). Never copy `prompt/`, `paper/`, `code/derivation/`, `lean4/Derivation/`, or `artifacts/` from `19L57G1`.
- A compiling Lean 4 theorem certifies formal validity within CIC only; it does not establish physical truth, ontology, or agency.

---

## 6. Research Paper Package & Notebook Discipline

- **Local Lean 4 Linkage**: Claim ledgers in self-contained paper directories must bind directly to local Lean 4 declarations (`lean4/`). Legacy `ENC-*` codes, `PaperAE*` prefixes, and dead external repository links are prohibited.
- **Companion Notebook Naming**: Jupyter companion notebooks under `jupyter_notebooks/` must use canonical `<paper_num>_<slug>.ipynb` naming. The prefixes `reviewer_` and `qm` (which misleadingly connotes quantum mechanics) are forbidden.
- **CWD-Independent Headless Execution**: Notebooks must dynamically resolve paths relative to their own file location and evaluate completely under `nbclient` without manual intervention.
- **Lake Build Directory ("b")**: Lake packages may configure `buildDir := "b"` to prevent Windows 260-character MAX_PATH path overflow; this directory is build scratch and excluded from version control.
- **Linter Honesty**: Never disable or silence markdown linters with suppression pragmas (`markdownlint-disable`). Formatting must legitimately satisfy line-length and style constraints.

---

## 7. Symbol Game & MSS-N Tower Monograph Integration Invariant

Whenever new monographs, research chapters, or theoretical derivations are ingested into `research/mssn_sn_tower/`, agents must execute a 5-point synchronized integration pass:

1. **Operational Toolkits (`toolkits/`):**
   - Extract actionable state machines, incremental lexers, and execution contracts into `toolkits/XX_<name>.md`.
   - Update `toolkits/readme.md` with the new toolkit entry.

2. **Encyclopedia Cards (`theorems/cards/`):**
   - Extract formal mathematical definitions, bounds, and theorems into discrete cards (`ENC-*`) with YAML frontmatter.
   - Declare explicit Lean 4 obligations (`lean_status`, `lean_refs`, `blocker`).
   - Increment the total card count and insert card references in `theorems/readme.md`.

3. **Wire Packet Synchronizations (`packets/`):**
   - Define exact packet wire schemas (`omega.*.v1`), DTO types, and typed error opcodes in the corresponding level file (`packets/<level>_packets.md`).

4. **Master Atlas Source Retention (`_archive/source_inputs_2026_09_25/atlas_direct/`):**
   - Retain complete atlas-source markdown in `research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/` to preserve narrative context, historical derivations, and claim ceilings.
   - Catalog the new volume in `research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/readme.md`.

5. **Master SPOE Synchronization (`mssn.md`):**
   - Update `research/mssn_sn_tower/mssn.md` across Phase 0 (theorems/cards), Phase 0.5 (atlas monographs), Phase 3 (packet wire encodings), and Phase 9 (operational toolkits).
   - Enforce zero UTF-8 BOM (`\xef\xbb\xbf`) and valid internal links.
