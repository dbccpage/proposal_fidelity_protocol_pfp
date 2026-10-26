---
id: ENC-0130
kind: theorem
name: "Syntactic Firewall Theorem"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §4.2 'Theorem (Syntactic Firewall Theorem)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0130 — Syntactic Firewall Theorem

## Statement

Pre-expansion AST safety checks are unsound for post-expansion
Rust artifacts when macros are allowed.

## Hypotheses

Verbatim setup from the source section:

> Let \(A=\mathrm{Parse}(\mathrm{rhs})\) be the pre-expansion Rust AST. Let
> \(\mathrm{Expand}(A,\mathcal E)\) be Rust macro expansion under macro
> environment \(\mathcal E\). Let `Unsafe(A)` mean the AST contains a forbidden
> unsafe construct.

## Proof

Suppose \(\mathcal E\) contains:

```rust
macro_rules! m {
    () => { unsafe { /* ... */ } };
}
```

Let `rhs` be:

```rust
m!()
```

The parsed AST contains a macro invocation node and no visible unsafe block, so
\(\neg Unsafe(A)\). A pre-expansion checker accepts. Macro expansion replaces
the invocation with `unsafe { ... }`, so
\(Unsafe(\mathrm{Expand}(A,\mathcal E))\). Therefore the pre-expansion property
does not imply the deployed post-expansion property. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| counterexample-by-macro: pre-expansion unsafe-freedom does not imply post-expansion unsafe-freedom in an abstract expand model | local | none identified | NOT-STARTED |

## Notes

- The theorem is unnamed in the source; the name is the §4.2 section heading.
- The source section closes with an inline "**Protected Rust subset
  corollary.** A total pre-expansion protected rewrite verifier is sound for
  `must_not_add_unsafe` only inside a macro-free protected subset, or else it
  must perform bounded expansion-aware checking and reject on timeout,
  expansion error, or budget exhaustion." That corollary is not a separate
  manifest row; its substance is subsumed by [[ENC-0132]] Protected Rust Subset
  Firewall Soundness (§4.4).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §4.2 "Syntactic Firewall Theorem"
  (statement and proof copied verbatim, including the two Rust code blocks).
  Original header line:
  `**Theorem.** Pre-expansion AST safety checks are unsound for post-expansion`

## Changelog

- 2026-06-09: ENC-0130 created (M2 E2 satellite extraction).
