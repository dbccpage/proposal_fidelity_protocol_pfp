---
pattern_id: HP_LN_004
name: constructive_kernel_discharge
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_LN_004_smuggled_custom_axiom_injection
language: lean4
authority_effect: None
---

# Healthy Pattern: Constructive Kernel Discharge (`HP_LN_004`)

## Description

All theorem obligations in Lean 4 formalization packages are proved constructively from declared inductive types, verified lemmas, and the foundational core axioms (`propext`, `Classical.choice`, `Quot.sound`). Zero custom synthetic `axiom` declarations are permitted.

## Structural Signature

```lean
-- Verified constructive theorem discharged to Lean 4 kernel
theorem matolcsi_weiner_subgap_r6_obstruction (M : Matrix (Fin 6) (Fin 6) ℂ)
    (hM : IsUnbiased M) : VanishingCyclePoly M := by
  intro cycle
  apply constructive_cycle_elimination
  exact hM
```

Axiom verification via Lake environment check:
```bash
lake env lean --run scripts/audit_axioms.lean
# Asserts: axioms(Theorem) ⊆ {propext, Classical.choice, Quot.sound}
```

## Remediation Applied

- Purge all custom synthetic `axiom` declarations from the Lean 4 source files.
- Replace synthetic assertions with constructive inductive proofs, explicit computational reductions, or open conjecture tags (`sorry` strictly gated under conjecture taxonomy, never claiming verification).
- Run `lake env lean` with automated `#print axioms` assertions in CI.
