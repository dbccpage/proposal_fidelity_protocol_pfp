---
pattern_id: AP_AUTOP_001
name: novella_verdict_without_checker_receipt
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Receipt", "Paper"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_AUTOP_001_typed_checker_receipt_binding
language: multi
authority_effect: None
---

# Anti-Pattern: Novella Verdict Without Checker Receipt (`AP_AUTOP_001`)

## Description

Recording a terminal verdict of `PASS_TO_MASTER` or `work_status: completed` in a review narrative, novella (`novella.md`), or summary (`summary.json`) while `checker_receipt` remains `null` and executable verification commands (`cargo test`, `lean`, or python gate tests) have not executed.

## Harmful Impact

- **False Verification Signaling:** Downstream agents reading `summary.json` or `terminal_verdict` may infer that a mathematical proof, gate check, or formal derivation has been mechanically verified, when in reality only literary dialogue or persona roleplay took place.
- **Null Checker Totality:** Audits across 50 run packages in `_ic/adversary/runs/` showed that 100% of run receipts had `checker_receipt: null`, yet three derivation batches claimed `PASS_TO_MASTER` purely from Apartment 50 novella prose.
- **Masked Technical Debt:** Unexecuted verification steps fail to register as open obligations, hiding unverified derivations from follow-up sprint planning.

## Concrete Witness

In `_ic/adversary/runs/adversary_top10_batch2_20261013/summary.json`:
```json
{
  "terminal_verdict": "PASS_TO_MASTER",
  "work_status": "completed",
  "tests_executed": null,
  "checker_receipt": null
}
```
The corresponding `novella.md` contains 400 lines of dramatic dialogue between Adversary, Defect Hunter, and Manuscript Truth praising the derivation, while zero executable Rust, Lean, or Python checks were run or bound.

## Corrective Approach

Adopt [`HP_AUTOP_001_typed_checker_receipt_binding`](../../helpful/autop/HP_AUTOP_001_typed_checker_receipt_binding.md):
- Enforce fail-closed verification: `terminal_verdict` may only transition to `PASS` or `PASS_TO_MASTER` if `checker_receipt` contains a non-null, validly hashed execution receipt.
- In the absence of an executed machine receipt, the terminal status must strictly remain `OPEN_RESIDUAL` or `UNVERIFIED_NARRATIVE`.
