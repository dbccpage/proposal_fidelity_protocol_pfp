# Restatement: `positioned_join`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed repository's own rewrite system is re-run from
the pinned clone, read only; nothing here is attributed to the seed.

## Obligation

For a peak of a rewrite system on words (one source term rewritten by two
different steps), replay every substitution from its term: the rule of each
step must occur at its position. Replay both arms from the two peak terms;
the arms must end at one term, and the declared join must be that term.

Here the system is the sealed two-rule system on event lists (adjacent
idempotence, terminal absorption), with each event of the sealed rewrite
alphabet written as one letter and absorption stated one following letter at
a time. A step counts only when its result is one of the sealed system's own
one-step reducts; the join must be the sealed normal form.

## Refused case

A join declared with both arms empty, where the two peak terms differ, is
refused: the arms do not meet.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed rewrite system and its battery | supplied object-language datum | re-run from the pinned clone (`derivation.trace_algebra`) |
| one letter per event of the rewrite alphabet | externally imposed challenge | the declared writing of event lists as words |
| per-letter absorption rules | externally imposed challenge | absorption stated one following letter at a time |
| steps_replayed, arms_meet, join_is_normal_form | derived definition | clauses decided on the replayed sealed system |
| `TraceAlgebra.rw_confluent`, `nf_unique`, `rewrite_not_complete`, `rw_sound` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The positive is found, not written: the first list of the sealed battery
with two stated steps whose results differ, and the arms that take the first
stated step until none applies. No peak of the stated sealed steps has an
empty arm (the replay searches the sealed battery up to length 4 and finds
none), so a join with both arms empty is never the answer here, and no single
edit of the positive can produce one.
