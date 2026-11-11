# WF15: Adversary tribunal

**Layer:** 7 · **Builds on:** [WF4](Workflow-WF4.md), [WF14](Workflow-WF14.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer7.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer7.py) (`AdversaryTribunal`) · **Folder:** [`workflows/wf15_adversary_tribunal`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf15_adversary_tribunal) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Prosecutor and defender commit before either reveals; only the model check rules.

Domain: a finite Kripke model and a claim ``M, w |= box psi``. Both sides
commit salted digests, then open them. The host checks each opening, checks
the defence by evaluating psi at every successor, and counts the prosecution
only when its witness is a successor at which psi fails. It refuses an opening
that does not match its commitment and a true but unwitnessed prosecution.

## Procedure

1. Prosecutor and defender submit independently; submissions are frozen
2. Neither sees the other before freezing
3. The host checks each claim on the finite model
4. Verdict comes only from the check; rhetoric is not evidence

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- Kripke model M = (W, R, V); M, w |= box phi iff phi holds at every R-successor of w
- argument acceptance: grounded extension of the attack graph, computed by the host
- finite predicate example: sum(left) <= sum(right) on 1..16 bounded integers

## Host check

`kripke_box_witness_check`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF15
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF15-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `prosecution_witnessed` | HOST_CERTIFIED | HOST_CERTIFIED | `PROSECUTION_UPHELD` |
| `defence_upheld_over_bogus_witness` | HOST_CERTIFIED | HOST_CERTIFIED | `DEFENCE_UPHELD` |
| `opening_changed_after_commit` | REFUSED | REFUSED | `COMMITMENT_MISMATCH` |
| `true_prosecution_without_failing_case` | REFUSED | REFUSED | `UNCONFIRMED_PROSECUTION` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 2 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `kripke_box_witness_check` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF15 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
