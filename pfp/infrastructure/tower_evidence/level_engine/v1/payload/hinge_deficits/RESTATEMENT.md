# Restatement: `hinge_deficits`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A closed surface of triangular patches carries exact squared edge lengths.
Every patch must be non-degenerate, and every angle must be read exactly
from a cosine table on squares, with no square root taken. At every corner
hinge the claimed deficit must be one turn less the angles of the patches
that contain the corner, and the claimed total must be their sum. The claim
is over the finite family of hinges: every one is checked.

## Refused case

A deficit term assembled from a patch that does not contain its hinge.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| corner, patch, edge, total | supplied object-language datum | the surface, its edges and its claims |
| spans, ends, uses | supplied object-language datum | patch corners, edge ends, each term's patches |
| squared lengths, claimed deficits, claimed total | supplied object-language datum | exact values on elements |
| spans_given, one_span, ends_given, one_ends, uses_given, uses_typed | derived definition | relational requirements over the claim |
| well_formed, nondegenerate, angles_exact, incidence, deficits, total | derived definition | clauses decided outside the grammar |
| the cosine table on squares | metatheory apparatus | a declared reading, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive is the tetrahedron's boundary with unit
squared lengths: fifteen elements, hosted since the carrier cap was lifted
in round P6. The kernel re-decides every clause but `well_formed`, over
the whole family of hinges.
