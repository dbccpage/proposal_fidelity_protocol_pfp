# WF9: Bounded check-and-repair

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 2 · **Builds on:** [WF2](workflow_wf2.md) · **Merges into:** nothing · **Kind:** procedure extension

**Check (Rust):** [`code/rust/pfp_operads/src/families/wf09.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/src/families/wf09.rs) · **Registry entry and fixtures:** [`pfp_core/workflow_families/layer2.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer2.py) (`BoundedCheckAndRepair`) · **Folder:** [`workflows/wf09_bounded_check_and_repair`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf09_bounded_check_and_repair) · **Tests:** [`code/rust/pfp_operads/tests/wf09.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/tests/wf09.rs), [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Check, return only the typed residual, allow at most L repairs.

Domain: XOR labels ``c`` on the edges of a graph. A consistent 0/1 vertex
labelling exists iff every cycle sum of ``c`` is 0 mod 2. The candidate
returns a set of edges to flip; the host accepts iff ``c + Delta`` is a
coboundary mod 2 and ``|Delta|`` is minimal. On rejection the next prompt
carries only the indices of the fundamental cycles that are still odd.

## Procedure

1. Check the reply
2. On rejection return only the typed residual (never the expected answer)
3. Allow at most L repair attempts
4. Stop at the first accepted reply or at the limit

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- XOR cycle: a consistent assignment exists iff the cycle sum of edge labels is 0 mod 2
- minimal repair: argmin |Delta| subject to c + Delta in im(delta_0) for the edge cochain c
- termination: attempts <= L, and each attempt is charged

## Host check

`xor_cycle_minimal_repair`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict. The Rust host runs it: `pfp_operad family` reads the task, writes the prompt, refuses a prompt that carries a sealed value and returns the verdict. Python asks the model and carries the reply back.

## Run it offline

No model call and no spend. From the repository root (the first line builds the host once):

```powershell
cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml
python -m pfp_core.workflow_families run WF9
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF9-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `repaired_on_second_try` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `non_minimal_never_accepted` | REFUSED | REFUSED | `REPAIR_LIMIT_EXHAUSTED` |
| `limit_exhausted` | REFUSED | REFUSED | `REPAIR_LIMIT_EXHAUSTED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `xor_cycle_minimal_repair` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF9 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
