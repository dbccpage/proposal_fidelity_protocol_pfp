# Restatement: `recomputed_labels`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite order of stages carries a family of finite sets: each element lies
at one stage, and restricts to exactly one element at every stage strictly
below its own, landing at that stage; restricting twice is restricting once.
A declared subfamily is closed under restriction. Each element carries a
label, a set of stages at or below its own. The label must be the recomputed
one: the stages where the element's restriction (at its own stage, the
element itself) lies in the subfamily. And the subfamily must be exactly the
set of elements labelled true, that is, whose label holds their own stage.

The order is chosen so that labels are not two-valued: one stage has two
stages below it, and a chain of three stages ends at the top, so an element
can be labelled with nothing, with everything at or below its stage, or with
a middle set such as one of the two lower stages.

## Refused case

Labels read two-valued on a subfamily that gives some elements a middle
value: a label that is not empty is read as every stage at or below, so an
element whose restrictions lie in the subfamily, while it does not, is
labelled true, and the subfamily is not the set of elements labelled true.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| stage, below | supplied object-language datum | the finite order, given closed under chains |
| element, at, restricts | supplied object-language datum | the family and its restrictions |
| in_sub | supplied object-language datum | the declared subfamily |
| label | supplied object-language datum | the declared labels |
| below_typed, below_transitive, below_strict, at_given, one_at, at_typed, restriction_total, restriction_from, restriction_down, restriction_lands, one_restriction, restrictions_compose | derived definition | relational requirements on the family |
| sub_typed, sub_closed | derived definition | relational requirements on the subfamily |
| label_typed, label_forward, label_back | derived definition | the label below its element's own stage, recomputed |
| true_on_sub, pullback | derived definition | the subfamily is the elements labelled true at their own stage |
| label_within | derived definition | a clause decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Every clause but one is carried by derivability: the
recomputed label is a pair of closures over the restrictions, and the
refused case is a closure from a label at its own stage to the subfamily.
That every stage of a label lies at or below its element's stage needs "its
own stage or one below it", which the grammar does not state as a closure,
so it is decided outside it.
