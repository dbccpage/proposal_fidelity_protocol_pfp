# WF33: Recursive re-entry with shared fuel

**Layer:** 9 · **Builds on:** [WF9](Workflow-WF9.md), [WF20](Workflow-WF20.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer9.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer9.py) (`RecursiveReentryWithSharedFuel`) · **Folder:** [`workflows/wf33_recursive_re_entry_with_shared_fuel`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf33_recursive_re_entry_with_shared_fuel) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Split a repair into child derivations that share one fuel counter and one budget.

Domain: XOR edge labels on a graph. A plan maps root edges onto children
(forward coverage must be a partition); each child re-enters the WF20 loop
on its subgraph, and its flips map back to root edges, where the union must
pass the root WF9 check. Every ask draws from a strictly decreasing fuel
counter. A stale parent receipt, a changed task or a fuel reset is refused.

## Procedure

1. An output becomes the next proposal
2. Check a backward solution map and a forward coverage map per edge
3. Bind the parent receipt
4. Charge every prefix against one original budget

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- at most floor(B / delta) operations under budget B; stale parent, changed task or fuel reset is refused

## Host check

`shared_fuel_parent_bound_reentry`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF33
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF33-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `two_children_share_fuel` | HOST_CERTIFIED | HOST_CERTIFIED | `REENTRY_CERTIFIED` |
| `stale_parent_receipt` | REFUSED | REFUSED | `STALE_PARENT_RECEIPT` |
| `changed_task_on_reentry` | REFUSED | REFUSED | `TASK_CHANGED` |
| `fuel_reset_by_child` | REFUSED | REFUSED | `FUEL_RESET` |
| `overlapping_coverage` | REFUSED | REFUSED | `COVERAGE_NOT_A_PARTITION` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `shared_fuel_parent_bound_reentry` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF33 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
