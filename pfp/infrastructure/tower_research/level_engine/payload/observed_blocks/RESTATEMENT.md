# Restatement: `observed_blocks`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed candidate space, observation and requirement
check are re-run from the pinned clone, read only; nothing here is attributed
to the seed.

## Obligation

A block map from a fine carrier onto a coarse carrier is total and onto.
Every pair of fine points it merges is recorded in a loss ledger. Every
ledger pair, and every erasure record, is a merged pair. A protected pair is
never merged unless an erasure record explicitly permits it.

Here the block map is the sealed observation of a hosted regime: each datum
goes to its class of equal profiles. The fixture has three data, one unary
form marking the first, and the requirement that the first two stay apart. It
is answered, for the demand that separates the second from the third, by the
sealed minimal response. The ledger is the regime's inseparable pairs, and
the protected pairs are its requirements.

## Refused case

A coarse map that silently merges a protected pair is refused: the candidate
that marks the second datum merges the first two in the observation, and
records the merge only as a loss.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the three-datum fixture, its requirement and the demand | externally imposed challenge | hosted by sealed events |
| the observation's quotient as a coarse map | externally imposed challenge | the declared coarse reading of a regime |
| observation_replayed, protected_replayed, ledger_complete, ledger_exact, no_silent_protected_merge | derived definition | clauses decided on the replayed sealed facts |
| `PrimDiff.collision_of_identifying_witness`, `obstruction_under_irrefl`, `Derivation.mark_progress` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The observation is a declared coarse reading, not a scale map of the system.
A valid response never merges a requirement, so on the positive the ledger
records only unprotected losses.
