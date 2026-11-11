# WF18: Dossier replay campaign

**Layer:** 6 · **Builds on:** [WF6](Workflow-WF6.md), [WF12](Workflow-WF12.md) · **Merges into:** nothing · **Kind:** harness gate

**Code:** [`pfp_core/workflow_families/layer6.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer6.py) (`DossierReplayCampaign`) · **Folder:** [`workflows/wf18_dossier_replay_campaign`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf18_dossier_replay_campaign) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Replay a frozen campaign dossier with zero model calls; every grade must reproduce.

Each cell stores its input, the raw reply bytes and their SHA-256 values; the
dossier pins the grader source. The host checks each digest and the pin,
regrades every stored reply with the weighted-cycle duality grader, and
refuses any drifted byte, drifted pin or grade that does not reproduce.

## Procedure

1. Fix five carriers and five representations (including emoji and glyph carrier encodings with an explicit legend)
2. Run the 5 x 5 baseline
3. Run five matched guidance trials
4. Replay from stored bytes and extract learning

## Mathematics

- frustrated spin triangle: no s in {+1,-1}^3 satisfies s_i s_j = -1 on all three edges (odd cycle)
- weighted cycle duality: a feasible potential exists iff no negative cycle exists
- design: 25 baseline cells + 5 matched cells, compared per carrier

## Host check

`dossier_replay_reproduces_grades`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF18
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF18-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `replay_reproduces_every_grade` | HOST_CERTIFIED | HOST_CERTIFIED | `REPLAY_REPRODUCED` |
| `reply_byte_drifted` | REFUSED | REFUSED | `STORED_BYTES_DRIFTED` |
| `grade_not_reproduced` | REFUSED | REFUSED | `EVERY_GRADE_REPRODUCES` |
| `grader_pin_drifted` | REFUSED | REFUSED | `SOURCE_PIN_DRIFT` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `dossier_replay_reproduces_grades` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF18 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
