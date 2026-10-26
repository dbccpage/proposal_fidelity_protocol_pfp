# Restatement: `shared_labels`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/natural_sections` is re-run from
the pinned clone, read only; it is not sealed, and it is admitted for a
replay by the author's ruling of 2026-09-25. Nothing here is attributed to
the seed.

## Obligation

Contexts are declared sets of items that may overlap. Each context carries a
rule, `differ` (its labels are pairwise distinct) or `equal` (its labels are
all the same), and a family gives one local choice per context, one label
per item, from a declared set of labels. Check that every context gets
exactly one choice of the right length, that every choice keeps its rule,
and that any two contexts sharing an item give it the same label, over every
pair of contexts, not only neighbours in list order. The replay also asks
the tree's own decider whether any agreeing family exists on the declared
contexts.

## Positive

The tree's re-presented four-site chain: six configurations of two occupied
sites, and six arrows between them, one of which exchanges the two labels.
The tree's decider finds that it carries a section; each context's choice is
that section read on its two items, carried out from the least configuration
along a breadth-first tree.

## Refused case

The tree's four-site square: six configurations and eight arrows, two of
which exchange the labels, around cycles of odd exchange count. The tree's
decider finds that it carries no section. The declared family keeps every
rule, and two contexts give one item two labels.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the tree's configurations, arrows and exchange bits, and its decider | supplied object-language datum | re-run from the pinned clone (`research/natural_sections`, research-tree evidence) |
| the re-presented chain, the square and the triangle | supplied object-language datum | the tree's own instances |
| a configuration written by its two site numbers; an arrow read as a context of two items | derived definition | `differ` when the arrow exchanges the labels, `equal` when it keeps them |
| the choices read from a breadth-first spread of labels | derived definition | computed by the replay, as the tree's decider builds its labels |
| one_choice_each, rule_kept, overlaps_agree, family_exists | derived definition | clauses decided on each packet |

## Notes

The tree's Lean proves that the chain has a section and the square has none;
this replay cites none of it and rests on the tree's Python alone. The rules
here have two items per context; no certificate that no agreeing family
exists is claimed beyond the tree's decider. The record books the custody:
the witness is research-tree evidence, not sealed.
