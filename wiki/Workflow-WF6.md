# WF6: Dialect sweep

**Layer:** 4 · **Builds on:** [WF5](Workflow-WF5.md) · **Merges into:** Sweep · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer4.py) (`DialectSweep`) · **Folder:** [`workflows/wf06_dialect_sweep`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf06_dialect_sweep) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Pose each seed item in k query-preserving dialects and grade every reply with one checker.

Items are linear systems ``A x = b``. A dialect permutes and scales rows and renames variables;
the host checks ``decode(rho_k(s)) = q(s)`` (same rank-test status, same decoded solution) before
anything is dispatched, then grades each capsule with the WF7 checker and reports acceptance per
dialect, item by item. A dialect that changes the query or an incomplete sweep is refused.

## Procedure

1. Freeze one seed and its host answer
2. Compile P* and k checked rewrites (dialects) of seed and P*
3. Dispatch each capsule once under the same model and parameters
4. Grade every reply with the same host checker
5. Report acceptance per dialect, item by item

## Mathematics

- dialect family {rho_k}: decode(rho_k(s)) = q(s) for every k (preservation precondition)
- acceptance A_k = (1/N) sum_i 1[check(r_ik)] compared pairwise on the same items
- exact rational structure delta: Net = Delta_created - Delta_removed

## Host check

`dialect_query_preservation_sweep`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF6
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF6-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `all_dialects_accepted` | HOST_CERTIFIED | HOST_CERTIFIED | `SWEEP_GRADED` |
| `one_dialect_fails_item_by_item` | HOST_CERTIFIED | HOST_CERTIFIED | `SWEEP_GRADED` |
| `dialect_zeroes_a_row` | REFUSED | REFUSED | `DIALECT_CHANGES_QUERY` |
| `dialect_shifts_rhs` | REFUSED | REFUSED | `DIALECT_CHANGES_QUERY` |
| `incomplete_sweep` | REFUSED | REFUSED | `INCOMPLETE_SWEEP` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `dialect_query_preservation_sweep` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF6 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
