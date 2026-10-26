# Restatement: `same_background`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite model of two-valued variables has one background variable; every
other variable has one earlier parent and a table from the parent's value
to its own. Given an observation, the backgrounds consistent with it are
found by trying every background value. Each is then run again with one
variable forced to a value, keeping the same background: the factual run
and the counterfactual run are twins. The claimed answer is the set of
values the asked variable takes in the counterfactual runs; when more than
one background is consistent, the answer is a set, never a pick.

## Refused case

A counterfactual that draws the background again instead of keeping the
factual one.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| variable, bit, parent, table | supplied object-language datum | the model |
| observed, forced, asked | supplied object-language datum | the observation, the forcing and the question |
| twin, factual, counter, answer | supplied object-language datum | the twins and the claimed answer |
| tables_given and the nine other relational clauses | derived definition | relational requirements over the claim |
| same_background, abduction_exact, answer_exact | derived definition | clauses decided outside the grammar |
| running a finite model | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The declared class is one background variable and
one parent per variable.
