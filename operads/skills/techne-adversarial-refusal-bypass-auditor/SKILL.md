---
name: techne-adversarial-refusal-bypass-auditor
description: "Generate hostile refusal-code permutations across evaluators and assert zero false-pass admissions."
operad_source_colours:
  - Code
  - Audit
operad_target_colour: Receipt
operad_arity: 2
operad_residual: diagnostic
families:
  - techne
  - testing
  - security
  - governance
---

# Techne Adversarial Refusal Bypass Auditor

**AuthorityEffect:** None.  
**Council:** `L3_logos_techne`  
**Status:** Active.

## Mission & Governance Invariants

The **Adversarial Refusal Bypass Auditor** stress-tests test harnesses, evaluator gates, and domain ports by generating hostile permutations of refusal codes, error envelopes, and malformed payload shapes. It asserts that no ambiguous, corrupted, or falsified refusal is ever mistakenly classified as a successful evaluation (`PASS` or `Ok`).

In accordance with Railway-Oriented Programming (ROP) and fail-closed security standards:

1. **Fail-Closed Gate Invariant:** Any response that is not explicitly and unambiguously valid `Ok(T)` must be routed to the refusal branch. Absence of a refusal key, presence of a non-standard refusal code, or a malformed status dictionary must never default to success.
2. **Conflicting Signal Rejection:** Payloads containing conflicting indicators (e.g. `{"status": "PASS", "refusal": "ERR_BLOCK"}` or `{"ok": true, "error": "fatal"}`) must trigger immediate execution halts and be rejected as hostile tampering.
3. **Type Coercion Immunity:** Evaluators must evaluate boolean and structural properties with strict type checks (`isinstance`, strict type equality). Evaluator logic must not treat `refusal=0`, `refusal=False`, `refusal="None"`, or empty collections as truthy passes.

---

## Targeted Adversarial Mutation Catalogue

| Mutation ID | Target Surface | Injected Hostile Shape | Expected Evaluator Behavior |
|---|---|---|---|
| `ARB-MUT-001` | Refusal Key Scrambling | `{"refusal_code": "ERR_FAIL"}` instead of `{"refusal": ...}` | Refused / parse error; never `PASS`. |
| `ARB-MUT-002` | Empty Payload | `{}` or `None` or `""` | Refused (`EMPTY_PAYLOAD_REFUSAL`). |
| `ARB-MUT-003` | Conflicting State | `{"status": "PASS", "refusal": "UNAUTHORIZED"}` | Immediate abort (`CONFLICTING_VERDICT_DEFECT`). |
| `ARB-MUT-004` | Bogus String Boolean | `{"success": "false", "refusal": null}` | Refused; string `"false"` must not evaluate as truthy. |
| `ARB-MUT-005` | Zero Integer Code | `{"error_code": 0, "status": "FAIL"}` | Fail-closed routing; error code 0 must not bypass failure. |
| `ARB-MUT-006` | Truncated Reason | `{"refusal": "REJECT", "message": None}` | Preserves refusal state; missing message must not cause default pass. |

---

## Operational Workflow

### 1. Running the Adversarial Audit

Execute the auditor against target evaluator test suites or bounded contexts:

```console
# Run targeted test sweep with hostile refusal injection
py -3.12 -m pytest omega_engine_operations/tests/unit/ -k "refusal"

# Execute standalone refusal bypass validation
py -3.12 -m omega_engine_operations.use_cases.verification.adversarial_refusal_audit --target <module_path>
```

### 2. Evaluator Assertion Rules

When authoring or reviewing evaluators:

```python
# FORBIDDEN: Permissive or unverified truthiness check
if not response.get("refusal"):
    proceed_as_pass()  # CHEAT: {} or missing key passes silently

# REQUIRED: Explicit variant inspection under ROP
if not response.is_ok:
    return StageRefusal(code=response.error.code, reason=response.error.reason)
```

### 3. Claim Hygiene & Audit Reporting

When recording audit results:
- State what the test suite supports (e.g., "Supports that 12 specific hostile refusal variants were rejected fail-closed").
- State what it does not support (e.g., "Does not show absence of arbitrary side-channel bypasses").
- Record narrowest defensible claim and report all unhandled edge cases under `AuthorityEffect: None`.
