---
id: ENC-0082
kind: theorem
name: "Soundness Anti-Forgery"
status: CONDITIONAL
conditional_on: ["Sound(V_Gamma) for S", "the GlobalValid gate of ENC-0099 entails V_Gamma=1"]
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.3"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.1 'Theorem IV.3'"
uses: ["ENC-0099"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0082 — Soundness Anti-Forgery

## Statement

If $V_\Gamma$ is sound for specification $S$ (i.e., $V_\Gamma(x,P) = 1 \Rightarrow \mathrm{True}_S(x,P)$), then $\mathsf{GlobalValid}$ implies $\mathrm{True}_S$.

## Hypotheses

(a) **Soundness of $V_\Gamma$ for $S$** (already named in the Statement): the
predicate $\mathrm{Sound}(V_\Gamma)$ for specification $S$ means exactly
$V_\Gamma(x,P) = 1 \Rightarrow \mathrm{True}_S(x,P)$ for every item $(x,P)$. This
is the hypothesis, not a derived fact.

(b) **The GlobalValid specification gate of [[ENC-0099]]** (DEFINED — a
*definition*, not a proven theorem). ENC-0099 declares that no validator may
emit $\mathsf{GlobalValid}$ without a named specification $S_F$ and a fixed
clause set $V_F = \bigwedge_i C_i$; under that gate a $\mathsf{GlobalValid}$
verdict on $(x,P)$ is, by definition, the validator's acceptance — i.e. it
entails $V_\Gamma(x,P) = 1$ on the relevant item(s). The proof cites this only
as the meaning of $\mathsf{GlobalValid}$; it does not assume ENC-0099 proves
anything.

## Proof

A short soundness unfold. Suppose $\mathsf{GlobalValid}$ holds on item $(x,P)$.

1. By the GlobalValid specification gate (hypothesis (b), [[ENC-0099]]), the
   verdict $\mathsf{GlobalValid}$ is — by definition of the gate — the
   acceptance of the fixed-clause validator under a named $S_F = S$; hence
   $V_\Gamma(x,P) = 1$.
2. By soundness of $V_\Gamma$ for $S$ (hypothesis (a)),
   $V_\Gamma(x,P) = 1 \Rightarrow \mathrm{True}_S(x,P)$.
3. Compose 1 and 2: $\mathsf{GlobalValid} \Rightarrow V_\Gamma(x,P) = 1
   \Rightarrow \mathrm{True}_S(x,P)$.

Therefore $\mathsf{GlobalValid}$ implies $\mathrm{True}_S$. $\square$

**Verifier-relative (firewall).** This is not unconditional or metaphysical
truth and mints **no authority**. $\mathrm{True}_S$ here means "true under the
specification $V_\Gamma$ actually checks": the conclusion is only as strong as
the clauses $\{C_i\}$ the validator tests, quoted from the source — "soundness
is only as strong as the specification $V_\Gamma$ checks." ENC-0099 supplies the
*definition* of $\mathsf{GlobalValid}$, not a proven entailment; the result is
therefore CONDITIONAL on both hypotheses above and is not mechanized.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| \(\mathsf{GlobalValid}\Rightarrow\mathrm{True}_S\) under the soundness hypothesis on \(V_\Gamma\) | local | none identified | NOT-STARTED |

## Notes

- The source follows the statement with a scope remark, quoted verbatim:
  "This is verifier-relative: soundness is only as strong as the specification
  $V_\Gamma$ checks."
- Anomaly: `[PROVED]` tag without any recorded proof at this location.
  Verifier adjudication 2026-06-09: a `[PROVED]` tag with no proof body and no
  pointer to an actual proof artifact does not license PROVED-PROSE ("never
  stronger than the source supports") — status set to SKETCH (statement
  asserted, proof absent), consistent with [[ENC-0083]]/[[ENC-0087]]. The
  source tag is quoted verbatim under Provenance.
- 2026-06-19: the unfold is now recorded (see Proof), lifting SKETCH →
  CONDITIONAL. It is **not** PROVED-PROSE: it rests on hypothesis (b), the
  GlobalValid gate of [[ENC-0099]], which is a *definition* (DEFINED), not a
  proven entailment. The result stays verifier-relative and mints no authority.

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.1
  (statement copied verbatim; no proof present in source). Original header
  line:
  `**Theorem IV.3 (Soundness Anti-Forgery).** [PROVED] If $V_\Gamma$ is sound for specification $S$ (i.e., $V_\Gamma(x,P) = 1 \Rightarrow \mathrm{True}_S(x,P)$), then $\mathsf{GlobalValid}$ implies $\mathrm{True}_S$.`

## Changelog

- 2026-06-09: ENC-0082 created (M2 E1 extraction).
- 2026-06-09: verification patch: status PROVED-PROSE → SKETCH (`[PROVED]` tag
  with no proof body does not license PROVED-PROSE; consistent with
  ENC-0083/ENC-0087).
- 2026-06-19: develop pass (tier T2): SKETCH → CONDITIONAL. Wrote the soundness
  unfold (Hypotheses + Proof); cites [[ENC-0099]] as the *definition* of
  $\mathsf{GlobalValid}$ (added to `uses`). conditional_on = ["Sound(V_Gamma)
  for S", "the GlobalValid gate of ENC-0099 entails V_Gamma=1"]. Statement
  byte-unchanged (migration VERIFIED). Verifier-relative hedge kept; no
  mechanization, mints no authority.
