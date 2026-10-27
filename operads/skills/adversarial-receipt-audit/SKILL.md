---
name: adversarial-receipt-audit
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
7. **Hermetic Task Scope (Zero Cross-Task Evidence Borrowing)**: Audit receipts must bind execution strictly to the evaluated task's current candidate bytes; borrowing or inheriting pass receipts or test digests from antecedent or foreign tasks is strictly refused (`ANTI-CROSS-TASK-EVIDENCE-BORROWING`).

AuthorityEffect: None.

## Lessons applied from Pilot 22 and Hodge

- Label validation counts as retained, rebound, compiled or freshly executed, with
  their source and module scope. A historical count never certifies the current head.
- Treat a raw file census, syntax projection or equal summary as navigation. Check
  the protected answer itself; include a coherent answer-changing control whose
  other digests have all been correctly rebuilt. Stale-hash controls are insufficient.
- Check that a proposed negative control actually differs from its valid baseline.
  The Hodge probe's original replacement `1` equaled the valid value; `2` was distinct.
- Establish that the baseline meets the control's preconditions, then check that
  the mutation reaches the intended guard and fails for the expected reason.
  Setting an already `OPAQUE` artifact to `OPAQUE` cannot demonstrate rejection
  of a `PROJECTED` artifact. A baseline failure does not establish mutant kills.
- Preserve earlier failed attempts when a corrected invocation succeeds. Attribute
  tests to the actual invocation and source module; duplicate snapshots and generated
  families share review and are not independent corroboration.

Source examples: [Pilot 22 contract](../../../_ic/nara/historical/oewas007/research/briefs/pfp_expansion/pilot22_typed_engine/revision2/candidate/README.md)
and [Hodge probe correction](../../../_ic/nara/historical/oewas007/research/briefs/pfp_migration/hodge_companion_research/critics/stage7/review_activity.json).
These are historical examples, not fresh execution results.

The [Deep Researcher probe corrections](../../../_ic/nara/historical/oewas007/research/briefs/deep_researcher_v0_1/early_failed_probe.md)
retain the invalid negative fixture and a deep-input check that depended on
interpreter recursion. Explicit input depth/node limits belong to the declared
parser contract; incidental interpreter limits do not define it. This guidance
does not adopt the historical parser's particular numeric limits for other tasks.

## Conditional bounds and check binding

Use `/adversary-proof-premise-rule` before consuming a conditional bound, and
`/adversary-check-sensitivity-pattern` before treating a component check as a
certificate of the assembled candidate. Those packages keep the retained
witnesses, later repairs, numerical limits and proposed fixes historical.
This audit does not rerun them.

Check each affected claim projection and keep different bounds' domains separate.
For composed checks, inspect auxiliary-source support and assembly as well as
pairwise components. Use `/adversary-proof-scope-rule` to distinguish quantitative
margins, qualitative consequences and endpoints; a zero lower bound does not
make the actual value zero. The typed packages carry the concrete witnesses and
their source-reported repair limits.
