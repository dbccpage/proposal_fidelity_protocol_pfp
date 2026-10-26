# Restatement: `formal_inverses`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite table of objects and arrows carries a full composition table: every
pair of arrows that meet has exactly one composite, of the right type; every
object has an identity that is a unit on both sides; and the two bracketings
of three arrows that meet agree. A declared class of weak arrows holds every
identity and is closed under composition. Each roof inverts one leg formally
and keeps the other: the inverted leg is weak, both legs start at one object,
and the roof runs from the inverted leg's end to the kept leg's end.

## Refused case

A roof that inverts an arrow outside the weak class.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| object, arrow, runs | supplied object-language datum | the objects and the arrows between them |
| identity, compose | supplied object-language datum | declared identities and the composition table |
| weak | supplied object-language datum | the declared class of weak arrows |
| roof | supplied object-language datum | the declared roofs, each a formal inverse and a kept leg |
| runs_given, one_runs, runs_typed, identity_given, one_identity, identity_endo, composable_total, one_composite, chain_middle, chain_ends, compose_typed, left_unit, right_unit, associative | derived definition | relational requirements on the table |
| weak_typed, weak_identities, weak_composes | derived definition | relational requirements on the weak class |
| inverts_weak, roof_left, roof_right | derived definition | relational requirements on the roofs |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Every clause is carried by derivability: the bracketing
law is a closure over three rows of the table, and the refused case is a
closure from a roof to the weak class. Classes of roofs, and whether roofs
compose, are not decided.
