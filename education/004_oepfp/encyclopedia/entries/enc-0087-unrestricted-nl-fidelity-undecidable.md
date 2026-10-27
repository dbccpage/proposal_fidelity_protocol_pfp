---
id: ENC-0087
kind: theorem
name: "Unrestricted NL Fidelity Is Undecidable"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.8"]
sources:
  - "engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "canonical_core_math_spine.md v1.5.2 §IV.2 'Theorem IV.8'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0087 — Unrestricted NL Fidelity Is Undecidable

## Statement

If the seed is unrestricted natural language, packet fidelity is not mechanically decidable. (Reduction to the halting problem.)

## Proof

Suppose for contradiction there exists a total computable fidelity predicate $F(T, p)$ that correctly decides whether a packet $p$ faithfully represents the semantic truth of an arbitrary unrestricted natural-language text $T$.

Let $M$ be an arbitrary Turing machine and $x$ an input. We construct an unrestricted natural-language text $T(M, x)$:

> "I assert that the Turing machine with description $M$ halts on input $x$. If this assertion is true, then the correct packet $p$ has $p.\mathsf{value} = 1$. If this assertion is false, then the correct packet $p$ has $p.\mathsf{value} = 0$."

Let $p_1$ be the packet where $p_1.\mathsf{value} = 1$. Because $T(M,x)$ binds the packet value directly to the halting status of $M$ on $x$, the fidelity predicate $F(T(M, x), p_1)$ must evaluate to true if and only if $M$ halts on $x$.

Since $F$ is assumed to be a mechanical decider, it would decide the Halting Problem. But the Halting Problem is undecidable, which gives a contradiction. Therefore, no such total mechanical decider $F$ can exist for unrestricted natural language. $\square$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| undecidability of packet fidelity for unrestricted natural-language seeds via reduction to the halting problem | local | none identified | NOT-STARTED |

## Notes

- Anomaly: the spine tags this `[PROVED]` but records only a one-parenthetical
  proof method, no worked proof body — status set to SKETCH (the encyclopedia
  status reflects the proof actually present; the source tag is quoted
  verbatim under Provenance). Upgrading to PROVED-PROSE requires writing out
  the halting-problem reduction.
- Companion negative result to Theorem IV.4 ([[ENC-0083]]), on the fidelity
  side rather than the verification side.

- PaperER007 reconciliation (2026-07-19): PaperER007 proves only a finite separation between eight-clause contract fidelity and detector adequacy, including rejection of a constant-pass detector. That result does not mechanize this entry's unrestricted-natural-language undecidability claim, so lean_status remains NOT-STARTED. AuthorityEffect remains None.

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.2
  (statement copied verbatim, including the parenthetical). Original header
  line:
  `**Theorem IV.8 (Unrestricted NL Fidelity Is Undecidable).** [PROVED] If the seed is unrestricted natural language, packet fidelity is not mechanically decidable. (Reduction to the halting problem.)`

## Changelog

- 2026-06-09: ENC-0087 created (M2 E1 extraction).
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
