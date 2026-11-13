---
id: ENC-0116
kind: theorem
name: "Cochain Obstruction Soundness"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.5 'Theorem (Cochain Obstruction Soundness)'"
uses: ["ENC-0050", "ENC-0057", "ENC-0067"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0116 — Cochain Obstruction Soundness

## Statement

If the cochain verifier checks
dimensions, basis hashes, coefficient membership, \(d_1d_0=0\), primal/dual
\(\Phi_1\) certificates when a certified scalar is claimed, \(d_1h\) for
\(\Gamma_2\), deterministic tie policies for \(\Xi\), and the finite
trichotomy predicates, then:

\[
V_{\mathrm{cochain}}(x,P)=1\Rightarrow S_{\mathrm{cochain}}(x,P).
\]

## Hypotheses

The source defines the semantic relation immediately above the theorem, verbatim:

Let \(S_{\mathrm{cochain}}\) mean (over the canonical invariants above):

- the cochain layer is valid over the declared coefficient domain;
- \(d_1d_0=0\);
- \(B^1=\mathrm{im}(d_0)\), \(Z^1=\ker(d_1)\), \(Q^1=C^1/B^1\), and
  \(H^1=Z^1/B^1\) are interpreted using the declared bases;
- \(\Phi_1\), \(\Gamma_2\), and \(\Xi\) are computed from their declared
  optimization, closure, and tie-policy definitions;
- all exact/tolerance comparisons use the declared arithmetic mode.

## Proof

Matrix and basis checks make the layer well typed. The equality
\(d_1d_0=0\) gives \(B^1\subseteq Z^1\), so the quotients \(Q^1\) and \(H^1\)
are well defined. For \(\Phi_1\), an accepted primal residual gives an upper
bound and an accepted dual witness satisfying \(d_0^T\phi=0\) and the declared
dual-norm bound gives a lower bound; equality of the two values proves
optimality by weak duality of the declared norm pair. \(\Gamma_2\) is
sound because it is recomputed as \(\|d_1h\|_1\). \(\Xi\) is sound when the
accepted \(h_1^\*\) and \(\phi^\*\) are the deterministic tie-selected
optimal witnesses and the density lift plus trace distance are recomputed
under their declarations. The trichotomy follows by case analysis on
\(\Phi_1=0\), \(\Phi_1>0\land\Gamma_2=0\), and
\(\Phi_1>0\land\Gamma_2>0\). \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| cochain verifier acceptance entails $S_{\mathrm{cochain}}$ (well-typedness, quotient well-definedness, $\Phi_1$ weak duality, $\Gamma_2$ recompute, $\Xi$ tie determinism, trichotomy cases) | local | none identified | NOT-STARTED |

## Notes

- The recited invariants (`d₁d₀=0`, `B¹`, `Z¹`, `Q¹`, `H¹`, `Φ₁`, `Γ₂`, `Ξ`,
  trichotomy) are canonical §III imports — see [[ENC-0050]] (Φ₁), [[ENC-0057]]
  (Γ₂), [[ENC-0067]] (Ξ), [[ENC-0062]] (trichotomy), [[ENC-0021]]/[[ENC-0022]]
  (complex and derived subspaces). The source's KEEP note: the *verifier*
  soundness theorem below "has only a `[PROVED]` register row in canonical
  §IV.4 — the proof lives only here" (register home: [[ENC-0090]]).
- The source follows the proof with a caveat, verbatim: "If \(\Phi_1\) is
  reported as a raw floating value without exact arithmetic, tolerance
  semantics, or a primal/dual certificate, this theorem does not apply."

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.5 "Soundness
  Per Packet Family" / "Cochain Obstruction Packet Soundness" (statement,
  hypotheses, and proof copied verbatim). Original header line:
  `**Theorem (Cochain Obstruction Soundness).** If the cochain verifier checks`

## Changelog

- 2026-06-09: ENC-0116 created (M2 E2 satellite extraction).
