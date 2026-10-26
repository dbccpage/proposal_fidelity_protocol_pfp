# Restatement: `glued_patches`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite set of points is covered by patches, and each patch carries a
section: a value at each of its points. Every point lies in a patch, each
section is defined exactly on its patch, sections agree wherever patches
overlap, and the claimed glue is one global assignment that restricts to
every section.

## Refused case

Sections that each agree with themselves but conflict on an overlap.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| point, patch, value, member | supplied object-language datum | the cover |
| assigns | supplied object-language datum | the sections |
| glue | supplied object-language datum | the claimed glue |
| covered, defined_on_patch, within_patch, glue_total, glue_restricts, one_assign, one_glue, member_typed, assigns_typed, glue_typed | derived definition | relational requirements over the claim |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Nothing is decided over values: every clause is
carried by derivability, and an overlap conflict is refused natively,
because with one glue value per point two disagreeing sections cannot both
restrict the glue. The reading is the function reading; the transport
reading is not decided.
