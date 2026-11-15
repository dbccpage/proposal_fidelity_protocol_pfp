# WF27: Hinted retraction with a stationary-loop detector

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 3 · **Builds on:** [WF9](workflow_wf9.md) · **Merges into:** WF9 · **Kind:** procedure extension

**Check (Rust):** [`code/rust/pfp_operads/src/families/wf27.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/src/families/wf27.rs) · **Registry entry and fixtures:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`HintedRetraction`) · **Folder:** [`workflows/wf27_hinted_retraction_with_a_stationary_loop_detector`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf27_hinted_retraction_with_a_stationary_loop_detector) · **Tests:** [`code/rust/pfp_operads/tests/wf27.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/tests/wf27.rs), [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> The WF9 repair loop with answer-free structural hints and a stationary-loop stop.

Domain: XOR edge labels, as in WF9. Each rejected turn adds a hint built
only from the host residual and the public graph: the vertex sets of the odd
fundamental cycles, never an edge to flip. If the residual at turn ``t``
equals the residual at ``t - 3`` the proposer is stuck: the run stops and is
refused with code ``STATIONARY_LOOP`` and the last hint. Malformed replies
never count as a stationary signal; exhausting the turn cap is refused.

## Procedure

1. Inject the residual vector and the non-zero cell ids each turn
2. Detect a stationary loop after 3 repeats
3. Force a structural lift or reframe
4. Stop at the turn cap

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- residual r_t = d c_t; stationary if r_t = r_{t-3}; path-integrated retry uses B_T^{-1}, not edge-local B_T

## Host check

`xor_residual_gate_stationary_loop`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict. The Rust host runs it: `pfp_operad family` reads the task, writes the prompt, refuses a prompt that carries a sealed value and returns the verdict. Python asks the model and carries the reply back.

## Run it offline

No model call and no spend. From the repository root (the first line builds the host once):

```powershell
cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml
python -m pfp_core.workflow_families run WF27
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF27-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `repaired_after_hint` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `repaired_after_three_hints` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `stationary_loop_stopped` | REFUSED | REFUSED | `STATIONARY_LOOP` |
| `empty_replies_are_not_a_stationary_signal` | REFUSED | REFUSED | `TURN_CAP_EXHAUSTED` |
| `turn_cap_exhausted` | REFUSED | REFUSED | `TURN_CAP_EXHAUSTED` |
| `malformed_repairs_until_cap` | REFUSED | REFUSED | `TURN_CAP_EXHAUSTED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `xor_residual_gate_stationary_loop` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF27 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
