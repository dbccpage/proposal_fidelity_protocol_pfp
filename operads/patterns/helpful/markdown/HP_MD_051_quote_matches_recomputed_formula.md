---
pattern_id: HP_MD_051
name: quote_matches_recomputed_formula
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_051_quoted_fraction_not_the_formula
language: markdown
authority_effect: None
---

# Healthy Pattern: The Quote Matches The Recomputed Formula (`HP_MD_051`)

## Description

When a markdown proof names an exact rational, the note also names the formula or function and the rational the review says recomputation returns. If those rationals differ, the printed literal is not the witness. A coarser inequality keeps its own statement.

## Construction

- Write the printed fraction and the recomputed fraction in the same sentence.
- For the historical TL-12 row, do not call `5673203/46006272` the value of `window_floor(1/192)`. The review states `window_floor(1/192) = 5706995/46006272`.
- Keep `>= 1/9` as the inequality the review says survived. It does not certify the printed fraction.
- A repair test pins the printed literal. A test that only asserts the function against itself does not repair this row.
- Do not recompute the formula in this digest. Both rationals above are quoted from the historical review.

## Limit

The witness in [AP_MD_051_quoted_fraction_not_the_formula](../../anti/markdown/AP_MD_051_quoted_fraction_not_the_formula.md) is the 2026-10-07 PR #583 review. No arithmetic, pytest, or paper command was rerun. The monograph was not opened.

`goo-figure-vector-arithmetic-integrity-gate` still owns PR #581 panel B, which labels `(-3, -3, 6)` as the L^2 residual while the review says the harmonic part is `(3, 3, 3)`. That row is `wrong-constant-in-paper` on a figure, not this printed-fraction pattern.

`AP_MD_001` still owns stale advertised commands, version-date strings, and reproduction lines, including this PR's `stale-doc-vs-code` rows and the brief command that exits 1 under the coverage addopts. The status header, the `theta>1/128` versus `(0, 1/96]` non-claim list, and the `w_cases` docstring stay there.

The brief route `SECOND_MOMENT_BOUND` names the same `||W|| <= 11` and 128-scaling. It is the stated cause of this printed fraction, not a second pattern.

`/adversary-proof-scope-rule` still keeps the written TL-3/TL-4 estimates outside the finite checks. The review says those estimates remain prose. This pattern does not certify them.

The self-comparison `window_floor == window_floor` stays with the test-quality law and `/adversary-check-sensitivity-pattern`. The missing support-radius witness is a different row and was not given this id. The ring diagnostic with no retained source was not given this id. `AP_MD_014` still owns a pass verdict whose counted payload is zero. PR #588's scan that returns `[]` and completes PASS is not this pattern.

## Dual Anti-Pattern

See [AP_MD_051_quoted_fraction_not_the_formula](../../anti/markdown/AP_MD_051_quoted_fraction_not_the_formula.md).
