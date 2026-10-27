---
pattern_id: HP_MD_014
name: verdict_keeps_payload_count
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_014_pass_to_master_with_zero_payload
language: markdown
authority_effect: None
---

# Healthy Pattern: Verdict Keeps The Payload Count (`HP_MD_014`)

## Description

The verdict is written beside the count that run validated. A zero demo count stays zero. Exit 0 is the process result for the command that ran. It does not fill an empty payload.

## Construction

- Put `PASS_TO_MASTER` or `PASS` next to the demo count from the same landing record.
- If that count is zero, write zero and name the removed entry point (`common_build.py` in this record).
- Do not upgrade six strand passes into a fresh 50-demo success.
- Keep exit 0 attached to `education_strands_gate`. The command receipt in this folder has no verdict field and no demo count.
- Keep the warning in the summary that quotes the verdict.

## Limit

The witness in [AP_MD_014_pass_to_master_with_zero_payload](../../anti/markdown/AP_MD_014_pass_to_master_with_zero_payload.md) is the historical folder `paper_landing_20261009`. No education gate was rerun. `education_strands.txt` was not read. The zero count and `PASS_TO_MASTER` wording are the README and `integration.json` limitations, not fields recomputed from the command JSON. This digest does not claim the current education gate still validates zero demos.

`/declared-vs-actual-gate` still separates `VACUOUS` from `PASS` when a stage has no input, and it marks a missing stage binary `BLOCKED`. This pattern does not replace that gate. The education command recorded here exited 0. It was not recorded as a missing stage binary.

`AP_MD_009` / `HP_MD_009` still cover a nested `PASSED` inside a failed exit. This pattern is the exit-0 case whose counted demo payload is zero.

`AP_PY_012` still forbids borrowing another task's `PASS_TO_MASTER`. `HP_PY_012` still rejects a hermetic run whose `passed_count` is 0. This landing's strand pass count is not that zero. The zero is the demo count in the same note.

`/adversary-proof-scope-rule` still bounds the single Lean module in this folder. `/adversarial-receipt-audit` still requires a green build claim to match the artifact. The stale WDP PDF, blocked release reviews, and unrefreshed checksums stay with that audit. They are not this pattern.

## Dual Anti-Pattern

See [AP_MD_014_pass_to_master_with_zero_payload](../../anti/markdown/AP_MD_014_pass_to_master_with_zero_payload.md).
