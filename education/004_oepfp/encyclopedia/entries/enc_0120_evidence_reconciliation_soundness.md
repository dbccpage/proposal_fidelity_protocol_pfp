---
id: ENC-0120
kind: theorem
name: "Evidence Reconciliation Soundness"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.7 'Theorem (Evidence Reconciliation Soundness)'"
uses: ["ENC-0119"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0120 — Evidence Reconciliation Soundness

## Statement

Suppose:

1. every legacy evidence value used by a packet is mapped by a total
   deterministic \(\rho_i\);
2. every validator, terminalizer, and packet-fidelity rule compares evidence
   only after applying \(\rho_i\);
3. no rule interprets `ExternalOracle` as truth, only as a route outside the
   local verifier boundary; and
4. every packet with evidence route \(e\) and ceiling \(c\) is accepted only if
   \(\mathrm{Allowed}(e,c)\) holds.

Then evidence-level reconciliation is deterministic and cannot assert that an
external oracle is mathematically stronger than boundary checking.

## Hypotheses

The source fixes the carrier and maps immediately above the theorem, verbatim:

Let:

```text
SymbolGameEvidenceRoute =
  GrammarOnly
  | SchemaChecked
  | LocalReplay
  | BoundaryChecked
  | ExternalOracle
```

with the routing order declared in section 1.6. This is a Symbol Game routing order, not the canonical evidence ceiling `e`.
A map into the canonical evidence ceiling must be declared before cross-spine use. It is a workflow order:
it says which pipeline boundary a packet has reached. It is not an order of
mathematical truth, proof strength, or customer-facing authority.

Let each legacy evidence enum \(E_i\) have a declared total map:

\[
\rho_i:E_i\to SymbolGameEvidenceRoute.
\]

Let:

\[
\mathrm{Allowed}(e,c)
\]

mean that evidence route \(e\) is allowed under the evidence ceiling \(c\).
The only semantic use of evidence levels is this finite predicate plus routing
decisions that explicitly mention it.

## Proof

Determinism follows because each \(\rho_i\) is a total function and
`SymbolGameEvidenceRoute` is finite. All comparisons reduce to finite lookup in the
canonical route set. Ceiling safety follows from assumption 4: if
\(\mathrm{Allowed}(e,c)\) fails, acceptance is impossible. Since assumption 3
forbids interpreting `ExternalOracle` as a truth-strength proposition, no
accepted packet can derive a mathematical-strength claim from the route order.
Thus reconciliation normalizes evidence routing without adding a truth claim.
\(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| determinism + ceiling safety + no-truth-strength for legacy-enum reconciliation onto the SG route | local | none identified | NOT-STARTED |

## Notes

- The routing order on `SymbolGameEvidenceRoute` is [[ENC-0119]] (§1.6 lemma).
- The source's KEEP note flags this row UNCERTAIN: the reconcile-onto-one-chain
  idea overlaps canonical Theorem II.12 (Ceiling Reconciliation, [[ENC-0046]]),
  "but the route carrier and the route-specific `ρ_i` / `Allowed(e,c)` machinery
  are not reproduced in canonical (different element sets per §1.6). Kept with a
  see-also to §II.7 Thm II.12. Flagged."

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.7 "Evidence
  Level Reconciliation" (statement, hypotheses, and proof copied verbatim).
  Original header line:
  `**Theorem (Evidence Reconciliation Soundness).** Suppose:`

## Changelog

- 2026-06-09: ENC-0120 created (M2 E2 satellite extraction).
