---
id: ENC-0104
kind: definition
name: "Forced Lift"
status: DEFINED
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IX.4"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IX.2 'Definition IX.4'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0104 — Forced Lift

## Statement

The fixed-layer algebra $\mathcal{O}_n$ is *sufficient*
until a context embedding $C$ produces a witness $w=(x,y,c)\in W_n$ that cannot be resolved
by any layer-$n$ repair or isometry (the quantifier below ranges over $E,I$ only: $C$
*produced* the witness and $R$ merely selects a representative, so neither discharges a
context-congruence failure):

$$
\exists\, w=(x,y,c)\in W_n : \quad \forall\, o_E,o_I \in \mathcal{O}_n,\quad
o_E\circ o_I(x) \not\sim_n o_E\circ o_I(y) \ \text{under context}\ c .
$$

At that point a **lift is forced**: the `LiftContract` authorizes
$\mathcal{O}_{n+1}=\mathcal{O}_n\cup\Delta\mathcal{O}_n$, where $\Delta\mathcal{O}_n$ is the
minimal declared operator family resolving the witnesses. What is **fixed** across the lift:
the five-class taxonomy $(E,I,C,R,M)$, the first-match priority rule, the rewrite table, and
the length-$\le 4$ compression bound. What **grows**: the carrier $C_n^\bullet$ (new
dimensions), the operator registry (new $E,I,C,R$ instances), the admissible-context set, and
the $S(n)$ level.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| formalize the forced-lift trigger predicate (unresolvable context witness over $E,I$) and the `LiftContract` extension $\mathcal{O}_{n+1}=\mathcal{O}_n\cup\Delta\mathcal{O}_n$ | local | none identified | NOT-STARTED |

## Notes

- The source section (§IX.2 The Lift Boundary and Cross-Layer Single Excursion)
  continues after this definition with a separate doctrinal paragraph,
  "**Cross-layer single-excursion discipline.**" (the inter-layer transport $\Lambda$ /
  descent–lift $D$ applied at most once per word, only with a declared transport
  certificate $\chi$; absent $\chi$ the terminal is a transport-coherence refusal). That
  paragraph is section prose, not part of Definition IX.4, and is not extracted here.
- The definition's frozen "length-$\le 4$ compression bound" tracks Theorem IX.3 as
  stated; §IX.1a refines that composition result (see ENC-0103 Notes).

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IX.2
  (statement copied verbatim; the source header carries no status bracket).
  Original header line:
  `**Definition IX.4 (Forced Lift).** The fixed-layer algebra $\mathcal{O}_n$ is *sufficient*`

## Changelog

- 2026-06-09: ENC-0104 created (M2 E1 extraction).
