# Restatement: `differential_pairs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two independent implementations of one function, each pinned here and
written independently of the other (rounding a rational half up, and half to
even), are run on the same canonical inputs. The two sides must be
different implementations; each claimed output must be what its
implementation returns; a case whose outputs differ must be recorded as a
disagreement and never merged; and every agreeing case must be merged,
once, with its output.

## Refused case

Different outputs merged silently.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| impl and its pinned number | supplied object-language datum | which implementation stands on each side |
| case and its input; integer and its value | supplied object-language datum | the inputs and the outputs |
| side_a, side_b, out_a, out_b, merged, disagrees | supplied object-language datum | the claimed runs, merges and disagreements |
| independent, sides_given, one_side_a, one_side_b, outputs_given, one_out_a, one_out_b, one_merge | derived definition | relational requirements over the claim |
| well_formed, outputs_exact, no_silent_merge, disagreements_recorded | derived definition | clauses decided outside the grammar |
| the two pinned implementations | metatheory apparatus | declared here |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Only rounding is hosted: the checker's other two
functions are not. By ruling D4 the level's checker is apparatus, so this
record counts in A, never in C.
