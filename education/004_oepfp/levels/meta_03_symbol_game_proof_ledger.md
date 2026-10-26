---
documentation_contract: symbol-game-documentation/v1
title: "3_symbol_game_proof_ledger: Formal Verification & Lean 4 Proof Ledger"
kind: grammar-reference
audience:
  - researchers
  - engineers
  - coding-agents
status: active
maturity: draft
claim_status: specified
authority_effect: "None"
source_paths:
  - omega_engine_education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/symbol_game_proof_ledger.md  # not found at source pin c419cc6beb (2026-10-20)
prerequisites:
  - ./meta_00_symbol_game_foundations.md
  - ./meta_01_symbol_game_historical_curriculum.md
  - ./meta_02_symbol_game_pfp.md
aliases:
  - 3_symbol_game.md
  - 3_symbol_game
related:
  - ./meta_00_symbol_game_foundations.md
  - ./meta_01_symbol_game_historical_curriculum.md
  - ./meta_02_symbol_game_pfp.md
last_verified: 2026-09-29
---

# 3_symbol_game_proof_ledger: Formal Verification & Lean 4 Proof Ledger

**AuthorityEffect:** None.  
**Scope:** Canonical verification ledger for all 50 formal Lean 4 theorems in `Paper043.lean` and modules under `Paper043/`.

## Current-source status (2026-10-20)

The receipts in Sections 1 to 4 are a historical record (last verified 2026-09-29) and are not reproducible at source pin `c419cc6beb`. Lean status at source pin `c419cc6beb` (read 2026-10-20; no Lean build run): there is no `Paper043.lean` file and no `Paper043/` folder. The Paper 043 statements live in namespace `PaperER007` across `lean4/*.lean`. Of the eleven files in the table below, five are roots of [`lean4/lakefile.lean`](../../../../lean4/lakefile.lean) (`ShadowFactorization`, `TypedPacketShadow`, `TriggerNotLicense`, `GrammarDepthCeiling` and `LiftPatchSemantics`), two are not roots (`FidelityAdequacy`, `OperationTreeFold`), and four state in their own headers that they do not elaborate (`FiniteConsequences`, `LggrNonFactorization`, `LpWeakDuality`, `TerminalizerPolicy`).

| Section 3 packet | File at the pin | Status at the pin |
| :--- | :--- | :--- |
| L043_01 Shadow | `lean4/ShadowFactorization.lean` | default library root |
| L043_02 LGGR | `lean4/LggrNonFactorization.lean` | header: import `LGGR` does not load |
| L043_03 Typed packet | `lean4/TypedPacketShadow.lean` | default library root |
| L043_04 Trigger | `lean4/TriggerNotLicense.lean` | default library root |
| L043_05 Fidelity | `lean4/FidelityAdequacy.lean` | not a library root |
| L043_06 Fixed alphabet | `lean4/GrammarDepthCeiling.lean` | default library root |
| L043_07 LP duality | `lean4/LpWeakDuality.lean` | header: does not elaborate, not typechecked |
| L043_08 Terminalizer | `lean4/TerminalizerPolicy.lean` | header: does not elaborate |
| L043_09 Operation fold | `lean4/OperationTreeFold.lean` | not a library root |
| L043_10 Lift patch | `lean4/LiftPatchSemantics.lean` | default library root |
| L043_11 ENC-0933 facade | `lean4/FiniteConsequences.lean` | header: does not elaborate (module `paper_er006` absent) |

The `PASS (2,974 jobs)`, `PASS (0 matches)` and `PASS (50 / 50)` rows below lack the exact command output, tool version and exit status, so they are not current evidence. The next test is a `lake build` of the default library with a dated receipt, followed by repair or retirement of the four non-elaborating files.

---

## 1. Verification Receipts & Build Gate

| Gate Metric | Command / Audit Rule | Formal Status | Scope & Boundary |
|---|---|---|---|
| **Aggregate Build** | `lake build Paper043` | **PASS (2,974 jobs)** | 11 modules under `Paper043/` and top-level target. |
| **Escape-Keyword Audit** | `rg '\bsorry\b\|\badmit\b\|\baxiom\b\|\bunsafe\b'` | **PASS (0 matches)** | Zero unproved escapes or custom axioms. |
| **Axiom Coverage** | 50 `#print axioms` commands matching 50 theorems | **PASS (50 / 50)** | Every public declaration is axiom-audited. |
| **Authority Terminal** | Terminal status & review | `OpenObstruction` | `AuthorityEffect: None`; zero authority minted. |

---

## 2. Axiom Partitioning Across the 50 Theorems

Paper 043 was recorded (2026-09-29) as introducing zero new axioms, with all theorems elaborating within standard Lean 4 / Mathlib foundations; at the source pin four of its files do not elaborate (see the current-source status above):

- **No Axioms (Pure Constructive Core, 27 Theorems):**  
  `shadow_collision_blocks_total_decoder`, `shadow_factorization_implies_fiber_invariance`, `shadow_coarsening_cannot_repair_collision`, `shadow_augmentation_must_separate_collision`, `shadow_derived_augmentation_cannot_repair_collision`, `lggr_minimal_delta`, `lggr_local_green_does_not_force_global_green`, `lggr_local_dashboard_identifies_good_and_bad`, `local_consistency_without_bridge_maps_is_not_ready`, `no_typed_packet_decoder_of_collision`, `finite_typed_packet_projection_collides`, `finite_typed_packet_targets_differ`, `finite_typed_packet_collision_blocks_total_decoder`, `zero_budget_blocks_every_licensed_lift`, `concrete_zero_budget_trigger_is_populated`, `concrete_zero_budget_trigger_has_no_licensed_target`, `exists_populated_zero_budget_trigger_without_license`, `constant_pass_detector_is_total`, `constant_pass_detector_not_adequate`, `eight_clause_fidelity_does_not_certify_constant_detector`, `eight_clause_fidelity_records_no_authority_expansion`, `detector_adequacy_rejects_constant_detectors`, `FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_symbols`, `FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_operators`, `FixedAlphabetTerm.fixed_alphabet_nesting_preserves_declarations`, `admitted_operation_effect_none`, `applyLift_advances_level`.

- **`[propext]` (Propositional Extensionality, 15 Theorems):**  
  `fidelity_clause_mem_all`, `replay_fidelity_clause_iff`, `replay_all_eight_fidelity_iff`, `finite_bool_fidelity_adequacy_separation`, `validator_report_exhaustive`, `terminalizer_total`, `terminalizer_deterministic`, `certificate_implies_every_gate`, `refusal_rows_preempt_certificate`, `repair_rows_preempt_certificate`, `refusal_or_repair_preempts_certificate`, `recursive_fold_retains_child_outputs`, `recursive_fold_composes_child_effect`, `internal_operation_tree_effect_closure`, `internal_operation_tree_outputs_not_authority`.

- **`[Quot.sound]` (Quotient Soundness, 4 Theorems):**  
  `shadow_quotient_descent_iff_fiber_invariance`, `lggr_global_green_does_not_descend`, `lggr_evaluator_defect_does_not_descend`, `symbol_game_lggr_authority_firewall_finite_consequences`.

- **`[propext, Quot.sound]` (3 Theorems):**  
  `applyLift_strictly_decreases_budget`, `applyLift_increases_declared_mass`, `applyLift_is_licensed`.

- **`[propext, Classical.choice, Quot.sound]` (1 Theorem):**  
  `lp_max_form_weak_duality` (exact weak LP duality over linearly ordered fields).

---

## 3. Formal Packet Census & Claim Scopes (L043_01 to L043_11)

| Module / Packet | Formal Theorems | Classification | Exact Scope & Surviving Boundary |
|---|---|---|---|
| **L043_01 & L043_02** (Shadow & LGGR Facades) | `shadow_collision_blocks_total_decoder`, `lggr_local_green_does_not_force_global_green`, `lggr_global_green_does_not_descend` | Imported wrappers | Discharges finite collision; does not prove every representation collides; zero sheaf cohomology claims. |
| **L043_03** (Typed-Packet Collision) | `no_typed_packet_decoder_of_collision`, `finite_typed_packet_collision_blocks_total_decoder` | Substantive lemma + finite countermodel | Shows existence of colliding pairs; does not assert that every packet forgets all truth. |
| **L043_04** (Trigger vs License) | `exists_populated_zero_budget_trigger_without_license` | Finite countermodel | Shows populated triggers do not imply a licensed lift; authority remains outside Lean. |
| **L043_05** (Fidelity & Adequacy) | `replay_all_eight_fidelity_iff`, `constant_pass_detector_not_adequate`, `finite_bool_fidelity_adequacy_separation` | Located contract model + separation | Separates 8-clause replay fidelity from detector adequacy; rejects trivial constant detectors. |
| **L043_06** (Fixed-Alphabet Depth) | `FixedAlphabetTerm.fixed_alphabet_nesting_preserves_declarations` | Narrow induction theorem | Shows unary nesting preserves declaration predicates; full $S(n)$ equality remains open. |
| **L043_07** (LP Weak Duality) | `lp_max_form_weak_duality` | Substantive theorem | States $c^\top x \le b^\top y$ for feasible $x, y \ge 0$ over linearly ordered field $K$; maximum form only (not typechecked at the pin). |
| **L043_08** (Terminalizer Policy) | `terminalizer_total`, `terminalizer_deterministic`, `certificate_implies_every_gate` | Finite policy theorems | States total determinism and gate implication for first-match table; host routing only. |
| **L043_09** (Operation Fold Recursion) | `recursive_fold_retains_child_outputs`, `internal_operation_tree_effect_closure` | Recursion + closure theorem | Shows child folding preserves output and closes with effect `.none`; firewall holds by definition. |
| **L043_10** (Lift Patch Semantics) | `applyLift_advances_level`, `applyLift_strictly_decreases_budget`, `applyLift_is_licensed` | Constructive count-shadow theorem | Derives licensed lift, level increment, and budget decrease from applicable patch; no obstruction killing. |
| **L043_11** (ENC-0933 Facade) | `symbol_game_lggr_authority_firewall_finite_consequences` | Wrapper | Finite consequence conjunction; authority exclusions are signature definitions. |

---

## 4. Key Epistemic Takeaways

1. **Receipt Integrity:** All 50 declarations build cleanly with zero unproved holes (`sorry`, `admit`).
2. **Strict Scope Discipline:** A green Lean build verifies only the exact compiled type on its declared carrier; it does not promote finite toy models into general physical theorems.
3. **Authority Firewall:** `admitted_operation_effect_none` and related theorems verify that all internal operation effects evaluate to `.none`; the Symbol Game never issues operational authority.

---

## 5. Claim Hygiene Quadrant

1. **What this supports:**
   - Mechanical audit of all 50 formal Lean 4 theorems in `Paper043.lean` with clean elaboration.
   - Exact cataloging of theorem classifications (substantive, structural, definition-unfolding).
2. **What this does not support:**
   - Does not claim formal Lean verification extends to unmechanized trans-base stages beyond S(6).
   - Does not assert that Lean theorem verification grants runtime operational authority.
3. **The narrowest defensible claim:**
   - The 50 theorems in `Paper043.lean` compile with no project-specific axioms or proof holes; theorem dependencies are limited to the listed Lean/Mathlib foundational axioms (`propext`, `Classical.choice`, `Quot.sound`).
4. **Next test needed:**
   - Maintain continuous Lake build verification on the local workstation.
