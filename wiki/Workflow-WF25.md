# WF25: Hierarchical decimation

**Layer:** 3 · **Builds on:** [WF24](Workflow-WF24.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`HierarchicalDecimation`) · **Folder:** [`workflows/wf25_hierarchical_decimation`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf25_hierarchical_decimation) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

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

`cycle_residual_preserving_decimation`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF25
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF25-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `tail_and_chains_decimated` | HOST_CERTIFIED | HOST_CERTIFIED | `DECIMATED` |
| `changed_cycle_residual` | REFUSED | REFUSED | `LABELS_ARE_PATH_SUMS` |
| `loop_dropped_as_tree` | REFUSED | REFUSED | `CYCLE_RANK_PRESERVED` |
| `path_is_not_a_walk` | REFUSED | REFUSED | `MALFORMED_CANDIDATE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `cycle_residual_preserving_decimation` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF25 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
