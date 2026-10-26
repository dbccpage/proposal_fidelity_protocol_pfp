# Restatement: `renamed_formulas`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two prenex formulas over unary and binary symbols are given, the second a
typed translation of the first: every symbol of the first language is
renamed to a symbol of the second language with the same number of places,
and the second formula is read back through the renaming. Each formula must
use only its own language's symbols, with their numbers of places, and only
variables its own prefix binds, each once. The declared fragment is every
interpretation of the first language on the domains {0, ..., n - 1} for
1 <= n <= k, where k is the hosted bound (at most 3, and at most 12 cells at
the top size). Both formulas are evaluated here on every structure of the
fragment, and they must agree on all of it. A second prefix that reorders
the first one's quantifiers is accepted only when that agreement holds: the
reordering is then proved within the fragment, and nowhere else.

## Refused case

A translation that swaps the order of two quantifiers and disagrees with the
first formula on some structure of the fragment.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| formula, translates | supplied object-language datum | the first formula and its translation |
| symbol, its text, unary, binary, declared | supplied object-language datum | the two languages |
| renamed | supplied object-language datum | the renaming of symbols |
| variable and its text; quantifier, opens, every, some, binds | supplied object-language datum | the prefixes, in declared order |
| node, matrix, within, reads, first, second, equal, negates, both, either | supplied object-language datum | the quantifier-free parts |
| bound and its value | supplied object-language datum | the largest domain of the fragment |
| every, some, both, either, negates, equal (as read here) | admitted primitive | the usual truth conditions on a finite domain; supplied vocabulary of the procedure, classified here |
| map_total, map_typed, one_image, keeps_unary, keeps_binary, one_arity | derived definition | relational requirements on the renaming |
| reads_declared, two_places, one_place, first_given, first_bound, second_bound, one_first, one_second, one_read | derived definition | relational requirements typing the formulas |
| nodes_placed, one_formula, tops_placed, negation_placed, both_placed, either_placed, quantifiers_placed, one_opening, binds_given, one_bound, one_kind | derived definition | relational requirements placing nodes and quantifiers |
| well_formed, bound_once, swap_proved, meaning_kept | derived definition | clauses decided outside the grammar, over the evaluation of both formulas on the whole fragment |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: both formulas and the
renaming are hosted, and the engine evaluates both on every structure of the
declared fragment itself (530 structures at bound 3 for the positive); a
reordering is decided by that exhaustion and by nothing else. The own
negative (bound 2) disagrees on two of its 18 structures. The extras show
the other side: a reordering of like quantifiers, and a swap of unlike ones
whose quantifier-free part separates the variables, are both proved within
the fragment, and the own negative's swap is proved within the fragment of
one-element domains only. By ruling D4 the level's checker is apparatus, so
this record counts in A, never in C.
