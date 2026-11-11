# WF28: Eight-role audit dialogue

**Layer:** 8 · **Builds on:** [WF15](Workflow-WF15.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer8.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer8.py) (`EightRoleAuditDialogue`) · **Folder:** [`workflows/wf28_eight_role_audit_dialogue`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf28_eight_role_audit_dialogue) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Eight roles in fixed order repair a potential; only the host defect decides.

Domain: measured edge differences ``c`` on a graph; a state role proposes a
vertex potential ``phi`` and the host defect is ``||c - delta phi||_1``.
Each role sees only the frozen earlier outputs and must quote their seal
head. State roles must strictly lower the defect; the run certifies only at
defect 0. A stale view, a non-descending step or any acceptance claim is refused.

## Procedure

1. Proposer, adversary, solver, overconfidence probe, stabilizer, schema auditor, truth repair, terminal arbiter in sequence
2. Each role sees only frozen earlier outputs
3. Host check decides; the arbiter cannot accept

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- strict descent of the l1 defect across the role sequence

## Host check

`strict_l1_defect_descent`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF28
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF28-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `strict_descent_to_zero` | HOST_CERTIFIED | HOST_CERTIFIED | `AUDIT_CLOSED` |
| `stabilizer_raises_defect` | REFUSED | REFUSED | `DEFECT_NOT_DESCENDING` |
| `arbiter_accepts` | REFUSED | REFUSED | `ROLE_CANNOT_ACCEPT` |
| `auditor_reads_stale_view` | REFUSED | REFUSED | `STALE_VIEW` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `strict_l1_defect_descent` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF28 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
