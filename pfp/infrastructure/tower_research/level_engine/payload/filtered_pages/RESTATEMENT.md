# Restatement: `filtered_pages`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite complex of cells over the two-element field, each cell with a
degree that no facet exceeds, carries a sequence of pages. Page `r` lists
cells and claims steps from cells to cells. Every claimed step lowers the
degree by exactly `r` and the dimension by one, and a step followed by a
step is zero. The claimed steps are the pairs of degree gap `r` that the
column reduction of the facet table finds, and page `r` lists exactly the
cells in no pair of smaller gap.

## Refused case

A cell removed by a step on an earlier page, listed again on a later page
with nothing to carry it back.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| cell, face, page, listed, step | supplied object-language datum | the cells and their facets, the pages, what each lists and claims |
| a cell's degree, a page's number | supplied object-language datum | exact values on elements |
| some_page, faces_typed, listed_typed, steps_typed | derived definition | relational requirements over the claim |
| well_formed, degrees_kept, steps_graded, square_zero, steps_recomputed, no_return, pages_recomputed | derived definition | clauses decided outside the grammar |
| column reduction over the two-element field | metatheory apparatus | the harness's recomputation, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive is the triangle with degree twice the
dimension: seven cells and three pages, ten elements. The order of cells for
the reduction is degree, then dimension, then declared position.
