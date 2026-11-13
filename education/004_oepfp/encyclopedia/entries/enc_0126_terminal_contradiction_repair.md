---
id: ENC-0126
kind: lemma
name: "Terminal Contradiction Repair Lemma"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §3.2 'Lemma (Terminal Contradiction Repair Lemma)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0126 — Terminal Contradiction Repair Lemma

## Statement

If \(C\) is decidable and \(C(\sigma,t)=0\), then a deterministic
terminalizer can emit `Repair(TerminalStatusMismatch)` in polynomial time.

## Hypotheses

Verbatim setup from the source section:

> Let \(\sigma\) be a checked packet state and \(t\) a model-declared terminal.
> Let \(C(\sigma,t)\) be a finite predicate expressing terminal consistency.

## Proof

Evaluate \(C\). If false, emit the fixed repair status and the
finite error payload. The computation is bounded by the runtime of \(C\) plus
constant payload construction. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| decidable \(C\) plus fixed payload construction yields a total deterministic Repair emission | local | none identified | NOT-STARTED |

## Notes

- The source section follows the lemma with worked examples (LP duality gap,
  code-rewrite skeleton, operator packet, cochain packet) of the consistency
  predicate \(C\); examples are not part of the statement.
- The section's canonical-home blockquote says the *abstract* terminalizer
  consistency theorem is canonical §VII.1 = [[ENC-0097]] (restated-by-reference
  there); this lemma — polynomial-time deterministic emission of
  `Repair(TerminalStatusMismatch)` from a decidable consistency predicate — is
  the distinct repair-emission claim and lives only in the satellite.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §3.2 "Terminal Contradiction Repair
  Lemma" (statement and proof copied verbatim). Original header line:
  `**Lemma.** If \(C\) is decidable and \(C(\sigma,t)=0\), then a deterministic`

## Changelog

- 2026-06-09: ENC-0126 created (M2 E2 satellite extraction).
