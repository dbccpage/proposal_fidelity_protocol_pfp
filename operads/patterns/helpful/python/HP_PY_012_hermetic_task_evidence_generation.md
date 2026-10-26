---
pattern_id: HP_PY_012
name: hermetic_task_evidence_generation
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_012_cross_task_evidence_borrowing
language: python
authority_effect: None
---

# Healthy Pattern: Hermetic Task Evidence Generation (`HP_PY_012`)

## Description

Evidence generation is strictly scoped to the evaluated task and its current candidate bytes. Pass verdicts and verification receipts must be generated from direct local test suite execution within the isolated task scope, refusing any foreign or antecedent receipt reuse.

## Structural Signature

```python
def verify_candidate_task_evidence(task_id: str, candidate_digest: str, runner: TestRunner) -> VerificationReceipt:
    result = runner.run_tests(scoped_task_id=task_id, candidate_hash=candidate_digest)
    if result.exit_code != 0 or result.passed_count == 0 or result.failed_count > 0:
        return VerificationReceipt(
            task_id=task_id,
            candidate_digest=candidate_digest,
            status=TerminalStatus.REJECTED,
            reason="Hermetic execution failed or zero tests executed.",
        )
    return VerificationReceipt(
        task_id=task_id,
        candidate_digest=candidate_digest,
        status=TerminalStatus.ACCEPTED,
        evidence_digest=result.evidence_digest,
    )
```

## Remediation Applied

- Enforce that `receipt.task_id == current_task_id` and `receipt.candidate_digest == hash(candidate_bytes)`.
- Refuse any evaluation that attempts to import or cite an antecedent task's receipt as proof of current correctness.
- Re-run the full acceptance command whenever candidate bytes change.
