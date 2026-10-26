---
id: ENC-0133
kind: lemma
name: "AdmissionStatus Is Not OperatorClass"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §5.1 'Lemma (AdmissionStatus Is Not OperatorClass)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0133 — AdmissionStatus Is Not OperatorClass

## Statement

\(\mathrm{Repairable}(reason)\) does not imply class \(M\).

## Hypotheses

Verbatim setup from the source section:

> `OperatorClass` is mathematical role:
>
> ```text
> E, I, C, R, M
> ```
>
> `AdmissionStatus` is validator state:
>
> ```text
> Admitted(class)
> Repairable(reason)
> Refused(reason)
> ```

## Proof

A proposal can describe a mathematical operation of class \(R\) but
omit the deterministic TieR policy required for admission. The operation is not
a mutation; it is an under-specified residual projection. The validator should
return `Repairable(TiePolicyMissing)`, not `Refused(Mutation)`. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| separation witness: a class-\(R\) proposal with missing TieR is `Repairable(TiePolicyMissing)` and not class \(M\) | local | none identified | NOT-STARTED |

## Notes

- The lemma is unnamed in the source; the name is the §5.1 section heading.
- The source marks this section "**KEEP — net-new.** The `AdmissionStatus` vs
  `OperatorClass` distinction (`Repairable(reason) ≠ class M`) is not
  reproduced in canonical."
- Companion claim: [[ENC-0134]] UnadmittedRelation makes the same separation
  precise for residual projection without TieR.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §5.1 "AdmissionStatus Is Not
  OperatorClass" (statement and proof copied verbatim). Original header line:
  `**Lemma.** \(\mathrm{Repairable}(reason)\) does not imply class \(M\).`

## Changelog

- 2026-06-09: ENC-0133 created (M2 E2 satellite extraction).
