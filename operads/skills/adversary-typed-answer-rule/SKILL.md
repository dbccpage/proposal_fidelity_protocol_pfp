---
name: adversary-typed-answer-rule
description: "Review exact task bindings, full typed answers and nested result snapshots."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-typed-answer-rule.json"
  core-contracts-digest: "sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "rule"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-typed-answer-rule

Generated guidance; edit the canonical typed contract and instruction resource.

# Complete typed answer and task binding

Use the existing Python runtime-invariants rule at an exact request/answer boundary. Compare the complete typed answer and complete task binding; true and 1 are distinct contract values. Snapshot nested result data so later input mutation cannot alter the evaluated answer. Keep raw byte identity separate from the declared semantic request encoding.

Read the retained Hodge candidate controls when relevant. Report the current source observation and its scope; retained checks are historical. This guidance introduces no universal JSON profile or authentication contract.

## Digested lesson

Source: `operads/rules/engineering/rl_python_contracts_and_runtime_invariants.md` @ `rule-factorization-v1-20261023` (sha256:cab311ef450208649020ff744361885b57c08d87b59dbbf7f2f865198f4918a2).

Source excerpt (evidence to inspect):

```text
At an existing exact contract boundary, compare the complete typed answer and its
complete task binding, then snapshot nested result data.
```

**Failed Claim:** Matching a selected field or a Python-equal value is sufficient to accept a submitted exact answer.

**Counterexample:** The retained Hodge controls change the task binding, substitute true for an integer and mutate nested input after evaluation.

**Cause:** Partial comparison, bool/int equality and shared mutable aliases can discard parts of the declared answer contract.

**Correction:** Compare every declared answer field using the existing typed comparison, check the complete request binding and snapshot nested result values.

**Verification:** The complete current rule and this lesson were re-read at f5af2f218b7ac0261f3f7c8fe62cad360e256f55 on 2026-10-19. The quoted guidance remains present; applicability and exceptions are unchanged. This updates current source custody only. Historical Hodge execution, detector effectiveness, and authority/admission promotion are not newly claimed. Source ownership relocated without changing the bound source bytes, quoted evidence, applicability, or admission; this is not new historical execution. On 2026-10-23 the compact rule retains the exact quoted evidence and routes to the preserved full definitions. The current source bytes are rebound without adding a dependency on the documentation skill. Applicability, exceptions, instruction and admission are unchanged. This source-content revision is not a new historical execution, admission or authority promotion.

**Applicability:** Existing exact request/answer boundaries with a declared type and task-binding contract.

**Exceptions:** Do not invent a universal JSON canonicalization profile, prescribe unrelated parser limits, claim authentication from a hash or infer general correctness from a finite match.

## Guidance contract

**Trigger:** Reviewing code that accepts an exact answer bound to a request or task.

**Predicate:** Every declared answer field and complete task binding agrees under the existing typed contract; accepted nested values are independent snapshots.

**Response:** Report a concrete mismatch or alias witness and repair the existing comparison/snapshot owner; preserve the declared encoding and unaffected behavior.

Ordered signature: `(code: Code) -> findings: Audit`.

Contracts: `sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
