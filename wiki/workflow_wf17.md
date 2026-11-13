# WF17: Witnessed-difference programme

**Layer:** 4 · **Builds on:** [WF10](workflow_wf10.md), [WF11](workflow_wf11.md) · **Merges into:** WF10 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer4.py) (`WitnessedDifferenceProgramme`) · **Folder:** [`workflows/wf17_witnessed_difference_programme`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf17_witnessed_difference_programme) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Every claimed difference needs a separating formula; every equivalence needs a bisimulation.

Instance: a finite labelled transition system (a.(b+c) versus a.b+a.c, and a.b versus a.b+a.b).
A difference claim is accepted only if a Hennessy-Milner formula holds on one state and fails on
the other; an equivalence only if the given relation contains the pair and is a bisimulation.
Unwitnessed claims, non-separating formulas and false bisimulations are refused.

## Procedure

1. State two artifacts and the claimed difference or equivalence
2. Require a witness for a difference and a certificate for an equivalence
3. Pair every theorem with countermodels
4. Host checks witnesses on finite instances

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- behavioral equivalence: a bisimulation relation B with (p, q) in B and matching transitions
- Fenchel-Rockafellar: inf_x f(x) + g(Ax) = sup_y -f^*(A^T y) - g^*(-y) under the stated qualification
- Cech gluing obstruction lives in the first Cech cohomology of the cover

## Host check

`hml_separator_bisimulation_check`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF17
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF17-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `difference_and_equivalence_witnessed` | HOST_CERTIFIED | HOST_CERTIFIED | `CLAIMS_WITNESSED` |
| `unwitnessed_difference` | REFUSED | REFUSED | `CLAIM0:WITNESSED` |
| `formula_does_not_separate` | REFUSED | REFUSED | `CLAIM0:SEPARATES` |
| `trace_equivalent_is_not_bisimilar` | REFUSED | REFUSED | `CLAIM0:BISIMULATION` |
| `claims_name_undeclared_states` | REFUSED | REFUSED | `CLAIM0:STATES_DECLARED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `hml_separator_bisimulation_check` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF17 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
