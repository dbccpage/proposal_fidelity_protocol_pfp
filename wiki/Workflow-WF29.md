# WF29: Checker synthesis scored by mutation kill rate

**Layer:** 4 · **Builds on:** [WF11](Workflow-WF11.md) · **Merges into:** WF11 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer4.py) (`CheckerSynthesisMutationKill`) · **Folder:** [`workflows/wf29_checker_synthesis_scored_by_mutation_kill_rate`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf29_checker_synthesis_scored_by_mutation_kill_rate) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Score a proposed checker by its mutation kill rate, after it passes every valid case.

The declared certificate is a vertex potential ``phi`` with ``delta phi = c`` on a fixed graph. The
checker is a tree over declared predicates (never model code). The host runs it on the public
valid panel and the sealed hostile mutants with exact.mutation_score, and certifies only a sound
checker (zero false rejections) whose kill rate meets the declared bar.

## Procedure

1. The model writes a checker for a declared certificate
2. Run it against valid cases and a hostile mutation suite
3. Score by kills and by false rejections

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- kill rate = killed / mutants; soundness requires zero false rejections on valid cases

## Host check

`mutation_kill_rate_with_valid_panel`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF29
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF29-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `sound_checker_kills_all` | HOST_CERTIFIED | HOST_CERTIFIED | `CHECKER_ACCEPTED` |
| `root_gauge_falsely_rejects` | REFUSED | REFUSED | `NO_FALSE_REJECTION` |
| `cycle_only_checker_too_weak` | REFUSED | REFUSED | `KILL_RATE_MEETS_BAR` |
| `model_code_not_executed` | REFUSED | REFUSED | `MALFORMED_CANDIDATE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `mutation_kill_rate_with_valid_panel` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF29 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
