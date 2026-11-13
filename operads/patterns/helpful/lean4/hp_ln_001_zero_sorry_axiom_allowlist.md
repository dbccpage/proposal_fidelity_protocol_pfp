---
pattern_id: HP_LN_001
name: zero_sorry_axiom_allowlist
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_LN_001_unmechanized_sorry_proof_claim
language: lean4
authority_effect: None
---

# Healthy Pattern: Zero-Sorry Axiom Allowlist (`HP_LN_001`)

## Description

Enforce full Lean 4 proof closure with zero `sorry` placeholders, verified via `#print axioms <theorem_name>` against a strictly audited foundational axiom allowlist (`propext`, `Classical.choice`, `Quot.sound`).

## Remediation & Implementation

```lean
-- Ensure all lemmas and theorems close completely without 'sorry'
theorem projector_idempotent (P : Endomorphism V) (hP : IsProjector P) :
  P ∘ P = P := by
  exact hP.idempotence

-- Verification command executed in local CI gate:
#print axioms projector_idempotent
-- Output must only contain standard Lean 4 axioms, never sorryAx
```

Automated verification gate script:
```powershell
lake build :all
lake exe check_axioms
```

## Operadic Property

Eliminates the `AP_LN_001` unmechanized sorry witness:
$$\|A_{\text{LN-001}}(H_{\text{LN-001}}(c))\| = 0$$
