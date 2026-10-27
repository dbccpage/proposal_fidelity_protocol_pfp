# Detailed definition: Documentation Estate & Submodule Layout (1)

**AuthorityEffect:** None.

Parent: [Documentation Estate & Submodule Layout](../../../../../rules/docs/rl_documentation_estate_and_submodule_layout.md). Load for the matching predicate, not every task.

# Rule: Documentation Estate, Submodule Layout & Link Relativity

**AuthorityEffect:** None.

This rule codifies documentation estate subdirectory isolation, curriculum storage port encapsulation, educational documentation submodule layout standards, dynamic test suite submodule root discovery, and relative Markdown link discipline across the workspace. Full procedural details reside in [`governance-clean-arch`](../../../../governance-clean-arch/SKILL.md) and [`governance-pedagogy`](../../../../governance-pedagogy/SKILL.md). For semiotic carrier quad-axis separation and pilot estate decoupling, see [`rl_pilot_estate_decoupling.md`](../../../../../rules/docs/rl_pilot_estate_decoupling.md).

---

## 1. Bounded Context Documentation Subdirectory Layout (`RULE_BOUNDED_CONTEXT_DOCS_001`)

> **Package Cleanliness & `_docs/` Isolation:**
>
> 1. **Zero Loose Documentation in Package Roots:** Operational packages and bounded contexts (e.g. under `operations/`) must never leave standalone markdown specification, ownership, or mapping documents loose in the package root.
> 2. **Canonical `_docs/` Subdirectory:** All module documentation, semantics maps, architecture guides, and ownership ledgers must reside in a dedicated `_docs/` subdirectory (e.g., `operations/skill_operad/_docs/`).

---

## 2. Documentation Path & Curriculum Storage Invariants (`RULE_CURRICULUM_STORAGE_DOCS_001`)

> **Documentation Path Fallback & Storage Port Invariants:**
>
> 1. **Zero-Padded Documentation Directories:** When resolving subdirectories under `documentation/`, verifiers, notebook runners, and test suites MUST account for canonical 3-digit zero-padded folder names (e.g., `001_oegen`, `002_oesn`, `003_oemssn`, `004_oepfp`, `014_normal_forms`) with fallback to unpadded numbers for legacy fixture/notebook compatibility.
> 2. **Curriculum Storage Port Encapsulation:** Lesson template generation logic belongs in `education/education_app/use_cases/curriculum/compiler.py`, and file system persistence MUST route through `CurriculumStoragePort` (`CurriculumFileSystemStorageAdapter`), keeping CLI generator scripts thin triggers.

---

## 3. Documentation Estate Index Scope & Curriculum Generation Discipline (`RULE_DOCS_INDEX_DISCIPLINE_001`)

> **Bounded Documentation Updates & Prohibitions on Speculative Lesson Synthesis:**
>
> 1. **Index & Hub Alignment:** When linking or documenting exploratory research projects (under `projects/`) in educational hubs (e.g. `210_engine_projects_and_monographs/`), agents must update the project catalogue in `README.md` without speculatively mutating high-level system topology diagrams or master indices unless explicitly instructed.
> 2. **No Speculative Curriculum Generation:** Agents must never invent or generate ad-hoc pedagogical curriculum lessons (`concepts/lesson_*.md`) or syllabus extensions unless specifically requested by the user. Formal curriculum generation must route through `CurriculumStoragePort` and compiler.
> 3. **Clean Windows Execution Standard:** When performing file maintenance via scripts on Windows, agents must use dedicated temporary scripts or explicit string literals avoiding unescaped backslash interpolation in `py -3.12 -c`.

---

## 4. Education Documentation Submodule Layout Standard (`RULE_EDUCATION_DOCS_SUBMODULE_LAYOUT_001`)

> **Canonical Submodule Directory Structure:**
>
> Numbered documentation modules in `education/documentation/` (such as `001_oegen`, `002_oesn`, `003_oemssn`, `004_oepfp`, `014_normal_forms`, etc.) must adhere to the four canonical documentation pillars and supporting operational assets:
>
> **The Four Educational Pillars:**
> 1. `grammar/`: Formal EBNF grammars (`*.ebnf`), dialect specifications, and syntax reference guides.
> 2. `papers/`: Formally structured research monographs and pre-print packages (`papers/<id>/paper.md`, `paper_change_log.md`, `paper_claim_ledger.md`). Single monolithic guides outside `papers/` are deprecated once mirrored into `papers/`.
> 3. `levels/`: Sequential discrete stages (`level_00_*.md` through `level_{NN}_*.md`) indexed by `README.md`, unified with Two Boxed Laws, state machine formalisms, and claim hygiene quadrants.
> 4. `domains/`: Concrete external domain integrations (e.g. `databases/`, `protocols/`, `physics/`) and bridge specifications.
>
> **Supporting Operational Directories:**
> 5. `lean4/`: Mechanized Lean 4 proof kernels, inductive definitions, and verified theorems.
> 6. `contracts/`: Machine-verifiable contract schemas (`contract.yaml`, `*.yaml`), failure modes, entry preconditions, and winning conditions.
> 7. `wire_representations/`: Operational wire specifications, token legends, syntax profiles (e.g. Tier H, Tier D, `mss-boundary-v1`), and AST/source recovery invariants.
> 8. `code/`: Executable diagnostic tools, checkers, and reference parsers (e.g., `check_mssn.py`, conformance test cases).
> 9. `code/tests/`: Targeted automated test suites and regression tests validating local code tools.
>
> **Test Suite Submodule Root Dynamic Resolution Invariant:**
> Automated test suites located under `code/tests/` must dynamically discover submodule and repository roots:
> - Do not hardcode static negative depth indexing (`parents[1]`), which fails when tests are moved into `code/tests/`.
> - Use dynamic resolution scanning parents for `levels`/`grammar` markers and repository markers (`.git`/`pixi.toml`).
>
> **Prohibited Legacy Fragmentation:**
> Creating or retaining ad-hoc decomposed directories (`applications/`, `core/`, `realizations/`, `verification/`) directly under education submodules is prohibited; all content must be consolidated into `levels/` and `domains/`.
>
> **Submodule Pillar Migration & Test Suite Path Parity:**
> When educational modules are refactored into the canonical four pillars, all test suites, fixtures, and audit runners referencing legacy paths must be updated synchronously to point to canonical paths (`levels/level_00_*.md`).

---
