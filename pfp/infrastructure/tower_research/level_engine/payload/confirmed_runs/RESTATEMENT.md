# Restatement: `confirmed_runs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A one-function recursion on naturals, `f(n)` equal to a base value on a
base case and to `f(n - k) + c` otherwise, is run from a declared input
with a declared measure `m(n) = a n + b`. Every recursive call must lower
the measure strictly, checked before the call is made, so no unbounded run
is ever attempted. The result must be confirmed by an evaluator whose
digest differs from the interpreter's, and every reported result, and the
declared output, must be the recomputed value.

## Refused case

A self-certified evaluation whose calls never lower the measure.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| number and its natural value | supplied object-language datum | the program's constants, the input and the results |
| evaluator and its digest | supplied object-language datum | the interpreter and the confirmers, identified by exact 32-byte values |
| base, step, measure, input, output, interpreter, confirms | supplied object-language datum | the program, the run and the reports |
| step_given, one_step, measure_given, one_measure, input_given, one_input, output_given, one_output, interpreter_given, one_interpreter, one_base_value, confirms_typed | derived definition | relational requirements over the claim |
| well_formed, decreasing, external, output_recomputed | derived definition | clauses decided outside the grammar |
| the bounded run | metatheory apparatus | the harness's evaluation, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Digests are hosted as values since round P6; what is
decided of them is only that the confirmer's is not the interpreter's. A
description of the interpreter run by itself is not hosted.
