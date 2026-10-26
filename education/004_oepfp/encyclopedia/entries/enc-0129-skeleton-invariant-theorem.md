---
id: ENC-0129
kind: theorem
name: "Skeleton Invariant Theorem"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §4.1 'Theorem (Skeleton Invariant Theorem)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0129 — Skeleton Invariant Theorem

## Statement

A total, non-panicking, value-preserving constructor that performs
nontrivial structural validation with observable rejection cannot preserve the
public type \(A\to T\). Its public return type must expose a rejection channel
\(T+E\).

## Hypotheses

Verbatim setup from the source section:

> Let the original constructor have public signature:
>
> \[
> f:A\to T.
> \]
>
> Let \(q:A\to\{\mathrm{true},\mathrm{false}\}\) be a nontrivial validation
> predicate, so some \(a_{\mathrm{bad}}\) satisfies \(q(a_{\mathrm{bad}})=0\).

## Proof

Since \(q\) is nontrivial, choose \(a_{\mathrm{bad}}\) with
\(q(a_{\mathrm{bad}})=0\). Structural validation requires rejecting
\(a_{\mathrm{bad}}\). Total non-panicking behavior means rejection must be
returned as a value, not via panic or divergence. That value is not in \(T\);
it is in an error channel \(E\). Therefore the codomain is \(T+E\), not \(T\).
\(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| total non-panicking validating constructor forces codomain \(T+E\) (coproduct rejection channel) | local | none identified | NOT-STARTED |

## Notes

- The theorem is unnamed in the source; the name is the §4.1 section heading.
- The source section continues with the `must_preserve_public_signature`
  consequence (rewriting `fn new(value: String) -> Self` to
  `fn new(value: String) -> Result<Self, E>` is a protected-skeleton violation
  unless a migration license covers the public API change and all incident
  caller edges) and the scope caveat: "This theorem does not say all validation
  requires API change. Panic, coercion, defaulting, hidden invalid state, and
  side-channel logging preserve the signature by violating other premises."
- The source marks §4 "**KEEP — net-new (proof bodies).** Canonical §IV.4
  carries only the register row 'Code Rewrite Boundary | [PROVED, within
  protected Rust subset]'"; the proof substance lives only in the satellite.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §4.1 "Skeleton Invariant Theorem"
  (statement and proof copied verbatim). Original header line:
  `**Theorem.** A total, non-panicking, value-preserving constructor that performs`

## Changelog

- 2026-06-09: ENC-0129 created (M2 E2 satellite extraction).
