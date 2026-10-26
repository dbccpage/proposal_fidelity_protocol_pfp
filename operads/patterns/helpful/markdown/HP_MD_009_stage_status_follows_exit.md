---
pattern_id: HP_MD_009
name: stage_status_follows_exit
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_009_nested_pass_on_failed_exit
language: markdown
authority_effect: None
---

# Healthy Pattern: Stage Status Follows The Exit (`HP_MD_009`)

## Description

The stage outcome is the process exit and the stage status. A nested checker that passed is named as that checker. It does not replace exit 1.

## Construction

- Write the command exit next to any nested verdict. `preflight exit=1` stays a failed preflight.
- Keep `BLOCKED` when the stage lists errors. Do not promote a nested `PASSED` to the stage outcome.
- If one subcheck passed and another failed, name both. The failed exit remains the stage result.
- Match a typed-rule score to the rule table. A 19 / 26 failure is not a pass.
- Cite the nested pass only for the checker it names, and only when that command's exit is 0.

## Limit

The witness in [AP_MD_009_nested_pass_on_failed_exit](../../anti/markdown/AP_MD_009_nested_pass_on_failed_exit.md) is the historical 2026-10-06 folder `2026-10-06_po_r2`. No preflight, gate, republication, pytest, ruff, notebook replay, or Lean build was rerun. The nested `PASSED` may have meant one subcheck. `exits.txt` still records `preflight exit=1`, so that word is not the process result. The exit file and the JSON are co-located historical records; this digest did not pair them by a new process id.

`/adversarial-receipt-audit` still checks a green claim against the artifact bytes. This pattern does not replace that audit. `/declared-vs-actual-gate` still separates `VACUOUS` from `PASS` and blocks a missing stage binary. `/woland-proof-scope-rule` still refuses to call a deposit with Lean sources purely computational because `lakefile.lean` is absent. `/woland-check-sensitivity-pattern` still binds each depth or path check to the path string it consumed. Deposit rules for `\maketitle`, Lake files, `evidence/`, and `verify_deposit.py` stay with `/governance-research-paper-edit-publish`.

A failed exit does not by itself prove which deposit bytes are wrong. Those findings remain the historical gate rows.

## Dual Anti-Pattern

See [AP_MD_009_nested_pass_on_failed_exit](../../anti/markdown/AP_MD_009_nested_pass_on_failed_exit.md).
