---
pattern_id: AP_MD_051
name: quoted_fraction_not_the_formula
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_051_quote_matches_recomputed_formula
language: markdown
authority_effect: None
---

# Anti-Pattern: Quoted Fraction Is Not The Formula (`AP_MD_051`)

## Description

A markdown proof quotes an exact rational at a named point. The formula printed beside that quote, or the function the proof says it quotes, evaluates to a different rational. A coarser inequality at the same point can still hold.

## Detection Signature

- The prose names both a printed fraction and the formula or function it claims to evaluate.
- Those two rationals differ.
- The same note says a weaker bound still holds.
- A test that asserts the function against itself does not pin the printed literal.
- Seen in the historical code-review record for PR 583 (`wrong-constant-in-paper`).
- A figure label that names the wrong vector is not this pattern. PR 581 panel B stays with `goo-figure-vector-arithmetic-integrity-gate`.

## Witness

Historical review, not a fresh recomputation. Source folder `_ic/nro/code_reviews/`. PR #583, head reviewed `f0c385f7c`, file `docs/meron_euclidean_thermodynamic_limit.md` line 475. This digest did not rerun the window arithmetic, pytest, or the independent script.

The review summary:

> The exact TL-12 constant quoted at theta=1/192, 5673203/46006272 (0.1233), does not equal window_floor(1/192) = 5706995/46006272 (0.1240); the printed number subtracted the second-moment term with ||W|| <= 11 (the brief's 128-scaling) instead of 11/2.

The failure scenario:

> A reader recomputing (3-t-t^2/4)/24 - 11t/78 at t=1/192 gets a different fraction than the written proof states; the conclusion (>= 1/9) survives, but the stated exact witness is wrong and the test could not catch it because it compared window_floor with itself.

The review says the repair commit `f10cc63f5` replaced the quoted constant with `5706995/46006272`. That sentence is historical. This digest did not open the monograph.

## Hazard & Failure Mode

- A reader copies `5673203/46006272` as `window_floor(1/192)`.
- A later note treats the surviving `>= 1/9` bound as a check of the printed fraction.
- The self-comparison test stays green after the printed literal changes.

## Dual Healthy Pattern

See [HP_MD_051_quote_matches_recomputed_formula](../../helpful/markdown/HP_MD_051_quote_matches_recomputed_formula.md).
