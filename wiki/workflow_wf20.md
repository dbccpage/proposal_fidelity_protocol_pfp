# WF20: Derivation loop with lift grants

**Layer:** 8 · **Builds on:** [WF9](workflow_wf9.md), [WF10](workflow_wf10.md), [WF19](workflow_wf19.md) · **Merges into:** WF9 · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer8.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer8.py) (`DerivationLoopWithLiftGrants`) · **Folder:** [`workflows/wf20_derivation_loop_with_lift_grants`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf20_derivation_loop_with_lift_grants) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> The WF9 repair loop, with structural lift grants when the defect stalls.

Domain: XOR edge labels, as in WF9. When the host defect (odd fundamental
cycles) does not strictly fall, the host issues a LIFT_REQUEST grant of
fundamental cycles or chords. The grant must be a function of the graph
alone, never of the labels or the repair. The loop halts on a certificate,
on budget or on the limit of 5; a request for non-structural data is refused.

## Procedure

1. Proposal against named obligations
2. Lift grant: the host licenses which higher structure may be used
3. Witness check on the exact finite control
4. Negative control
5. Learning refinement for the next loop; stop at the loop limit

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- loop state (P_t, G_t, W_t); P_{t+1} = refine(P_t, residual_t) with t <= 5
- metric/cochain bridge: additive curvature and metric Regge holonomy are checked separately
- terminal policy: halt on certificate, on budget, or on the loop limit, whichever comes first

## Host check

`structural_lift_grant_loop`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF20
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF20-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `stall_then_lift_then_derived` | HOST_CERTIFIED | HOST_CERTIFIED | `DERIVED` |
| `first_try_without_lift` | HOST_CERTIFIED | HOST_CERTIFIED | `DERIVED` |
| `lift_request_for_target_values` | REFUSED | REFUSED | `LIFT_SCOPE_VIOLATION` |
| `loop_limit_of_five_exhausted` | REFUSED | REFUSED | `HALTED_ON_LIMIT` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `structural_lift_grant_loop` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF20 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
