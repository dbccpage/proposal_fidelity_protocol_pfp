# Restatement: `tagged_digest`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed compression instance is re-run from the pinned
clone, read only; nothing here is attributed to the seed.

## Obligation

Each container is decoded by the decoder its own tag names, with no default
decoder, and the decoded body must re-encode to itself. Its digest must be
the SHA-256 of the exact canonical bytes of its tag and body (sorted keys, no
whitespace, ASCII).

Here the containers carry sealed answers: the number of signature classes on
the domain `0, 1, 2` under the indicator question of `0`, before and after
the family is duplicated (tag `t0`, a natural), and each element's signature
under the duplicated family as a binary word (tag `t1`).

## Refused case

A changed body under an unchanged digest is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed domain, family, signatures and class counts | supplied object-language datum | re-run from the pinned clone (`derivation.compression`) |
| tags `t0` and `t1`, and the canonical digest | externally imposed challenge | the declared container dialects and digest rule |
| bodies_replayed, tags_known, bodies_decode, digests_bound | derived definition | clauses decided on the replayed sealed facts |
| `Compression.dup_no_refine`, `postcompose_no_refine`, `refinement_tie` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The two counts are equal because duplicating the family refines nothing. The
digest is a function of the body, which is why a digest of existing answers
adds no question. The tag dialects are the target's; the sealed repository
has none.
