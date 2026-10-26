---
id: ENC-0140
kind: corollary
name: "Safe Compression Policy for I"
status: CONDITIONAL
conditional_on: ["fixed cochain layer", "exact or declared-tolerance arithmetic", "declared action domain", "replayable witnesses"]
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §6.5 'Corollary (Safe Compression Policy for I)'"
uses: ["ENC-0138", "ENC-0139"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0140 — Safe Compression Policy for I

## Statement

Every \(I\)-packet must declare one of:

```text
quotient_only
representative_composable
```

If it declares `quotient_only`, it may preserve \(\Phi_1\) and permute classes
in \(Q^1\), but it may not participate in `I·E` transport, representative
normal-form compression, or claims about transformed exact-repair witnesses.

If it declares `representative_composable`, it must provide enough data for
the verifier to check:

```text
I_C(d0 alpha) = d0 T_I(alpha)
```

for every exact-repair edge used by the packet, or for the entire declared
allowed domain if the packet claims global transport.

This resolves the witness rule: \(B^1\)-transport is required exactly at the
representative-composable boundary, not for quotient-only \(I_Q\).

## Proof

Work under the section-level hypotheses inherited from [[ENC-0138]] Transport
Witness Is Necessary for Representative Compression and [[ENC-0139]]
Quotient-Only I Cannot Transport E: a fixed cochain layer, exact or
declared-tolerance arithmetic, a declared action domain, and replayable
witnesses. The source's admission split has exactly the two policy declarations
named in the statement, `quotient_only` and `representative_composable`.

In the `quotient_only` case, [[ENC-0139]] forbids composing \(I_Q\) with
exact-repair transport as a representative-level map: the packet may act on
quotient classes and preserve \(\Phi_1\), but it lacks representative data.
Therefore it cannot justify claims about \(I\cdot E\), normal-form transport,
or transformed exact-repair witnesses.

In the `representative_composable` case, [[ENC-0138]] gives the missing
transport witness requirement: validity of the representative rewrite forces
the representative boundary equality. With the source's notation
\(\alpha' = T_I(\alpha)\), the verifier must be able to check

```text
I_C(d0 alpha) = d0 T_I(alpha)
```

on every exact-repair edge used by the packet, or globally on the declared
domain if the packet claims global transport. These two cases cover the safe
compression boundary: either the packet stays quotient-only and makes no
representative transport claim, or it supplies the representative witness that
licenses such a claim.

## Hypotheses

- The same section-level blanket hypotheses propagated from [[ENC-0138]] and
  [[ENC-0139]]: fixed cochain layer, exact or declared-tolerance arithmetic,
  declared action domain, and replayable witnesses.
- The packet declaration is interpreted under the source's §6.5/§8.12 admission
  split between quotient-only \(I_Q:Q^1\to Q^1\) and
  representative-composable \(I_C:C^1\to C^1\).

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| policy soundness: the two-way declaration plus witness check excludes every ill-typed or witness-free `I·E` compression | local | depends on ENC-0138/ENC-0139 mechanization | NOT-STARTED |

## Notes

- The source carries no separate proof body for this corollary. The proof above
  derives the policy from the source's admission split plus [[ENC-0138]]
  (transport witness necessity) and [[ENC-0139]] (quotient-only \(I_Q\) is not
  composable with \(E_\alpha\)). Status is therefore CONDITIONAL, not
  PROVED-PROSE: the inherited section-level hypotheses remain active.
- Section-level blanket from the source (§6 preamble): "All results in this
  section are conditional on a fixed cochain layer, exact or
  declared-tolerance arithmetic, a declared action domain, and replayable
  witnesses."
- Kept net-new per the source's §6.5 KEEP note (the `I_Q`/`I_C` admission
  split is finer than canonical §IV.5).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §6.5 "I Admission Split and
  Transport Witness Rule" (statement copied verbatim). Original header line:
  `#### Corollary: Safe Compression Policy for I`

## Changelog

- 2026-06-09: ENC-0140 created (M2 E2 satellite extraction).
- 2026-06-12: OPEN → SKETCH. Added two-case policy soundness sketch from
  [[ENC-0138]] and [[ENC-0139]].
- 2026-06-20: SKETCH → CONDITIONAL. Promoted the two-case policy argument to a
  proof while propagating the section-level hypotheses from [[ENC-0138]] and
  [[ENC-0139]]; no PROVED-PROSE claim is made.
