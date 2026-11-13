# WF49: Query-preservation stage and mode campaign

**Layer:** 8 · **Builds on:** [WF8](workflow_wf8.md), [WF22](workflow_wf22.md) · **Merges into:** nothing · **Kind:** experiment design

**Code:** [`pfp_core/workflow_families/layer8.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer8.py) (`QueryPreservationCampaign`) · **Folder:** [`workflows/wf49_query_preservation_stage_and_mode_campaign`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf49_query_preservation_stage_and_mode_campaign) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Run staged, sealed packets through mode lanes; a stage passes only if the query is unchanged.

Domain: an exact linear query ``A x = b`` re-encoded per lane (json,
augmented rows, columns). Each stage packet must quote the previous seal
chain head; the host decodes it with the lane's own decoder and requires
exact equality with the original query, not an equivalent one. A lane stops
at its first safety regression (an unlisted field such as an answer).

## Procedure

1. Run declared stages and mode contracts over task families
2. Independent oracle per family
3. Stop a lane on any safety regression

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- a stage passes only if the decoded query is unchanged

## Host check

`decoded_query_equality_seal_chain`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF49
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF49-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `all_lanes_preserve_query` | HOST_CERTIFIED | HOST_CERTIFIED | `QUERY_PRESERVED` |
| `row_scaled_equivalent_not_equal` | REFUSED | REFUSED | `QUERY_CHANGED` |
| `relay_injects_answer_lane_stopped` | REFUSED | REFUSED | `SAFETY_REGRESSION` |
| `forged_previous_seal` | REFUSED | REFUSED | `SEAL_CHAIN_BROKEN` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `decoded_query_equality_seal_chain` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF49 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
