# Restatement: `bounded_mask`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed truncated-search world, its response menu and its
repair check are re-run from the pinned clone, read only; nothing here is
attributed to the seed.

## Obligation

A formula over finite domains is evaluated by enumerating every assignment.
Its quantifier mask is recomputed from its tree. Its step count, the number of
atom evaluations under full enumeration, must fit the declared budget. An
unbounded quantifier is refused before any evaluation: a budget never turns
it into a value.

Here the formula is the sealed obstruction claim for the truncated-search
world: for every position of the sealed response menu, the position is none
of the positions the sealed repair check accepts. The bound is the menu's
length.

## Refused case

The obstruction claim quantified over an unbounded domain, with a finite
step budget, is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed truncated-search world, menu and repair check | supplied object-language datum | re-run from the pinned clone (`derivation.represented`) |
| the obstruction claim as a bounded formula | externally imposed challenge | the repairing positions written as atoms |
| menu_replayed, bounded, mask_replayed, within_budget, value_replayed | derived definition | clauses decided on the replayed sealed facts |
| `Represented.incomplete_search_false_alarm` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The formula's atoms name the repairing positions that the sealed repair
check finds. The target decides the enumeration, the mask and the budget,
and the replay decides that the domain is the whole menu. A search cut at the
first entry reports an obstruction: the target accepts that formula, because
it is true for its own bound, but the replay refuses it, because the bound is
not the menu's length. That is the sealed false alarm.
