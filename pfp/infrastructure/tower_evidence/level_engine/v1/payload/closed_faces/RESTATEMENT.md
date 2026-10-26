# Restatement: `closed_faces`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A solid cell on four corners is bounded by four triangular faces. Each face
is a closed walk reached from the base corner by a connector walk, and
carries a value: a permutation of a finite set of labels. When transports
are given on the six edges, each face's value must be the ordered product
along its connector, its walk and its connector reversed. Multiplied in
their declared order, the four face values must give the unit. Products are
ordered throughout: nothing is read through a parity or another unordered
shadow.

## Refused case

Face values whose parities balance while their ordered product is a
three-cycle.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| corner, label, face, slot | supplied object-language datum | the cell, the labels, the faces, the walk positions |
| joins, runs | supplied object-language datum | each face's connector and boundary walk, by slot |
| sends, link | supplied object-language datum | face values and edge transports |
| a face's place, a slot's index | supplied object-language datum | exact values on elements |
| sends_given, one_send, one_join, one_run, one_link, joins_typed, runs_typed, links_typed | derived definition | relational requirements over the claim |
| well_formed, walks_ok, boundary_ok, faces_match, closed | derived definition | clauses decided outside the grammar |
| composition of permutations | metatheory apparatus | the harness's products, and their Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive has fifteen elements (four corners, three
labels, four faces, four slots), hosted only since the carrier cap was
lifted in round P6.
