---
id: ENC-0114
kind: theorem
name: "LP Optimality Soundness"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "symbol_game_math_spine.md math_spines_v002 §1.5 'Theorem (LP Optimality Soundness)'"
  - "proof_obligations.md v1.3.5 §13 'Theorem (LP-RatOpt soundness)' (section 'PO-C4-FLS — VerifierFamilySoundness', 'Concrete Instance — LP-RatOpt')"
uses: []
lean_status: MECHANIZED-PARTIAL
lean_refs:
  - "engine/lean4/008_engine_runtime/007_the_symbol_game/PaperER007/L007_07_LPWeakDuality.lean"
  - "PaperER007.lp_max_form_weak_duality"
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0114 — LP Optimality Soundness

## Statement

\[
V_{\mathrm{LP}}(x,P)=1\Rightarrow
z^\*\text{ is an optimal primal solution with value }v.
\]

## Hypotheses

The source fixes the verifier immediately above the theorem, verbatim:

Use exact arithmetic over a declared ordered field, or over a declared exact
ordered coefficient domain where the displayed weak-duality argument is valid.
For optimality packets, normalize the LP to the canonical primal/dual pair:

\[
\begin{aligned}
\text{Primal: } & \min c^T z && \text{s.t. } Az=b,\; z\ge 0,\\
\text{Dual: } & \max b^T y && \text{s.t. } A^T y\le c.
\end{aligned}
\]

Let \(V_{\mathrm{LP}}\) accept an optimality packet only if it verifies:

1. \(Az^\*=b\) and \(z^\*\ge 0\);
2. \(A^T y^\*\le c\);
3. \(c^Tz^\*=b^Ty^\*=v\);
4. all comparisons use exact arithmetic, or a declared tolerance profile whose
   semantics is part of \(S_{\mathrm{LP}}\).

## Proof

For any primal feasible \(z\) and dual feasible \(y\):

\[
b^Ty=y^TAz=(A^Ty)^Tz\le c^Tz,
\]

because \(A^Ty\le c\) and \(z\ge 0\). This is weak duality. For the accepted
witnesses \(z^\*,y^\*\), the verifier checks \(c^Tz^\*=b^Ty^\*=v\). Hence
every feasible \(z\) has \(c^Tz\ge v=c^Tz^\*\). Therefore \(z^\*\) is optimal.
\(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| weak duality + gap-zero acceptance implies primal optimality over a declared exact ordered domain | local | none identified | NOT-STARTED |

## Notes

- The source's KEEP note: canonical §IV.4 / §X.2 list "LP Optimality (weak
  duality) | [PROVED]" as a register row only (see [[ENC-0090]] for the schema
  and its register); "the weak-duality proof below lives only here."
- The source follows the proof with the infeasibility-certificate paragraph,
  verbatim: "For infeasibility packets in the same canonical form, a sound
  certificate is a vector \(y\) such that:
  \[
  A^Ty\ge 0
  \quad\text{and}\quad
  b^Ty<0.
  \]
  If \(Az=b,z\ge0\) existed, then \(b^Ty=y^TAz=(A^Ty)^Tz\ge0\), contradiction.
  Thus an accepted Farkas certificate proves primal infeasibility. Other LP
  forms must first be normalized with a semantics-preserving normalization proof."
- Variant statement in proof_obligations.md v1.3.5 §13, PO-C4-FLS "Concrete
  Instance — `LP-RatOpt`": "**Theorem (`LP-RatOpt` soundness).**
  \(V_{\mathrm{LP}}(p)=\mathsf{Accept} \Rightarrow
  \mathsf{Spec}_{\mathrm{LP}}(p)\)" where
  \(\mathsf{Spec}_{\mathrm{LP}}(p) :\equiv (Az^\*=b\wedge z^\*\ge0\wedge
  c^Tz^\*=v) \wedge \forall z.\,(Az=b\wedge z\ge0\Rightarrow c^Tz\ge v)\) —
  the same soundness claim (acceptance entails primal optimality with value
  \(v\), proved by the same weak-duality argument), repackaged as a
  [[ENC-0164]] verifier-family instance. Differences (variant only, NOT
  merged): the variant is **exact-rational only** with carrier tag
  `canonical-rational-min-lp-v1` and "no floating tolerance. A tolerance-based
  LP verifier would be a different family" (this entry's clause 4 instead
  admits "a declared tolerance profile whose semantics is part of
  \(S_{\mathrm{LP}}\)"); the variant prepends four typed admission gates
  (exact-rational parse, required fields, carrier tag, normalizer/replay-hash)
  and a dimension clause ahead of the three mathematical clauses, with typed
  refusal coverage. Variant status: "`LP-RatOpt` family instance: PROVED-PROSE
  by exact weak duality"; its implementation-boundary note records that the
  current LP realizer may cite the theorem only after enforcing the listed
  acceptance clauses and typed refusals.

- PaperER007 reconciliation (2026-07-19): PaperER007 proves maximum-form weak duality over a field with LinearOrder and IsStrictOrderedRing. The entry's minimum/equality-form verifier theorem, zero-gap optimality step, normalization bridge, tolerance semantics, and norm/dual-norm argument are not thereby mechanized. AuthorityEffect remains None.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.5 "Soundness
  Per Packet Family" / "LP Packet Soundness" (statement, hypotheses, and proof
  copied verbatim). Original header line:
  `**Theorem (LP Optimality Soundness).**`

## Changelog

- 2026-06-09: ENC-0114 created (M2 E2 satellite extraction).
- 2026-06-09: variant provenance appended (M2 E3): proof_obligations.md §13
  PO-C4-FLS `LP-RatOpt` soundness instance recorded as duplicate variant
  (Notes + sources only; Statement untouched).
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
