# Restatement: `paired_frames`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two named factors, declared in an order, each carry a row of exact pairs
`a + b i` on their slots. Joining them gives a row of size m n, whose place
n i + j holds the product of the first factor's slot i and the second
factor's slot j when the first factor runs slowest. A claimed joined row
states its size and its reading, the factor that runs slowest in it. When
the second factor runs slowest, the claim must carry the exchange table,
which sends place n i + j to place m j + i, and the joined row must be the
product row carried through that table; when the first runs slowest, no
table is given and the joined row is the product row itself.

Order is hosted data, never element position. Every slot and every joined
place carries its index as a hosted natural, the factor order is the hosted
relation `before`, the reading is the hosted relation `slowest`, and the
exchange table is the hosted relation `exchange` over places. Rows are read
in the order of these indices, and the product is carried through the
hosted table itself.

## Refused case

A joined row read with the second factor slowest, a permuted factor order,
with no exchange table to carry it back.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| factor | supplied object-language datum | the two factors, each carrying its name as a text |
| slot, slot_of, entry | supplied object-language datum | each factor's slots, each carrying its index, and the row's pairs |
| place, joined | supplied object-language datum | the joined row's places, each carrying its index, and their pairs |
| before | supplied object-language datum | the declared factor order |
| slowest | supplied object-language datum | the declared reading |
| exchange | supplied object-language datum | the declared exchange table over places |
| claimed, number | supplied object-language datum | the claimed size and the exact values |
| slots_owned, one_owner, rows_given, one_entry, joined_given, one_joined, reading_given, one_reading, order_given, one_order, order_strict, size_given, one_size, one_exchange, exchange_typed | derived definition | relational requirements over the claim |
| indices_in_line, names_apart, size_claimed, reading_transported, exchange_exact, product_exact | derived definition | value clauses, decided over exact values |
| products of exact pairs; sorting by hosted indices | metatheory apparatus | the harness's exact arithmetic and reading order |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive joins A = (3/5, 4/5 i), declared first,
with B = (1, 0), with B read slowest: the joined places 0 to 3 hold 3/5,
4/5 i, 0 and 0, and the exchange table sends places 0, 1, 2, 3 to 0, 2, 1,
3 (15 elements). A table that is given when the first factor runs slowest,
or that is not the factor exchange, is `exchange_exact`'s refusal; a
missing table under a permuted reading is `reading_transported`'s.
