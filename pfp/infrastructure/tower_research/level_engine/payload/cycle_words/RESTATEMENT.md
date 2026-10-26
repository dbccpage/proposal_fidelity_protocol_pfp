# Restatement: `cycle_words`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Over a hosted table of allowed steps between letters, the words of length two
are read cyclically: a word's two steps are first-to-second and
second-to-first, and turning it once exchanges its letters. The words whose
steps are all allowed are grouped into rings. Each ring holds exactly the
turns of its lead; its lead is the least of those turns (letters in the
declared order, words by their letters); its declared span is the least
number of turns that returns the lead; and every word whose steps are allowed
lies in exactly one ring.

## Refused case

A constant word declared a ring of least span two is refused: turning it once
already returns it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| letter, step | supplied object-language datum | the table of allowed steps between letters |
| word, first, second | supplied object-language datum | words of length two, spelled by their letters |
| ring, lies_in, lead, span, count | supplied object-language datum | the declared rings, their leads and declared spans |
| steps_typed, first_given, one_first, second_given, one_second, spelled, lies_typed, one_ring, steps_allowed, turn_closed, lead_given, one_lead, lead_lies, covered, span_given, one_span | derived definition | relational requirements over the claim |
| one_class, span_least, lead_least | derived definition | clauses decided over the hosted structure |
| length two | externally imposed challenge | the declared class: words carry exactly two letters |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The span and the least-lead clauses read the declared
order of letters and exact naturals, outside the grammar.
