# Restatement: `killed_mutants`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A base list of naturals is audited with mutants. Each mutant names a pinned
operator, the entry it acts at, a value (read by `set` only) and the
invariant it is meant to break; the claim also records, for each mutant,
the invariants that kill it. The engine applies every operator itself and
evaluates every declared invariant on every changed list. The base must
hold every declared invariant; every operator must change the base; every
mutant must be killed by some declared invariant (every declared mutant
counts as dangerous); a killed mutant must be killed by its intended
invariant; and the recorded kills must be the recomputed ones.

## Refused case

A surviving mutant: a changed list that no declared invariant kills is
flagged, even when the claim records its survival honestly.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| entry and its value | supplied object-language datum | the base list, in declared order |
| invariant, operator, with their texts | supplied object-language datum | the declared invariants and the operators the mutants name |
| mutant and its value; at, applies, intends, kills | supplied object-language datum | the mutants and the recorded kills |
| the invariants `nondecreasing`, `distinct`, `nonempty` | metatheory apparatus | supplied vocabulary, pinned and restated here exactly |
| the operators `set`, `delete`, `duplicate`, `swap` | metatheory apparatus | supplied vocabulary, pinned and restated here exactly |
| position_given, one_position, positions_are_entries, operator_given, one_operator, intent_given, one_intent, intents_declared, kills_declared | derived definition | relational requirements over the claim |
| well_formed, base_holds, mutants_change, mutants_killed, intended_kills, matrix_exact | derived definition | clauses decided outside the grammar, over the applied operators |

## Notes

`intended_kills` is read over the killed mutants: a survivor is refused by
`mutants_killed`, which is decided first in the pinned order, so the two
clauses never double-count one defect.

On a base of distinct entries in order, `delete` never kills (a sublist of
such a list keeps both invariants) unless the base has one entry, where
`nonempty` kills it; the extra fixture `single` shows that case.

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the base, the mutants
and the recorded kills are hosted, and every changed list is computed and
judged here. By ruling D4 the level's checker is apparatus, so this record
counts in A, never in C.
