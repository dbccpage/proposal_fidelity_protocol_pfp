# WF35: Proposal-channel comparison

**Layer:** 6 · **Builds on:** [WF6](Workflow-WF6.md), [WF12](Workflow-WF12.md) · **Merges into:** nothing · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer6.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer6.py) (`ProposalChannelComparison`) · **Folder:** [`workflows/wf35_proposal_channel_comparison`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf35_proposal_channel_comparison) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Compare proposal channels under one fixed host check; acceptance depends only on reply bytes.

Each arm (prompt, grammar mask, logit mask, ...) answers the same weighted
digraph items. The host grades every reply with the one pinned duality
grader, ignores any acceptance a channel reports for itself, and reports
per-arm accepts and discordant pairs. It refuses arms with different
checkers or budgets and any channel whose self-reported accept set differs.

## Procedure

1. Fix the host check
2. Vary only the channel: prompt, glyph code, logit mask, grammar mask, typed tree, attention or activation bias
3. Compare per item

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- channel invariance: the accept set depends on the reply, never on the channel that produced it

## Host check

`channel_blind_fixed_oracle`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF35
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF35-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `channels_compared_on_one_checker` | HOST_CERTIFIED | HOST_CERTIFIED | `CHANNELS_COMPARED` |
| `arms_used_different_checkers` | REFUSED | REFUSED | `ARMS_NOT_MATCHED` |
| `arms_used_different_budgets` | REFUSED | REFUSED | `ARMS_NOT_MATCHED` |
| `channel_label_claims_acceptance` | REFUSED | REFUSED | `ACCEPT_SET_DEPENDS_ONLY_ON_BYTES` |
| `grammar_mask_accepts_parallel_edge_violation` | REFUSED | REFUSED | `ACCEPT_SET_DEPENDS_ONLY_ON_BYTES` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `channel_blind_fixed_oracle` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF35 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
