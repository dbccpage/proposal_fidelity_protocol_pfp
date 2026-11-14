# WF56: Host-run operad candidates

**Status:** offline runner with fixtures; no model run yet. **Kind:** procedure extension. **Builds on:** [WF2](../wf02_full_slots/README.md).

**Goal:** Have the reply name the operation it used in a form the host can run, and let the host run it.

## Why

In WF2 to WF5 a reply lists operad candidates: a signature and a sentence about
what the operation means. The host can check the signature. It cannot check the
sentence, so every such candidate stays unverified. WF56 asks for less freedom
and gets a check in return: the candidate picks its body from a closed list,
and the host executes it.

## How it works

1. The task is an integer sum. The prompt lists the colours (`Integer`,
   `IntegerList`) and the bodies (`identity`, `sum`, `product`, `difference`,
   `pack`, `sum_list`) a candidate may use.
2. The model replies with candidates and an answer:

   ```json
   {"candidates": [{"id": "add-the-list", "sources": ["IntegerList"], "target": "Integer", "body": "sum_list"}],
    "answer": {"total": 6}}
   ```

3. The host types every candidate, then runs each one that has a body on the
   task's values and on probe cases the prompt never carried.
4. The host compares each result with the result of its own judge.
5. The host judges the answer.

The run is certified when at least one candidate is verified, none is refused
and the answer is accepted.

## The check

All of it is the Rust host [`pfp_operad`](../../code/rust/pfp_operads/README.md).
The Python asks the model and hands the reply to the host.

| The host says | When |
| --- | --- |
| `HOST_VERIFIED` | The body gave the judge's result on every case. |
| `REFUSED` | The candidate is ill typed, its id repeats, or its body gave another result on a case. |
| `UNVERIFIED_CANDIDATE` | It has no body (`NO_BODY`) or its inputs do not take the cases' values (`DOES_NOT_FIT_CASE`). |

A candidate's inputs take a case in one of two shapes: one `IntegerList`, or
one `Integer` per value. The reply cannot supply an expected value, a verdict
or a body outside the list; the host refuses such a request whole.

## Run it offline

Build the host once (`cargo build --release -p pfp_operads` in `code/rust`), then
from the repository root:

```powershell
python -m pfp_core.workflow_families run WF56
python -m pytest pfp_core/workflow_families/tests -q -k "WF56 or candidates"
```

[`examples/product_by_coincidence.json`](examples/product_by_coincidence.json)
is a request for the host. On the task's values `1, 2, 3` a product and a sum
agree. The probes tell them apart:

```powershell
cd code/rust
cargo run -p pfp_operads -- run ../../workflows/wf56_host_run_operad_candidates/examples/product_by_coincidence.json
```

The host answers `FAIL`: `multiply` is refused on the second case, and
`add-the-list` is verified.

## Limits

- `HOST_VERIFIED` covers the cases given. It is not a proof that the candidate
  is the sum on every input.
- The list of bodies is short and the only task is the integer sum of WF1.
- Candidates run on 64-bit integers. A case with a larger value is refused; the
  judge itself has no such limit.
- A verified candidate shows the reply named a correct operation. It does not
  show that the model used it to reach its answer.

## Predicted effect for a model campaign

A model that names the wrong operation is caught even when its answer is right,
and probes catch an operation that agrees on the task's values by coincidence.
Not measured yet.

More: [wiki page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_wf56) · [machine-readable entry](../../dag/reviews/workflows_audit.json)
