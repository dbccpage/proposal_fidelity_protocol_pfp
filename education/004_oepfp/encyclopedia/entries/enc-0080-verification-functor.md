---
id: ENC-0080
kind: definition
name: 'Verification Functor $\mathcal{V}$'
status: DEFINED
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.1"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.1 'Definition IV.1'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0080 — Verification Functor $\mathcal{V}$

## Statement

Fix a task family $X$, a finite packet grammar $\Gamma$, a total deterministic parser $\mathrm{Parse}_\Gamma$, a local replay checker $L_\Gamma$, and a global boundary verifier $V_\Gamma$. The verification functor is the composite:

$$
\mathcal{V} : \mathbf{Packet}(\Gamma) \to \{\mathsf{ParseError},\, \mathsf{LocalInvalid},\, \mathsf{LocalValidGlobalInvalid},\, \mathsf{GlobalValid}\}
$$

defined by the sequential evaluation:

1. $\mathrm{Parse}_\Gamma(P)$. Failure $\Rightarrow \mathsf{ParseError}$.
2. $L_\Gamma(x, P)$. Failure $\Rightarrow \mathsf{LocalInvalid}$.
3. $V_\Gamma(x, P)$. Failure $\Rightarrow \mathsf{LocalValidGlobalInvalid}$.
4. Otherwise $\Rightarrow \mathsf{GlobalValid}$.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| definition of the four-outcome sequential verification functor \(\mathcal{V}\) over \(\mathbf{Packet}(\Gamma)\) | local | none identified | NOT-STARTED |

## Notes

- §IV.1 is titled "The Verification Functor (Proofer Mode)".

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.1
  (statement copied verbatim; definition carries no status bracket).
  Original header line:
  `**Definition IV.1 (Verification Functor $\mathcal{V}$).** Fix a task family $X$, a finite packet grammar $\Gamma$, a total deterministic parser $\mathrm{Parse}_\Gamma$, a local replay checker $L_\Gamma$, and a global boundary verifier $V_\Gamma$. The verification functor is the composite:`

## Changelog

- 2026-06-09: ENC-0080 created (M2 E1 extraction).
