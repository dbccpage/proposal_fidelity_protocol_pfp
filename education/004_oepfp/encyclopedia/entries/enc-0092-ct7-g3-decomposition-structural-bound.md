---
id: ENC-0092
kind: theorem
name: "CT-7: G3 Decomposition & Structural Bound"
status: SKETCH
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.6.1", "spine:CT-7", "paper:999:CT-7"]
sources:
  - "canonical_omega_math_spine.md v1.5.2 §IV.6 'Theorem IV.6.1'"
  - "proof_obligations.md v1.3.5 §17.7 'Theorem (Threshold evaluator, structural bound)' (variant)"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0092 — CT-7: G3 Decomposition & Structural Bound

## Statement

For per-sample composition defect $D_i \in \{-1, 0, +1\}$ and Normalized Gap Defect $\mathrm{NGD} = \mathrm{LPR} - \mathrm{GPR} = \frac{1}{N}\sum D_i$:
Under one-sided G3 violations ($c_i \le a_i b_i$), negative defects vanish ($p_- = 0$) and $\mathrm{NGD} = p_+ \ge 0$.

Under G1+G2 with a threshold evaluator $\mathbf{1}[A \le \tau]$, action additivity $A[\gamma_2 \star \gamma_1] = A[\gamma_2] + A[\gamma_1]$, local thresholds $\tau_1, \tau_2$, and a strict global threshold $\tau < \tau_1 + \tau_2$:

$$
\boxed{
0 \le \mathrm{NGD} \le \Pr[\tau < X + Y \le \tau_1 + \tau_2]
}
$$

The gap is strictly bounded by the probability mass in the interference region (a trapezoidal strip in the $(X,Y)$ plane).

## Proof Pointer

No proof body accompanies this theorem in the source (§IV.6): the `[PROVED]`
tag is carried with no *Proof.* environment, sketch, or external pointer.
(CT-7 is the EPK aggregate-cancellation bound; the spine records the statement
only.) Verifier adjudication 2026-06-09: status set to SKETCH (see Notes).

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| G3 decomposition (\(p_-=0\), \(\mathrm{NGD}=p_+\ge0\)) and the boxed interference-region bound under G1+G2 threshold-evaluator hypotheses | local | none identified | NOT-STARTED |

## Notes

- §IV.6 ("Aggregate-Cancellation Bound (CT-7)") opens with the context
  sentence, quoted verbatim: "The Local-Green/Global-Red phenomenon (evaluator
  limit failures over composed valid sub-components) imposes quantitative
  structural bounds."
- The G1/G2/G3 composition conditions are the EPK composition conditions
  referenced by the statement's hypotheses (action additivity, threshold
  evaluator); they are named, not restated, in this spine section.
- Variant provenance (E3 dedup, manifest row 37): `proof_obligations.md`
  v1.3.5 §17.7 'Theorem (Threshold evaluator, structural bound)' is the same
  boxed bound, phrased with the strictness condition trailing — "when \(\tau
  < \tau_1 + \tau_2\) (global threshold strict). The gap is the probability
  mass in the **interference region** — a trapezoidal strip in the \((X,Y)\)
  plane. \(\square\)" — and closed with \(\square\) but again with NO proof
  body (section status: "DISCHARGED. Residual: CT-7-H1 (G1), CT-7-H2 (G2),
  CT-7-H3 (threshold evaluator form)"), so nothing there upgrades this
  entry's SKETCH. The companion §17.7 'Theorem (G3 decomposition)' carries
  strictly more content (the unconditional identity \(\mathrm{NGD}=p_+-p_-\),
  \(|\mathrm{NGD}|\le p_++p_-\), two-sided G3 vanishing) and is NET-NEW as
  [[ENC-0188]].
- Anomaly: `[PROVED]` tag without any recorded proof at this location.
  Verifier adjudication 2026-06-09: a `[PROVED]` tag with no proof body and no
  pointer to an actual proof artifact does not license PROVED-PROSE ("never
  stronger than the source supports") — status set to SKETCH (statement
  asserted, proof absent), consistent with [[ENC-0083]]/[[ENC-0087]]. The
  source tag is quoted verbatim under Provenance. Upgrading to PROVED-PROSE
  requires a recorded proof.

## Provenance

- Extracted 2026-06-09 from `canonical_omega_math_spine.md` v1.5.2, §IV.6
  (statement copied verbatim; no proof present in source). Original header
  line:
  `**Theorem IV.6.1 (CT-7: G3 Decomposition & Structural Bound).** [PROVED]`

## Changelog

- 2026-06-09: ENC-0092 created (M2 E1 extraction).
- 2026-06-09: verification patch: status PROVED-PROSE → SKETCH (`[PROVED]` tag
  with no proof body does not license PROVED-PROSE; consistent with
  ENC-0083/ENC-0087).
- 2026-06-09: E3 dedup — variant provenance from proof_obligations.md v1.3.5 §17.7 (manifest row 37, DUPLICATE-OF this entry); G3-decomposition sub-theorem split out as ENC-0188.
