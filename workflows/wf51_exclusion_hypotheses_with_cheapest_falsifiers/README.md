# WF51: Exclusion hypotheses with cheapest falsifiers

**Status:** offline runner with fixtures; no model run yet. **Kind:** meta workflow. **Builds on:** [WF14](../wf14_immune_failure_classification/README.md), [WF31](../wf31_multi_agent_tournament_with_held_out_cross_validation/README.md).

**Goal:** Treat every "don't search here" as a hypothesis. Spend tests where model families disagree, and still test cheap dead branches.

## Why

Models share training data, so their mistakes are correlated. Three seats of one
family agreeing that a branch is dead is one opinion, not three, and a confident
wrong exclusion can hide the real answer.

## How it works

1. Seats from several model families propose exclusions. Each names a falsifier
   (the cheapest test that would show it wrong) and its cost.
2. The host counts agreement by family (`pfp_core/exclusions.py`):
   - **frontier**: families disagree, or one family splits;
   - **uncorroborated**: only one family supports it;
   - **probably dead**: at least `min_families` families agree.
3. Falsifiers run frontier first, then uncorroborated, then probably-dead ones no
   dearer than `dead_floor`, all under `retest_budget`.
4. A refuted exclusion reopens its branch. The solver sees only open branches.
5. Control arm: the same task with `retest: false`.

## The check

Exact polynomial evaluation of every falsifier point and of the answer. A
"no root" claim is checked by scanning every open branch.

## Run it offline

```powershell
python -m pfp_core.workflow_families run WF51
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF51-"
python -m pytest pfp_core/tests/test_exclusions.py -q
```

The fixture `control_without_retest_hides_the_answer` is the point of the
workflow: with retests off, the run ends in a lawful typed refusal ("no root in
the open branches") while the real root sits in a wrongly excluded branch.

## Predicted effect for a model campaign

On held-out tasks with a planted wrong exclusion, the retest arm recovers the
answer more often than the control arm at a small extra cost (the falsifier
points), and seats of one family agree on wrong exclusions more often than
seats of different families. Neither is measured yet.

More: [wiki page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_wf51) · [machine-readable entry](../../dag/reviews/workflows_audit.json)
