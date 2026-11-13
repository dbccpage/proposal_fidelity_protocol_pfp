# WF14: Immune failure classification

**Layer:** 6 · **Builds on:** [WF7](workflow_wf7.md), [WF12](workflow_wf12.md) · **Merges into:** nothing · **Kind:** meta workflow

**Code:** [`pfp_core/workflow_families/layer6.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer6.py) (`ImmuneFailureClassification`) · **Folder:** [`workflows/wf14_immune_failure_classification`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf14_immune_failure_classification) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Classify refused runs into epitopes and admit detector rules only on two signals.

Domain: replies giving the monic polynomial with stated rational roots. The
host verifies the seal on its self panel of clean replies, kills any rule
that fires on that panel, and admits a surviving rule only when each failure
it matches carries an allowlisted host danger signal of the rule's epitope.
It refuses autoimmune rules, pattern-only matches and mislabelled epitopes.

## Procedure

1. Seal a self panel of known-good outputs
2. Propose candidate detectors (antibodies) from observed failures
3. Reject any detector that fires on the self panel
4. Admit a detector only with two signals: a failure match and a host check

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- negative selection: keep d iff for all s in Self, match(d, s) < theta
- two-signal gate: admit iff signal_1 (pattern) and signal_2 (host evidence)
- self-tolerance = 1 - false positives on Self / |Self|

## Host check

`thymus_two_signal_admission`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF14
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF14-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `two_signal_rules_admitted` | HOST_CERTIFIED | HOST_CERTIFIED | `RULES_ADMITTED` |
| `autoimmune_rule_killed` | REFUSED | REFUSED | `NO_AUTOIMMUNE_RULE` |
| `pattern_only_on_clean_failure` | REFUSED | REFUSED | `EVERY_RULE_TWO_SIGNAL_ADMITTED` |
| `mislabelled_epitope` | REFUSED | REFUSED | `EVERY_RULE_TWO_SIGNAL_ADMITTED` |
| `forged_self_panel_seal` | REFUSED | REFUSED | `SELF_PANEL_SEAL_BROKEN` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `thymus_two_signal_admission` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF14 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
