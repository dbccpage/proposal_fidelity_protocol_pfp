# Restatement: `lineage_pins`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Every derived value must point to immutable inputs. Each derived record
names its inputs, each a source or a derived record listed earlier, with
the digest the input had when it was used. Its value must be its operation
(a sum or a product) of its inputs' values; every record's digest must hash
its content; and every pinned digest must still be its input's digest, so
an input changed after use is caught.

## Refused case

A missing source: an input that is no record at all.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| record and its value | supplied object-language datum | sources and derived records, in declared order |
| seal, pin and their digests | supplied object-language datum | exact 32-byte values |
| source, sums, multiplies, sealed, reads | supplied object-language datum | the lineage graph |
| inputs_are_records, sealed_given, one_seal, derived_read, sources_read_nothing, one_operation | derived definition | relational requirements over the claim |
| inputs_earlier, values_exact, digests_exact, pins_hold | derived definition | clauses decided outside the grammar |
| SHA-256 of the canonical JSON content | metatheory apparatus | a declared convention, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the lineage is a hosted
graph whose missing source is refused natively, by a closure over the
records. By ruling D4 the level's checker is apparatus, so this record
counts in A, never in C.
