---
id: ENC-0102
kind: proposition
name: "Syntactic Non-Introduction of $M$"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IX.2"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IX.1 'Proposition IX.2'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0102 — Syntactic Non-Introduction of $M$

## Statement

No admitted
rewrite rule over $\{E,I,C,R\}$ has the refused class $M$ in its codomain; hence rewriting a
word over $\{E,I,C,R\}$ never *introduces* $M$.

## Proof

*Proof.* Every admitted §IV.5 rule
($E\circ E$, $R\circ R$, $R\circ E$, $I\circ E$) has codomain in $\{E,I,C,R\}^\ast$; by
Thm IV.12 un-witnessed rules are refused, not applied. $\square$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| codomain check over the admitted rewrite rule table: no rule has $M$ in its codomain (syntactic non-introduction) | local | none identified | NOT-STARTED |

## Notes

- The source tag is `[PROVED — syntactic]` (verbatim); normalized to PROVED-PROSE.
  The "syntactic" qualifier is load-bearing — see the next note.
- The source immediately follows the proposition with this scope-limiting note (verbatim):
  "**Note (semantic closure deferred).** This is the *syntactic* statement. *Semantic* closure —
  that every admissible composite is itself admissible and never refuses to $M$ — is a stronger
  claim requiring the rewrite system to be complete/confluent; it is part of obligation
  IX-REWRITE and is **not** established here. (The earlier "the monoid is closed" phrasing
  conflated rewrite *soundness* with *closure*.)"
- Statement label is "Proposition IX.2"; the source also has a section heading
  "### IX.2 The Lift Boundary and Cross-Layer Single Excursion" later in §IX — the
  alias `spine:IX.2` here refers to the proposition, which lives under the section
  heading "### IX.1 The Fixed-Layer Class Monoid $\mathcal{O}_n$".

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IX.1
  (statement and proof copied verbatim; the *Proof.* is inline in the source
  paragraph). Original header line:
  `**Proposition IX.2 (Syntactic Non-Introduction of $M$).** [PROVED — syntactic] No admitted`

## Changelog

- 2026-06-09: ENC-0102 created (M2 E1 extraction).
