# WF12: Mechanism-control arms

**Layer:** 5 · **Builds on:** [WF6](workflow_wf6.md), [WF3](workflow_wf3.md) · **Merges into:** Sweep · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer5.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer5.py) (`MechanismControlArms`) · **Folder:** [`workflows/wf12_mechanism_control_arms`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf12_mechanism_control_arms) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Run a mechanism arm against matched null and random controls on the same items.

Items are integer sums graded by one host checker. The paired effect is
``d_i = 1[check(B, i)] - 1[check(A, i)]``; the proposer's arm ranks are a
potential on the arm-comparison graph, accepted iff its coboundary equals
every paired total, which is invariant under ``r -> r + c``. Controls must be
matched first: a zero null vector and a random vector with the mechanism's
exact squared norm.

## Procedure

1. Hold the carrier fixed; vary only the mechanism note
2. Run baseline, typed-witness and mechanism arms on the same items
3. Grade with one registered checker
4. Compare arms item by item

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- rank difference: r_i - r_j recovered from a gauge-fixed assignment; gauge freedom r -> r + c leaves differences unchanged
- paired effect: d_i = 1[check(arm_B, i)] - 1[check(arm_A, i)]

## Host check

`integer_rank_difference_certificate`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF12
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF12-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `gauge_shifted_ranks_certified` | HOST_CERTIFIED | HOST_CERTIFIED | `ARMS_COMPARED` |
| `inflated_mechanism_effect` | REFUSED | REFUSED | `RANK_DIFFERENCES_MATCH_PAIRED_TOTALS` |
| `random_control_norm_differs` | REFUSED | REFUSED | `CONTROLS_UNMATCHED` |
| `arm_on_different_items` | REFUSED | REFUSED | `MALFORMED_CANDIDATE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `integer_rank_difference_certificate` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF12 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
