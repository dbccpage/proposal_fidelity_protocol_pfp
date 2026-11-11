# WF41: Detector adequacy and two-signal admission

**Layer:** 7 · **Builds on:** [WF14](Workflow-WF14.md) · **Merges into:** WF14 · **Kind:** meta workflow

**Code:** [`pfp_core/workflow_families/layer7.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer7.py) (`DetectorAdequacyTwoSignal`) · **Folder:** [`workflows/wf41_detector_adequacy_and_two_signal_admission`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf41_detector_adequacy_and_two_signal_admission) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Admit a detector only with a complete calibration record and two independent signals.

Domain: the WF14 polynomial replies for fixed roots. The submission must carry
positive, negative, collision and metamorphic cases and one representative per
epitope class, so detector and host classifier agree on a class-representative
set. The host also requires zero hits on the sealed self panel and an
allowlisted Signal 2 observer distinct from the matcher; a pattern alone stays
diagnostic. It refuses missing classes, self hits and inconsistent rewrites.

## Procedure

1. Admit a detector only with positive, negative, collision and metamorphic cases plus one representative per class
2. Two signals: pattern match and structural defect; pattern alone is diagnostic only
3. Bind a human decision to the receipt digest
4. Report effective diversity of the self panel

## Mathematics

- finite calibration completeness: D = A iff D = A on a class-representative set R (sharp)

## Host check

`detector_calibration_completeness`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF41
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF41-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `calibrated_detector_admitted` | HOST_CERTIFIED | HOST_CERTIFIED | `DETECTOR_ADMITTED` |
| `missing_class_representative` | REFUSED | REFUSED | `ONE_REPRESENTATIVE_PER_CLASS` |
| `fires_on_sealed_self_panel` | REFUSED | REFUSED | `ZERO_SELF_PANEL_HITS` |
| `whitespace_rewrite_changes_firing` | REFUSED | REFUSED | `METAMORPHIC_CONSISTENT` |
| `pattern_alone_reported_as_danger` | REFUSED | REFUSED | `TWO_INDEPENDENT_SIGNALS` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `detector_calibration_completeness` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF41 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
