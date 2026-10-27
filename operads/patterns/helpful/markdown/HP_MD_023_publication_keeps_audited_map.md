---
pattern_id: HP_MD_023
name: publication_keeps_audited_map
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_023_zero_exit_publishes_later_bytes
language: markdown
authority_effect: None
---

# Healthy Pattern: Publication Keeps The Audited Map (`HP_MD_023`)

## Description

A zero audit exit is cited with both source maps. If any path differs, the publication is a later read, not the build's bytes. The downstream rejection stays in the same sentence.

## Construction

- Put `audit_exit`, `actual_lean_executed`, and `downstream_snapshot_reader` in one sentence. Exit 0 with `LEAN_SNAPSHOT_INVALID` is a false-success publication.
- Quote both hashes for every path that differs. Here that path is `Fixture.lean`. Matching hashes on the other four files do not repair it.
- Do not call the downstream reader bypassed. The historical review says it rejected the inconsistent map.
- A later closure that refuses `LEAN_SOURCE_CHANGED` is a different run. Do not merge its clean `returncode` 0 into the race receipt.
- The reproduction script's own exit 0 means its assertions about the race held. It is not an audit pass.

## Limit

The witness in [AP_MD_023_zero_exit_publishes_later_bytes](../../anti/markdown/AP_MD_023_zero_exit_publishes_later_bytes.md) is the historical folder `pfp_swarm_2026-09-27`, fixture `audit_after_collect_521w3h78`. No probe, pytest, republication gate, notebook, or Lean build was rerun. `actual_lean_executed` is false. The manuscript repair described in `math_review.md` is a historical claim of that review, not a fresh execution in this digest.

Preflight `PASS` beside Stage Ω `BLOCKED` stays with `/adversary-check-sensitivity-pattern`. This folder's `after/001-preflight.json` has `returncode` 0 and `preflight_verdict` `PASSED` together; that pair is not `AP_MD_009`. `after/001-republication-gate.json` has `returncode` 1 and `status` `BLOCKED`. A path over 250 characters stays with `AP_MD_017`. A gate error called mathematical research stays with `AP_MD_016`. `/adversary-proof-scope-rule` still separates mocked custody from a Lean proof. `/adversary-check-sensitivity-pattern` still says a downstream check that catches the mutation is not a refutation of every later check.

A zero exit on an unchanged map can still be a real local publication of those bytes. This pattern only refuses to ignore a hash that changed between the build receipt and the audit receipt.

## Dual Anti-Pattern

See [AP_MD_023_zero_exit_publishes_later_bytes](../../anti/markdown/AP_MD_023_zero_exit_publishes_later_bytes.md).
