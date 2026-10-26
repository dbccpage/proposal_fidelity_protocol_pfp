---
id: ENC-1209
kind: theorem
name: "Fixed-Alphabet Unary Nesting Preserves Declarations"
status: MECHANIZED
conditional_on:
  - "Terms use only the PaperER007.FixedAlphabetTerm atom and unary constructors over fixed Symbol and Operator types"
  - "The repeated unary operator satisfies the supplied allowedOperator predicate"
  - "The input term satisfies the supplied symbol and operator declaration predicates"
layer: symbol-game
tower_level: null
primitive: null
aliases:
  - "paper:er007:fixed-alphabet-unary-nesting"
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md Current Formal Core and Part III Q3"
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_proof_ledger.md Current PaperER007 Lean Core"
uses: []
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_grammar_depth_ceiling.lean"
  - "PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_preserves_declarations"
extracted: 2026-07-19
migration: EXTRACTED
---

# ENC-1209 - Fixed-Alphabet Unary Nesting Preserves Declarations

## Statement

Let Symbol and Operator be arbitrary types, let allowedSymbol and
allowedOperator be declaration predicates, and let term be a
PaperER007.FixedAlphabetTerm. If an operator op is allowed and term satisfies both
declaration predicates, then for every natural depth, repeatedly wrapping term
with the unary constructor labelled by op preserves both declaration
predicates.

Equivalently at the two component projections, unary nesting introduces no
symbol rejected by allowedSymbol and no operator rejected by allowedOperator.

## Hypotheses

- The syntax carrier is the narrow atom/unary PaperER007.FixedAlphabetTerm.
- The same supplied operator op is used at each added layer.
- allowedOperator op holds.
- The original term already satisfies the relevant declaration predicate.

No parser, denotational semantics, arity system, full grammar, or equivalence
between a grammar ceiling and S(n) is assumed.

## Proof Pointer

Mechanized in
omega_engine/lean4/008_engine_runtime/007_the_symbol_game/PaperER007/L007_06_GrammarDepthCeiling.lean.

The exact Lean theorems are:

- PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_symbols
- PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_operators
- PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_preserves_declarations

Each proof is induction on the natural nesting depth. The successful
lake build PaperER007 receipt reports the three theorems as axiom-free.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| fixed-alphabet unary nesting preserves supplied symbol declarations | PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_symbols | none | MECHANIZED |
| fixed-alphabet unary nesting preserves supplied operator declarations | PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_operators | none | MECHANIZED |
| conjunction of both declaration-preservation properties | PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_preserves_declarations | none | MECHANIZED |
| full PaperER007 grammar ceiling equals S(n) | PaperER007 monograph Part III | parser, expressivity, arity, and denotational boundaries remain absent | SKETCH |

## Notes

- This is a narrow internal syntax-closure theorem. It supports the statement
  that adding depth with an already declared unary operator does not itself add
  declarations.
- It does not prove parser correctness, semantic completeness, arbitrary
  operator-tree closure, or the full grammar-ceiling equality.
- AuthorityEffect remains None. The theorem changes neither evidence nor
  authority status.

## Provenance

Created 2026-07-19 during the dedicated PaperER007 Lean-core reconciliation,
after semantic search found no existing encyclopedia owner for this exact
fixed-alphabet unary-nesting theorem.

## Changelog

- 2026-07-19: ENC-1209 created with exact PaperER007 Lean bindings. No broader
  grammar claim or authority status was upgraded.
