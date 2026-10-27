---
id: ENC-0083
kind: theorem
name: "No-Free-Lunch from Syntax"
status: CONDITIONAL
conditional_on: ["the finite packet grammar can encode, for every Turing machine M and input w, a packet whose semantic content is the Sigma^0_1 assertion 'M halts on w' (sufficient expressiveness to represent computation); without this the no-free-lunch claim is vacuous"]
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.4"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.1 'Theorem IV.4'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0083 — No-Free-Lunch from Syntax

## Statement

Finite packet grammar alone does not make semantic truth decidable. (Reduction to the halting problem.)

## Hypotheses

- **(Expressiveness.)** The finite packet grammar $G$ can encode, for every
  Turing machine $M$ and input $w$, a packet $P_{M,w}\in L(G)$ whose semantic
  content is the $\Sigma^0_1$ assertion "$M$ halts on $w$", and the map
  $(M,w)\mapsto P_{M,w}$ is computable. (Without some such expressiveness the
  statement is vacuous; this is the regime the theorem addresses.)
- **(Computability background.)** The halting problem
  $H=\{(M,w): M \text{ halts on } w\}$ is undecidable (Turing).

## Proof

The source records only the parenthetical method "(Reduction to the halting
problem.)"; here is the worked reduction.

Suppose, for contradiction, that **semantic truth over $G$ is decidable**: there
is a total computable predicate $\mathsf{True}_G$ that, given any packet
$P\in L(G)$, decides whether $P$'s semantic content holds.

By the expressiveness hypothesis the map $(M,w)\mapsto P_{M,w}$ is computable and
$P_{M,w}\in L(G)$ carries the semantic content "$M$ halts on $w$". Compose:

$$
(M,w)\ \longmapsto\ P_{M,w}\ \longmapsto\ \mathsf{True}_G(P_{M,w}).
$$

This composite is a total computable predicate, and by construction it returns
$\top$ iff $M$ halts on $w$ — i.e. it **decides $H$**. That contradicts the
undecidability of the halting problem. Hence no such $\mathsf{True}_G$ exists.

Therefore the finite packet grammar, however well it generates syntactically
well-formed packets, does **not** render semantic truth decidable. Membership in
$L(G)$ (a syntactic property) is decidable; semantic truth is not — there is **no
free lunch from syntax**: decidability of the generator does not transfer to the
semantic predicate. $\qquad\blacksquare$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| undecidability of semantic truth over a finite packet grammar via reduction to the halting problem | local | none identified | NOT-STARTED |

## Notes

- Anomaly: the spine tags this `[PROVED]` but records only a one-parenthetical
  proof method, no worked proof body — originally set to SKETCH (the encyclopedia
  status reflects the proof actually present; the source tag is quoted verbatim
  under Provenance). 2026-06-19: the halting-problem reduction is now written
  out; status raised to CONDITIONAL on the grammar-expressiveness hypothesis
  (encoding $M$-halts-on-$w$). The reduction is complete under that hypothesis,
  so CONDITIONAL→PROVED-PROSE is available in a later pass once the
  expressiveness is fixed as part of the theorem's scope (it is intrinsic to a
  "no free lunch from syntax" claim).

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.1
  (statement copied verbatim, including the parenthetical). Original header
  line:
  `**Theorem IV.4 (No-Free-Lunch from Syntax).** [PROVED] Finite packet grammar alone does not make semantic truth decidable. (Reduction to the halting problem.)`

## Changelog

- 2026-06-09: ENC-0083 created (M2 E1 extraction).
- 2026-06-19: SKETCH→CONDITIONAL (core-math-dev, tier T2). Wrote out the
  halting-problem reduction (the source's parenthetical method): decidability of
  semantic truth over $L(G)$ would decide $H$ via $(M,w)\mapsto P_{M,w}\mapsto
  \mathsf{True}_G(P_{M,w})$. Added `## Hypotheses` (grammar expressiveness +
  computability background); `conditional_on` names the expressiveness. Statement
  verbatim-unchanged; Lean obligation unchanged (NOT-STARTED).
