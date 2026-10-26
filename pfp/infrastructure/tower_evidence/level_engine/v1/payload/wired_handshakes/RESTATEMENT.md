# Restatement: `wired_handshakes`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite graph of components with named ports, each port an output or an
input carrying a nominal message type, is joined by wires. Every wire joins
declared ports, one output to one input, of the same type; which end is the
output is read from the port declarations, not from the wire's order. Each
port is wired at most once. A handshake needs both directions: whenever
some wire carries messages from one component to another, another must
carry messages back.

## Refused case

Two output ports joined by one wire.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| component, port, msgtype, port_of, sends, receives, carries | supplied object-language datum | the components and their ports |
| wire, joins | supplied object-language datum | the wires |
| first_end_declared, second_end_declared, not_two_outputs, not_two_inputs, same_type, one_type, one_owner, one_way_per_port | derived definition | relational requirements over the claim |
| wired_once, both_directions | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the ports and wires are
hosted objects of the grammar, and the direction and type laws are carried
by derivability; only "wired once" and "both directions" are decided
outside it. By ruling D4 the level's checker is apparatus, so this record
counts in A, never in C.
