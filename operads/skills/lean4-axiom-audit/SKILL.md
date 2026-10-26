---
name: lean4-axiom-audit
description: "Audit Lean 4 theorems and proof files for non-standard custom axiom injections and sorry claims."
operad_source_colours: ["Code", "Proof"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, lean4, audit]
---

# Lean 4 Axiom & Sorry Audit (`lean4-axiom-audit`)

**AuthorityEffect:** None.

## Purpose

Enforce that Lean 4 theorems claiming unconditional truth or formal verification rely exclusively on standard foundational Lean 4 axioms (`[propext, Classical.choice, Quot.sound]`), containing zero unmechanized `sorry` placeholders and zero non-standard custom axioms.

## Core Rules

1. **Standard Foundational Axiom Boundary**:
   Permitted axioms are strictly limited to the foundational set:
   - `propext` (Propositional Extensionality)
   - `Classical.choice` (Axiom of Choice)
   - `Quot.sound` (Quotient Soundness)
2. **Zero Sorry Invariant**:
   Theorem bodies must contain zero instances of `sorry`. A claim containing `sorry` is an open conjecture, not a verified theorem.
3. **Zero Custom Axiom Invariant**:
   Declaring domain theorems or premises as Lean 4 `axiom` declarations (e.g. `axiom canonicalBranchReconstructionMap`) is an uncertified bypass and triggers an unconditional rejection verdict.

## Verification Procedure

1. **Inspect AST for Sorry and Custom Axioms**:
   ```powershell
   # Scan for sorry tokens across target lean directory
   rg -n "\bsorry\b" lean4/research_programs/
   # Scan for axiom declarations
   rg -n "^\s*axiom\s+" lean4/research_programs/
   ```
2. **Execute Lake Environment Axiom Query**:
   ```powershell
   cd lean4/research_programs/<program_name>
   lake env lean --run <check_script.lean>
   ```
   Or evaluate theorem dependencies:
   ```lean
   #print axioms <TheoremName>
   ```
3. **Emit Verification Receipt**:
   Record status `PASS` only when the printed dependency list contains solely standard foundational axioms and zero custom axioms. Any custom axiom triggers `INTEGRITY_VIOLATION`.
