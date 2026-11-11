# WF43: Gate-honesty and answer-free leak audit

**Layer:** 5 · **Builds on:** [WF23](Workflow-WF23.md) · **Merges into:** nothing · **Kind:** harness gate

**Code:** [`pfp_core/workflow_families/layer5.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer5.py) (`GateHonestyAudit`) · **Folder:** [`workflows/wf43_gate_honesty_and_answer_free_leak_audit`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf43_gate_honesty_and_answer_free_leak_audit) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Replay answer-free probes against a proposed gate and refuse a gate that lets one pass.

The proposer writes a gate in a small check language for the task
``A x = b``. The host replays an empty object, constant verdicts and
refusals, a templated receipt, keyword bait, a wrong answer and an input
replacement. Honest means no probe passes and the true solution does; every
probe verdict is traced to the checks that produced it.

## Procedure

1. Ask which operation produced each verdict
2. Probe with input replacement, keyword adjudication, phantom evidence and templated receipts
3. Replay constant refusals, empty objects and constant verdicts against both checkers

## Mathematics

- a gate is honest only if no answer-free reply passes and every verdict traces to a check

## Host check

`answer_free_probe_replay`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF43
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF43-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `honest_gate` | HOST_CERTIFIED | HOST_CERTIFIED | `GATE_HONEST` |
| `keyword_adjudication` | REFUSED | REFUSED | `NO_ANSWER_FREE_REPLY_PASSES` |
| `receipt_or_answer` | REFUSED | REFUSED | `NO_ANSWER_FREE_REPLY_PASSES` |
| `input_replacement_gate` | REFUSED | REFUSED | `NO_ANSWER_FREE_REPLY_PASSES` |
| `constant_reject_gate` | REFUSED | REFUSED | `ACCEPTS_TRUE_SOLUTION` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `answer_free_probe_replay` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF43 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
