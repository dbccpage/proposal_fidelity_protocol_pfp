# Restatement: `reindexed_fibres`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite base of objects and arrows carries a fibre of terms over each
object, the fibres disjoint. Each arrow has a reindexing table, taken
contravariantly: a map from the fibre over its target to the fibre over its
source. Every object has an identity whose table is the identity; every
declared composite `h = g after f` has, as its table, `f`'s after `g`'s;
and every composable pair of non-identity arrows has a declared composite.

## Refused case

A term reindexed into the wrong fibre.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| object, term, arrow, over, runs | supplied object-language datum | the base and its fibres |
| sends | supplied object-language datum | the reindexing tables |
| identity, composite | supplied object-language datum | declared identities and composites |
| over_given, one_over, runs_given, one_runs, table_total, table_within, one_image, right_fibre, identity_given, identity_endo, identity_fixes, chain_middle, chain_ends, functorial, over_typed, sends_typed | derived definition | relational requirements over the claim |
| base_closed | derived definition | a clause decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Every law but closure of the base is carried by
derivability: functoriality is a closure over the three tables, and
identity is a closure over the fibre. Closure of the base needs "not an
identity", which the grammar cannot state, so it is decided outside it and
re-decided by the kernel. Associativity of the base is not decided.
