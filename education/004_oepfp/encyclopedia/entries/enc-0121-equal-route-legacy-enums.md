---
id: ENC-0121
kind: corollary
name: "Equal-Route Legacy Enums Are Routing-Interchangeable, Provenance-Preserving"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.7 'Corollary (unnamed)'"
uses: ["ENC-0120"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0121 — Equal-Route Legacy Enums Are Routing-Interchangeable, Provenance-Preserving

## Statement

If two legacy evidence enums map to the same
`SymbolGameEvidenceRoute`, the pipeline may treat them identically for routing and
ceiling checks, but it may not erase oracle provenance, trust model, or scope
unless those fields are separately declared non-semantic.

## Proof

The theorem covers route equality only. Oracle provenance, trust
model, and scope are not elements of `SymbolGameEvidenceRoute`; if they affect packet
semantics, they must be carried in the packet family or oracle policy fields.
\(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| route-equality interchangeability with provenance/trust/scope non-erasure | local | none identified | NOT-STARTED |

## Notes

- The corollary is unnamed in the source; the entry name is editorial.
- "The theorem" in the proof is Evidence Reconciliation Soundness,
  [[ENC-0120]] (same §1.7).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.7 "Evidence
  Level Reconciliation" (statement and proof copied verbatim). Original header
  line:
  `**Corollary.** If two legacy evidence enums map to the same`

## Changelog

- 2026-06-09: ENC-0121 created (M2 E2 satellite extraction).
