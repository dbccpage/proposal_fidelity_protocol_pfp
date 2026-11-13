# WF34: Future-faithful compression and bounded context

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 8 · **Builds on:** [WF8](workflow_wf8.md), [WF22](workflow_wf22.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer8.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer8.py) (`FutureFaithfulCompression`) · **Folder:** [`workflows/wf34_future_faithful_compression_and_bounded_context`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf34_future_faithful_compression_and_bounded_context) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Compress a repair history to root, champion, two recent attempts and evidence references.

Domain: a WF9-style XOR repair history. The host verdict on a continuation
(REPEAT, UNKNOWN_REFERENCE, IMPROVES, NO_PROGRESS) is computed from the full
history and from the proposed compressed state; the compression is accepted
only if every declared continuation gets the identical verdict. A
compression that drops needed state, or forges the root, is refused.

## Procedure

1. Compress state only if enablement, cost, successors and terminal labels all survive
2. Stage boundaries require equal states, not equal diagnostics
3. Bounded context keeps root, champion, two recent attempts and evidence references
4. Compare with a full-history arm at the same ceiling

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- coarsest stable refinement; states equal under every finite continuation

## Host check

`continuation_verdict_equality`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF34
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF34-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `faithful_compression` | HOST_CERTIFIED | HOST_CERTIFIED | `COMPRESSION_FAITHFUL` |
| `dropped_old_evidence_reference` | REFUSED | REFUSED | `IDENTICAL_VERDICTS_ON_EVERY_CONTINUATION` |
| `kept_one_recent_attempt` | REFUSED | REFUSED | `IDENTICAL_VERDICTS_ON_EVERY_CONTINUATION` |
| `latest_attempt_as_champion` | REFUSED | REFUSED | `IDENTICAL_VERDICTS_ON_EVERY_CONTINUATION` |
| `forged_root` | REFUSED | REFUSED | `ROOT_BOUND_TO_SPEC` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `continuation_verdict_equality` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF34 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
