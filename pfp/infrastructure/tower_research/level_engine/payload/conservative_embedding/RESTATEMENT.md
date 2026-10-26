# Restatement: `conservative_embedding`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed candidate space, validity check and observation
are re-run from the pinned clone, read only; nothing here is attributed to
the seed.

## Obligation

An old presentation embeds conservatively into a new one: every old
generator has an image; two old generators the old presentation keeps apart
are not identified in the new one; and every old equation still holds in the
new one. Arrows between generators, where any are stated, meet at their
endpoints, and the two sides of a two-cell join the same endpoints.

Here the presentations are stages of a hosted regime. A supplied fixture
(three data, one unary form marking the first, the first two required
apart) is answered, for the demand that separates the second from the third,
by the sealed minimal response. The old stage presents the data its
requirements name; the new stage presents all data after the response. A
stage's equations are the pairs it cannot separate.

## Refused case

A new equation that identifies two old generators is refused: the candidate
that marks the second datum separates the demanded pair but identifies the
protected one, and the sealed validity check refuses it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the three-datum fixture and its requirement | externally imposed challenge | hosted by sealed events |
| the demand on the second and third data | externally imposed challenge | the new separation asked for |
| stages as presentations | externally imposed challenge | a stage's data as generators, its inseparable pairs as equations |
| old_replayed, new_is_a_response, sealed_valid, embedding_total, keeps_apart, keeps_equations, no_cells | derived definition | clauses decided on the replayed sealed facts |
| `Derivation.mark_progress`, `validResponse_ext`, `validResponse_dropRules` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The sealed grammar states no arrow between data, so no two-cell is presented
and the endpoint clauses are not bitten. The sealed validity check protects
the required pairs, and the target protects every pair of old generators.
The two agree here because the old stage presents exactly the data of its
one requirement.

The embedding-retraction field of the sealed growth proposal is not cited.
Its only reported instance is the identity (`upProposal`, where the
retraction holds by definition), and it belongs to a growth proposal, which
the embargo excludes.
