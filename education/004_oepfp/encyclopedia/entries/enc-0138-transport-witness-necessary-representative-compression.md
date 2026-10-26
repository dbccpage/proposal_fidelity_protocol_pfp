---
id: ENC-0138
kind: theorem
name: "Transport Witness Is Necessary for Representative Compression"
status: CONDITIONAL
conditional_on: ["fixed cochain layer", "exact or declared-tolerance arithmetic", "declared action domain", "replayable witnesses"]
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §6.5 'Theorem (Transport Witness Is Necessary for Representative Compression)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0138 — Transport Witness Is Necessary for Representative Compression

## Statement

Assume \(I_C:C^1\to C^1\) is additive on the relevant representative domain.
If the rewrite:

\[
I_C\circ E_\alpha = E_{\alpha'}\circ I_C
\]

is valid as an equality of representative-level maps, then:

\[
I_C(d_0\alpha)=d_0\alpha'.
\]

## Proof

Evaluate both sides at the zero representative \(0\in C^1\). Since
\(E_\alpha(0)=d_0\alpha\) and additivity gives \(I_C(0)=0\):

\[
(I_C\circ E_\alpha)(0)=I_C(d_0\alpha),
\]

while:

\[
(E_{\alpha'}\circ I_C)(0)=E_{\alpha'}(0)=d_0\alpha'.
\]

Equality of the maps implies equality of these values, so
\(I_C(d_0\alpha)=d_0\alpha'\). \(\square\)

## Hypotheses

- Section-level blanket from the source (§6 preamble), verbatim: "All results
  in this section are conditional on a fixed cochain layer, exact or
  declared-tolerance arithmetic, a declared action domain, and replayable
  witnesses." (This is the `conditional_on` list.)
- \(I_C\) is a representative-composable isometry: a declared lift
  \(I_C:C^1\to C^1\) with a replayable transport rule, quotient-well-defined
  (\(x-y\in B^1\Rightarrow I_C(x)-I_C(y)\in B^1\)), per the §6.5 admission
  split.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| evaluate-at-zero argument: representative-level rewrite validity forces \(I_C(d_0\alpha)=d_0\alpha'\) under additivity | local | none identified | NOT-STARTED |

## Notes

- The source marks §6.5 "**KEEP — net-new (finer than canonical).** The split
  of admitted quotient isometries into quotient-only `I_Q` vs
  representative-composable `I_C`, with the transport-witness-necessity theorem
  and the 'quotient-only `I` cannot transport `E`' theorem, is finer than
  canonical §IV.5 (which states the `I·E` transport identity but not this
  admission split)."
- The source adds after the proof, verbatim: "Thus the transport witness is not
  optional for representative compression; it is exactly the value needed to
  make the rewrite true."
- Companions: [[ENC-0139]] Quotient-Only I Cannot Transport E and [[ENC-0140]]
  Safe Compression Policy for I. The canonical `I·E` transport identity lives
  in the §IV.5 identities table (cf. [[ENC-0101]] Fixed-Layer Operator
  Algebra).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §6.5 "I Admission Split and
  Transport Witness Rule" (statement and proof copied verbatim). Original
  header line:
  `#### Theorem: Transport Witness Is Necessary for Representative Compression`

## Changelog

- 2026-06-09: ENC-0138 created (M2 E2 satellite extraction).
