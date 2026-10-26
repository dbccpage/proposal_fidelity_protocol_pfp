---
pattern_id: HP_MD_028
name: stage_fail_names_the_runner
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_028_runner_outage_scored_as_package_fail
language: markdown
authority_effect: None
---

# Healthy Pattern: The Stage Fail Names The Runner (`HP_MD_028`)

## Description

A `FAIL` that never starts the package stays a runner limit. The sentence names the unreachable host or the interpreter that has no module. A later exit 0 on another interpreter is a different run.

## Construction

- Keep `lake build failed (exit 1)` next to `Failed to connect to github.com port 443` and `git` exit 128. That pair is a clone outage, not a proof failure.
- Keep `pytest failed (exit 1)` next to `Python39_64\python.exe` and `No module named pytest`. Do not call it a collected test failure.
- Keep packaging `BLOCKED` as blocked by those runner rows. Do not rename the rows into candidate defects.
- An offline `git` exit 128 remains that command's exit. It does not become a theorem defect, and a different run's exit 0 does not erase it.
- Quote a later `lake build` or pytest exit 0 only with its interpreter and its own review. Do not write that exit into the swarm receipt.
- Do not cite either exit as Zenodo readiness. The co-located reviews stay `NOT READY FOR ZENODO REPUBLICATION`.

## Limit

The witness in [AP_MD_028_runner_outage_scored_as_package_fail](../../anti/markdown/AP_MD_028_runner_outage_scored_as_package_fail.md) is the historical pair `008_so_k_invariant_gauge_classification_swarm_receipt.json` and `009_coordinate_wise_additivity_swarm_receipt.json`, review `SWARM_REV_20260927_223121`, dated 2026-09-27, plus the two republication reviews bound to commit `e4a1214bb3e47570b0f74ecc9117c98f27a26b5e`. No gate, pytest, lake, notebook, or network command was rerun. The exit-0 rows are historical observations in those reviews, not a fresh build.

`AP_MD_022` still owns `does not depend on any axioms` beside a failed `.olean` create. `AP_MD_016` still owns a real lint, hash, or missing-file error that a canned sentence calls mathematical research. These receipts do not use that sentence. `/declared-vs-actual-gate` still separates `VACUOUS` from `PASS`. Stage `interactive_pedagogy_and_replay` is `PASS` here with "No companion execution receipt found in code/." That row is not this pattern. `AP_MD_014` still owns a pass verdict with a zero payload. `AP_MD_020` still owns "No local notebooks found." `AP_MD_001` still owns stale paths and version-date drift. `AP_MD_023` still owns a zero exit whose published bytes differ from the audited map. `AP_MD_026` still owns unscored Stage Ω rows presented as a finished gate. `/woland-proof-scope-rule` still separates a clean Lean build from prose scope. `/adversarial-receipt-audit` still owns a receipt that does not match its claim. `/glossa-public-math-dialect-firewall` still owns public authority dialect. `AP_LN_002` still owns an unconstrained Mathlib rebuild. `AP_PY_007` still owns a committed rebuildable artifact. This pattern does not close identity, verifier, notebook, bibliography, or theorem-hypothesis findings in the two reviews.

## Dual Anti-Pattern

See [AP_MD_028_runner_outage_scored_as_package_fail](../../anti/markdown/AP_MD_028_runner_outage_scored_as_package_fail.md).
