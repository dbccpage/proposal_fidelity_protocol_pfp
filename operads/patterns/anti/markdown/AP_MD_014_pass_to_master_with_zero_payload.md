---
pattern_id: AP_MD_014
name: pass_to_master_with_zero_payload
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_014_verdict_keeps_payload_count
language: markdown
authority_effect: None
---

# Anti-Pattern: Pass To Master With A Zero Payload (`AP_MD_014`)

## Description

A landing note quotes `PASS_TO_MASTER` or `PASS`, together with exit 0, as if that run validated a demo suite. The same note says the counted demo payload is zero because the historical demo entry point was removed.

## Detection Signature

- The command receipt for `education_strands_gate` has `exit_code` 0. That receipt does not itself contain the verdict word or the demo count.
- The same folder's README pairs `PASS_TO_MASTER` for six strands with zero validated demos and a removed entry point.
- The same folder's integration limitations pair a six-strand `PASS` with zero demos and a removed `common_build.py` location.
- A later summary keeps the verdict and drops the zero count.

## Witness

Historical landing record, not a fresh education-gate run. This digest did not rerun the gate and did not read its stdout. Source folder `_ic/inr/core_paper_reviews/paper_landing_20261009/`.

`README.md`:

> The education gate passes all six strands with `PASS_TO_MASTER`. It reports zero validated MSS-N demos and a warning because its historical demo entry point was removed on main. This receipt does not claim a fresh 50-demo validation.

`integration.json` limitations:

> Education strands gate reports PASS for six strands but validates zero demos because its old common_build.py location was removed on main. No fresh 50-demo success is claimed.

`education_strands.json` records `exit_code` 0 for `operations.use_cases.cicd.education_strands_gate --json`.

## Hazard & Failure Mode

- A checklist that requires a 50-demo `PASS_TO_MASTER` is treated as satisfied by this run.
- Six strand passes are counted as demo checks that did not run.
- The warning about the removed entry point drops out of the summary.

## Dual Healthy Pattern

See [HP_MD_014_verdict_keeps_payload_count](../../helpful/markdown/HP_MD_014_verdict_keeps_payload_count.md).
