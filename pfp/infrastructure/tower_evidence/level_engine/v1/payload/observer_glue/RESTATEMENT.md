# Restatement: `observer_glue`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/g014_observer_descent` is re-run
from the pinned clone, read only; it is not sealed, and it is admitted for a
replay by the author's ruling of 2026-09-25. Nothing here is attributed to
the seed.

## Obligation

A finite set of loci is covered by declared observers, each reading a subset.
Each observer holds a record, a value at each locus it reads. Check that the
observers cover every locus, that each record is defined on exactly its
observer's loci, that any two records agree at every shared locus, and that
the declared glue, one value per locus, is the gluing of the records.

Every clause is decided by the tree's own code: its projection of a state
onto an observer's loci, its compatibility check on shared loci, its
coverage check, and its gluing of compatible records.

## Refused case

Records that agree inside each observer but disagree at a shared locus: the
tree's own perturbation, one more at the first locus the first two observers
share. The tree's gluing refuses it with an explicit mismatch.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the tree's observers, projection, compatibility check and gluing | supplied object-language datum | re-run from the pinned clone (`research/g014_observer_descent`, research-tree evidence) |
| three observers over four loci, and the state 100, 200, 300, 400 | supplied object-language datum | the tree's own compatible-cover fixture |
| covered, on_patch, overlaps_agree, glue_replayed | derived definition | clauses decided by the tree's code on each packet |

## Notes

The tree's Lean proves gluing on one fixed cover of three loci; this replay
cites none of it and rests on the tree's Python alone. The record books the
custody: the witness is research-tree evidence, not sealed.
