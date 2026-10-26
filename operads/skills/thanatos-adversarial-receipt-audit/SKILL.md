---
name: thanatos-adversarial-receipt-audit
description: "Audit receipts adversarially for semantic lies, un-recomputed bindings and evidence that does not match the claim."

operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# adversarial-receipt-audit

## Purpose

Orchestrates multi-perspective adversarial receipt audits across paper claims, proof ledgers, and build receipts.

## Rules

1. **Multi-Auditor Fanout**: Enumerate claim-bearing artifacts and assign independent auditors with explicit attack requirements.
2. **Adversarial Refutation**: Refute plausible-but-wrong findings; default to REFUTED when uncertain.
3. **Semantic Verification**: Verify that green build claims match the actual content and authority level of built artifacts.
4. **Post-Audit Source Continuity**: Audit receipts must bind the exact source hashes examined; snapshot emission must verify that no byte has changed post-audit before emitting publication receipts (`ANTI-POST-AUDIT-MUTATION-RACE`).
5. **Scoped State Digest Attribution**: State digests must explicitly declare omitted variables (e.g. remaining fuel, diagnostic findings) rather than asserting universal state identity (`ANTI-INCOMPLETE-STATE-DIGEST-OVERCLAIM`).
6. **Feasibility Validation Before Objective Equality**: Auditing dual witness receipts requires independent verification of primal feasibility, boundary divergence, and capacity constraints; objective equality without feasibility is an adversarial defect.

AuthorityEffect: None.
