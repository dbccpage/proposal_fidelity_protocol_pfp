# Exclusion hypotheses

Part of [Epistemic Immune System](EIS.md). Workflow: [WF51](Workflow-WF51.md)

An exclusion ("don't search there", "that branch is dead", an antibody that
blocks a pattern) is a hypothesis, not a fact. Models share training data, so
their mistakes are correlated: several seats of one model family agreeing is one
opinion, and a confident wrong exclusion can hide the real answer.

## The rules

1. **No exclusion without a falsifier.** Every exclusion names the cheapest test
   that would show it wrong, and that test's cost. One without is refused with
   `EXCLUSION_WITHOUT_FALSIFIER`.
2. **Agreement is counted by model family.** Seats of one family collapse to one
   vote.

   | Votes | Status | Meaning |
   | --- | --- | --- |
   | families disagree, or one family splits | `FRONTIER` | Test here first |
   | only one family supports it | `UNCORROBORATED` | Correlated support; test next |
   | at least `min_families` families agree | `PROBABLY_DEAD` | Still tested if cheap |

3. **Cheap dead branches still get tested.** Falsifiers run frontier first, then
   uncorroborated, then probably-dead ones no dearer than `dead_floor`, cheapest
   first, under one budget. Dearer dead ones are skipped as `DEAD_ABOVE_FLOOR`
   and anything that does not fit as `OVER_BUDGET`.
4. **Results are recorded, not assumed.** A falsifier that fires marks the
   exclusion `REFUTED` and reopens its branch; one that does not marks it
   `SURVIVED_TEST`. An untested exclusion keeps a status that describes votes,
   never a fact.

## The cemetery

A candidate killed by a host check stays buried, because the check is
deterministic. A candidate killed by a model seat (a critic, a judge) is an
exclusion hypothesis: `headstone_exclusion` turns its headstone into one, with
the killing seat's family as its only vote, so it is `UNCORROBORATED` and can be
retested. A model seat with no known family is refused rather than guessed.

## Relation to existing rules

- Antibody admission already refuses model consensus as evidence
  ([Antibody lifecycle](EIS-Antibody-Lifecycle.md)) and counts observations that
  share a model only once. Family counting extends that from one model id to a
  model family.
- The [two-signal gate](EIS-Two-Signal-Gate.md) refuses a danger signal derived
  from the match it confirms. Family counting applies the same idea to votes.

## Code

`pfp_core/exclusions.py` (`ExclusionHypothesisV1`, `plan_retests`, `run_plan`,
`headstone_exclusion`), tests in `pfp_core/tests/test_exclusions.py`. No model
campaign has measured the effect yet; [WF51](Workflow-WF51.md) states the
prediction.
