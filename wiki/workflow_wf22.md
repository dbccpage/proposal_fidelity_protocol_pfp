# WF22: Certified cost ladder

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet. The pilots/ folder holds data from earlier model experiments run with an older harness; they are records, not runs of this runner.

**Layer:** 7 · **Builds on:** [WF6](workflow_wf6.md), [WF8](workflow_wf8.md), [WF18](workflow_wf18.md) · **Merges into:** Sweep · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer7.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer7.py) (`CertifiedCostLadder`) · **Folder:** [`workflows/wf22_certified_cost_ladder`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf22_certified_cost_ladder) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Escalate from cheap to expensive arms only after a host refusal, on one budget.

Items are linear systems graded by the WF7 rank test; each arm reply ends with
one canonical ``ANSWER:`` line. The host requires arms in strictly increasing
cost, moves an item up a rung only when the host refused the rung below,
charges every rung to one cap, and reports cost per certified item. It
refuses unordered ladders, a spend past the single cap, and exhausted ladders.

## Procedure

1. Pre-register items, arms and hypotheses
2. Every arm ends with one canonical ANSWER line or ANSWER: UNRESOLVED <code>
3. Run every item under every arm
4. Evaluate hypotheses item by item with refutation criteria

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- cost to certified correct: C_arm = total spend / #accepted
- paired test on discordant items (McNemar-style): b = #(A ok, B fail), c = #(A fail, B ok)
- bluff rate per arm, as in WF7

## Host check

`cost_ladder_refusal_escalation`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF22
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF22-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `escalated_after_bluff` | HOST_CERTIFIED | HOST_CERTIFIED | `LADDER_CERTIFIED` |
| `ladder_not_cost_ordered` | REFUSED | REFUSED | `LADDER_NOT_COST_ORDERED` |
| `spend_past_single_cap` | REFUSED | REFUSED | `BUDGET_EXHAUSTED` |
| `ladder_exhausted_on_bluffs` | REFUSED | REFUSED | `EVERY_ITEM_CERTIFIED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `cost_ladder_refusal_escalation` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF22 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
