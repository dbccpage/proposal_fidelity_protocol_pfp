---
name: woland-hermetic-task-audit
description: "Audit Woland runs and teamwork packages for hermetic task execution, zero evidence borrowing across tasks, and strict input schema enforcement."
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, woland, audit, verification]
---

# Woland Hermetic Task Audit (`woland-hermetic-task-audit`)

**AuthorityEffect:** None.

## Purpose

Enforce that execution runs, teamwork packets, and review artifacts in `_ic/darpa/woland/runs/` adhere strictly to hermetic task scope:
1. **Zero Evidence Borrowing**: Evidence and receipts must originate exclusively from local test executions against the current task's frozen candidate bytes. Borrowing or inheriting an antecedent task's `PASS_TO_MASTER` receipt without fresh local execution is refused.
2. **Strict Schema Enforcement**: Input steps and arguments must be strictly checked against declared schemas; silent coercion of scalars into operations or silent dropping of non-matching items is refused.

## Core Rules

1. **Exact-Byte Task Binding**:
   - The evaluated `receipt.json` must record `task_id == current_task_id` and match the SHA-256 of candidate files on disk.
   - Any reference to an external or prior run's receipt as justification for current pass status triggers `REJECTED: TASK_EVIDENCE_BORROWING_LEAK`.

2. **Executed Test Count Verification**:
   - The receipt or test output must certify positive passed test counts (`passed > 0`) with zero failures and zero collection errors.
   - A pass verdict accompanying 0 executed tests triggers `REJECTED: NO_TESTS_EXECUTED`.

3. **Strict Input Schema Parity**:
   - Parsers must emit typed `RefusalRecord` (e.g. `BAD_STEP`) on malformed scalar steps or invalid operation names.
   - Silent conversion or dropping of list elements is an automatic audit failure (`AP_PY_013`).

## Audit Checklist & Verification Commands

```powershell
# 1. Verify candidate hash against receipt binding
python -c "
import json, hashlib
with open('receipt.json', 'r') as f: r = json.load(f)
assert r.get('task_id') == '<current_task_id>'
assert r.get('candidate_digest') == '<expected_hash>'
"

# 2. Check for cross-task borrowing leakage
grep -rn "evidence.*=.*antecedent" _ic/darpa/woland/runs/<task_id>/
```

## Emission

- **PASS**: Sealed verification receipt with local candidate digest and non-zero test execution record.
- **REJECTED**: Typed refusal with reason `TASK_EVIDENCE_BORROWING_LEAK` or `SILENT_INPUT_SCHEMA_COERCION`.
