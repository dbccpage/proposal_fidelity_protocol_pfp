# Restatement: `resolution_claims`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Claims about propositional clause sets are accepted only with an object
replayed here, independent of whatever produced the claim. An
unsatisfiable answer needs a resolution refutation: every step resolves two
available clauses on a pivot that occurs positively in the first and
negatively in the second, its clause is the resolvent, and the last derived
clause is empty. A satisfiable answer needs a consistent model that
satisfies every clause.

## Refused case

A solver's success flag with no proof object.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| variable, claim, clause, pos_in, neg_in, of_claim | supplied object-language datum | the clause sets and the steps' clauses |
| resolves | supplied object-language datum | the steps |
| unsat, sat, true_in, false_in | supplied object-language datum | the answers and the models |
| clauses_owned, one_owner, pivot_positive, pivot_negative, model_consistent, one_resolution | derived definition | relational requirements over the claim |
| answered, steps_available, resolvents_exact, refutes, model_satisfies | derived definition | clauses decided outside the grammar, over the replay |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the proof object is a
hosted structure, replayed step by step here; resolvents are recomputed,
never read. By ruling D4 the level's checker is apparatus, so this record
counts in A, never in C.
