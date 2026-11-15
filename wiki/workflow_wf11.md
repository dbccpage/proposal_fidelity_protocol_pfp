# WF11: Dual-certificate synthesis

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet. The pilots/ folder holds data from earlier model experiments run with an older harness; they are records, not runs of this runner.

**Layer:** 3 · **Builds on:** [WF3](workflow_wf3.md), [WF9](workflow_wf9.md) · **Merges into:** WF1 · **Kind:** task preset

**Check (Rust):** [`code/rust/pfp_operads/src/families/wf11.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/src/families/wf11.rs) · **Registry entry and fixtures:** [`pfp_core/workflow_families/layer3.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer3.py) (`DualCertificateSynthesis`) · **Folder:** [`workflows/wf11_dual_certificate_synthesis`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf11_dual_certificate_synthesis) · **Tests:** [`code/rust/pfp_operads/tests/wf11.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/pfp_operads/tests/wf11.rs), [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Certify an LP optimum with an exact dual, or infeasibility with a Farkas vector.

Domain: ``max c.x`` subject to ``A x <= b, x >= 0`` over Q. An optimum needs
primal and dual feasibility and ``c.x = b.y``; complementary slackness is
recorded as a second check of the same fact. Infeasibility needs ``y >= 0``,
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

`lp_dual_and_farkas_certificate`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict. The Rust host runs it: `pfp_operad family` reads the task, writes the prompt, refuses a prompt that carries a sealed value and returns the verdict. Python asks the model and carries the reply back.

## Run it offline

No model call and no spend. From the repository root (the first line builds the host once):

```powershell
cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml
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

Back to [all workflow families](workflow_families.md).
