# WF47: Resumable bounded frontier search

**Layer:** 3 · **Builds on:** [WF9](Workflow-WF9.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer3.py) (`ResumableFrontierSearch`) · **Folder:** [`workflows/wf47_resumable_bounded_frontier_search`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf47_resumable_bounded_frontier_search) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> A bounded sign-gauge search in deterministic batches, resumable under one ledger.

Domain: a signed graph; a gauge is ``s_v in {+1, -1}`` with ``sigma_uv = s_u s_v``.
Candidates are enumerated lexicographically in fixed batches; each batch is
a sealed checkpoint carrying the presentation key and the cumulative spend.
A resume must replay the contiguous chain from index 0 under the same key,
and the ledger must continue. Budget resets, changed problems and partial
replays are refused; exhausting a frustrated graph is a typed obstruction.

## Procedure

1. Deterministic lexicographic batches
2. Statuses: verified, unknown with suffix, restricted obstruction
3. Continuing requires replaying the contiguous chain from index 0

## Mathematics

- the presentation key includes basis and representation, so a resumed search cannot silently change problem

## Host check

`sign_gauge_checkpoint_chain`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF47
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF47-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `resumed_search_verifies_gauge` | HOST_CERTIFIED | HOST_CERTIFIED | `GAUGE_VERIFIED` |
| `frustrated_graph_exhausted` | TYPED_REFUSAL | TYPED_REFUSAL | `RESTRICTED_OBSTRUCTION` |
| `budget_reset_on_resume` | REFUSED | REFUSED | `BUDGET_RESET` |
| `changed_problem_on_resume` | REFUSED | REFUSED | `PRESENTATION_KEY_CHANGED` |
| `resume_skips_replay` | REFUSED | REFUSED | `RESUME_NOT_REPLAYED_FROM_ZERO` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `sign_gauge_checkpoint_chain` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF47 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
