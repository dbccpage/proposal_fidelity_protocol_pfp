# WF45: Finite terminal selector and plenitude test

**Layer:** 2 · **Builds on:** [WF7](Workflow-WF7.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer2.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer2.py) (`FiniteTerminalSelector`) · **Folder:** [`workflows/wf45_finite_terminal_selector_and_plenitude_test`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf45_finite_terminal_selector_and_plenitude_test) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Select within a declared finite candidate family, or name why no unique selection exists.

Domain: candidate polynomials with exact coefficients and observations
``|p(x) - y| <= tol``. The survivor set fixes the terminal: one survivor is Accepted,
several Underdetermined, none Refuted, and an empty family or empty evidence Refused.
The host then adds a candidate that agrees with a survivor on every observation and
checks that the survivor count rises, so acceptance stays relative to the family.
Dropping competitors from the family, or claiming a terminal the survivors do not give,
is refused.

## Procedure

1. Check every candidate against evidence with tolerances
2. Return Accepted, Underdetermined, Refuted or Refused for the family
3. Add indistinguishable candidates and check the survivor count rises
4. Deleting competitors is not evidence

## Mathematics

- unique acceptance is only relative to the declared family

## Host check

`finite_survivor_set_verifier`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF45
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF45-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `unique_survivor_accepted` | HOST_CERTIFIED | HOST_CERTIFIED | `ACCEPTED_WITHIN_FAMILY` |
| `two_survivors_underdetermined` | TYPED_REFUSAL | TYPED_REFUSAL | `UNRESOLVED_UNDERDETERMINED` |
| `no_survivor_refuted` | TYPED_REFUSAL | TYPED_REFUSAL | `UNRESOLVED_INCONSISTENT` |
| `bluff_accept_when_underdetermined` | REFUSED | REFUSED | `TERMINAL_MATCHES_SURVIVOR_SET` |
| `competitor_deleted_to_force_accept` | REFUSED | REFUSED | `DECLARED_FAMILY_KEPT` |
| `wrong_survivor_selected` | REFUSED | REFUSED | `SELECTION_IS_THE_SURVIVOR` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `finite_survivor_set_verifier` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF45 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
