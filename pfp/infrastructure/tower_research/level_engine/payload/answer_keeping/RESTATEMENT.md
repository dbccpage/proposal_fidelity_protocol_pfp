# Restatement: `answer_keeping`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A claim that one question is at least as hard as another needs a map from
the first question's instances to the second's that keeps every answer. The
questions here are "is a multiple of the modulus", with a declared source
modulus and target modulus, two or three. The map must give one image to
every source instance from zero to a declared bound, and each instance and
its image must get the same answer. This is a fence: a pass says only that
the map keeps the answers up to the bound.

## Refused case

Counts offered in support, with no map: keys, labels, counts and timings
are never evidence of a map.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| num, instance | supplied object-language datum | the numbers and the source instances |
| sends | supplied object-language datum | the map |
| source_mod, target_mod | supplied object-language datum | the two questions |
| offered | supplied object-language datum | counts offered in support |
| map_given, one_image, map_typed, no_surrogate, source_given, one_source, target_given, one_target | derived definition | relational requirements over the claim |
| moduli_declared, instances_counted, answers_kept | derived definition | clauses decided outside the grammar |
| remainders of natural numbers | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. No statement about how hard either question is, for
any size, follows from a pass.
