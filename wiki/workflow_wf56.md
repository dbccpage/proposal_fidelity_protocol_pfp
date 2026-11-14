# WF56: Host-run operad candidates

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 2 · **Builds on:** [WF2](workflow_wf2.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/candidates.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/candidates.py) (`HostRunOperadCandidates`) · **Folder:** [`workflows/wf56_host_run_operad_candidates`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf56_host_run_operad_candidates) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> A reply names the operation it used, with a body from a closed list, and the host runs it.

Domain: integer sums, the task of WF1. In WF2 to WF5 an operad candidate is
a signature and a sentence, so the host can type it and no more. Here a
candidate is ``{"id", "sources", "target", "body"}``: colours from the
canon's ``task_value_colour`` and a body the host can execute. The run:

1. Stage ``solve`` returns candidates and an answer.
2. The host types every candidate and runs each one that has a body on the
   task's case and on the sealed probe cases. It compares each result with
   its own judge's; the caller supplies no expected value.
3. The host judges the answer.

A candidate is ``HOST_VERIFIED`` when its body gave the judge's result on
every case, ``REFUSED`` when it is ill typed or gave another result, and
``UNVERIFIED_CANDIDATE`` when it has no body or does not fit the cases.
The run is certified when at least one candidate is verified, none is
refused and the answer is accepted.

## Procedure

1. One reply gives candidates and an answer; each candidate names source colours, a target colour and a body from the host's closed list
2. The host types every candidate by the canon's task value colours
3. The host runs each candidate that has a body on the task's case and on sealed probe cases
4. The host compares each result with its own judge's result; the caller supplies no expected value
5. The host judges the answer

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- HOST_VERIFIED(c) iff body(c) is in the closed list and eval(c, x) = f(x) for every case x, with f the host judge
- REFUSED(c) iff c is ill typed, its id repeats, or eval(c, x) != f(x) for some case x it fits
- certified iff some candidate is HOST_VERIFIED, none is REFUSED and the answer equals f(x0) on the task's case x0
- probes: cases the prompt never carries, so a body that agrees on x0 by coincidence is still refused

## Host check

`rust_candidate_body_run_against_host_judge`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF56
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF56-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `list_sum_is_verified` | HOST_CERTIFIED | HOST_CERTIFIED | `CANDIDATE_VERIFIED` |
| `one_input_per_value_is_verified` | HOST_CERTIFIED | HOST_CERTIFIED | `CANDIDATE_VERIFIED` |
| `an_unverified_extra_does_not_block` | HOST_CERTIFIED | HOST_CERTIFIED | `CANDIDATE_VERIFIED` |
| `product_agrees_only_on_the_task_case` | REFUSED | REFUSED | `CANDIDATE_REFUSED` |
| `signature_without_a_body` | REFUSED | REFUSED | `NO_VERIFIED_CANDIDATE` |
| `colour_outside_the_task_colours` | REFUSED | REFUSED | `CANDIDATE_REFUSED` |
| `verified_operation_with_a_wrong_answer` | REFUSED | REFUSED | `ANSWER_REJECTED` |
| `body_outside_the_closed_list` | REFUSED | REFUSED | `BAD_REQUEST` |
| `reply_that_marks_itself_verified` | REFUSED | REFUSED | `BAD_REQUEST` |
| `reply_without_candidates` | REFUSED | REFUSED | `BAD_REQUEST` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 7 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `rust_candidate_body_run_against_host_judge` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF56 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
