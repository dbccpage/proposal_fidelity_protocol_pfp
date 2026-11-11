# WF13: Exact-domain capsule battery

**Layer:** 2 · **Builds on:** [WF1](Workflow-WF1.md), [WF7](Workflow-WF7.md) · **Merges into:** WF1 · **Kind:** task preset

**Code:** [`pfp_core/workflow_families/layer2.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer2.py) (`ExactDomainCapsuleBattery`) · **Folder:** [`workflows/wf13_exact_domain_capsule_battery`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf13_exact_domain_capsule_battery) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Run a battery of exact-domain capsules, each judged by its own registered checker.

Domains: stabilizer commutation (symplectic product mod 2), U(1) anomaly sums
(sum q and sum q^3), commutators in S_n, and a WF7 linear capsule that must be
answered or refused by the rank test. Every domain needs a checker before any
capsule is dispatched. Results are per domain over the full declared denominator:
a missing or malformed reply counts as a failure, and no cross-domain average is formed.

## Procedure

1. One catalog challenge becomes one capsule
2. A domain checker is registered before dispatch
3. One reply or typed refusal per capsule
4. Results stay per domain; no cross-domain average is claimed

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- stabilizer codes: generators commute iff their symplectic product is 0 mod 2
- U(1) anomaly freedom: sum_i q_i = 0 and sum_i q_i^3 = 0 over the declared charges
- Regge deficit: epsilon = 2 pi - sum of dihedral angles at a hinge
- commutator [g, h] = g^-1 h^-1 g h, checked in the declared finite group

## Host check

`per_domain_registered_checker`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF13
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF13-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `every_capsule_passes` | HOST_CERTIFIED | HOST_CERTIFIED | `BATTERY_PASSED` |
| `dropped_capsule_keeps_denominator` | REFUSED | REFUSED | `CAPSULE:REFUSE` |
| `bluff_on_refusal_capsule` | REFUSED | REFUSED | `CAPSULE:REFUSE` |
| `missed_anticommuting_pair` | REFUSED | REFUSED | `CAPSULE:STAB3` |
| `unregistered_domain_not_dispatched` | REFUSED | REFUSED | `UNREGISTERED_DOMAIN` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `per_domain_registered_checker` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF13 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
