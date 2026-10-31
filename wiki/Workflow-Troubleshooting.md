# A workflow stopped. What now?

**First: keep the actual reply and the check result.** Find the failed step
before requesting another response. A refusal can be the correct result.

| What you see | What it means | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: omega_engine_pfp` | You used an older integration command in the standalone repo. | Use [Integration status](Workflow-Integration-Status.md) and the current WF1 walkthrough. |
| `ModuleNotFoundError: jsonschema` | The optional pure task-turn checker dependency is missing. | Install the pinned dependency on the WF1 page in the same Python environment. |
| The run folder already exists | A fresh attempt would overwrite evidence. | Keep it; choose a new run folder for a new attempt. |
| Wrong task/attempt ID or input digest | The reply belongs to a different prepared turn. | Match the reply to its original task; do not edit the raw reply to make it fit. |
| Extra prose, code fences or malformed JSON | The model did not satisfy the reply contract. | Retain the raw bytes and report a contract failure. |
| Missing slot or invalid field type | The response is structurally incomplete. | Inspect the named field and original schema before a new attempt. |
| Arity does not match the ordered ports | The operation metadata is inconsistent. | Count typed inputs; one list port can contain many elements. |
| Unknown witness/source reference | A reference does not resolve in the declared contract. | Keep it as rejected; ask for a valid reference only in an explicitly new attempt. |
| JSON is valid, but the answer is wrong | Shape passed; the task check failed. | Record a task failure and its independent checker result. |
| Locals pass and the global check fails | The global requirement is not established. | Keep all local/global results; refuse selection until the declared global check passes. |
| Rewrite leaves unresolved meaning | Preservation has not been established. | Stop before mining/solving; clarify or implement a new source-language contract. |
| Cost is missing or a send is ambiguous | Liability is unknown. | Keep the reservation and stop dependent calls; reconcile through the provider adapter. |
| The batch does not fit | Five independent caps would exceed the shared allowance. | Refuse before dispatch; declare a new bounded plan if changing the workflow. |

## Three failures that need different fixes

**Contract failure:** the reply cannot be checked as submitted. Improve the
contract or provider projection in a new version, keeping the failure.

**Task failure:** the reply fits the contract but fails the independent task
check. A stricter JSON parser alone will not correct the answer.

**Checker defect:** the checking system crashed or could not decide its declared
property. Stop generation; fix the checker/integration and keep the original result.

These are not automatically three counted hallucinations. A false-claim count
needs a stated claim set and independent audit. [Results and costs](Workflow-Results.md)
shows how those distinctions were used in the first experiments.

## Resume without losing your place

Write down: recipe/version, run folder, last completed step, pending liabilities
and the next allowed action. Rechecking saved bytes makes no model call.
For a new paid attempt, preserve lineage and the remaining original allowance.

[Back to workflows](Workflows.md) · [Glossary](Workflow-Glossary.md)

## Migrated runners

Install with `python -m pip install ".[workflows]"` using Python 3.12+.
Use `pfp.workflows.wf0001` through `wf0005`; keep older `omega_engine_pfp`
commands with their original integration. `NATIVE_BUDGET_UNAVAILABLE` applies
to the optional native hard-budget path; the documented commands use the
accounted estimated path. Never switch to unbounded billing to bypass a refusal.
See [Install and run](Workflow-Running.md) for the exact argument shapes.
