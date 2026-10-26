# Restatement: `bound_axioms`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A proof over a declared list of axioms is rechecked step by step against a
fixed table of two rules: a line may cite an axiom that states its term, or
detach from two strictly earlier lines, the second claiming that the
first's term implies the line's. The axiom list is bound by a digest: the
SHA-256 of its canonical JSON (sorted keys, no white space, ASCII), with an
atom written `p<k>` by its place and an implication as `["->", a, b]`. The
declared conclusion is the last line's term.

## Refused case

A line that rests on its own report of having been checked: a report is not
a rule of the table.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| term, imp | supplied object-language datum | the formulas |
| axiom, states | supplied object-language datum | the axiom list, in declared order |
| line, claims, cites, detaches, reports | supplied object-language datum | the proof and each line's support |
| seal and its digest | supplied object-language datum | the bound digest, an exact 32-byte value |
| concludes | supplied object-language datum | the declared conclusion |
| states_given, one_state, claims_given, one_claim, one_imp, imp_typed, concluded, one_conclusion | derived definition | relational requirements over the claim |
| terms_finite, bound, rules_only, earlier_only, steps_match, concludes_last | derived definition | clauses decided outside the grammar |
| SHA-256 and the canonical JSON | metatheory apparatus | a declared convention, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The digest is hosted as a value since round P6; the
kernel re-decides the four step clauses, and the digest clause stays
computed.
