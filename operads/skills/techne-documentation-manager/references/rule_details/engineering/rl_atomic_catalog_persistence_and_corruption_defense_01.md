# Detailed definition: Atomic Catalog Persistence (1)

**AuthorityEffect:** None.

Parent: [Atomic Catalog Persistence](../../../../../rules/engineering/rl_atomic_catalog_persistence_and_corruption_defense.md). Load for the matching predicate, not every task.

# Engineering Rule: Atomic Catalog Persistence and Corruption Defense (`RL_ENG_CATALOG_001`)

**AuthorityEffect:** None.

## Mandate

All persistent catalogs, state indices, and antibody repositories must implement corruption defense and atomic persistence to prevent data loss.

## Invariants

1. **Fail-Closed Loading:** Corrupted or unreadable JSON files must raise explicit fatal errors (such as `ValueError` or `CorruptCatalogError`). Silently swallowing decode errors and resetting internal state to `{}` is strictly prohibited.
2. **Atomic Replacement:** Updates to persistent catalogs must write to a temporary file (`.tmp`) and atomically rename (`replace`) onto the target path.
3. **Rolling Backup:** Prior to replacing the canonical catalog file, existing on-disk state must be preserved in a rolling backup (`.bak`).
