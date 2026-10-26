# Restatement: `overlap_choices`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite scenario has items, labels, and contexts. Each context names its
items and one local rule: its chosen labels are pairwise distinct, or all
the same. A family gives one choice per context, a label for each of its
items, following its rule. Wherever two contexts share an item, their
choices give it the same label; this is checked over every pair of
contexts, not only neighbours.

## Refused case

Three contexts in a cycle, each with the distinct rule over two labels:
each choice follows its own rule, and two of them give a shared item
different labels.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| item, context, label, member | supplied object-language datum | the scenario |
| differ, equal | supplied object-language datum | each context's local rule |
| chooses | supplied object-language datum | the family of local choices |
| members_given, chosen, one_choice, choice_typed | derived definition | relational requirements over the claim |
| local_rules, overlaps_agree | derived definition | clauses decided outside the grammar (they need distinctness) |
| comparison of finite labels | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. This level decides a claimed family; it does not
certify that no agreeing family exists.
