---
id: ENC-0119
kind: lemma
name: "Pipeline Evidence Routing Relation Is a Total Order"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.6 'Lemma (unnamed)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0119 — Pipeline Evidence Routing Relation Is a Total Order

## Statement

The routing relation above is a total order.

## Hypotheses

"The routing relation above" is the source's pipeline routing-level chain,
defined immediately before the lemma, verbatim:

Define the pipeline routing levels:

```text
GrammarOnly < SchemaChecked < LocalReplay < BoundaryChecked < ExternalOracle
```

This is a routing convention, not an absolute truth-strength theorem.
`ExternalOracle` means "routed outside the local verifier boundary." Its
mathematical strength depends on the oracle type, scope, and trust model.

## Proof

It is defined by listing five distinct elements in sequence and
using index order. Integer order on indices is total. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| totality of the five-element index order on the SG routing levels | local | none identified | NOT-STARTED |

## Notes

- The lemma is unnamed in the source; the entry name is editorial (descriptive
  of the section content), not a source label.
- The source's KEEP note flags this row UNCERTAIN and explains why it is NOT a
  duplicate of the canonical ceiling chain: the carrier differs — "this route
  order uses `GrammarOnly/SchemaChecked/LocalReplay/BoundaryChecked/
  ExternalOracle` whereas canonical `𝔼` uses `ShapeOnly/LocalReplay/
  BoundaryChecked/ExternalOracleRequired/EmpiricalOracleRequired`. The
  route-specific lattice is not the canonical `𝔼`". See-also [[ENC-0045]]
  (Canonical Ceiling Chain 𝔼, Def II.11) and [[ENC-0046]] (Ceiling
  Reconciliation, Thm II.12).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.6 "Pipeline
  Evidence Level Normalization" (statement, hypotheses context, and proof
  copied verbatim). Original header line:
  `**Lemma.** The routing relation above is a total order.`

## Changelog

- 2026-06-09: ENC-0119 created (M2 E2 satellite extraction).
