---
pattern_id: AP_MD_031
name: enumeration_baseline_credits_cochain
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_031_direct_baseline_before_cochain_gain
language: markdown
authority_effect: None
---

# Anti-Pattern: Enumeration Baseline Credits The Cochain (`AP_MD_031`)

## Description

An efficiency sentence compares a cochain reconstruction only with brute-force enumeration. The drop in checker calls is the generic gain of using the linear structure. A direct reconstruction already has that gain. The cochain encoding is then credited with it, and the extra representation work is omitted.

## Detection Signature

- The comparison class for an efficiency claim is enumeration or brute force alone.
- A direct reconstruction that uses the same linear structure is missing, or its checker-call count is not stated.
- The cochain method adds a scalar, a canonical closure check, or other representation work that is not in the comparison.
- The gap versus enumeration is then called a cochain or encoding advantage.

## Witness

Historical review and receipts, not a fresh experiment. This digest did not rerun native tests, the replay, lake, or XeLaTeX. Run `wdp_question_encoding_20261008`, read from `_ic/darpa/research/`. Audit row `QPE_AUDIT_4` in `wdp_question_encoding_inputs/r1_stage3.json` says:

> Comparing a cochain reconstruction only with brute force would attribute a generic linear-structure gain to cochains.

`wdp_question_encoding_inputs/r1_stage4.json` records the counted comparison that blocks that attribution:

> Enumeration uses 20375 checker calls; direct and cochain reconstruction each use 125. Cochain adds one scalar and one canonical closure check per successful proposal; no advantage over the strong direct baseline is established.

`wdp_question_encoding_receipts/validation_summary.json` keeps the same limit: "The cochain reconstruction has no measured gain over direct reconstruction." `r1_stage6.json` says: "Enumeration counts agree with the finite ranks, and the stronger direct reconstruction baseline prevents attributing its algebraic benefit to cochains." The frozen result states that negative comparison. It does not itself assert a cochain speedup. Do not treat these quotes as a fresh measurement or as evidence that a current manuscript still omits the direct baseline.

## Hazard & Failure Mode

- A later note cites 20375 enumeration checks against 125 cochain checks and calls that an encoding advantage.
- Direct reconstruction, which uses the same 125 checks, drops out of the summary.
- The added cochain closure and representation work disappears, and the finite count is generalized to wall-clock cost or to another workload.

## Dual Healthy Pattern

See [HP_MD_031_direct_baseline_before_cochain_gain](../../helpful/markdown/HP_MD_031_direct_baseline_before_cochain_gain.md).
