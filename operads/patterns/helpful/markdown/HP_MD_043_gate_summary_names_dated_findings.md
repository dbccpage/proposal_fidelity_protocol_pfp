---
pattern_id: HP_MD_043
name: gate_summary_names_dated_findings
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_043_equal_gate_counts_hide_finding_change.md
language: markdown
authority_effect: None
---

# Healthy Pattern: A Gate Summary Names the Dated Findings (`HP_MD_043`)

## Description

When two publication receipts share a pass count and a fail count, the summary names the receipt and the finding identities that receipt records. Equal counts are not one failure set.

## Construction

- Put the timestamp or receipt filename in the same sentence as 26 passed and 8 failed.
- For the 2026-10-08 receipt, keep `.pytest_cache/.gitignore` and `indexed_count` 1646 on `R_MANIFEST_BIJECTION`. Do not replace that finding with `manifests/coverage.json`.
- For the 2026-10-09 receipt, keep `manifests/coverage.json` and `indexed_count` 1682 on that rule. Keep `evidence/` on `R_RESTRICTED_DIR_STRUCTURE`. Do not import `.pytest_cache/` or `__pycache__/` from the earlier receipt into those later findings.
- Do not add the two fail counts. The README already says overlapping checks must not be added into a whole-suite test count.
- A `PASS` on `artifact_consistency` in `inputs/r5_checks.json` does not rewrite `overall_status` `FAIL` in `receipts/r5_policy_gates.json`.

## Limit

The witness is the historical folder `_ic/darpa/research/wdp_full_audit`, receipts `baseline_gates.json` dated 2026-10-08 and `r5_policy_gates.json` dated 2026-10-09. No publication gate, pytest, Lean, archive build, or checksum command was rerun. Lines after 1000 in both receipts were not read. Five later rules are `FAIL` in the read prefix (`R_MANIFEST_BIJECTION`, `R_RESTRICTED_DIR_STRUCTURE`, `R_NO_TOC`, `R_MD_UL_STYLE_DASH`, `R_NOTEBOOK_NAMING`). The header says eight failures, so three failing rule ids stay unnamed. `R_PDF_RENDERABLE` in the read prefix is `PASS` on both, with `pdf_path` `000_witnessed_difference_programme.pdf` and 1145517 bytes, then `witnessed_difference_programme.pdf` and 1155710 bytes. Those passing rows are not this pattern.

`/declared-vs-actual-gate` was the owner opened. It still checks that declared stage binaries exist and that host mirrors match. An absent binary is `BLOCKED`, and `VACUOUS` stays distinct from `PASS`. That rule is not these two count tuples. `/woland-proof-scope-rule` still keeps a `Verified` disposition from being a proof of every theorem. The README already says that. `/woland-proof-premise-rule` still carries hypotheses into an unbuilt claim. The README's next derivation is proposed only. `/woland-check-sensitivity-pattern` still binds a mutation to its consumer. The mutation sentence in the README was not rechecked. `/woland-scoped-reuse-pattern` still labels reused evidence historical. These two files are separate receipts. `/adversarial-receipt-audit` still owns a visual-inspection gap on a documentation pass. That field was not in the read prefix. `AP_MD_016` still owns calling a gate failure mathematical research. The README names archive formatting separately from two ordinary uses of "proves". `AP_MD_026` still owns a ceiling stop. Both receipts record 26 and 8. `AP_MD_028` still owns a runner outage scored as a package failure. The blocked Mathlib cache is a different sentence from the eight rule failures. `AP_MD_023` still owns a zero exit that publishes later bytes. `final_git_index_binding.json` records `PASS` for 1696 files and source sha256 `057052783ab5631adc746136bd0ce175286baf7579c87fb5e09927d88f233f88`, the same digest `inputs/r5_route.json` stores as `current_source_sha256`. That binding is not a publication-suite pass. `AP_MD_014` still owns a pass with an empty payload. This binding's file count is 1696. `AP_MD_007` still owns a package list compared with itself. The inventory prefixes are path rows. `AP_MD_009` still owns a nested pass inside a failed exit. `inputs/r5_checks.json` is a sibling file. `AP_MD_020` still owns a local notebook-absence note. The later read prefix fails `R_NOTEBOOK_NAMING` for archive notebook paths. `AP_MD_024` is titled obligations_verdict_lists_none. This pattern does not rescore `residual_ids`. `AP_MD_027` is titled requirement_fails_on_another_witness. This pattern only refuses treating the shared 26 and 8 as the same findings.

A receipt may be summarized with its own 26 and 8 when the findings named are the ones that receipt lists.

## Dual Anti-Pattern

See [AP_MD_043_equal_gate_counts_hide_finding_change.md](../../anti/markdown/AP_MD_043_equal_gate_counts_hide_finding_change.md).
