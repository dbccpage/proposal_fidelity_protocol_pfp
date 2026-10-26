# Detailed definition: Research Papers, Monographs & Formal Mechanization (1)

**AuthorityEffect:** None.

Parent: [Research Papers, Monographs & Formal Mechanization](../../../../../rules/papers/rl_research_paper_and_monograph_packaging.md). Load for the matching predicate, not every task.

# Rule: Research Paper, Monograph & Formal Mechanization Invariants

**AuthorityEffect:** None.

This rule codifies hermetic paper package verification, code generator authority, Lean 4 proof kernel census standards, exact mathematical solvers, and comprehensive claim-code mapping. Cross-reference publication rubric: [`rl_coda_publication_and_monograph_specifications.md`](../../../../../rules/papers/rl_coda_publication_and_monograph_specifications.md), evaluator discipline: [`rl_paper_epistemic_evaluator_and_namespace_discipline.md`](../../../../../rules/papers/rl_paper_epistemic_evaluator_and_namespace_discipline.md), and deposit packaging fences: [`rl_paper_deposit_release_envelope_and_manifest_fences.md`](../../../../../rules/papers/rl_paper_deposit_release_envelope_and_manifest_fences.md).

---

## Paper Standalone Archive Isolation & Test Execution Invariant (`RULE_PAPER_ARCHIVE_ISOLATION_001`)

> **Hermetic Paper Package Verification:**
>
> 1. **Zero Monorepo Ambient Escapes:** Code and test files residing under research paper packages (e.g., `research/papers/{slug}/code/` or `coda_atlas/{slug}/code/`) must be hermetic and execute cleanly when invoked with `cwd={paper_dir}`. Imports of unpinned, top-level monorepo files (e.g., `import quickstart`) or sibling paper code are strictly prohibited and constitute blocker-level deposit defects.
> 2. **Standardized Subprocess Replay:** Automated review tools (`omega_engine_research_papers.use_cases.paper_review.cli`) must invoke test runners (`pytest`) within the paper package scope (`cwd={paper_dir}`) to ensure isolation and detect ambient namespace leaks before release bundling.

---

## Atlas Code Generator & Research Paper Parity Invariant (`RULE_ATLAS_GENERATOR_PAPER_PARITY_001`)

> **Code-Generated Paper Purity:**
>
> 1. **Generator Authority over Stage Papers:** In `research/mssn_sn_tower/math/mssn/`, individual stage markdown files (`mss_000.md` through `mss_100.md`) are code-generated artifacts maintained by `research/mssn_sn_tower/code/python/build_atlas.py`.
> 2. **Byte-Level Parity Test:** Tests in `test_mss100.py` assert strict byte-level equality between `text_for(stage)` and the paper on disk (`test_every_generated_paper_matches_current_stage_obligation`).
> 3. **Generator-First Updates:** When stage obligations, Lean 4 proof kernels, reproduction commands, or domain verifiers are added for a stage, the modification MUST be implemented within `build_atlas.py` (or declared stage metadata), and papers regenerated via `python -m research.mssn_sn_tower.code.python.build_atlas`.
> 4. **No Unsynchronized Edits:** Never manually edit generated `mss_*.md` files without updating `build_atlas.py`.

---

## Research Paper Publication, Exact Solvers & Mathematical Verification Invariant

> **Academic Publication, Exact Arithmetic & Proof Engine Discipline:**
>
> 1. **Regime Model Soundness vs. Operational Pipeline Separation:** When a formalization models both an operational execution record and an abstract epistemic regime, soundness theorems must be strictly scoped to the regime model; records never imply truth without a validated regime embedding ($R_\Pi$).
> 2. **Exact Rational Verifier Float & Bool Firewall:** Solvers and verifiers must validate scalars, matrices, and shapes, strictly rejecting floats and booleans (`TypeError` on `isinstance(value, bool)`); rounding must never cancel positive defects.
> 3. **Defensive Certificate Payload Immutability:** Dataclass certificate records must freeze mutable matrices into `ImmutableMatrix` during `__post_init__` to prevent post-verification mutation.
> 4. **Fail-Closed Terminal Route Dispatching:** Dispatchers must independently verify underlying certificate invariants ($\Phi_1=0$, $\Gamma_2=0$, zero residual, zero duality gap) against input data rather than trusting enums.
> 5. **Layout Margin Purity & Non-Trivial Solvers:** TeX logs must report zero `Overfull \hbox` warnings. Math and code blocks must fit page margins; Markdown lists require preceding blank lines. Solvers must compute verified exact solutions over $\mathbb{Q}$ and never return trivial constants; cycle repairs must evaluate descent on exact quotient potential $\Phi_1 = \|[h]\|_{Q1}$.
> 6. **Merkle Tape Commitment & Ledger Classification:** Verification tapes must hash the canonical RFC 8785 JSON representation of the `outcome` payload. Protocol declarations and dataclasses must not be labeled `Finite theorem` without executable checkers and test assertions.

---

## Standalone Lean 4 Proof Kernel Packaging & Axiom Census Invariant

> **Hermetic Lean 4 Release Bundling & Axiom Totality:**
>
> 1. **Self-Contained `lean4/` Directory in Formal Paper Packages:**
>    - Research papers declaring Lean 4 mechanization must package a hermetic, standalone `lean4/` directory containing:
>      - `lean-toolchain` pinning the exact repository compiler toolchain.
>      - `lakefile.lean` declaring package configuration without monorepo root escapes.
>      - All formal proof modules required to verify paper claims.
>      - An audited census file (`Census.lean`) auditing `#print axioms` across all paper theorems.
> 2. **Automated Deposit Verification & Mandatory Census Gate (`verify_deposit.py --lean`):**
>    - Deposit verification must execute `lake build` and `lake env lean Census.lean` (or `lake exe census`) within the paper package directory.
>    - **Mandatory Census Presence:** `verify_deposit.py` must fail closed if `Census.lean` does not exist; it must never report passing census verification when the census file is absent.
>    - **Inventory Reconciliation:** The verifier must verify an explicit, documented list of expected claim declarations against the actual declarations output by `#print axioms`, failing closed on missing declarations.
>    - **Axiom Whitelist Enforcement:** `#print axioms` must report strictly standard Lean 4 kernel axioms (`propext`, `Quot.sound`, `Classical.choice`), failing closed if any custom or unwhitelisted axiom is reported.

---

## Comprehensive Claim-Code Map Invariant (`RULE_CLAIM_CODE_MAP_COMPREHENSIVE_001`)

> **Bijective Claim-to-Code Mapping:**
>
> 1. **Full Claim Inventory Coverage:** `docs/claim_code_map.yaml` must map every paper claim and lemma to its executing Python, Rust, or Lean test or solver implementation. Single-stub maps fail pre-flight audit.
