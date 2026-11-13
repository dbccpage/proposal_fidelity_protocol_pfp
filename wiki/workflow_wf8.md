# WF8: Staged sealed packets

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet. The pilots/ folder holds data from earlier model experiments run with an older harness; they are records, not runs of this runner.

**Layer:** 4 · **Builds on:** [WF2](workflow_wf2.md), [WF5](workflow_wf5.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer4.py) (`StagedSealedPackets`) · **Folder:** [`workflows/wf08_staged_sealed_packets`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf08_staged_sealed_packets) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Run a task as declared stages; seal each stage packet before the next stage reads it.

Stage i returns ``{stage, carry, payload, prev, seal}``. The host checks that ``carry`` holds the
fenced question byte for byte (ProtectedContract), that ``prev = h_{i-1}``, that
``seal = H(h_{i-1} || payload)`` (exact.seal_chain over the task seed), and recomputes the stage
from the previous verified payload. Instance: eliminate, solve, residual for ``A x = b``.
Subclasses override ``stages``, ``same_payload`` and ``final_check``.

## Procedure

1. Choose a mode contract and wire encoding
2. Split the task into k declared stages
3. Seal each stage output (hash chain) before the next stage reads it
4. Check every stage receipt and the final answer

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- composition F = f_k o ... o f_1 with typed interfaces between stages
- seal chain h_0 = H(seed), h_i = H(h_{i-1} || payload_i); any edit breaks every later h_j

## Host check

`stage_seal_chain_recompute`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF8
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF8-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `three_sealed_stages` | HOST_CERTIFIED | HOST_CERTIFIED | `SEALED_PIPELINE` |
| `packet_edited_after_seal` | REFUSED | REFUSED | `SEAL_MISMATCH` |
| `chain_link_broken` | REFUSED | REFUSED | `CHAIN_BROKEN` |
| `fence_dropped_from_packet` | REFUSED | REFUSED | `FENCE_VIOLATED` |
| `sealed_but_wrong_stage` | REFUSED | REFUSED | `STAGE_RECOMPUTE_MISMATCH` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `stage_seal_chain_recompute` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF8 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
