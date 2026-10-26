# Restatement: `site_checks`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/p209c_stabilizer_codes` is re-run
from the pinned clone, read only; it is not sealed, and it is admitted for a
replay by the author's ruling of 2026-09-25. Nothing here is attributed to
the seed.

## Obligation

Words over n two-bit sites are written (x | z), two bit strings of length n.
Two words commute when their exchange count, x . z' + z . x', is even. A
declared set of checks must commute pairwise, and the reading of each
declared error, one bit per check, set when the error and that check do not
commute, must be nonzero and different for every error. Check that every
word has length n in both halves (a word of another length is refused before
any comparison, never cut), that the checks commute, that the readings are
nonzero and distinct, and that the claimed readings are those readings.

Every comparison of two words is the tree's own commutation test on the
tree's own words; a declared (x | z) pair becomes the tree's word through the
tree's own (x, z) reading of its four site letters.

## Positive

The tree's three-site code: two checks, reading the first two sites and the
last two sites, and the three single-site flips of its own table, whose
readings in that table are 10, 11 and 01.

## Refused case

The tree's own pair of words over the same three sites, every site flipped
and every site signed. Its test and its Lean find that they do not commute:
they meet at three sites, an odd count.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the tree's words, their (x, z) reading and their commutation test | supplied object-language datum | re-run from the pinned clone (`research/p209c_stabilizer_codes`, research-tree evidence) |
| the three-site code's two checks and its table of flips with their readings | supplied object-language datum | the tree's own fixture |
| the pair that does not commute, the unseen sign at the first site, the four-site code | supplied object-language datum | the tree's own fixtures and tests |
| lengths, checks_commute, readings_distinct, readings_replayed | derived definition | clauses decided on each packet |

## Notes

The tree's Lean states the commutations and readings of its fixtures as
equalities on a declared table; this replay cites none of it and rests on
the tree's Python alone. The tree's seven-site code is not used. The record
books the custody: the witness is research-tree evidence, not sealed.
