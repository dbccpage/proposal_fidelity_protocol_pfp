# WF16: Substrate crosswalk

**Layer:** 4 · **Builds on:** [WF5](workflow_wf5.md), [WF10](workflow_wf10.md) · **Merges into:** WF5 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer4.py) (`SubstrateCrosswalk`) · **Folder:** [`workflows/wf16_substrate_crosswalk`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf16_substrate_crosswalk) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Map one finite task between two substrates and require the same host verdict in both.

Source: an edge cochain ``c`` on an oriented graph (exact iff every fundamental cycle sum is 0).
Target: a signed incidence matrix ``D`` and vector ``y`` (exact iff ``rank D = rank [D|y]``).
A crosswalk maps vertices to columns and edges to signed rows; the host checks it is bijective,
preserves every incidence relation and transports ``c`` to ``y``, and records where valid
crosswalks differ (non-unique choices). A broken relation or a verdict mismatch is refused.

## Procedure

1. Declare source and target substrates (e.g. prose, Lean, finite tables)
2. Translate generators and relations
3. Check that relations are preserved on the target
4. Record every non-unique choice

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- a crosswalk F: C -> D is accepted iff F(r) holds in D for every relation r of C
- non-uniqueness: F and F' both preserve relations yet differ on a generator; both are recorded

## Host check

`incidence_rank_crosswalk`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF16
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF16-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `one_crosswalk_preserves` | HOST_CERTIFIED | HOST_CERTIFIED | `CROSSWALK_PRESERVED` |
| `two_crosswalks_non_unique` | HOST_CERTIFIED | HOST_CERTIFIED | `CROSSWALK_PRESERVED` |
| `orientation_sign_dropped` | REFUSED | REFUSED | `CROSSWALK0:RELATIONS_PRESERVED` |
| `two_vertices_one_column` | REFUSED | REFUSED | `CROSSWALK0:BIJECTIVE` |
| `target_data_not_transported` | REFUSED | REFUSED | `VERDICTS_IDENTICAL` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `incidence_rank_crosswalk` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF16 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
