# Restatement: `witnessed_triples`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

One natural-number variable ranges over a finite interval. A triple states a
precondition interval, a step that adds a constant, and a postcondition
interval. A proved triple carries a witness: exactly the domain values in its
precondition, each landing in the postcondition after the step. A refuted
triple carries one counterexample: a domain value in the precondition whose
step leaves the postcondition. A triple that is neither asserts nothing. Each
witness is replayed by enumeration.

## Refused case

A triple that stands as proved with no witness is not proved: however
satisfiable it looks, it stays unproved until a witness is given.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| num, claim, domain | supplied object-language datum | the values, the triples and the interval of the variable |
| pre, post, adds | supplied object-language datum | each triple's intervals and step |
| proved, refuted, certified, case | supplied object-language datum | each triple's standing and witness |
| domain_given, one_domain, pre_given, one_pre, post_given, one_post, adds_given, one_adds, one_standing, witnessed, refuted_has_case | derived definition | relational requirements over the claim |
| cases_complete, cases_hold, refutation_exact | derived definition | value clauses, decided over exact values |
| enumeration of a finite interval | metatheory apparatus | the harness's replay, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The witness is part of the claim and is replayed; no
outside decision procedure is consulted.
