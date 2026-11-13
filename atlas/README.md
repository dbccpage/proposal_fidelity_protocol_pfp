# Atlas

AuthorityEffect: None.

The atlas is the single research record of this repository: one paper, one
claim ledger, one change log, and the archive of the source manuscripts they
are drawn from.

| File | What it holds |
| --- | --- |
| [`atlas_change_log.md`](atlas_change_log.md) | What changed in the atlas, and when. |
| [`archive/`](archive/README.md) | The source papers: the PFP series 000–021 and the finite obstruction calculus and authority series 001–016. |

The archive was `papers/` until 2026-11-13. It was moved with `git mv`, so every
manuscript, manifest, release ZIP and receipt keeps its bytes and its SHA-256.
Frozen audit records under `dag/reviews/`, `dag/research/`, `dag/migrations/`,
`dag/handoff/` and `governance/evidence/` still write the old prefix; read
`papers/X` there as `atlas/archive/X`. The rule is recorded as data in
[`archive_path_map.json`](archive_path_map.json).

The atlas paper (`atlas.md`) and its claim ledger (`atlas_claim_ledger.md`)
follow in the next change. Written derivations, one file per DAG node, go in
[`dag/derivations/`](../dag/derivations/README.md).
