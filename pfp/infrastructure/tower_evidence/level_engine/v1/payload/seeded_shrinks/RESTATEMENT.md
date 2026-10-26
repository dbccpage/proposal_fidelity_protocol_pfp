# Restatement: `seeded_shrinks`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A reported failure of a pinned property (the sum is below `k`, or `k` does
not occur) on generated input must be replayable from its seed: the pinned
generator, a 32-bit linear congruential sequence started at the seed, must
regenerate the failing input, and the property must fail on it. The shrink
trace must take single steps (remove one entry, or lower one by one), each
still failing, and from its last list no single step may still fail.

## Refused case

A reported failure with no seed: it is quarantined, not accepted.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| bound, seed, property and their values | supplied object-language datum | the generator's bounds, the seed, the property |
| list, entry, of | supplied object-language datum | the failing input and the shrink trace |
| entries_placed, one_list | derived definition | relational requirements over the claim |
| well_formed, seeded, replayed, is_failure, shrink_steps, shrunk | derived definition | clauses decided outside the grammar |
| the pinned generator and properties | metatheory apparatus | declared here |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the failure and its
trace are hosted lists, replayed here. By ruling D4 the level's checker is
apparatus, so this record counts in A, never in C.
