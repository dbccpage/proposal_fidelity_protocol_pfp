# Restatement: `coloured_slots`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Operations have ordered input slots, at least one, and one output; each slot
and each output carries a colour. The operations are cut off at a bound on
the number of slots, the number of hosted slot positions. Each colour has a
unit operation, with one slot and output of that colour. A substitution table
puts one operation's output into a slot of another and names the result.
Inside the bound, every substitution whose colours match has exactly one row;
the result's slots are the outer operation's, with the inner operation's
slots in place of the one filled, and its output is the outer operation's;
putting an operation into a unit, or a unit into a slot, gives the operation
back; and substituting twice gives the same operation however it is
bracketed, whether the second substitution goes into the inner operation or
beside it.

## Refused case

A row that puts an output into a slot of another colour.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| colour, slot, op | supplied object-language datum | the colours, the slot positions (their number is the bound) and the operations |
| input, output | supplied object-language datum | each operation's slot colours and output colour |
| unit | supplied object-language datum | the declared unit of each colour |
| subst | supplied object-language datum | the substitution table |
| output_given, one_output, output_typed, input_typed, one_input, inputs_start, inputs_contiguous_2 | derived definition | relational requirements on the operations |
| unit_given, one_unit, unit_typed, unit_profile, unit_one_slot | derived definition | relational requirements on the units |
| subst_typed, one_result, slot_exists, colours_match, result_output, unit_outside, unit_inside | derived definition | relational requirements on the table |
| result_inputs, table_full, brackets | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The refused case is carried by derivability: a row's
inner output must have the colour of the outer slot, a closure over the row
and the slot. So are the unit laws and the output of a result. The result's
slots, whether the table is full inside the bound, and bracketing all move
slot positions by the width of an operation, which is arithmetic on
positions, so they are decided outside the grammar.
