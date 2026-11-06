# Amendment A1: numeric claims earn no O units

**AuthorityEffect:** None.

**Recorded:** 2026-10-22 (UTC). This is after Arm S ran, but before Arm F ran and before any scoring. No score of this cohort existed when it was written. `protocol.md` is unchanged, and its pinned sha256 still holds.

## Change

Under protocol.md §5.3, an O unit includes "one verified ... exact numeric claim". A numeric claim supplies its own expression and value. The host only recomputes the arithmetic, so a correct claim shows the model can do arithmetic, not that the claim bears on the node. The user decided ("anyone can say 10+4 = 11") that such claims should carry no credit. The ladder now applies the same rule by default (`numeric_counts=False`, PR #165).

A1 adds a second scoring, `score.py --exclude-numeric`. It drops `verified_numeric_claims` from every O count in both arms. False numeric claims stay refused claims in both arms.

## Reporting

- Both scorings are reported. The as-registered score is `score.py` without the flag, and the A1 score is written to `scores/<stamp>_A1_no_numeric/`.
- The A1 score is the headline, by the user's decision.
- The as-registered score is reported next to it unchanged, so the effect of the amendment is visible.
- The decision rule (§7) is applied to both.

## Scorer fixes found at first scoring (2026-10-22, before any result was reported)

- **A1 inert under `--reverify-o`.** The first `--exclude-numeric` run filtered only the stored-delta path. With `--reverify-o`, units come from the fresh re-verification, so its report was identical to the as-registered one. The filter now applies on both paths.
- **Partial accepts mislabelled.** Attempts with status `accepted_partial` were not counted as answered, so such a prompt was labelled `NOT_RUN`. It is now `PARTIAL_NOT_ACCEPTED`, and `skipped_ungroundable` is now `SKIPPED_UNGROUNDABLE`. Under §5.3 neither outcome earns units, as before, so no verdict depends on this change.

## Deviations recorded at the same time

- **Arm S ladder version.** Arm S ran on the ladder from main after the ladder fixes (#164: `accepted_partial`, `skipped_ungroundable`, the verifier fixes and the retrieval change) were merged into this branch. Its credit rule still counted numeric claims, because #165 was not yet merged. Arm F runs on the same ladder code.
- **Leak-guard refusal.** Control FQ-CONTINUUM-HILBERT-LIFT-CONSTRUCTION (stratum C) was refused by the leak guard. After the retrieval change, its packet contained the Arm F markers `GaussRat` and `HilbertLift`. It is recorded as not run. Stratum C carries no parity claim, so no decision depends on it.
