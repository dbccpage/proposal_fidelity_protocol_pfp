# WF46: Boundary sufficiency and gluing diagnostic

**Layer:** 3 · **Builds on:** [WF4](Workflow-WF4.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer3.py) (`BoundarySufficiency`) · **Folder:** [`workflows/wf46_boundary_sufficiency_and_gluing_diagnostic`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf46_boundary_sufficiency_and_gluing_diagnostic) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Test whether boundary packets between patch agents decide global consistency.

Domain: a rational cochain on a graph split into two edge patches. Each run
returns a local potential per patch. The host keeps the locally accepted
runs, glues them by the packet (the declared interface vertices), and runs
the global evaluator on the glued trace. It reports
``NGD = Pr(global fail | all locals pass)``, undefined with no accepted run,
and refuses when a packet passes but the glued trace fails.

## Procedure

1. Check that the handoff object between isolated agents keeps everything the global evaluator needs
2. Report NGD over runs; undefined when no run is locally accepted
3. Report completed share and backlog

## Mathematics

- NGD = Pr(global fail | all locals pass)

## Host check

`glued_trace_global_evaluator`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF46
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF46-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `consistent_cover_packet_sufficient` | HOST_CERTIFIED | HOST_CERTIFIED | `BOUNDARY_SUFFICIENT` |
| `obstruction_seen_by_full_packet` | HOST_CERTIFIED | HOST_CERTIFIED | `BOUNDARY_SUFFICIENT` |
| `lossy_packet_hides_obstruction` | REFUSED | REFUSED | `BOUNDARY_INSUFFICIENT` |
| `no_locally_accepted_run` | REFUSED | REFUSED | `NGD_UNDEFINED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `glued_trace_global_evaluator` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF46 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
