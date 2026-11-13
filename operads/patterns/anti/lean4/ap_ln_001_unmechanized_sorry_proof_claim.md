---
pattern_id: AP_LN_001
name: unmechanized_sorry_proof_claim
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_LN_001_zero_sorry_axiom_allowlist
language: lean4
authority_effect: None
---

# Anti-Pattern: Unmechanized Sorry Proof Claim (`AP_LN_001`)

## Description

Leaving `sorry` or admitting unverified axioms in Lean 4 proof kernels (`lean4/research_programs/`) while simultaneously asserting formal verification or mathematical theorem status in accompanying papers or claim registries.

## Detection Signature

- AST / Grep pattern:
  `grep -rn "sorry" lean4/` or `axiom` outside of declared foundational axiomatic bases.
- Compiler Diagnostic:
  Lean 4 warning: `declaration uses 'sorry'`.
- Claim Mismatch:
  Paper claiming "mechanized in Lean 4" when the corresponding Lake build emits `#print axioms` containing `sorryAx`.

## Hazard & Failure Mode

- Violates `RULE_CLAIM_HYGIENE_001` and `governance-lean4-estate`.
- Destroys truth-preservation across research programs.
- Emits spurious verification claims.

## Dual Healthy Pattern

See [HP_LN_001_zero_sorry_axiom_allowlist](../../helpful/lean4/HP_LN_001_zero_sorry_axiom_allowlist.md).
