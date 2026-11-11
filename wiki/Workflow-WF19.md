# WF19: Failure-derived rule transfer

**Layer:** 7 · **Builds on:** [WF12](Workflow-WF12.md), [WF14](Workflow-WF14.md) · **Merges into:** nothing · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer7.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer7.py) (`FailureDerivedRuleTransfer`) · **Folder:** [`workflows/wf19_failure_derived_rule_transfer`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf19_failure_derived_rule_transfer) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Rules extracted from training failures are admitted only if they transfer to held-out tasks.

Rules are proposed from public training failures, screened by the thymus on
the sealed self panel and admitted on two signals (WF14). The host then
scores them on disjoint sealed held-out replies: gain = accuracy(rules) -
accuracy(no rules). It refuses zero gain, autoimmune rules after two stages,
overlapping splits, and halts when two independent clean checkers disagree.

## Procedure

1. Compare baseline, typed-witness and failure-derived rule prompts
2. Use disjoint held-out cases
3. Allow at most two stages; checker disagreement stops the run
4. A rule stays a candidate until transfer and self-tolerance are measured

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- transfer gain = acc(rule, held-out) - acc(baseline, held-out) on disjoint items
- a rule is admitted only if gain > 0 and self-tolerance holds (WF14)

## Host check

`held_out_transfer_gain`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF19
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF19-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `rules_transfer_to_held_out` | HOST_CERTIFIED | HOST_CERTIFIED | `RULES_TRANSFER` |
| `refined_after_thymus_kill` | HOST_CERTIFIED | HOST_CERTIFIED | `RULES_TRANSFER` |
| `overfit_rule_no_gain` | REFUSED | REFUSED | `TRANSFER_GAIN_POSITIVE` |
| `autoimmune_after_two_stages` | REFUSED | REFUSED | `SELF_TOLERANCE_HOLDS` |
| `overlapping_split` | REFUSED | REFUSED | `SPLIT_OVERLAP` |
| `checkers_disagree_on_repeated_root` | REFUSED | REFUSED | `CHECKER_DISAGREEMENT` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `held_out_transfer_gain` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF19 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
