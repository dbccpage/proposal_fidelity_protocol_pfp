---
id: ENC-0131
kind: theorem
name: "Finite Cfg Boundary Decidability"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §4.3 'Theorem (Finite Cfg Boundary Decidability)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0131 — Finite Cfg Boundary Decidability

## Statement

Checking protected item presence/signature preservation over
\(K_\Phi\) is decidable.

## Hypotheses

Verbatim setup from the source section:

> Let \(\Phi\) be the finite set of `cfg` and `cfg_attr` predicates guarding the
> protected item and enclosing reachability. Let \(Atoms(\Phi)\) be the finite
> set of cfg atoms in those predicates.
>
> Construct \(K_\Phi\) as all structurally valid assignments to those atoms:
> features as independent Booleans, name atoms as Booleans, and mutually
> exclusive target keys as finite one-of choices.

## Proof

Enumerate each \(c\in K_\Phi\). For each \(c\), evaluate cfg removal
and cfg_attr expansion on the original and rewritten ASTs, then compare:

- whether the protected item is present;
- whether its public signature projection is unchanged.

\(K_\Phi\) is finite, and each per-configuration check is finite over finite
ASTs. Therefore the full check terminates. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| termination/decidability of presence+signature comparison over the finite configuration model \(K_\Phi\) | local | none identified | NOT-STARTED |

## Notes

- The theorem is unnamed in the source; the name is the §4.3 section heading.
- Distinct from [[ENC-0081]] Boundary Decidability and [[ENC-0098]] Symbol Game
  Boundary Decidability (canonical IV.2 / VII.2): those concern the packet
  verification pipeline; this one concerns Rust `cfg`/`cfg_attr` configuration
  enumeration in the code-rewrite boundary.
- The source section adds two qualifiers, verbatim:
  - "**Relative completeness.** If a cfg-based mutation uses only atoms already
    in \(Atoms(\Phi)\), it changes presence or signature under some assignment
    iff the \(K_\Phi\) enumeration observes it."
  - "**Residual L1.** A rewrite can introduce a new cfg atom. Close this by
    rule: `new cfg atom inside protected region ⇒
    BoundaryViolation(NewCfgAtom)` unless an explicit config/migration license
    admits that atom."

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §4.3 "Finite Cfg Boundary
  Decidability" (statement and proof copied verbatim). Original header line:
  `**Theorem.** Checking protected item presence/signature preservation over`

## Changelog

- 2026-06-09: ENC-0131 created (M2 E2 satellite extraction).
