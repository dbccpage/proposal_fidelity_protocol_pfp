# WF38: Diagnostic-trace proposal selection

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 3 · **Builds on:** [WF9](workflow_wf9.md) · **Merges into:** WF9 · **Kind:** procedure extension

**Check (Rust):** [`code/rust/pfp_operads/src/families/wf38.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/src/families/wf38.rs) · **Registry entry and fixtures:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`DiagnosticTraceSelection`) · **Folder:** [`workflows/wf38_diagnostic_trace_proposal_selection`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf38_diagnostic_trace_proposal_selection) · **Tests:** [`code/rust/pfp_operads/tests/wf38.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/tests/wf38.rs), [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Rank candidate repairs by the host's own defect recomputation, never the model's score.

Domain: a rational edge cochain with defect ``Phi = sum |cycle sums|``. Each
candidate is a sparse edge correction. The host recomputes ``Phi`` after
each one, keeps only strict decreases, and ranks by ``(Phi, |delta|_1, name)``.
A self-reported score is never read. If no candidate strictly lowers ``Phi``
the selection is refused.

## Procedure

1. The model proposes candidates; it never reports its own score
2. The host recomputes Phi, Gamma and other channels
3. Filter by strict lexicographic decrease and a ratio ceiling
4. Rank with fixed weights; ties by name; every observer must pass in the multi-observer form

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- primal-dual witness: B^T phi = 0, ||phi||_inf <= 1, phi . c = ||h||_1; Gamma <= ||D|| Phi

## Host check

`host_recomputed_defect_ranking`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict. The Rust host runs it: `pfp_operad family` reads the task, writes the prompt, refuses a prompt that carries a sealed value and returns the verdict. Python asks the model and carries the reply back.

## Run it offline

No model call and no spend. From the repository root (the first line builds the host once):

```powershell
cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml
python -m pfp_core.workflow_families run WF38
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF38-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `host_ranks_by_defect` | HOST_CERTIFIED | HOST_CERTIFIED | `SELECTED` |
| `confident_but_worse` | REFUSED | REFUSED | `NO_STRICT_DECREASE` |
| `gauge_move_is_not_a_decrease` | REFUSED | REFUSED | `NO_STRICT_DECREASE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `host_recomputed_defect_ranking` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF38 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
