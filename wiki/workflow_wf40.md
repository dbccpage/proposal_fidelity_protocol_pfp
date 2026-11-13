# WF40: Restart boundary after exhausted repair

**Layer:** 9 · **Builds on:** [WF9](workflow_wf9.md), [WF20](workflow_wf20.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer9.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer9.py) (`RestartBoundaryAfterExhaustedRepair`) · **Folder:** [`workflows/wf40_restart_boundary_after_exhausted_repair`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf40_restart_boundary_after_exhausted_repair) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> After repair ends with a positive residual, take exactly the boundary action the cochain admits.

Domain: a 2-complex (graph plus faces) carrying measured edge values ``c``;
repair proposes potentials ``phi`` in the WF20 loop. On exhaustion the host
classifies ``c``: unclosed (a face sum is nonzero) admits a typed refusal
with that face; closed non-exact admits a lift ``c = delta phi + k h`` with a
closed ``h`` as preservation witness; exact admits a restart seeded only with
the immutable spec and verified refusal receipts. A changed claim set is refused.

## Procedure

1. When bounded repair ends with a positive residual, choose exactly one of: typed refusal, lift request, restart seed carrying the residual
2. A lift needs a preservation witness
3. A changed claim set is a new problem, not a repair

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- cochain trichotomy: exact / unclosed / closed non-exact; lift authorised only with Delta > 0

## Host check

`cochain_trichotomy_boundary`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF40
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF40-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `exact_restart_repairs` | HOST_CERTIFIED | HOST_CERTIFIED | `RESTART_REPAIRED` |
| `unclosed_typed_refusal` | TYPED_REFUSAL | TYPED_REFUSAL | `UNCLOSED_COCHAIN` |
| `closed_non_exact_lift` | HOST_CERTIFIED | HOST_CERTIFIED | `LIFT_AUTHORISED` |
| `restart_with_changed_claims` | REFUSED | REFUSED | `NEW_PROBLEM_NOT_REPAIR` |
| `restart_seed_carries_history` | REFUSED | REFUSED | `SEED_ONLY_SPEC_AND_RECEIPTS` |
| `lift_without_closed_witness` | REFUSED | REFUSED | `ACTION_MATCHES_TRICHOTOMY` |
| `false_refusal_on_exact` | REFUSED | REFUSED | `ACTION_MATCHES_TRICHOTOMY` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `cochain_trichotomy_boundary` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF40 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
