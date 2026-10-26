# Discovery and runtime-path rules

- `AGT-PATH-0001` -- Only `Active` and explicitly allowlisted `Canary` skills may
  occupy an automatic discovery path.
- `AGT-PATH-0002` -- Mutation profiles remain outside automatic discovery and
  may be injected only by an admitted host for one leased session.
- `AGT-PATH-0003` -- Quarantined, archived, deprecated, draft, and retired assets
  never enter provider discovery roots.
- `AGT-PATH-0004` -- `.agents` never stores leases, runtime receipts, transcripts,
  worktrees, costs, terminal records, scheduler state, journals, or secrets.
- `AGT-PATH-0005` -- Nested rules may narrow but never widen root rules.
