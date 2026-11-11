# WF36: Guarded staged slot materialisation

**Layer:** 5 · **Builds on:** [WF8](Workflow-WF8.md) · **Merges into:** WF8 · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer5.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer5.py) (`GuardedStagedSlotMaterialisation`) · **Folder:** [`workflows/wf36_guarded_staged_slot_materialisation`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf36_guarded_staged_slot_materialisation) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Stage 1 fills typed cochain slots; a complete guard with one retry gates stage 2.

Edge values on a graph are partly fixed, partly slots. The syndrome
``r = S c`` over the full cycle matrix is the single object used for the
verdict, the retry prompt and the audit. Stage 2 must give a potential with
``delta phi = c``. Abstention is accepted only when the rank test shows no
filling exists; a guard over a strict subset of cycles is refused with a
false-green kernel witness.

## Procedure

1. Stage 1 emits typed slots
2. A complete guard with one retry gates stage 2 or abstains
3. Two-stage tree-then-chord for higher cycle rank
4. A dichotomic guard removes the lazy false-refusal attractor

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- syndrome r* = S c shared across verdict, repair and audit; a partial guard leaves a false-green kernel

## Host check

`exact_cochain_check`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF36
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF36-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `materialised_first_try` | HOST_CERTIFIED | HOST_CERTIFIED | `MATERIALISED` |
| `repaired_from_shared_syndrome` | HOST_CERTIFIED | HOST_CERTIFIED | `MATERIALISED_AFTER_RETRY` |
| `abstain_on_closed_nonexact_cycle` | TYPED_REFUSAL | TYPED_REFUSAL | `ABSTAIN_NOT_MATERIALISABLE` |
| `partial_guard_false_green` | REFUSED | REFUSED | `PARTIAL_GUARD` |
| `lazy_false_abstention` | REFUSED | REFUSED | `FALSE_ABSTENTION` |
| `guard_red_after_retry` | REFUSED | REFUSED | `GUARD_RED_AFTER_RETRY` |
| `stage2_drifts_from_slots` | REFUSED | REFUSED | `STAGE2_POTENTIAL_EXPLAINS_SLOTS` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `exact_cochain_check` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF36 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
