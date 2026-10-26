---
id: ENC-0115
kind: theorem
name: "Code Rewrite Boundary Soundness"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §1.5 'Theorem (Code Rewrite Boundary Soundness)'"
uses: ["ENC-0090"]
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0115 — Code Rewrite Boundary Soundness

## Statement

If the code-rewrite verifier
checks exact span binding, `rhs` parseability, protected signature equality,
declared skeleton invariants, cfg-atom preservation or cfg enumeration, and the
macro/attribute firewall or expansion-aware substitute, then:

\[
V_{\mathrm{code}}(x,P)=1\Rightarrow S_{\mathrm{code}}(x,P).
\]

## Hypotheses

The source defines the semantic relation immediately above the theorem, verbatim:

Let \(S_{\mathrm{code}}\) mean the source-level rewrite relation:

- the `lhs` is exactly the AST node selected by the protected span or node id;
- replacing that node by `rhs` produces a parseable Rust item of the declared
  syntactic category;
- every declared protected-skeleton invariant is preserved in the verifier's
  semantic envelope;
- no forbidden macro, attribute, cfg, unsafe, ABI, export, or carrier mutation
  crosses the declared firewall.

## Proof

Each conjunct of \(S_{\mathrm{code}}\) is one of the verifier's
accepted checker predicates or follows from a checker predicate by definition:
span binding gives the selected node, parseability gives a well-formed
replacement item, signature and skeleton checks give protected-boundary
preservation, cfg enumeration or cfg-atom rejection gives configuration
boundary preservation, and the macro/attribute firewall removes post-parse
syntax injection from the verifier envelope. By the packet-family soundness
schema, acceptance implies \(S_{\mathrm{code}}\). \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| per-conjunct checker-predicate discharge + schema application for the code-rewrite verifier | local | none identified | NOT-STARTED |

## Notes

- The source's KEEP note: canonical §IV.4 lists "Code Rewrite Boundary |
  [PROVED, within protected Rust subset]" as a register row only (see
  [[ENC-0090]]); the proof lives only here.
- The source follows the proof with a scope caveat, verbatim: "This theorem is
  source-envelope soundness. It is deployed Rust artifact soundness only if the
  semantic envelope includes a proved protected Rust subset or expansion-aware
  verification."

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §1.5 "Soundness
  Per Packet Family" / "Code Rewrite Packet Soundness" (statement, hypotheses,
  and proof copied verbatim). Original header line:
  `**Theorem (Code Rewrite Boundary Soundness).** If the code-rewrite verifier`

## Changelog

- 2026-06-09: ENC-0115 created (M2 E2 satellite extraction).
