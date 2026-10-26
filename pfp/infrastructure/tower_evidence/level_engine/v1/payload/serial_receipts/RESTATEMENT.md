# Restatement: `serial_receipts`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite schedule of reads, writes, commits and aborts over keys is
replayed. No operation may touch a key whose last write belongs to another
transaction that has neither committed nor aborted. The conflict graph over
the committed transactions (an edge from one to another when an operation of
the first precedes a conflicting operation of the second on the same key,
one of them a write) must be acyclic. The receipts must list the committed
transactions once each, in an order every conflict edge respects, and each
receipt must bind the digests of the states before and after its
transaction, the writes applied along that order to the base state.

## Refused case

A conflicting write while the key's last writer is still open.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| txn, key, token, base | supplied object-language datum | the transactions and the base state |
| op, acts, reads, writes, commits, aborts | supplied object-language datum | the schedule, in declared order |
| receipt, receipt_for, stamp, parent_stamp, state_stamp | supplied object-language datum | the receipts and their digests |
| a stamp's digest | supplied object-language datum | an exact 32-byte value |
| acts_given, one_txn, receipt_given, one_receipt_txn, parent_given, one_parent, state_given, one_state, one_base | derived definition | relational requirements over the claim |
| well_formed, strict_writes, conflict_acyclic, serial_order, parents_exact, states_exact | derived definition | clauses decided outside the grammar |
| SHA-256 of the canonical JSON state | metatheory apparatus | a declared convention, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A state is the canonical JSON object from key names to
token names, named by position. Digests are hosted as values since round
P6, and the engine recomputes every state digest itself.
