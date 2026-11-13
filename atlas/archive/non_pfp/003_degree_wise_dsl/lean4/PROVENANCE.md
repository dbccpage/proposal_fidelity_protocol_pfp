# Lean 4 Provenance and Compile Receipts: Paper FOC-006

**Review scope (2026-09-30). Nonclaims:** This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.

## Environment

* Toolchain: `leanprover/lean4:v4.33.1`
* Standard foundational axioms: `{propext, Quot.sound}`
* Proof-placeholder commands: absent across all claim-bearing modules

## Module Inventory & Axiom Audit

* `DegreeSeparation.lean`: 355 lines, 0 proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `Census.lean`: 25 lines (replays all 19 declarations and prints axiom audit)

All axiom reports conclude strictly inside the standard Lean kernel pair (`propext`, `Quot.sound`). Zero custom or unverified axioms are admitted.
