# Detailed definition: Paper Epistemic Evaluator & Namespace Discipline (1)

**AuthorityEffect:** None.

Parent: [Paper Epistemic Evaluator & Namespace Discipline](../../../../../rules/papers/rl_paper_epistemic_evaluator_and_namespace_discipline.md). Load for the matching predicate, not every task.

# Rule: Paper Epistemic Evaluator, Functorial Purity & Namespace Discipline

**AuthorityEffect:** None.

This rule codifies preprint namespace de-slop, categorical functorial purity, mechanism inventory discipline, and evaluator supremacy across research papers and monographs. Cross-reference publication packaging invariants: [`rl_research_paper_and_monograph_packaging.md`](../../../../../rules/papers/rl_research_paper_and_monograph_packaging.md).

---

## Preprint & Paper Namespace De-Slop Invariant

> **Canonical Example & Harness De-Slop:**
>
> 1. **No Transient Paper Prefixes in Engine Code:**
>    When test fixtures, example binaries, or benchmarking suites graduate from research preprints into canonical Rust crates (`omega_engine/crates_rs/`) or engine operations packages (`omega_engine_operations/`), transient paper identifiers (e.g., `paper070_`, `paperer008_`, `paper012_`) must be eliminated from:
>    - Filenames (e.g., `benchmarks.rs`, `replays.rs` instead of `paper070_benchmarks.rs`).
>    - Example directory names (e.g., `examples/replays/` instead of `examples/paper070_replays/`).
>    - Module path attributes (e.g., `#[path = "replays/cases.rs"]` and `#[path = "../examples/replays/cases.rs"]`).
>    - Example CLI invocation strings in JSON manifests / generator commands.
> 2. **Git History Preservation:**
>    All renames and relocations must be staged via `git mv` to preserve provenance and avoid untracked file clutter.
> 3. **Scoped Compilation & Test Verification:**
>    After de-slopping examples and test harnesses, run scoped compilation (`cargo check -p <crate> --examples --tests`) and targeted tests on the impacted modules.

---

## Categorical Functorial Purity & Self-Verifiable Release Packaging Invariant (`RULE_CATEGORICAL_NO_MAP_FALLACY_PROHIBITION_001`)

> **Categorical Precision, Deposit Self-Containment & Living Documentation Discipline:**
>
> 1. **Categorical No-Map Fallacy Prohibition:**
>    - Demonstrating or mechanizing that two constructors $i_A: A \to A \oplus B$ and $i_B: B \to A \oplus B$ have disjoint images in a coproduct or sum type guarantees non-cohabitation of values, but does NOT imply the absence of natural transformations ($\operatorname{Nat}(F, G) = \emptyset$) between functors landing in those types. (Countermodel: two constant singleton functors $\Delta_A, \Delta_B$ have a natural transformation between them while their coproduct injections remain distinct).
>    - Authors and agents must never claim categorical impossibility or label general functorial non-existence as OPEN when based on constructor disjointness.
>    - Promotion boundaries must be explicitly scoped: characterized as interface routing policies, typing constraints, or functor category restrictions.
> 2. **Self-Verifiable Release Archive Extraction Law:**
>    - Standalone release archives (`<pkg>_<date>.zip` / `.tar.gz`) must be completely self-contained and verifiable post-extraction.
>    - Packaging scripts (`build_deposit_zip.py`, `rebuild_release.py`) must package the necessary checksum manifests (`SHA256SUMS` and/or `MANIFEST.sha256`) directly into the archive.
>    - Verification scripts (`verify_deposit.py`) must implement resilient fallback between `SHA256SUMS` and `MANIFEST.sha256`, dynamically stripping external archive files (`.zip`, `.tar.gz`) when checking directory tree contents post-extraction.
>    - Before any release is finalized, extraction verification must be tested by unpacking into an isolated directory and running `python verify_deposit.py`.
> 3. **Living Documentation & Recompiled Deliverable Synchronization:**
>    - Quick start guides, `README.md`, and walkthroughs must reference active, executable entry points (e.g. `lake env lean Core.lean`), never stale, pre-refactor, or deleted module filenames.
>    - Rendered publication deliverables (PDFs) must be recompiled immediately upon any textual or architectural modification to LaTeX or Markdown sources, ensuring that rendered documents contain zero stale module paths or superseded claims.

---

## Stage 0 Preflight Inventory, Link Purity & Claim Index Invariant

> **Preflight Packaging Fences & Envelope Hygiene:**
>
> 1. **Mandatory Mechanism Inventory Slots:** Every monograph containing a mechanism inventory table MUST include the `AuthorityEffect` slot explicitly declared as `None` (`| **AuthorityEffect** | None |`).
> 2. **Zero Raw Monorepo Path Escapes:** Publish-facing monographs and documentation must never contain raw repository file paths (e.g. `omega_engine/...`). Pointers must resolve via public DOIs or URLs.
> 3. **Retirement of Claim Ledgers:** Claim ledgers (`<slug>_claim_ledger.md`, `claim_ir.yaml`, `claim_code_map.yaml`, `lean_claim_map.md`) are retired from papers' release suites and must not be generated or required.

---

## Evaluator Supremacy, Authority Separation & Reference Module Hygiene Invariant (`RULE_EVALUATOR_SUPREMACY_AUTHORITY_SEPARATION_001`)

> **Evaluator Supremacy, Diagnostic Binding & Epistemic Authority Discipline:**
>
> 1. **Checklist Conjunction vs. Operational Authority Separation:**
>    - Conjunction of checklist gates (even 8 passing Booleans) must NEVER be promoted to operational `AUTHORITY` without a verified, evidence-bearing `TerminalWitness` ($t, IsAuth$).
>    - Passing gate checklists yields `CHECKLIST_CERTIFIED` (or scoped certificate), with text stating that sufficiency to operational authority is refused.
>    - Evaluators must fail-close: unhalted traces return `PROPOSAL_ONLY`; zero residual defect without verified gates returns `NON_AUTHORITY_HALT`.
>
> 2. **Field and Diagnostic Binding Invariant:**
>    - Evaluators must never trust caller-supplied diagnostic tuples (e.g. $(\Phi_1, \Gamma_2, \Xi)$) alone when candidate objects (`initial_field`, `proposed_field`, or candidate traces) are provided.
>    - The host evaluator must independently compute diagnostics directly from the candidate field/trace, verifying that caller-supplied values match certified field calculations to prevent detached or spoofed diagnostic bypasses.
>
> 3. **Exhaustive Carrier Quotient Factorization:**
>    - Quotient and dashboard factorization verifiers (such as LGGR) cannot evaluate isolated or sampled pairs alone.
>    - Verifying that a local dashboard factors through a quotient requires testing constancy across the entire partition/equivalence class on declared finite carriers. If any pair in the same class has conflicting local values, factorization is refused.
>
> 4. **Strict Boolean Type Validation on Gate Vectors:**
>    - Gate structures/vectors must enforce strict boolean typing (`isinstance(val, bool)`) in `__post_init__` to prevent string truthiness bypasses (such as `GateStack(*["False"] * 8)` evaluating to True).
>
> 5. **Dual Formulation / Discount Grounding for Trace Kernels:**
>    - Continuous discounting formulas ($e^{-\lambda C - \mu R}$) and discrete exact-rational Padé surrogates ($1 / (1 + \lambda C + \mu R)$ in $\mathbb{Q}$) must be explicitly declared and distinguished.
>    - Strict non-negativity and exact rational types must be enforced on costs, risks, and sensitivities.
>
> 6. **Unbundled Mechanization Scoping & License Cleanliness:**
>    - If Lean 4 proof sources are not bundled and verifiable within the standalone paper release, all manuscript text, claim ledgers, and description files must explicitly scope Lean references as unbundled external design sketches, certifying verification solely through the sovereign Python reference suite.
>    - Strict license parity: `LICENSE-CODE` must match `README.md` and `pyproject.toml` (Apache-2.0 standard).
>    - Zero literal `##` LaTeX typos in manuscript formulas.
---
