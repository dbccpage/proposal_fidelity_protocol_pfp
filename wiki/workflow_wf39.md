# WF39: Authority firewall gate

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 5 · **Builds on:** [WF1](workflow_wf1.md), [WF23](workflow_wf23.md) · **Merges into:** nothing · **Kind:** harness gate

**Code:** [`pfp_core/workflow_families/layer5.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer5.py) (`AuthorityFirewallGate`) · **Folder:** [`workflows/wf39_authority_firewall_gate`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf39_authority_firewall_gate) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Accept a reply only when every guard in the vector passes.

The task fixes the public cochain; the reply supplies only the witness
potential and a receipt. The host replays the registered verifier on the
task's own edges and values and checks: payload bound to the task, authority effect 'None' with no
extra fields, verifier registered, witness bound to the exact payload hash,
replay hash, replay match, zero defect and a fresh nonce. A failed guard
becomes residual evidence; self-certifying or escalating receipts are refused.

## Procedure

1. A rejected or obstructed reply can only become residual evidence, never an accept
2. Accept requires every guard: replay hash, replay match, terminaliser, exhaustion, zero defect, descent witness, freshness
3. Packet gates C1-C8 keep tool halt separate from authority
4. Witness must be bound to a registered verifier and the exact payload hash

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- accept iff AllGuardsPass; a non-zero obstruction class cannot satisfy a truthful zero-defect guard

## Host check

`authority_guard_vector`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF39
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF39-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `all_guards_pass` | HOST_CERTIFIED | HOST_CERTIFIED | `ALL_GUARDS_PASS` |
| `self_certifying_receipt` | REFUSED | REFUSED | `AUTHORITY_ESCALATION` |
| `authority_escalation` | REFUSED | REFUSED | `AUTHORITY_ESCALATION` |
| `stale_nonce` | REFUSED | REFUSED | `FRESH_NONCE` |
| `truthful_nonzero_defect` | REFUSED | REFUSED | `ZERO_DEFECT` |
| `trivial_self_chosen_payload` | REFUSED | REFUSED | `PAYLOAD_NOT_BOUND_TO_TASK` |
| `witness_bound_to_other_payload` | REFUSED | REFUSED | `WITNESS_BOUND_TO_PAYLOAD` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 6 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `authority_guard_vector` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF39 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
