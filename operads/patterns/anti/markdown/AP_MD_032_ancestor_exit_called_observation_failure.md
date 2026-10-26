---
pattern_id: AP_MD_032
name: ancestor_exit_called_observation_failure
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_032_ancestor_exit_names_both_commits
language: markdown
authority_effect: None
---

# Anti-Pattern: Ancestor Exit Called An Observation Failure (`AP_MD_032`)

## Description

`git merge-base --is-ancestor` exits 1 with empty stderr when the first commit is not an ancestor of the second. The local-CI wrapper allows only exit 0, so that predicate result is stored as `Git observation failed with 1: no stderr`. The receipt names an observation failure. It does not name the ancestor check.

## Detection Signature

- A `local_ci` result has `status` `FAIL`.
- The detail contains `Git observation failed with 1: no stderr` and does not contain `merge-base`, `is-ancestor`, or `ancestor`.
- The same object records `expected_main` and `expected_head`.
- Exit 1 of `git merge-base --is-ancestor` means the first commit is not an ancestor. Errors are a nonzero status other than 1. The wrapper treats every status other than 0 as an observation failure.
- A co-located note may name ancestry. That note is not the check detail.

## Witness

Historical disposition. This digest did not rerun local CI, git, or the ancestry check, and did not check out the trusted head. Source folder `_ic/darpa/research/po000_review_repairs_receipts/`.

`reviewed_head_direct_interpreter_disposition.json` requests head `43461b2fae959db1f6fd43ac1f397672d07f5376` and trusted head `37438f8783110324d15c38762c418be936a70d83`. The result name is `local_ci`, status `FAIL`. Its detail is:

> CHILD_EXIT_NONZERO: local_ci exited 2: local_ci: REFUSED: INVALID_RECORD: Git observation failed with 1: no stderr

The same object sets `expected_head` to `43461b2fae959db1f6fd43ac1f397672d07f5376` and `expected_main` to `37438f8783110324d15c38762c418be936a70d83`. `verifier_command` is null. `phase_timings_seconds.verification` is 0.0.

`README.md` in that folder says:

> Retrying with the real Python interpreter reached local CI and was refused with `CHILD_EXIT_NONZERO` / `INVALID_RECORD: Git observation failed with 1`. The historical head predates the current-main baseline. The trusted `local_ci.assert_base_relation` invokes `git merge-base --is-ancestor expected_main expected_head`; this ancestry requirement is false for those exact objects. The reviewed source is not thereby mathematically refuted.

The current tree's `assert_base_relation` still calls `run("merge-base", "--is-ancestor", expected_main, expected_head)`, and `run` still refuses any return code other than 0 with `Git observation failed with {code}: {stderr or 'no stderr'}`. That reading was not executed. It is the current function that emits the receipt sentence. The trusted copy at `37438f8783110324d15c38762c418be936a70d83` was not opened.

## Hazard & Failure Mode

- A later note treats `Git observation failed with 1: no stderr` as a git outage or an empty transport failure.
- The false ancestor relation between those two commits drops out of the summary.
- The refusal is then cited as a mathematical refutation of the reviewed source, which the co-located note denies.
- A repair that only adds stderr text still hides the predicate, because this exit has no stderr.

## Dual Healthy Pattern

See [HP_MD_032_ancestor_exit_names_both_commits](../../helpful/markdown/HP_MD_032_ancestor_exit_names_both_commits.md).
