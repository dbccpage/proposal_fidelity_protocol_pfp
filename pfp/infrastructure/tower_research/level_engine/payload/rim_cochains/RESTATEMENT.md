# Restatement: `rim_cochains`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite two-dimensional complex has oriented edges and triangular faces.
Its incidence tables are derived from the cells, never accepted: the edge
table puts minus one at an edge's first vertex and one at its second, and the
face table puts one or minus one where a face's boundary runs along or
against an edge. Claimed tables must be those derived tables, and must
compose to zero. The rim is exactly the edges with one incident face,
together with their end vertices, so a cochain vanishing on the rim stays
vanishing under the incidence maps. The cells off the rim are claimed too.

## Refused case

An invalid rim: the diagonal of a square split in two declared part of the
rim, though two faces meet on it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| vertex, edge, face, ends, face_of | supplied object-language datum | the cells |
| d0_plus, d0_minus, d1_plus, d1_minus | supplied object-language datum | the claimed tables' nonzero entries |
| rim_edge, rim_vertex, inner_vertex, inner_edge, inner_face | supplied object-language datum | the claimed rim and the cells off it |
| ends_given, one_ends, face_given, one_face | derived definition | relational requirements over the claim |
| complex_ok, nilpotent, incidence_exact, rim_exact, relative_exact | derived definition | clauses decided outside the grammar |
| integer incidence arithmetic | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Supplied tables that compose to zero are not enough:
they must be the tables of the declared cells.
