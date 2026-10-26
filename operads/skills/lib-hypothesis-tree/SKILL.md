---
name: lib-hypothesis-tree
description: "Use when iteratively improving an artifact under an evaluator. Hypothesis tree with held-out merge gate."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# lib-hypothesis-tree

## References

## Constraints

## Related skills

## Invariants

### Example

## Procedure

**Do not activate** for one-shot fixes, `/rip-papers`, `/math-prover`, or promotion.

## When to activate

**AuthorityEffect: None.** Merge ≠ proof eligibility ≠ paper ACCEPT ≠ release.
**held-out merge gate**. Dev scores guide search; only held-out non-regression admits merges.

## note: pattern only (hypothesis tree refinement / held-out gate); reimplemented

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
