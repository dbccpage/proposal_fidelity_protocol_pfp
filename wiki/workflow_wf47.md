# WF47: Resumable bounded frontier search

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 3 · **Builds on:** [WF9](workflow_wf9.md) · **Merges into:** nothing · **Kind:** procedure extension

**Check (Rust):** [`code/rust/pfp_operads/src/families/wf47.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/src/families/wf47.rs) · **Registry entry and fixtures:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`ResumableFrontierSearch`) · **Folder:** [`workflows/wf47_resumable_bounded_frontier_search`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf47_resumable_bounded_frontier_search) · **Tests:** [`code/rust/pfp_operads/tests/wf47.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/tests/wf47.rs), [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> A bounded sign-gauge search in deterministic batches, resumable under one ledger.

Domain: a signed graph; a gauge is ``s_v in {+1, -1}`` with ``sigma_uv = s_u s_v``.
Candidates are enumerated lexicographically in fixed batches; each batch is
a sealed checkpoint carrying the presentation key and the cumulative spend.
A resume must replay the contiguous chain from index 0 under the same key,
and the ledger must continue. Budget resets, changed problems and partial
replays are refused; exhausting a frustrated graph is a typed obstruction.

## Procedure

1. Deterministic lexicographic batches
2. Statuses: verified, unknown with suffix, restricted obstruction
3. Continuing requires replaying the contiguous chain from index 0

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- the presentation key includes basis and representation, so a resumed search cannot silently change problem

## Host check

`sign_gauge_checkpoint_chain`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict. The Rust host runs it: `pfp_operad family` reads the task, writes the prompt, refuses a prompt that carries a sealed value and returns the verdict. Python asks the model and carries the reply back.

## Run it offline

No model call and no spend. From the repository root (the first line builds the host once):

```powershell
cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml
python -m pfp_core.workflow_families run WF47
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF47-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `resumed_search_verifies_gauge` | HOST_CERTIFIED | HOST_CERTIFIED | `GAUGE_VERIFIED` |
| `frustrated_graph_exhausted` | TYPED_REFUSAL | TYPED_REFUSAL | `RESTRICTED_OBSTRUCTION` |
| `budget_reset_on_resume` | REFUSED | REFUSED | `BUDGET_RESET` |
| `changed_problem_on_resume` | REFUSED | REFUSED | `PRESENTATION_KEY_CHANGED` |
| `resume_skips_replay` | REFUSED | REFUSED | `RESUME_NOT_REPLAYED_FROM_ZERO` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `sign_gauge_checkpoint_chain` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF47 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
