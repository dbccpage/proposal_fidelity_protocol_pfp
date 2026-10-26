# Restatement: `granted_steps`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed represented world and its step are re-run from
the pinned clone, read only; nothing here is attributed to the seed.

## Obligation

Each operation has an effect row, and each scope grants a set of effects.
Scopes form a tree, and a nested scope grants nothing its parent does not.
Every execution edge runs in its innermost scope; its effects are the union of
its operations' rows, and they must lie within that scope's grant. An edge
performing an operation with no row is refused.

Here the effects are the sealed world's two capabilities: the licence to
augment its views, and a budget to spend. An operation's row is computed from
the sealed step. A capability is in the row exactly when the operation changes
the world, and withdrawing that capability alone makes the step inert. The
outer scope is the world as it is; the inner scope is the same world with the
licence withdrawn.

## Refused case

An effect outside the granted capability is refused: adding a view in the
scope without the licence, where the sealed step is inert.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed truncated-search world and its step | supplied object-language datum | re-run from the pinned clone (`derivation.represented`) |
| three events: add a view, mark, note | externally imposed challenge | the declared operations |
| the two scopes | externally imposed challenge | the world, and the world without the licence |
| rows_replayed, scopes_replayed, operations_known, edges_progress | derived definition | clauses decided on the replayed sealed facts |
| `Represented.progress_needs_license`, `progress_needs_budget`, `GraphGenesis.proposal_confers_no_execution` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The sealed gates guard progress, a state-level licence and budget. This is
not an effect-typing discipline, and the record claims nothing beyond it.
A row declared smaller than the computed one would pass a checker that
trusts declared rows; the replay refuses it, because it computes each row.
