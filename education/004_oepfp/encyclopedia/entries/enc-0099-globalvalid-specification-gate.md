---
id: ENC-0099
kind: theorem
name: "GlobalValid Specification Gate"
status: DEFINED
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:VII.3", "po:PO-PFVS"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §VII.3 'Theorem VII.3'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0099 — GlobalValid Specification Gate

## Statement

Strengthens
Theorem IV.11. Every admitted packet family declares the triple
(**Specification** \(S_F\); **Validator** \(V_F=\bigwedge_i C_i\) with the
clause set \(\{C_i\}\) **fixed independent of the input \((x,P)\)**;
**SoundnessStatus** = the lemmas \(\{C_i\Rightarrow\varphi_i\}\) and the
entailment \(\bigwedge_i\varphi_i\Rightarrow S_F\)). No validator may emit
\(\mathsf{GlobalValid}\) without a named \(S_F\); with the clause set fixed this
is **entailed, not stipulated** — a \(\mathsf{GlobalValid}\) carrying no named
\(S_F\) is a verdict whose predicate \(S_F(x,P)\) has no referent (ill-typed).
Verifier-relative throughout (Theorem IV.3; the C4 verifier-soundness axiom,
catalog audit #11, is located not eliminated). See PO-PFVS.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| typed gate: $\mathsf{GlobalValid}$ constructible only with a named $S_F$ and a fixed clause set (ill-typedness of referent-free verdicts) | local | none identified | NOT-STARTED |

## Notes

- The source tag is the non-standard `[SPECIFIED]` (verbatim). The statement is a
  specification gate (the section heading reads "GlobalValid Specification Gate
  (PO-PFVS done condition)"): it declares what every admitted packet family must
  carry; no proof is claimed in the source and none is restated here. Normalized to
  DEFINED — not upgraded to any PROVED status.
- The PO-name PO-PFVS appears in the source section heading and in the statement body
  ("See PO-PFVS.").

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §VII.3
  (statement copied verbatim). Original header line:
  `**Theorem VII.3 (GlobalValid Specification Gate).** [SPECIFIED] Strengthens`

## Changelog

- 2026-06-09: ENC-0099 created (M2 E1 extraction).
