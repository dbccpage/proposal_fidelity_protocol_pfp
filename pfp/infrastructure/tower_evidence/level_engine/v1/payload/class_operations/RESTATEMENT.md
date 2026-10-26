# Restatement: `class_operations`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A closed complex of triangular patches over the two-element field carries an
operation from edge cochains to patch cochains, given by a quadratic
formula: at each patch, a sum of products of a cochain's values on two
edges, plus a constant. For every declared test cochain, which must have
zero coboundary, the operation's value class must not depend on the
representative: adding the coboundary of any corner cochain changes the
value by a coboundary. For every declared self-map of the complex, the
operation of the pulled-back cochain and the pull-back of the operation's
value must differ by a coboundary.

## Refused case

An operation whose value class moves when a coboundary is added to its
input.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| corner, patch, spans | supplied object-language datum | the complex |
| term, constant | supplied object-language datum | the operation's formula |
| cochain, carries | supplied object-language datum | the declared test cochains, by support |
| map, sends | supplied object-language datum | the declared self-maps |
| spans_given, one_span, sends_given, one_image, carries_typed, terms_typed, constant_typed | derived definition | relational requirements over the claim |
| complex_ok, test_cocycles, class_kept, natural | derived definition | clauses decided outside the grammar |
| elimination over the two-element field | metatheory apparatus | the harness's coboundary test, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive is the six-corner closed surface with
ten patches, one test cochain and one map: eighteen elements, the size the
carrier cap was lifted to in round P6. Its operation is the square by front
and back edges, and the test cochain is one whose square is not a
coboundary, so the positive is not answered by a vanishing value. Which
operation a formula computes is not decided.
