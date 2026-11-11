# WF26: Multi-round antibody dialogue

**Layer:** 7 · **Builds on:** [WF9](Workflow-WF9.md), [WF14](Workflow-WF14.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer7.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer7.py) (`MultiRoundAntibodyDialogue`) · **Folder:** [`workflows/wf26_multi_round_antibody_dialogue`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf26_multi_round_antibody_dialogue) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Each host-classified failure becomes a typed negative constraint carried into later rounds.

Domain: the monic polynomial with stated roots (WF14). The exact oracle is
equality with the expanded product. A rejected round adds the epitope's fixed
constraint (never a coefficient value) to the antibody set, and every later
prompt carries the whole set. Refused: recurring failures that exhaust the
round limit and replies that never parse.

## Procedure

1. Run up to R dialogue rounds on one task
2. Turn each recorded hallucination into a typed negative-constraint antibody
3. Carry accumulated antibodies into the next round
4. Accept only on the exact oracle

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- antibody set A_{t+1} = A_t ∪ {typed constraint from failure_t}; stop when check passes or t = R

## Host check

`epitope_antibody_exact_oracle`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF26
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF26-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `repaired_with_two_antibodies` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `recurring_epitope_exhausts_rounds` | REFUSED | REFUSED | `REPAIR_LIMIT_EXHAUSTED` |
| `never_parses` | REFUSED | REFUSED | `REPAIR_LIMIT_EXHAUSTED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `epitope_antibody_exact_oracle` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF26 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
