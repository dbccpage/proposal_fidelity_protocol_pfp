# Restatement: `host_bound_verdict`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed first separation is re-run from the pinned clone,
read only; nothing here is attributed to the seed.

## Obligation

A terminal claim is accepted only through the host. The verifier must be the
host's own; the claim's scope must be that verifier's scope; the terminal
must be the one the host's re-run gives; and the recorded output must be that
re-run's output. Nothing the candidate writes about the result is read as the
result.

Here the claim is a sum over sealed counts: the tied classes the first
separation retains in each admission reading under the item-count measure,
and their total over both readings. The host's verifier is a sum check.

## Refused case

A terminal declared by the candidate's own script, not by the host's
verifier, is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed first separation in both readings | supplied object-language datum | re-run from the pinned clone (`derivation.engine`, `partial_decide`) |
| the claim as a sum of tied-class counts | externally imposed challenge | the declared terminal claim |
| host and candidate verifiers, the sum scope | externally imposed challenge | the verifier the host pins, and the one it refuses |
| claim_replayed, verifier_bound, scope_bound, terminal_earned, output_bound | derived definition | clauses decided on the replayed sealed facts |
| `Represented.progress_needs_license`, `GraphGenesis.proposal_confers_no_execution`, `Derivation.mu1_minimum_not_unique` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The sealed theorems carry the discipline: a proposal carries no authority,
and progress needs a licence. The host's verifier and its digests are the
target's apparatus, not sealed content.
