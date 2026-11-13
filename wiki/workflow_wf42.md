# WF42: Reasoning-trace validation

**Layer:** 5 · **Builds on:** [WF10](workflow_wf10.md), [WF21](workflow_wf21.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer5.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer5.py) (`ReasoningTraceValidation`) · **Folder:** [`workflows/wf42_reasoning_trace_validation`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf42_reasoning_trace_validation) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Extract a claim graph from a trace and certify it, or certify its obstruction.

Each step 'u - v = k' is an edge cochain value. The host computes the
obstruction ``Phi`` and a dual circulation. A consistent trace needs a
potential explaining every step and a conclusion the steps force; an
obstructed trace needs a correction with ``||r||_1 = Phi`` (primal = dual).
Hidden obstructions and conclusions that contradict the steps are refused.

## Procedure

1. A fixed extractor turns the model's text into a claim, citation or tool graph
2. The host computes the obstruction and a dual witness
3. Emit a typed status
4. Run an adversarial battery against the extractor

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- Exact only describes the extractor's image; a three-claim cycle with Phi = 1 and phi = (1,1,1) is the worked obstruction

## Host check

`rational_lp_primal_dual_check`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF42
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF42-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `consistent_trace` | HOST_CERTIFIED | HOST_CERTIFIED | `TRACE_VALID` |
| `three_claim_cycle_obstructed` | TYPED_REFUSAL | TYPED_REFUSAL | `TRACE_OBSTRUCTED` |
| `conclusion_contradicts_steps` | REFUSED | REFUSED | `CONCLUSION_MATCHES_STEPS` |
| `hidden_obstruction` | REFUSED | REFUSED | `HIDDEN_OBSTRUCTION` |
| `non_minimal_correction` | REFUSED | REFUSED | `PRIMAL_EQUALS_DUAL` |
| `unextractable_step` | REFUSED | REFUSED | `MALFORMED_CANDIDATE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `rational_lp_primal_dual_check` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF42 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
