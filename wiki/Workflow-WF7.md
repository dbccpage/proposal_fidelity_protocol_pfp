# WF7: Typed refusal

**Layer:** 1 · **Builds on:** [WF1](Workflow-WF1.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer1.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer1.py) (`TypedRefusal`) · **Folder:** [`workflows/wf07_typed_refusal`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf07_typed_refusal) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Answer ``A x = b`` exactly, or refuse with the code the rank test predicts.

The host decides answerability by Rouche-Capelli: a unique solution needs
``rank(A) = rank([A|b]) = n``. A confident answer to an unanswerable task is
a bluff; a refusal of a solvable task is a false refusal. Both are refused.

## Procedure

1. Declare the answerability predicate and the refusal codes
2. Pose an underdetermined or undefined task
3. Accept only the correct typed refusal or a checked answer
4. Count bluffs: a confident answer to an unanswerable task

## Mathematics

- answerable(A x = b) iff rank(A) = rank([A|b]) = n; otherwise the right outcome is UNRESOLVED <code>
- bluff rate = #(answered and unanswerable) / #unanswerable

## Host check

`typed_refusal_rank_test`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF7
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF7-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `solvable_answered` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFIED` |
| `inconsistent_refused` | TYPED_REFUSAL | TYPED_REFUSAL | `UNRESOLVED_INCONSISTENT` |
| `underdetermined_refused` | TYPED_REFUSAL | TYPED_REFUSAL | `UNRESOLVED_UNDERDETERMINED` |
| `bluff_on_inconsistent` | REFUSED | REFUSED | `BLUFF` |
| `false_refusal_on_solvable` | REFUSED | REFUSED | `FALSE_REFUSAL` |
| `wrong_code` | REFUSED | REFUSED | `WRONG_REFUSAL_CODE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `typed_refusal_rank_test` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF7 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
