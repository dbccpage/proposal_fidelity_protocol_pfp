# Restatement: `typed_queries`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A conjunctive question over typed tables, with named-column atoms and
constants, is translated before it is evaluated: every atom names only its
table's columns, every variable has one type, every constant lies in its
column's type, and every output variable occurs in an atom. Every stored
row must fit its table, and the claimed answers must be exactly the answer
set the finite join recomputes, with set semantics.

## Refused case

An absent column, refused during translation.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| type, value, member | supplied object-language datum | the typed domains |
| table, column, column_of, typed, row, stored, cell | supplied object-language datum | the schema and the stored rows |
| atom, var, atom_on, binds_var, binds_const, slot, out | supplied object-language datum | the question |
| answer, gives | supplied object-language datum | the claimed answers |
| columns_present, constant_columns_present, one_type, constants_typed, outputs_bound, rows_full, rows_within, cells_typed, one_typed, one_column_of, one_answer_value | derived definition | relational requirements over the claim |
| answers_exact | derived definition | a clause decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Translation is carried by derivability in full: every
translation check is a closure or a totality over the hosted question. Only
the join's answer set is computed outside the grammar.
