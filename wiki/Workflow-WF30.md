# WF30: Constraint-forcing anti-recitation

**Layer:** 1 · **Builds on:** [WF1](Workflow-WF1.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer1.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer1.py) (`ConstraintForcingAntiRecitation`) · **Folder:** [`workflows/wf30_constraint_forcing_anti_recitation`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf30_constraint_forcing_anti_recitation) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> A sorting network under constraints that a memorised network breaks.

The task forces a comparator prefix and forbids some comparators. The host
checks the constraints, the size bound, and sorting by the 0-1 principle:
a comparator network sorts every input iff it sorts all ``2^n`` binary ones.

## Procedure

1. Add task constraints that break memorised textbook answers (forced prefix, forbidden step)
2. Check with the exact property (e.g. the 0-1 principle)

## Mathematics

- a comparator network sorts all inputs iff it sorts all 2^n binary inputs

## Host check

`comparator_network_zero_one_principle`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF30
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF30-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `constrained_network_sorts` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFIED` |
| `recited_textbook_network` | REFUSED | REFUSED | `FORCED_PREFIX_KEPT` |
| `prefix_kept_but_unsorted` | REFUSED | REFUSED | `SORTS_ALL_BINARY_INPUTS` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `comparator_network_zero_one_principle` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF30 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
