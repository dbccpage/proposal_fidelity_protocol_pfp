# WF37: Evidence-bound harness evolution

**Layer:** 8 · **Builds on:** [WF19](workflow_wf19.md), [WF22](workflow_wf22.md) · **Merges into:** nothing · **Kind:** meta workflow

**Code:** [`pfp_core/workflow_families/layer8.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer8.py) (`EvidenceBoundHarnessEvolution`) · **Folder:** [`workflows/wf37_evidence_bound_harness_evolution`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf37_evidence_bound_harness_evolution) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Replace the incumbent harness only on untainted, Pareto-front, privately confirmed evidence.

Genomes live in a ``civilization.Lineage``; contamination taints every
descendant. ``civilization.select`` places public results in the 60/30/10
reserves with four-axis Pareto dominance. The challenger must then win an
exact sign test against the incumbent on the sealed private split and again
on a fresh panel. A tainted, dominated or unconfirmed replacement is refused.

## Procedure

1. An outer model rewrites a small harness (prompt, workflow, search and context policy)
2. UCB1 plus softmax search over strategies; scoped failure memory
3. Public and private grading split
4. Fresh confirmation before replacing the incumbent
5. Untouched transfer and ablation panels

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- paired bootstrap, exact sign test, Holm correction over transfer and ablation contrasts

## Host check

`taint_pareto_sign_test_confirmation`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF37
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF37-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `confirmed_front_challenger` | HOST_CERTIFIED | HOST_CERTIFIED | `INCUMBENT_REPLACED` |
| `tainted_descendant_proposed` | REFUSED | REFUSED | `CHALLENGER_UNTAINTED` |
| `fresh_confirmation_fails` | REFUSED | REFUSED | `FRESH_SIGN_TEST` |
| `pareto_dominated_challenger` | REFUSED | REFUSED | `CHALLENGER_ON_FRONT` |
| `fresh_panel_reuses_private_item` | REFUSED | REFUSED | `GRADING_SPLITS_DISJOINT` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `taint_pareto_sign_test_confirmation` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF37 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
