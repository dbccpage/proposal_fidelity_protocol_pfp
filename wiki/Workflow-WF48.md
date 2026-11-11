# WF48: Commit-reveal with a hostile mutation gate

**Layer:** 5 · **Builds on:** [WF11](Workflow-WF11.md), [WF23](Workflow-WF23.md) · **Merges into:** WF23 · **Kind:** harness gate

**Code:** [`pfp_core/workflow_families/layer5.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer5.py) (`CommitRevealMutationGate`) · **Folder:** [`workflows/wf48_commit_reveal_with_a_hostile_mutation_gate`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf48_commit_reveal_with_a_hostile_mutation_gate) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Commit an artifact before reveal, then require two checkers to kill every mutant.

The judge manifest names two registered checkers and is committed with a
sealed salt. The proposer commits ``H(salt || potential)`` for a public
cochain, then reveals. The host checks the commitment, both checkers accept
the artifact and its gauge shift, and both reject every hostile mutant. A
changed artifact after commit, or a surviving mutant, is refused.

## Procedure

1. Commit the judge manifest
2. Freeze the solver and commit its hash
3. Reveal hidden cases (base, relabel/gauge controls, poison bait) and score
4. Kill a hostile certificate-mutation suite with both checkers

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- commit H(salt || artifact) before reveal; both checkers must reject every mutant

## Host check

`dual_checker_mutation_suite`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF48
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF48-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `committed_and_both_checkers_kill` | HOST_CERTIFIED | HOST_CERTIFIED | `COMMIT_REVEAL_CERTIFIED` |
| `artifact_changed_after_commit` | REFUSED | REFUSED | `ARTIFACT_CHANGED_AFTER_COMMIT` |
| `weak_checker_lets_mutant_survive` | REFUSED | REFUSED | `LENGTH_ONLY.V1:KILLS_EVERY_MUTANT` |
| `committed_wrong_artifact` | REFUSED | REFUSED | `RESIDUAL.V1:ACCEPTS_ARTIFACT_AND_GAUGE` |
| `manifest_swapped_after_commit` | REFUSED | REFUSED | `MANIFEST_COMMITMENT_MATCHES` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `dual_checker_mutation_suite` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF48 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
