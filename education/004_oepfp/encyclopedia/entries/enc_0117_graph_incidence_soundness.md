---
id: ENC-0117
kind: theorem
name: "Graph Incidence Soundness"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.5 'Theorem (Graph Incidence Soundness)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0117 — Graph Incidence Soundness

## Statement

If the graph-incidence verifier checks
the finite carrier, edge endpoints, orientation, incidence-matrix entries,
dimension agreement, and recomputes every claimed boundary, coboundary,
degree, cut, cycle, or conservation equation by matrix multiplication, then:

\[
V_{\mathrm{graph}}(x,P)=1\Rightarrow S_{\mathrm{graph}}(x,P).
\]

## Hypotheses

The source defines the semantic relation immediately above the theorem, verbatim:

Let \(S_{\mathrm{graph}}\) mean that a finite graph incidence claim is true
for the declared vertex set, edge set, orientation, and incidence matrix.

For an oriented graph \(G=(V,E)\), the incidence matrix \(B\) has one column per
edge and one row per vertex, with:

\[
B_{v,e} =
\begin{cases}
-1 & v=\mathrm{tail}(e),\\
+1 & v=\mathrm{head}(e),\\
0 & \text{otherwise}.
\end{cases}
\]

## Proof

The carrier and endpoint checks define a unique oriented incidence
matrix \(B\). Entry checks ensure the packet's matrix is that matrix. Every
accepted graph-incidence claim is then a finite matrix equation over the
declared coefficient domain. Since the verifier recomputes those equations
exactly, each accepted equation is true in the declared graph. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| oriented-incidence-matrix uniqueness + recomputed-equation truth for accepted graph packets | local | none identified | NOT-STARTED |

## Notes

- The source's KEEP note: canonical §IV.4 lists "Graph Incidence | [PROVED]"
  as a register row only (see [[ENC-0090]]); "the incidence-matrix soundness
  proof below lives only here."

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.5 "Soundness
  Per Packet Family" / "Graph Incidence Packet Soundness" (statement,
  hypotheses, and proof copied verbatim). Original header line:
  `**Theorem (Graph Incidence Soundness).** If the graph-incidence verifier checks`

## Changelog

- 2026-06-09: ENC-0117 created (M2 E2 satellite extraction).
