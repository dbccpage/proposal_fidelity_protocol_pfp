# Atlas change log

AuthorityEffect: None.

## 2026-11-13: claim-level review against the DAG

- Every archive claim reviewed against the audit derivations
  (`atlas_claim_matches.json`): 73 matched, 115 partial (96 supports,
  19 narrows), 419 gaps.
- Matched and partial claims gain 265 DAG edges from the audit nodes
  (`states_same_claim_as`, `partially_supports`, `narrows`).
- 504 proposed derivations written to `dag/derivations/`, one per gap and per
  partial claim that has one.

## 2026-11-13: paper, claim ledger and DAG correspondence

- Added `atlas.md`, `atlas_claim_ledger.md` and `atlas_claim_ledger.json`,
  generated in part by `dag/build_atlas.py`.
- 607 claims copied from the archive: from each paper's own claim ledger, and
  from the manuscript (`atlas_manuscript_claims.json`) for PFP 011 and 014–018.
  Each is a new `archive_claim` node in `dag/derivations_dag.json`.
- The 740 existing derivation nodes each carry an `atlas_ledger_id`; the
  ledger has 1,347 rows for 1,347 derivation nodes.
- Copied text follows the repository rename map; archive paths keep their
  real spelling.

## 2026-11-13: atlas created from papers/

- `papers/` moved to `atlas/archive/` with `git mv`. No archived byte changed,
  so every SHA-256 pin to a manuscript, manifest or release ZIP still holds.
- Live references were rewritten from `papers/` to `atlas/archive/`: the
  repository README, the wiki, `docs/`, `lean4/`, `workflows/`, the governance
  policy and baseline, and the path fields of the top-level `dag/*.json` files.
  Frozen, hash-pinned audit records keep the old prefix; see
  [`archive_path_map.json`](archive_path_map.json).
- Added `dag/derivations/` for written derivations, one file per DAG node.
