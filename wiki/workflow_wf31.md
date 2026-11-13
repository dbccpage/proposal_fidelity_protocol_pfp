# WF31: Multi-agent tournament with held-out cross-validation

**Layer:** 1 · **Builds on:** [WF1](workflow_wf1.md) · **Merges into:** nothing · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer1.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer1.py) (`HeldOutTournament`) · **Folder:** [`workflows/wf31_multi_agent_tournament_with_held_out_cross_validation`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf31_multi_agent_tournament_with_held_out_cross_validation) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Several proposers fit a public training share; the host scores a sealed held-out share.

Each proposer returns exact polynomial coefficients. The referee counts
held-out points the polynomial hits exactly, against a declared baseline
control. Selection is refused when the training and held-out ids overlap,
and no winner is certified unless it strictly beats the baseline.

## Procedure

1. Several proposers answer the same packet each round
2. Include a random-baseline negative control
3. Proposers see a training share of the instance; the host scores the held-out share
4. Rank per budget

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- exact referee: SO(4N), det = +1, defect <= tolerance; held-out score on the 30% the proposer never saw

## Host check

`exact_held_out_referee`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF31
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF31-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `held_out_winner` | HOST_CERTIFIED | HOST_CERTIFIED | `WINNER_SELECTED` |
| `no_one_beats_baseline` | REFUSED | REFUSED | `WINNER_BEATS_BASELINE` |
| `split_overlap` | REFUSED | REFUSED | `SPLIT_OVERLAP` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `exact_held_out_referee` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF31 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
