# WF27: Hinted retraction with a stationary-loop detector

**Layer:** 3 · **Builds on:** [WF9](Workflow-WF9.md) · **Merges into:** WF9 · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer3.py) (`HintedRetraction`) · **Folder:** [`workflows/wf27_hinted_retraction_with_a_stationary_loop_detector`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf27_hinted_retraction_with_a_stationary_loop_detector) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> The WF9 repair loop with answer-free structural hints and a stationary-loop stop.

Domain: XOR edge labels, as in WF9. Each rejected turn adds a hint built
only from the host residual and the public graph: the vertex sets of the odd
fundamental cycles, never an edge to flip. If the residual at turn ``t``
equals the residual at ``t - 3`` the loop is stationary and stops with the
typed code ``STATIONARY_LOOP``; exhausting the turn cap is refused.

## Procedure

1. Inject the residual vector and the non-zero cell ids each turn
2. Detect a stationary loop after 3 repeats
3. Force a structural lift or reframe
4. Stop at the turn cap

## Mathematics

- residual r_t = d c_t; stationary if r_t = r_{t-3}; path-integrated retry uses B_T^{-1}, not edge-local B_T

## Host check

`xor_residual_gate_stationary_loop`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF27
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF27-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `repaired_after_hint` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `stationary_loop_stopped` | TYPED_REFUSAL | TYPED_REFUSAL | `STATIONARY_LOOP` |
| `turn_cap_exhausted` | REFUSED | REFUSED | `TURN_CAP_EXHAUSTED` |
| `malformed_repairs_until_cap` | REFUSED | REFUSED | `TURN_CAP_EXHAUSTED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `xor_residual_gate_stationary_loop` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF27 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
