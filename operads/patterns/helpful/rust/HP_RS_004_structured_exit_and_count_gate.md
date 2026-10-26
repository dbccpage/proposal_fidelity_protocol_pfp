---
pattern_id: HP_RS_004
name: structured_exit_and_count_gate
category: helpful_pattern
operad_type: Isomorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "exact"
dual_pattern: AP_RS_004_unvetted_early_process_exit
language: rust
authority_effect: None
---

# Helpful Pattern: Structured Exit and Count Gate (`HP_RS_004`)

## Description

Verifying candidate test runs by parsing structured runner output for positive execution counts (`passed > 0`), ensuring zero failures and zero errors (`failed == 0`, `errors == 0`), and rejecting test suites that terminate with zero executed assertions.

## Implementation Pattern

```python
# In test oracles / test runners:
match = re.search(r"(\d+)\s+passed", stdout)
passed_count = int(match.group(1)) if match else 0
if passed_count == 0 or returncode != 0:
    return Refusal(code="NO_TESTS_EXECUTED", message="No tests passed")
```

## Guarantees Under Declared Assumptions

- Disallows silent early exit (`os._exit(0)` / `process::exit(0)`) from counterfeiting test pass receipts.
- Ensures evidence corresponds to real assertion executions.
