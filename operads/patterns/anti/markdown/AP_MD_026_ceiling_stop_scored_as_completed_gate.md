---
pattern_id: AP_MD_026
name: ceiling_stop_scored_as_completed_gate
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_026_ceiling_stop_keeps_unscored_rows
language: markdown
authority_effect: None
---

# Anti-Pattern: Ceiling Stop Scored As A Completed Gate (`AP_MD_026`)

## Description

A review report says a snapshot byte-limit stop was eliminated and that the republication gate then finished with PASS and FAIL totals. The receipt in the same folder has one FAIL, the detail that no partial PASS is permitted, and the predicates named in that scoreboard are NOT_VERIFIED.

## Detection Signature

- The republication receipt `status` is `BLOCKED`.
- `counts` are `FAIL` 1 and `NOT_VERIFIED` 51, with no `PASS` count.
- Check `A01` is `FAIL`, and its detail says the snapshot byte limit was exceeded and no partial PASS is permitted.
- The report assigns 20 `PASS` and 5 `FAIL`, and it names `A04`, `A05`, `A07`, `F01`, and `H05` as `FAIL`.
- Those five ids are `NOT_VERIFIED` in the receipt.
- The same report still asks what to do with the oversized tar.

## Witness

Historical receipts. This digest did not rerun the gate, rebuild the archive, or open the tar. Source folder `_ic/inr/omega_paper_reviews/symbol_game_swarm_2026-10-02/`.

`004_the_symbol_game_native_verification_and_evidence_custody/republication_gate_receipt.json` has `status` `BLOCKED`. Check `A01` is `FAIL`. Its detail is:

> snapshot byte limit exceeded; no partial PASS is permitted

`counts` are `FAIL` 1 and `NOT_VERIFIED` 51. `A04`, `A05`, `A07`, `F01`, and `H05` are `NOT_VERIFIED`. `snapshot_sha256` is empty and `files` is empty.

`THE_SYMBOL_GAME_SWARM_REVIEW_REPORT.md` says:

> resolving the snapshot ceiling failure. Stage Ω gate now runs cleanly to completion (20 static predicates PASS, 5 FAIL on manifest bijection/quiz placeholders).

The same file later says:

> 20 static predicates `PASS`, 5 `FAIL` (`A04`, `A05`, `A07`, `F01`, `H05`), 27 `NOT_VERIFIED`. The snapshot byte limit blocker was eliminated

The next-test bullet in that file still names `audited_source/pfp-iv-native-source-52cb5457.tar` at 90.9 MB.

Papers 002 and 003 in this folder have receipt counts that match the report's Stage Ω bullets. Those bullets are not this pattern.

## Hazard & Failure Mode

- A later note treats `A04`, `A05`, `A07`, `F01`, and `H05` as scored manifest or notebook failures.
- A compression sentence is cited as a repair the receipt did not record.
- `no partial PASS` drops out, so 51 unscored rows look like a finished gate.

## Dual Healthy Pattern

See [HP_MD_026_ceiling_stop_keeps_unscored_rows](../../helpful/markdown/HP_MD_026_ceiling_stop_keeps_unscored_rows.md).
