---
id: ENC-0893
kind: theorem
name: "Diagnostic Rank and Refusal Calibration Are Non-Authority"
status: MECHANIZED
conditional_on:
  - "Rank suggestions carry an explicit AuthorityEffect field"
  - "Refusal calibration is modeled by false-refusal count bounded by a declared budget"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:diagnostic-rank-refusal-calibration"]
sources:
  - "s_n_packets_and_the_symbol_game.md §9 'Theorem 12: Ranking and Refusal Calibration Are Diagnostic'"
  - ".planning/2026-06-12-immune-review.md §20 'Missing Theorem List'"
uses: ["ENC-0803", "ENC-0804", "ENC-0890"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0893 - Diagnostic Rank and Refusal Calibration Are Non-Authority

## Statement

A diagnostic rank suggestion has authority effect `none`. If false refusals are
bounded by the declared false-refusal budget, the autoimmune-exceeded predicate
is false. With zero false-refusal budget, calibration forces zero false
refusals.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.diagnostic_rank_suggestion_non_authority`
- `SnSymbolGameAndPackets.calibrated_refusal_not_autoimmune_exceeded`
- `SnSymbolGameAndPackets.zero_false_refusal_budget_forces_zero_false_refusals`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This entry does not prove [[ENC-0803]] inverse residual PageRank stability.
- This entry does not prove a product-level [[ENC-0804]] autoimmune refusal
  bound. It supplies the finite calibration contract that such a product proof
  would have to instantiate.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass.

## Changelog

- 2026-06-13: ENC-0893 created with Lean mechanization.

