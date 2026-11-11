# WF11: Dual-certificate synthesis

**Layer:** 3 · **Builds on:** [WF3](Workflow-WF3.md), [WF9](Workflow-WF9.md) · **Merges into:** WF1 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`DualCertificateSynthesis`) · **Folder:** [`workflows/wf11_dual_certificate_synthesis`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf11_dual_certificate_synthesis) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Certify an LP optimum with an exact dual, or infeasibility with a Farkas vector.

Domain: ``max c.x`` subject to ``A x <= b, x >= 0`` over Q. An optimum needs
primal and dual feasibility and ``c.x = b.y``; complementary slackness is
checked as an independent second checker. Infeasibility needs ``y >= 0``,
``A^T y >= 0`` and ``b.y < 0``. A feasible pair with a positive gap is a
weak-duality bound, not a certificate, and is refused.

## Procedure

1. Publish the participant packet; keep the judge packet sealed
2. Team writes a solver that emits certificates, not just answers
3. Commit H(salt || solver) before hidden cases are revealed
4. Judge checks each certificate with exact dot products

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- LP optimality: x >= 0, A x <= b, y >= 0, A^T y >= c, c.x = b.y (weak duality closes the gap)
- infeasibility (Farkas): y >= 0, A^T y >= 0, b.y < 0
- max-flow value = min-cut capacity; assignment potentials u_i + v_j <= c_ij with equality on the matching
- Bareiss fraction-free elimination keeps every intermediate an exact integer

## Host check

`lp_dual_and_farkas_certificate`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF11
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF11-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `optimum_with_exact_dual` | HOST_CERTIFIED | HOST_CERTIFIED | `OPTIMAL` |
| `farkas_infeasibility` | TYPED_REFUSAL | TYPED_REFUSAL | `PRIMAL_INFEASIBLE` |
| `weak_duality_bound_only` | REFUSED | REFUSED | `WEAK_DUALITY_ONLY_BOUND` |
| `dual_infeasible_y` | REFUSED | REFUSED | `DUAL_FEASIBLE` |
| `wrong_farkas_vector` | REFUSED | REFUSED | `FARKAS_ATY_NONNEGATIVE` |
| `prose_infeasibility_claim` | REFUSED | REFUSED | `MALFORMED_CANDIDATE` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `lp_dual_and_farkas_certificate` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF11 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
