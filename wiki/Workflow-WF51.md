# WF51: Exclusion hypotheses with cheapest falsifiers

**Layer:** 7 · **Builds on:** [WF14](Workflow-WF14.md), [WF31](Workflow-WF31.md) · **Merges into:** nothing · **Kind:** meta workflow

**Code:** [`pfp_core/workflow_families/layer7.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer7.py) (`ExclusionHypothesisRetest`) · **Folder:** [`workflows/wf51_exclusion_hypotheses_with_cheapest_falsifiers`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf51_exclusion_hypotheses_with_cheapest_falsifiers) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Treat every "don't search here" as a hypothesis and spend tests where models disagree.

Domain: integer roots of an integer polynomial over named, disjoint integer
branches. Stage ``exclude`` returns exclusions: a branch, the seats that
voted on it with their model family, and a falsifier (witness points inside
the branch, cost = number of points). The host classifies each exclusion
with ``pfp_core.exclusions`` (seats of one family are one vote), plans
falsifiers frontier first, then uncorroborated, then probably-dead ones no
dearer than ``dead_floor``, under ``retest_budget``, and evaluates them
exactly. A refuted exclusion reopens its branch. Stage ``solve`` sees only
open branches and returns a root, or ``null`` to claim there is none; the
host checks the root or scans every open branch. With ``retest`` false the
same task is the control arm: no falsifier runs, and a wrong exclusion
can hide the answer behind a lawful typed refusal.

## Procedure

1. Seats from several model families propose exclusions, each with a falsifier and its cost
2. The host counts agreement by model family: disagreement is frontier, one family is uncorroborated, several agreeing families are probably dead
3. Falsifiers run frontier first, then uncorroborated, then probably-dead ones no dearer than the dead floor, under one retest budget
4. A refuted exclusion reopens its branch; the solver sees only open branches
5. Control arm: the same task with retests off

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- seats of one family are one vote, because shared training makes their errors correlated
- an exclusion with no falsifier is refused before any test runs
- a no-root claim is checked by exhaustive scan of the open branches, so the control arm's typed refusal is lawful but can hide the answer

## Host check

`exact_falsifier_and_open_branch_check`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF51
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF51-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `planted_wrong_exclusion_refuted_by_cheap_retest` | HOST_CERTIFIED | HOST_CERTIFIED | `ROOT_CERTIFIED` |
| `same_family_agreement_is_one_vote` | HOST_CERTIFIED | HOST_CERTIFIED | `ROOT_CERTIFIED` |
| `control_without_retest_hides_the_answer` | TYPED_REFUSAL | TYPED_REFUSAL | `NO_ROOT_IN_OPEN_BRANCHES` |
| `exclusion_without_falsifier` | REFUSED | REFUSED | `EXCLUSION_WITHOUT_FALSIFIER` |
| `falsifier_outside_its_branch` | REFUSED | REFUSED | `FALSIFIER_OUTSIDE_BRANCH` |
| `answer_in_closed_branch` | REFUSED | REFUSED | `ANSWER_IN_CLOSED_BRANCH` |
| `false_no_root_claim` | REFUSED | REFUSED | `MISSED_ROOT_IN_OPEN_BRANCH` |
| `wrong_root` | REFUSED | REFUSED | `ROOT_VERIFIED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 5 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `exact_falsifier_and_open_branch_check` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF51 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
