# Restatement: `mutant_challenges`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A challenger audits a pinned check (non-decreasing, distinct, or a sum at
most a bound; never the producer's own code) with negative fixtures. The
base fixture must pass the check; every challenge's mutant must differ from
the base; running the check on each mutant must refuse it; and each
recorded result must be the recomputed one.

## Refused case

A negative fixture that still passes: it is flagged.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| list, entry, of | supplied object-language datum | the base and the mutants, lists of naturals |
| subject and bound, with their values | supplied object-language datum | the pinned check chosen, and its bound |
| recorded_pass, recorded_fail | supplied object-language datum | the challenger's recorded results |
| entries_placed, one_list | derived definition | relational requirements over the claim |
| well_formed, base_passes, mutants_differ, mutants_refused, results_exact | derived definition | clauses decided outside the grammar |
| the three pinned checks | metatheory apparatus | declared here, never supplied by the producer |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the fixtures and their
mutants are hosted claims, and the check runs on them here. By ruling D4
the level's checker is apparatus, so this record counts in A, never in C.
