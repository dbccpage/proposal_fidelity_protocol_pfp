---
rule_id: RL_ENG_ORACLE_001
name: fail_closed_epistemic_oracle_verification
category: engineering
subsystem: adversary
authority_effect: None
paths:
  - "education/**/atlas/**"
---

# Rule: Fail-Closed Epistemic Verification

**AuthorityEffect:** None.

**Guard:** Fail-Closed Epistemic Verification invariants.

**Compose:** [shared boundary vocabulary](../../skills/techne-documentation-manager/references/rules_index.md#shared-boundary-vocabulary). Read the relevant definition before acting; retain its conditions, exceptions, witnesses and refusal.

## Definitions, loaded on demand

- [Part 1](../../skills/techne-documentation-manager/references/rule_details/engineering/rl_fail_closed_epistemic_oracle_verification_01.md): Engineering Rule: Fail-Closed Epistemic Oracle Verification (`RL_ENG_ORACLE_001`); Mandate; Invariants.

## Stable invariant references

`RULE_CICD_AUDITOR_CENSUS_AND_STANDBY_GATE_001`, `RULE_CROSS_LANGUAGE_COMPLEXITY_AND_INTEGRITY_001`, `RULE_FAIL_CLOSED_FORMAL_TOOLCHAIN_001`.
