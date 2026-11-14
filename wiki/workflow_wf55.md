# WF55: Failure ledger with trial-gated rules

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 7 · **Builds on:** [WF1](workflow_wf1.md), [WF14](workflow_wf14.md) · **Merges into:** nothing · **Kind:** meta workflow

**Code:** [`pfp_core/workflow_families/learning.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/learning.py) (`FailureLedgerTrialGatedRules`) · **Folder:** [`workflows/wf55_failure_ledger_with_trial_gated_rules`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf55_failure_ledger_with_trial_gated_rules) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Keep failures in a ledger and load a rule in later runs only after it wins a held-out trial.

Domain: integer sums, the task of WF1. The task carries the ledger so far,
answers the host rejected in earlier runs, and held-out cases. The run:

1. The host replays the ledger's chain and lists the rules already admitted.
2. The host judges each reported failure itself and writes its record; an
   answer the judge accepts cannot be recorded as a failure.
3. Stage ``propose`` returns one rule: an id, a capability kind, a constraint
   in words and the failures it comes from.
4. Each held-out case is answered twice: stage ``baseline`` with the admitted
   rules, stage ``treated`` with the proposed rule added.
5. The host judges both answers of every case and writes the trial record.
6. The ledger admits the rule only on that trial, when it gained correct
   answers and broke no case the baseline had right.

The outcome carries the new ledger. Give it to the next run as ``ledger``
and that run's prompts carry the admitted rule. A rejected rule stays in
the ledger and can be tried again.

## Procedure

1. The host replays the ledger's hash chain and lists the rules already admitted
2. The host judges each reported failure itself and writes its record; a correct answer cannot be recorded as a failure
3. A model proposes one rule from the recorded failures
4. Each held-out case is answered twice: without the proposed rule and with it
5. The host judges both answers of every case and writes the trial record
6. The ledger admits the rule only on that trial; the next run loads every admitted rule

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- admit iff treated_correct > baseline_correct and clean_panel_hits = 0, on the rule's latest trial
- clean_panel_hits = number of held-out cases the baseline answered correctly and the treated run did not
- held out: the trial's case ids share nothing with the failures the rule was derived from
- entry hash = SHA-256(domain line, seq, previous hash, record), so an edited, reordered or cut ledger does not replay

## Host check

`rust_ledger_admission_on_host_judged_trial`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF55
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF55-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `rule_admitted_on_a_winning_trial` | HOST_CERTIFIED | HOST_CERTIFIED | `RULE_ADMITTED` |
| `later_run_loads_the_admitted_rule` | HOST_CERTIFIED | HOST_CERTIFIED | `RULE_ADMITTED` |
| `no_gain_is_not_earned` | REFUSED | REFUSED | `NOT_EARNED` |
| `a_rule_that_breaks_a_clean_case` | REFUSED | REFUSED | `NOT_EARNED` |
| `a_correct_answer_is_not_a_failure` | REFUSED | REFUSED | `NOT_A_FAILURE` |
| `trial_on_the_failures_the_rule_came_from` | REFUSED | REFUSED | `SPLIT_OVERLAP` |
| `rule_from_an_unrecorded_failure` | REFUSED | REFUSED | `UNKNOWN_FAILURE` |
| `rule_that_names_its_own_admission` | REFUSED | REFUSED | `BAD_REQUEST` |
| `edited_ledger_is_refused` | REFUSED | REFUSED | `CHAIN_BROKEN` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 7 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `rust_ledger_admission_on_host_judged_trial` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF55 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
