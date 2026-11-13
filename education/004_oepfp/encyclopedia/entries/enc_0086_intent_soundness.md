---
id: ENC-0086
kind: corollary
name: "Intent Soundness"
status: CONDITIONAL
conditional_on: ["F(s,P)=1 ties P to Intent(s) per ENC-0084", "Sound(V_Gamma) relative to Intent(s)"]
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.7"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.2 'Corollary IV.7'"
uses: ["ENC-0084"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0086 — Intent Soundness

## Statement

$F(s, P) = 1 \;\wedge\; V_\Gamma(P) = 1 \;\wedge\; \mathrm{Sound}(V_\Gamma) \;\Rightarrow\; \mathrm{True}_{\mathrm{Intent}(s)}(P)$.

## Hypotheses

(a) **The three antecedents** (already named in the Statement):
$F(s,P) = 1$, $V_\Gamma(P) = 1$, and $\mathrm{Sound}(V_\Gamma)$. These are the
hypotheses of the implication, not derived facts.

(b) **The Fidelity predicate $F(s,P)$ of [[ENC-0084]]** (DEFINED — a
*definition*, not a proven theorem). Per ENC-0084, $F(s,P) = 1$ holds iff the
seven fidelity clauses (task identity, constraint, protected-boundary, terminal-
target, evidence-ceiling, oracle-policy, and allowed-transform preservation) all
hold between the seed $s$ and the packet $P$. The proof cites this only as the
*meaning of fidelity*: $F(s,P) = 1$ is, by definition, the statement that $P$
faithfully realizes / is on-spec for the intent specification $\mathrm{Intent}(s)$
carried by $s$. It does not assume ENC-0084 proves anything.

## Proof

A short soundness unfold.

1. By the Fidelity predicate (hypothesis (b), [[ENC-0084]]), $F(s,P) = 1$ ties
   $P$ to the intent specification $\mathrm{Intent}(s)$: $P$ is, by definition of
   $F$, on-spec for $\mathrm{Intent}(s)$. Hence the specification relative to
   which $V_\Gamma$ is to be read is $\mathrm{Intent}(s)$.
2. By soundness of $V_\Gamma$ relative to that specification
   (hypothesis (a), $\mathrm{Sound}(V_\Gamma)$ for $\mathrm{Intent}(s)$):
   $V_\Gamma(P) = 1 \Rightarrow \mathrm{True}_{\mathrm{Intent}(s)}(P)$.
3. Compose: given $V_\Gamma(P) = 1$ (hypothesis (a)) and step 1 fixing the
   relevant spec as $\mathrm{Intent}(s)$, step 2 yields
   $\mathrm{True}_{\mathrm{Intent}(s)}(P)$.

Therefore $F(s,P) = 1 \wedge V_\Gamma(P) = 1 \wedge \mathrm{Sound}(V_\Gamma)
\Rightarrow \mathrm{True}_{\mathrm{Intent}(s)}(P)$. $\square$

**Verifier-relative (firewall).** This is not unconditional or metaphysical
truth and mints **no authority**. $\mathrm{True}_{\mathrm{Intent}(s)}(P)$ here
means "true under the specification $V_\Gamma$ actually checks for
$\mathrm{Intent}(s)$": the conclusion is only as strong as the clauses
$V_\Gamma$ tests. ENC-0084 supplies the *definition* of fidelity (the meaning of
$F(s,P) = 1$), not a proven entailment; the result is therefore CONDITIONAL on
both hypotheses above and is not mechanized. This is the twin of
[[ENC-0082]] (same soundness-unfold shape).

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| intent soundness implication \(F(s,P)=1\wedge V_\Gamma(P)=1\wedge\mathrm{Sound}(V_\Gamma)\Rightarrow\mathrm{True}_{\mathrm{Intent}(s)}(P)\) | local | none identified | NOT-STARTED |

## Notes

- Anomaly: `[PROVED]` tag without any recorded proof at this location.
  Verifier adjudication 2026-06-09: a `[PROVED]` tag with no proof body and no
  pointer to an actual proof artifact does not license PROVED-PROSE ("never
  stronger than the source supports") — status set to SKETCH (statement
  asserted, proof absent), consistent with [[ENC-0083]]/[[ENC-0087]]. The
  source tag is quoted verbatim under Provenance. Upgrading to PROVED-PROSE
  requires a recorded proof.
- 2026-06-19: the unfold is now recorded (see Proof), lifting SKETCH →
  CONDITIONAL. It is **not** PROVED-PROSE: it rests on hypothesis (b), the
  Fidelity predicate $F(s,P)$ of [[ENC-0084]], which is a *definition* (DEFINED),
  not a proven entailment. The result stays verifier-relative and mints no
  authority.

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.2
  (statement copied verbatim; no proof present in source). Original header
  line:
  `**Corollary IV.7 (Intent Soundness).** [PROVED] $F(s, P) = 1 \;\wedge\; V_\Gamma(P) = 1 \;\wedge\; \mathrm{Sound}(V_\Gamma) \;\Rightarrow\; \mathrm{True}_{\mathrm{Intent}(s)}(P)$.`

## Changelog

- 2026-06-09: ENC-0086 created (M2 E1 extraction).
- 2026-06-09: verification patch: status PROVED-PROSE → SKETCH (`[PROVED]` tag
  with no proof body does not license PROVED-PROSE; consistent with
  ENC-0083/ENC-0087).
- 2026-06-19: develop pass (tier T2): SKETCH → CONDITIONAL. Wrote the soundness
  unfold (Hypotheses + Proof); cites [[ENC-0084]] as the *definition* of the
  Fidelity predicate $F(s,P)$ (added to `uses`). conditional_on = ["F(s,P)=1
  ties P to Intent(s) per ENC-0084", "Sound(V_Gamma) relative to Intent(s)"].
  Statement byte-unchanged (migration VERIFIED). Verifier-relative hedge kept;
  no mechanization, mints no authority. Twin of ENC-0082.
