# Restatement: `compiled_branches`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A loop-free source expression over one natural input (the input, natural
constants, sums, differences, and a choice between two arms on a strict
comparison) is given with a compiled program for a small stack machine
(push a natural, load the input, add, subtract, jump on a strict comparison,
jump, halt), declared inputs, a fuel and a claimed table of results. The
bounded fragment is the declared inputs under the declared fuel. On every
declared input the source is evaluated here and the program is run here,
executing at most fuel + 1 instructions. The inputs must take both arms of
every choice in the source; no run may pop too few entries, halt on an empty
stack or pass the last instruction; every run must halt within the fuel;
every halted run must give the source's result; and the table must be the
source's results on exactly the declared inputs.

## Refused case

A compiled branch that changes the result: the program's jump on the
comparison leads to code that gives another result than the source's arm.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| node, root, reads_input, constant and its value, plus, minus, if_less | supplied object-language datum | the source expression; a node may be shared |
| instr, push and its value, load, add, sub, jump_if_less, jump, halt | supplied object-language datum | the program, in declared order |
| number and its value, input, table_row, fuel | supplied object-language datum | the declared inputs, the claimed table and the fuel |
| the machine's steps (as read here) | admitted primitive | the usual meaning of each instruction on a stack of exact integers; supplied vocabulary of the procedure, classified here |
| root_typed, one_root, plus_typed, minus_typed, if_typed | derived definition | relational requirements on the source |
| jumps_land, plain_jumps_land, one_target, one_plain_target | derived definition | relational requirements on the program: a jump names an instruction |
| inputs_numbers, rows_typed, one_row, rows_given, fuel_typed, one_fuel | derived definition | relational requirements on the inputs, the table and the fuel |
| well_formed, never_stuck, arms_covered, halts, branch_kept, table_exact | derived definition | clauses decided outside the grammar, over the evaluation of the source and the runs of the program |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the source, the program,
the inputs, the fuel and the table are hosted, and the engine evaluates the
source and runs the program with the fuel itself. The positive is "if n < 3
then n + 3 else n", compiled with the input loaded twice so that one copy
survives the comparison; its inputs 1, 3 and 6 take both arms, the middle
one on the boundary. An extra compiles the same source arm by arm into
another program with the same results, and is accepted: the runs are
compared, not the programs. By ruling D4 the level's checker is apparatus,
so this record counts in A, never in C.
