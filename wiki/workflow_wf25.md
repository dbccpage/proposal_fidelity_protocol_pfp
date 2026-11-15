# WF25: Hierarchical decimation

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 3 · **Builds on:** [WF24](workflow_wf24.md) · **Merges into:** nothing · **Kind:** procedure extension

**Check (Rust):** [`code/rust/pfp_operads/src/families/wf25.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/src/families/wf25.rs) · **Registry entry and fixtures:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`HierarchicalDecimation`) · **Folder:** [`workflows/wf25_hierarchical_decimation`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf25_hierarchical_decimation) · **Tests:** [`code/rust/pfp_operads/tests/wf25.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/tests/wf25.rs), [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Decimate tree and degree-2 parts of a cochain graph without changing any cycle residual.

The candidate returns a reduced multigraph whose edges are signed walks in
the original graph, each labelled with its exact path sum. The host checks
every walk, every label, equal first Betti number, and that the lifted
fundamental cycles have full rank ``b1`` (so ``H_1`` maps isomorphically and
every cycle residual survives). A changed label or a dropped loop is refused.

## Procedure

1. Certify trivially flat sub-blocks at zero tokens
2. Evaluate only the non-contractible loops
3. Check that the remaining holonomies commute
4. Optional second pass aggregates macro-blocks

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- flat blocks contribute the identity; global flatness reduces to the cycle holonomies of the quotient

## Host check

`cycle_residual_preserving_decimation`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict. The Rust host runs it: `pfp_operad family` reads the task, writes the prompt, refuses a prompt that carries a sealed value and returns the verdict. Python asks the model and carries the reply back.

## Run it offline

No model call and no spend. From the repository root (the first line builds the host once):

```powershell
cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml
python -m pfp_core.workflow_families run WF25
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF25-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `tail_and_chains_decimated` | HOST_CERTIFIED | HOST_CERTIFIED | `DECIMATED` |
| `changed_cycle_residual` | REFUSED | REFUSED | `LABELS_ARE_PATH_SUMS` |
| `loop_dropped_as_tree` | REFUSED | REFUSED | `CYCLE_RANK_PRESERVED` |
| `path_is_not_a_walk` | REFUSED | REFUSED | `PATHS_ARE_WALKS` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `cycle_residual_preserving_decimation` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF25 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
