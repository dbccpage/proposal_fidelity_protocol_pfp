# Detailed definition: Paper Epistemic Evaluator & Namespace Discipline (2)

**AuthorityEffect:** None.

Parent: [Paper Epistemic Evaluator & Namespace Discipline](../../../../../rules/papers/rl_paper_epistemic_evaluator_and_namespace_discipline.md). Load for the matching predicate, not every task.

## Lean 4 Kernel Decidability, Markdown Formats & Metadata Parity (`RULE_LEAN4_KERNEL_DECIDABILITY_PURITY_001`)

> **Kernel Decidability, Markdown Syntax & Deposit Versioning Invariants:**
>
> 1. **Lean 4 Kernel Decidability and Axiom Purity (`RULE_LEAN4_KERNEL_DECIDABILITY_PURITY_001`):**
>    Theorems over finite discrete structures and decidable bounds must be verified using native kernel computation (`decide`, `rfl`) rather than unverified VM reflection (`native_decide`). Kernel-certified proofs ensure zero-axiom purity without injecting external C++ runtime trust axioms (`_native.native_decide.ax_*`). Release packages containing Lean 4 mechanizations must generate and package an `axiom_report.txt` verifying that proofs depend only on standard whitelisted axioms (`propext`, `Quot.sound`, `Classical.choice`).
>
> 2. **Markdown Unordered List Formatting Consistency (`RULE_MARKDOWN_UNORDERED_LIST_CONSISTENCY_001`):**
>    In compliance with workspace Markdownlint standards (MD004), all unordered list items in monograph prose, change logs, and study guides must use dash markers (`-`) rather than asterisk markers (`*`) to maintain stylistic uniformity across repository documents.
>
> 3. **Claim Ledger Pytest Reference Syntax (`RULE_CLAIM_LEDGER_TEST_NAME_SYNTAX_001`):**
>    In packages maintaining claim ledgers, any row referencing a computational test verifier must declare the full test locator including module filename (`<test_module>.py::<test_func>`) to satisfy automated verification parsers and CI test runners.
>
> 4. **Zenodo Metadata Version Tracking (`RULE_ZENODO_METADATA_VERSIONING_IDENTIFIERS_001`):**
>    When updating or re-certifying a paper deposit package, `zenodo_metadata.json` and `.zenodo.json` must include `related_identifiers` linking `isVersionOf` to the deposit's Concept DOI to ensure persistent lineage tracking.
