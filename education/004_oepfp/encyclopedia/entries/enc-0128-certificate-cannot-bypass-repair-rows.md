---
id: ENC-0128
kind: corollary
name: "Certificate Cannot Bypass Repair Rows"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "symbol_game_math_spine.md trunk Part III §3.3 'Corollary (Certificate Cannot Bypass Repair Rows)'"
uses: ["ENC-0127"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_terminalizer_policy.lean"
  - "PaperER007.refusal_rows_preempt_certificate"
  - "PaperER007.repair_rows_preempt_certificate"
  - "PaperER007.refusal_or_repair_preempts_certificate"
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0128 — Certificate Cannot Bypass Repair Rows

## Statement

Under the first-match
table, a packet with `TiePolicyMissing`, `TerminalMismatch`, `Suboptimal`,
`EvidenceCeilingExceeded`, or repairable boundary violation cannot terminalize
as `Certificate`.

## Proof

Each listed predicate matches a higher-priority repair row than the
certificate row. First-match evaluation stops before row 7. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| no listed repair-class predicate reaches the certificate row under first-match evaluation of the 8-row table | local | none identified | NOT-STARTED |

## Notes

- "The first-match table" is the concrete 8-row terminalizer policy table of
  [[ENC-0127]] (same source section), whose statement reproduces the table
  verbatim under Hypotheses.

- PaperER007 reconciliation (2026-07-19): PaperER007 mechanizes refusal and repair preemption for its finite first-match report model. This supports the exact routing claim only; it is not a terminal seal or authority theorem. AuthorityEffect remains None.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §3.3 "Concrete Terminalizer Policy
  Table" (statement and proof copied verbatim). Original header line:
  `**Corollary (Certificate Cannot Bypass Repair Rows).** Under the first-match`

## Changelog

- 2026-06-09: ENC-0128 created (M2 E2 satellite extraction).
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
