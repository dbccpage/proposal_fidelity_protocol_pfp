# WF10: Local-to-global obstruction certificate

**Layer:** 3 · **Builds on:** [WF4](Workflow-WF4.md), [WF9](Workflow-WF9.md) · **Merges into:** WF4 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`ObstructionCertificate`) · **Folder:** [`workflows/wf10_local_to_global_obstruction_certificate`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf10_local_to_global_obstruction_certificate) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Glue local sections of an edge cochain into a global potential, or certify the obstruction.

Domain: a rational 1-cochain ``c`` on a graph covered by patches that each
carry a local section. A gluing is a vertex potential with ``c - delta phi = 0``
on every edge; an obstruction is a closed signed cycle on which ``c`` sums to
a nonzero value, a nonzero class in ``H^1``. Prose claims, open paths and
zero-sum cycles are refused. Later families call ``certify_gluing`` and
``certify_obstruction`` directly.

## Procedure

1. Declare the cover, cochains and restriction maps
2. Agents certify local sections on each patch
3. Host computes the global obstruction class
4. Accept a gluing witness or an obstruction certificate, never a prose claim

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- H^1 = ker(delta_1) / im(delta_0); a class [c] != 0 means local green, global red
- three-patch observer visibility: each observer sees zero on its edges, yet sum_alpha J^alpha(s) > 0 for the glued section
- Hodge: c = delta alpha + delta^* beta + h with h harmonic (exact rational arithmetic)
- integer lift: an obstruction in H^1(X; Z) can survive the map to rational coefficients only if it is non-torsion

## Host check

`cochain_gluing_or_cycle_obstruction`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF10
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF10-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `consistent_cover_glued` | HOST_CERTIFIED | HOST_CERTIFIED | `GLUED` |
| `twisted_cover_obstructed` | TYPED_REFUSAL | TYPED_REFUSAL | `GLOBAL_OBSTRUCTION` |
| `prose_gluing_claim` | REFUSED | REFUSED | `MALFORMED_CANDIDATE` |
| `bluffed_potential_on_twisted_cover` | REFUSED | REFUSED | `ZERO_RESIDUAL_ON_EVERY_EDGE` |
| `open_path_witness` | REFUSED | REFUSED | `OPEN_CYCLE_WITNESS` |
| `zero_holonomy_witness` | REFUSED | REFUSED | `ZERO_HOLONOMY_WITNESS` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `cochain_gluing_or_cycle_obstruction` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF10 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
