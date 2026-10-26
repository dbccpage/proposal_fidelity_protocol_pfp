# Restatement: `limited_runs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A counter-machine program (increment, decrement-or-branch, halt) is run from
declared registers under a step bound and a value bound. Every jump must
name an instruction and every counted register must exist. The run is
replayed: a halt is a completion; reaching the step bound is a timeout; a
register above the value bound stops the run at the limit. The captured
exit kind, registers and step count must be the replayed ones, and only a
halt is a completion.

## Refused case

A run that timed out, captured as a completed one.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| instr, inc, dec, halt | supplied object-language datum | the program, in declared order |
| register and its initial value; bound and its value | supplied object-language datum | the start and the limits |
| final, final_of, capture, halted, timed_out, at_limit | supplied object-language datum | the captured exit state |
| inc_targets, dec_targets, one_final, finals_given | derived definition | relational requirements over the claim |
| well_formed, no_false_completion, exit_exact, state_exact, steps_exact | derived definition | clauses decided outside the grammar, over the replay |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the program and its
terminals are hosted, and running out of fuel is never a halt, the
represented-execution terminal discipline. By ruling D4 the level's checker
is apparatus, so this record counts in A, never in C.
