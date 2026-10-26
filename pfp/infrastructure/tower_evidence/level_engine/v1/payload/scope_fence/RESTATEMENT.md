# Restatement: `scope_fence`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A claim about a hosted finite table of steps names one value and reads it as
a pole of the table's walk count: the determinant of `I - uA` is zero at the
named value `u`, where `A` is the 0/1 table of arcs. The claim's reading and
its scope are derived from the evidence, which is a finite table: the only
supported reading is the pole reading, and the only supported scope is the
table itself. Nothing the claim declares about its reading or scope is taken
as given.

## Refused case

The same value relabelled with a reading that reaches past the table (a zero
of an object the table does not present) is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| node, arc | supplied object-language datum | the evidence: a finite table of steps |
| claim, val, names | supplied object-language datum | a claim and the exact value it names |
| kind, of_kind | supplied object-language datum | the claim's reading; the first element is the pole reading |
| reach, in_scope | supplied object-language datum | the claim's scope; the first element is the table itself |
| arcs_typed, named, one_value, kind_given, one_kind, scope_given, one_scope | derived definition | relational requirements over the claim |
| kind_derived, scope_derived | derived definition | the two fence requirements, fixed by the evidence type |
| vanishes | derived definition | the determinant clause, decided over exact values |
| determinant over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The determinant is decided outside the grammar
(hosted, not native); the kernel re-decides it for every fixture whose
relational clauses hold.
