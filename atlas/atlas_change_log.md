# Atlas change log

AuthorityEffect: None.

## 2026-11-13: atlas created from papers/

- `papers/` moved to `atlas/archive/` with `git mv`. No archived byte changed,
  so every SHA-256 pin to a manuscript, manifest or release ZIP still holds.
- Live references were rewritten from `papers/` to `atlas/archive/`: the
  repository README, the wiki, `docs/`, `lean4/`, `workflows/`, the governance
  policy and baseline, and the path fields of the top-level `dag/*.json` files.
  Frozen, hash-pinned audit records keep the old prefix; see
  [`archive_path_map.json`](archive_path_map.json).
- Added `dag/derivations/` for written derivations, one file per DAG node.
