# WF24: Pinned-token operational scratchpad

**Layer:** 2 · **Builds on:** [WF2](Workflow-WF2.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer2.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer2.py) (`PinnedTokenScratchpad`) · **Folder:** [`workflows/wf24_pinned_token_operational_scratchpad`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf24_pinned_token_operational_scratchpad) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Loop holonomy with pinned edge tokens, an exact scratchpad and two agreeing checkers.

Domain: an S_n gauge field on edges; token ``eK+`` is U(eK) and ``eK-`` its inverse.
The reply echoes the pinned loop tokens, lists every partial product
g_k = g_(k-1) * U(token_k), and gives the holonomy and whether it is the identity.
The host folds the loop twice, by permutation composition and by permutation-matrix
products, and the two must agree. A reoriented token, a copied or skipped step, or a
wrong flatness claim is refused.

## Procedure

1. Pin canonical coordinate tokens in the reply grammar
2. Require an operational scratchpad of the exact computation (e.g. path products)
3. Check the final answer with dual independent checkers

## Mathematics

- holonomy along a loop: g_acc <- g_acc * U(e) for each edge e, compared with the identity

## Host check

`dual_holonomy_checkers`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF24
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF24-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `nontrivial_holonomy` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFIED` |
| `flat_loop` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFIED` |
| `reoriented_token_claims_flat` | REFUSED | REFUSED | `TOKENS_PINNED` |
| `copied_final_skips_a_step` | REFUSED | REFUSED | `SCRATCHPAD_STEPS_EXACT` |
| `flat_claim_on_nontrivial_loop` | REFUSED | REFUSED | `FLATNESS_MATCHES` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 3 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `dual_holonomy_checkers` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF24 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
