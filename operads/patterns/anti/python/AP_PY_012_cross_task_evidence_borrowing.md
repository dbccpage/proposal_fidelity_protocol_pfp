---
pattern_id: AP_PY_012
name: cross_task_evidence_borrowing
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_012_hermetic_task_evidence_generation
language: python
authority_effect: None
---

# Anti-Pattern: Cross-Task Evidence Borrowing (`AP_PY_012`)

## Description

A task or evaluation loop borrows, inherits, or reuses a verification receipt, test digest, or `PASS_TO_MASTER` marker from an antecedent or foreign task rather than executing independent verification against its own frozen candidate bytes.

## Detection Signature

- A task completion or receipt emitter references `receipt.task_id != current_task_id` or copies an external test digest without local execution.
- Observed in `oewas009_20261011_cross_engine_ingress`: "The task cannot borrow another task's evidence. Inheriting an antecedent's PASS_TO_MASTER receipt or test digest without fresh execution on the current task's exact candidate bytes."
- Code pattern:
  ```python
  if antecedent_receipt.status == "PASS_TO_MASTER":
      return current_task.mark_passed(evidence=antecedent_receipt.evidence)
  ```

## Hazard & Failure Mode

- Violates `RL_ENG_ORACLE_001` (Fail-Closed Epistemic Oracle Verification) and `RULE_RESEARCH_LOOP_EVIDENCE_001`.
- Permits an unvalidated candidate or corrupted patch to masquerade as verified by inheriting historical passes.
- Destroys provenance integrity and breaks hermetic audit custody.

## Dual Healthy Pattern

See [HP_PY_012_hermetic_task_evidence_generation](../../helpful/python/HP_PY_012_hermetic_task_evidence_generation.md).
