# WF44: Exact certificate presets

**Layer:** 4 · **Builds on:** [WF11](workflow_wf11.md), [WF10](workflow_wf10.md) · **Merges into:** WF11 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer4.py) (`ExactCertificatePresets`) · **Folder:** [`workflows/wf44_exact_certificate_presets`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf44_exact_certificate_presets) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Check a certificate against a registered exact schema; type-check before evaluating.

Presets: a coboundary potential (``delta phi = c``), an l1 primal-dual pair (residual
``r = w + B f``, circulation ``z`` with ``B^T z = 0`` and ``|z_e| <= cap_e``, and
``w . z = sum cap_e |r_e|``), and a solution in canonical rational form. A certificate with a
float, a wrong shape or the wrong schema is refused before any equation is evaluated.

## Procedure

1. The model emits a certificate: l1 potential, residual and dual circulation; a sparse representative; an equal-weight pairing involution; or a typed DSL program
2. The host checks it exactly; ill-typed programs are refused before evaluation

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- r = w + B f, B^T z = 0, |z_e| <= w_e, w . z = ||r||_1 (weak duality)

## Host check

`exact_certificate_presets`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF44
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF44-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `coboundary_potential_valid` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFICATE_VALID` |
| `l1_dual_pair_optimal` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFICATE_VALID` |
| `canonical_rational_solution` | HOST_CERTIFIED | HOST_CERTIFIED | `CERTIFICATE_VALID` |
| `non_canonical_rational` | REFUSED | REFUSED | `CANONICAL_FORM` |
| `dual_not_a_circulation` | REFUSED | REFUSED | `DUAL_IS_CIRCULATION` |
| `ill_typed_short_dual` | REFUSED | REFUSED | `ILL_TYPED` |
| `float_in_certificate` | REFUSED | REFUSED | `FLOAT_IN_CERTIFICATE` |
| `wrong_schema_named` | REFUSED | REFUSED | `ILL_TYPED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 5 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `exact_certificate_presets` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF44 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
