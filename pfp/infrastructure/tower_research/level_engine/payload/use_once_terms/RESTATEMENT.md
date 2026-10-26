# Restatement: `use_once_terms`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Terms of a use-once language are finite trees: a name, a pair of two terms,
a copy (consumes a name and binds two fresh names of its kind in a body)
and a discard (consumes a name unused). Use counts are computed from the
leaves and the binders, never read. Every consumed name is in scope; no
name is consumed twice; every name in scope is consumed; copies and
discards consume only kinds declared copyable; and the declared type is the
computed pair type.

## Refused case

A protected resource used twice without a copy.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| name, kind, in_context, copyable | supplied object-language datum | the context and the copyable kinds |
| node, root, var, pair, copy, discard | supplied object-language datum | the term tree |
| tnode, leaf, both, declared | supplied object-language datum | the declared type |
| root_given, one_root, declared_given, one_declared, in_context_typed, var_typed | derived definition | relational requirements over the claim |
| well_formed, in_scope, at_most_once, at_least_once, copy_kinds, type_exact | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The sealed grammar has no use-count discipline of its
own: the counts are this level's, computed outside it, and re-decided by the
kernel's walk of the tree.
