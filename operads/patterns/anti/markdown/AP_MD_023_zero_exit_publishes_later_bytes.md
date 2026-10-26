---
pattern_id: AP_MD_023
name: zero_exit_publishes_later_bytes
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_023_publication_keeps_audited_map
language: markdown
authority_effect: None
---

# Anti-Pattern: Zero Exit Publishes Later Bytes (`AP_MD_023`)

## Description

A Lean audit publication returns 0 and writes an audit receipt from a later source read. The build receipt in the same folder also has returncode 0, but one source hash differs. Quoting either return code as a hash-bound audit drops that difference. The downstream snapshot reader already rejects the pair.

## Detection Signature

- `lean_audit_race.audit_exit` is 0 and `audit_receipt_returncode` is 0.
- `actual_lean_executed` is false, `post_collect_source_published` is true, and `build_audit_source_hashes_differ` is true.
- `downstream_snapshot_reader` is `LEAN_SNAPSHOT_INVALID`.
- In the preserved fixture, `build_receipt.json` and `axiom_audit_receipt.json` both have `returncode` 0, and `Fixture.lean` is not the same hash.

## Witness

Historical receipts. This digest did not rerun the probe, pytest, the republication gate, or Lean. Source folder `_ic/inr/omega_paper_reviews/pfp_swarm_2026-09-27/`.

`math_probe_results.json`:

> "audit_exit": 0,
> "audit_receipt_returncode": 0,
> "actual_lean_executed": false,
> "mock_report_observed_original": true,
> "post_collect_source_published": true,
> "build_audit_source_hashes_differ": true,
> "downstream_snapshot_reader": "LEAN_SNAPSHOT_INVALID",

`audit_after_collect_521w3h78/evidence/v2/lean/build_receipt.json` records `Fixture.lean` as `30f81fbfd599efeb0ea51f874085c9fb36aabf773e6025f6ca2d94ddb1164927` with `returncode` 0 and `sources_stable` true. `axiom_audit_receipt.json` in that same directory records `Fixture.lean` as `709ffd3928406dedcd56d088720a9f8e5b20dba64ad1d172a862b733e51808e6` with `returncode` 0. The other four source hashes match.

`math_review.md`:

> This is a false successful audit publication and invalid output, **not a demonstrated bypass of the downstream snapshot reader**. No actual Lean theorem was compiled during this probe.

## Hazard & Failure Mode

- A later note treats `audit_exit` 0 as proof that the published bytes were the audited bytes.
- The disagreeing `Fixture.lean` hash and `LEAN_SNAPSHOT_INVALID` drop out of the summary.
- `actual_lean_executed: false` is read as a Lean kernel pass.
- The false-success receipt is then used as if the downstream snapshot reader had accepted it.

## Dual Healthy Pattern

See [HP_MD_023_publication_keeps_audited_map](../../helpful/markdown/HP_MD_023_publication_keeps_audited_map.md).
