---
pattern_id: HP_MD_032
name: ancestor_exit_names_both_commits
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_032_ancestor_exit_called_observation_failure
language: markdown
authority_effect: None
---

# Healthy Pattern: An Ancestor Exit Names Both Commits (`HP_MD_032`)

## Description

When `git merge-base --is-ancestor` exits 1 and writes no stderr, say that the first commit is not an ancestor of the second, and quote both commit ids. Do not call that exit a git observation failure.

## Construction

- Allow exit 1 from `merge-base --is-ancestor` as the false predicate. The refusal sentence names `expected_main`, `expected_head`, and that the main commit is not an ancestor of the head.
- Keep `Git observation failed with N` for a git command that failed to run, timed out, or returned a status the predicate does not use. Empty stderr on `--is-ancestor` exit 1 is not that case.
- Keep a real nonzero git stderr next to the observation sentence. Do not rewrite it into an ancestry claim.
- Quote the co-located note's ancestry sentence with the receipt. Do not replace the receipt with the note, and do not drop the note's limit that the source is not mathematically refuted.
- Exit 0 of `--is-ancestor` is the only ancestor pass. A missing error string is not that pass.

## Limit

The witness in [AP_MD_032_ancestor_exit_called_observation_failure](../../anti/markdown/AP_MD_032_ancestor_exit_called_observation_failure.md) is the historical file `reviewed_head_direct_interpreter_disposition.json` beside `README.md` in `_ic/darpa/research/po000_review_repairs_receipts/`. No local CI, git, or ancestry command was rerun. The current `assert_base_relation` still routes that exit through the observation sentence. That is a source reading, not a fresh refusal.

`AP_MD_028` still owns a lake or pytest failure whose stderr is a network refusal or a missing module. This receipt's detail has no such stderr. `AP_MD_009` still owns a nested `PASSED` on a failed exit. This result status is `FAIL`, and there is no nested pass. `AP_MD_027` still owns a requirement sentence whose detail names a different object. This detail does not restate another requirement; it omits the ancestor predicate. `po000-pr600-current-disposition.json` names `Unknown JSON field: "baseRefOid"`, and its `local_ci` detail says `not executed because locus setup refused`. That row did not run the ancestor check. `po000-pr600-repaired-environment-disposition.json` names `GITHUB_BASE_OID_MISMATCH` and both base oids. That locus line already names its comparison. Neither PR file is this witness. Their unrun `local_ci` status `FAIL` was not given this id. `/woland-proof-scope-rule` still separates `current_replay_verdict.json` `pass` and an empty `errors` array from `refusals_present`, `open_obligations_present`, and `promotion_eligible` false in `current_replay.json`. `AP_MD_001` still owns the round-one README Lake and stdlib-only sentences. Those rounds record the sentences as later documentation repairs. This pattern does not rerun them and does not call the historical `pass` verdicts a fresh replay.

## Dual Anti-Pattern

See [AP_MD_032_ancestor_exit_called_observation_failure](../../anti/markdown/AP_MD_032_ancestor_exit_called_observation_failure.md).
