---
pattern_id: AP_LN_004
name: smuggled_custom_axiom_injection
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_LN_004_constructive_kernel_discharge
language: lean4
authority_effect: None
---

# Anti-Pattern: Smuggled Custom Axiom Injection (`AP_LN_004`)

## Description

Injecting custom `axiom` declarations (e.g. `axiom tao_fails_conjecture2`, `axiom canonicalBranchReconstructionMap`) in Lean 4 formalization packages to bypass difficult proof obligations, while claiming mathematical completion or formal verification in accompanying papers and dossiers.

## Detection Signature

- AST / Grep pattern:
  `grep -rnE "^\s*axiom\s+" lean4/research_programs/`
- Lean 4 Environment Axiom Print:
  `#print axioms <TheoremName>` emitting identifiers outside `[propext, Classical.choice, Quot.sound]`.
- Observed in `task_adversary_mub6_mission2_axiom_purge_20261009` (Act VIII: The Trial of the Three Smuggled Axioms):
  "A procedural shortcut occurred in the previous watch. To bind the sporadic literature classes, three synthetic axioms were injected rather than discharged constructively to core kernels."

## Hazard & Failure Mode

- Introduces potential logical inconsistency into the proof environment (a false axiom can prove `False`).
- Violates `RULE_CLAIM_HYGIENE_001`, `lean4-axiom-audit`, and `governance-lean4-estate`.
- Destroys truth-preservation across research programs by treating unproven conjectures as certified truths.

## Dual Healthy Pattern

See [HP_LN_004_constructive_kernel_discharge](../../helpful/lean4/HP_LN_004_constructive_kernel_discharge.md).
