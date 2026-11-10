# SN09 retained evidence

AuthorityEffect: None. This archive is historical data, not runnable pilot code.

`sn09_legacy_sources.zip` preserves `sources.json` and its nine snapshots from
commit `2653895c8e7382e9657c0c0cabe93b8c1f99599a`, under
`_ic/darpa/research/briefs/pfp_migration/sn09_research/`. The NARA copy at that
commit has the same inventory and ledger blob identities. The adjacent manifest
records every source path, Git blob, raw-byte SHA-256 and byte length.

The archive SHA-256 is
`6859afe672cee08ccb15845eeb83f846623b5c9c2de70dc155fafb9a2771d413`.
It was built from `git cat-file blob` bytes, with the inventory first and then
snapshots in inventory order. ZIP entries use DEFLATE and normalized timestamps
`1980-01-01 00:00:00`; timestamps are packaging metadata, not historical dates.
Tests verify member bytes independently of ZIP metadata and compression.

Tests open members as data without extraction, import or execution. AST and
literal evaluation recover the original twenty controls. JSON inspection checks
that the retained response lacks `untrusted_output` while its retained receipt
claims a passing gate. This contradiction is preserved, not replayed or repaired.

The ledger snapshot's inventory source is an education path. Its identity with
the deleted PFP owner has not been established. The current sibling
`../budget_ledger.py` is a changed, separately tested offline derivative with its
own schema and caps; it is not loaded from this archive. Historical defaults and
receipts provide no live spending authorization, model measurement or proof.
