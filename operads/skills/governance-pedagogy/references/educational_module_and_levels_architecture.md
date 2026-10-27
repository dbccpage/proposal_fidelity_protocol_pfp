# Educational Module and Levels Architecture Discipline

AuthorityEffect: None.

## 1. Educational Module Renumbering & Propagation Protocol

Educational modules under `education/documentation/` follow strict decimal stratification prefixes (`NNN_<name>`). When a module prefix is modified (e.g., shifting $160 \to 170$ to insert a new bounded context):

1. **Atomic Directory Rename**:
   Use `git mv` to rename the parent folder:
   `git mv documentation/NNN_<name> documentation/MMM_<name>`

2. **Track Directory Cascade Propagation**:
   All internal numbered curriculum tracks must be renumbered to maintain track ID parity:
   `curriculum/NN00_<slug> -> curriculum/MM00_<slug>`
   `curriculum/NN10_<slug> -> curriculum/MM10_<slug>`

3. **Intra-Module Link & Header Reconciliation**:
   - Update track references and directory table links in `documentation/MMM_<name>/curriculum/README.md`.
   - Update individual track `README.md` and lesson header frontmatter to match the new track IDs.
   - Assert zero dangling links to the old `NNN` prefix.

---

## 2. Levels Catalog Architecture

Every numbered educational module supporting progressive mastery should maintain a `levels/` directory containing:

### A. Manuscript Truth Index (`levels/README.md`)
- **Metadata Frontmatter**: `documentation_contract: symbol-game-documentation/v1`, `authority_effect: "None"`, and `source_paths`.
- **Architectural Stratification**: 4 to 5 structural regimes grouping the level progression.
- **Mermaid Progression DAG**: Visual sequence from Level 00 to the apex verification boundary.
- **Canonical Level Registry Table**: Columns for `Level`, `Title`, `Regime`, `Primary Module / Contract`, and `Key Invariant & Scope`.
- **Claim Hygiene Quadrant**: Explicit breakdown of:
  1. What it supports.
  2. What it does not support.
  3. The narrowest defensible claim.
  4. The next test needed.

### B. Individual Level Specifications (`level_NN_<slug>.md`)
Each level document must contain:
1. **Frontmatter Contract**: `level: N`, `status: active`, `authority_effect: "None"`.
2. **Schematic Architecture**: Diagram illustrating the primary data flow or component interactions.
3. **Mathematical Formalism**: Exact definitions, invariant equations, and state spaces.
4. **Implementation References**: Pointers to canonical Python modules, Rust crates, or Lean 4 kernels.
5. **Target Checkers & Falsifiers**: Concrete test descriptions or code snippets reproducing rejections.
6. **Scope & Claim Boundary Table**: Two-column matrix explicitly defining:
   - **CAN Show in this Level**: Bounded model properties and local tests.
   - **CANNOT Show in this Level**: Unproved generalizations, empirical transfers, or out-of-scope assumptions.

---

## 3. 5-Cell Laboratory Workbench Anatomy

In accordance with `LabEngineer` standards, all companion Jupyter notebooks (`.ipynb`) in curriculum tracks must adhere to a 5-step cell sequence:

1. **Cell 1: Environment Preflight Check**:
   - Asserts runtime interpreter version (`sys.version_info >= (3, 10)`).
   - Validates that required dependencies or path hooks are initialized.
2. **Cell 2: Domain Model & Invariant Definition**:
   - Declares domain dataclasses or contracts with explicit boundary validation methods.
3. **Cell 3: Prediction Gate**:
   - Requires explicit learner commitment to an expected outcome string prior to running dynamic tests:
     `prediction = "..."`
     `assert prediction == "..."`
4. **Cell 4: Dynamic Execution & Assertions**:
   - Executes the active computational pipeline.
   - Asserts state updates and invariants without silent failure fall-throughs.
5. **Cell 5: Falsifier & Counterexample Gate**:
   - Executes an intentionally malformed or hostile input.
   - Asserts that the system raises the expected typed exception or returns a refusal code.

---

## 4. Prose Decoupling and Claim Discipline

- **Prose Budget in Notebooks**: Markdown cells in notebooks must remain strictly $\le 25$ lines. In-depth theoretical exposition belongs in companion `concepts/` documents.
- **Epistemic Taxonomy**: All lessons must observe the 8-tag epistemic taxonomy:
  `[Declared]`, `[Model]`, `[Executed]`, `[Tested]`, `[Pinned]`, `[Formal]`, `[External]`, and `[Open]`.
- **Claim Discipline**: Never describe toy implementations or bounded test runs as mathematical proofs or generalized truths.
