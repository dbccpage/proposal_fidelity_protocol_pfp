# Deposit Envelope Purity Gate

AuthorityEffect: None. This gate refuses; it does not mint, promote, or alter doctrine.

## The Principle

> Public preprint deposit packages must be purged of private execution receipts (`evidence/`), legacy migration folders (`reconstruction_v1/`), and uncurated top-level tests outside `code/tests/`.

## Invariants

1. **Purge Internal Receipts**: Transient runner logs, evidence receipts (`evidence/`), and intermediate test dumps must be stripped from public deposit packages.
2. **Purge Legacy Scaffolding**: Old migration snapshots (`reconstruction_v1/`) must not be bundled in release archives.
3. **Structured Test Placement**: Test harnesses must be located strictly under `code/tests/` (or package-local `tests/`), never left orphaned at the deposit root.
4. **Deposit Manifest Verification**: All release files must be enumerated in a single flat `SHA256SUMS` manifest matching 100% of deposit contents.
5. **Two-Way Manifest Bijection (`ANTI-DEPOSIT-VERIFIER-FAIL-OPEN`)**: Verifiers must assert a strict two-way bijection: every deposited on-disk payload file must be named in `SHA256SUMS`, and every entry in `SHA256SUMS` must exist on disk with matching SHA-256 digest. Any unmanifested file present in the package root or payload tree must fail closed.
6. **Archive Member Digest Concordance (`ANTI-STALE-ARCHIVE-DESYNC`)**: The release ZIP archive (`<slug>_<date>.zip`) must be verified against the on-disk tree; every member in the ZIP must have an identical SHA-256 digest to the manifest-bound on-disk payload file. Stale ZIP archives differing from current on-disk files are strictly refused.
7. **Version Lineage Parity**: Release candidate version numbers and DOIs must align across `README.md`, `pyproject.toml`, `zenodo_metadata.json`, and `<slug>_change_log.md`.
8. **Review documents and claim ledgers:** Claim ledgers follow `rl_paper_harmonization_and_provenance_discipline.md`. Exclude `publication_review_*.md`, `review_validation_*.json`, review swarm dossiers, and audit receipts from the deposit.
