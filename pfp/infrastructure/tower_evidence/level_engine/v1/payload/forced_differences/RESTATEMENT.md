# Restatement: `forced_differences`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A Boolean model over uniform independent source bits gives each variable as
a truth table of its parents, and its parent graph must be acyclic. For a
treatment and an outcome, the claimed observed difference (the outcome's
rate when the treatment is one, less its rate when zero, conditioning) and
the claimed forced difference (the same after replacing the treatment's
equation by a constant, and re-evaluating) must both be the exact counts
over every source assignment.

## Refused case

An observed correlation labelled as a forced effect: the claimed forced
difference repeats the observed one while the true forced difference
differs.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| source, variable, pattern, parent, fires | supplied object-language datum | the model |
| treatment, outcome, observed, forced | supplied object-language datum | the report |
| treatment_given, one_treatment, outcome_given, one_outcome, fires_typed | derived definition | relational requirements over the claim |
| well_formed, acyclic, observed_exact, not_relabelled, forced_exact | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive has one source bit driving Z, and X and
Y each copy Z: observed difference 1, forced difference 0. The kernel
re-decides acyclicity and both differences by enumerating every source
assignment.
