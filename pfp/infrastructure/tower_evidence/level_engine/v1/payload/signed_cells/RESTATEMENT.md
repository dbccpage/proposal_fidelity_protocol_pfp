# Restatement: `signed_cells`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite two-dimensional table of cells declares vertices, edges (each from
a tail to a head) and faces (each a signed sum of edges). Every reference
must name a declared cell of the right kind: an edge's ends are declared
vertices, and a face's terms are declared edges. The boundary maps are
derived from the cells, never supplied: the boundary of an edge is its
head minus its tail, and for every face the boundary of its boundary is
zero at every vertex, with integer coefficients.

## Refused case

A dangling edge: an edge whose end is no declared vertex.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| cell, vertex, edge, face, plus, minus | supplied object-language datum | the cell table |
| ends_declared, plus_declared, minus_declared, one_edge, kinds_apart, plus_typed, minus_typed | derived definition | relational requirements over the claim |
| boundary_closed | derived definition | a clause decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A dangling reference is refused natively, by a
closure over the declared cells; only the integer boundary sum is decided
outside the grammar, and the kernel re-decides it.
