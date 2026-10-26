# OEWAS007 decision: canonical development storage with historical byte custody

**Status:** `IMPLEMENTED_BOUNDED`; remaining full epic automation/admission scope is `RESEARCH_HOLD`.
**Base:** `4d207641277ef3d3af16e11aafb411ada1ee10ed`.
**AuthorityEffect:** None.

The user explicitly directed that all current use switch to `_ic` and confirmed this is development work with no production deployment. This decision supersedes the earlier opt-in/default-legacy design. [OEWAS007](../epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md) owns the default and repository data transition; [OEWAS009](../epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oewoland_plan.md) owns its real producer/reader integration. Full research obligations do not postpone the authorized development cutover. Earlier sealed decisions, receipts and input bytes are retained in additive planning custody records.

## Decision and existing ownership

Reuse `AgencyCode`, the canonical YAML and `IntelligenceCommunity`; create no second agency registry. The [route adapter](../../../omega_engine_operating_system/adapters/intelligence_custody/ic_routing.py) and [migration executor](../../../omega_engine_operating_system/adapters/intelligence_custody/ic_migration.py) own one deterministic versioned relation. Current default writers choose canonical `_ic` paths without a migration marker. If a checkout-local marker is present, malformed binding refuses; its absence does not restore a legacy writer default. Migration metadata binds historical custody, not execution authority.

Active coordination uses `_ic/odni/migration/checkout-writer.lock`. The old `_intelligence/_oeos/checkout-writer.lock`, if inventoried, is ordinary retained payload at `_ic/odni/oeos_control/checkout-writer.lock`. It is no longer the active coordination anchor. Current workers use the canonical lock/state domain after development quiescence; no continuing old-worker compatibility is claimed. The repository-root resolver retains its established meaning, including linked-worktree resolution and `OMEGA_INTELLIGENCE_ROOT` as a repository-root override.

| Legacy namespace | Canonical destination | Containment decision |
| --- | --- | --- |
| `_intelligence/_woland` | `_ic/darpa/woland` | Keep complete bout bundles and sibling journals together. Current canon explicitly names Woland bouts in DARPA's mission. |
| `_intelligence/_oeos` | `_ic/odni/oeos_control` | Preserve former OEOS control payload, distinct from current migration lock/control and packet custody. |
| `_intelligence/oeos` | `_ic/odni/oeos` | Preserve the complete packet/collector resource family and historical database rows. |
| `_intelligence/harvest` | `_ic/nara/harvest` | Keep vault, indexes and sealed resources together; the canon includes sealed harvest vaults under NARA. |
| `_intelligence/archive` | `_ic/nara/_archive` | Preserve historical structure and refuse conflicting destination bytes. |
| `_intelligence/research` | `_ic/darpa/research` | Preserve research namespace and receipt relationships. |
| `_intelligence/antibodies` | `_ic/cdc/antibodies` | Preserve existing pharmacy resource family and admission state. |
| Namespaces without another explicit route | `_ic/nara/legacy/<legacy namespace>` | Deterministic containment preserves the original namespace; it is not writer admission. |

Other explicit routes preserve `omega_paper_reviews` under INR; `code_reviews`, `coverage` and `documentation` under NRO; `omc_dags` under NGA; and `blackrod` under FBI. A complete Woland bundle is stored once under DARPA; agency placement does not create a confidentiality classification, actor license or detector admission. Consumers needing another view refer to the same stored bundle.

## Physical development cutover and portable history

The PR includes repository development-data relocation, not just path configuration. The exact source set, destination paths, file/Git digests and any conflict are recorded by `receipts/oewas007_20261010/development_cutover.json` and its inventory/Git-blob crosswalk in the [root execution directory](../../../receipts/oewas007_20261010/). At the pinned base, 6,672 tracked legacy files provide historical context; the final ledger determines this transition's actual scope. The disposable rehearsal is separate evidence and predates final guard refinements.

Two artifact families protect history. Canonical copies serve current use. Exact original snapshots are also stored at `_ic/nara/historical/oewas007/<legacy suffix>`, because SQLite databases and runtime journals can change after cutover. Original paths can move without rewriting original receipt bodies or changing content-addressed identifiers. Both destination families must match the original file hashes and committed Git blobs.

The portable historical pair `_ic/odni/migrations/oewas007/receipt.json` and `inventory.json` binds the frozen inventory, original source revision, exact file size/hash and original-to-canonical/snapshot relation. This plural `migrations` namespace is distinct from checkout-local singular `_ic/odni/migration`. Portable reads must work in another checkout without comparing that checkout to the build worktree's absolute root. Checkout-local activation/inventory/state remains ignored. It must not be committed as universal tracked metadata.

Historical resolution validates an available original or unchanged canonical copy against its requested original pin, then uses the bound original snapshot when current bytes changed or moved. Missing/malformed or checksum-mismatched maps, wrong explicit caller pins, tampered snapshots or unavailable matching bytes refuse. The receipt cross-checks its inventory source identity; it is not an independent cryptographic provenance authority. A newer journal is never silently substituted for unavailable older evidence. Git source revisions are custody anchors, not permission to accept arbitrary current paths.

Root `_ic/** -text` and retained nested attributes preserve exact historical bytes through Git staging. Independent committed-blob comparison is required for canonical and snapshot families. Filesystem hashing alone does not establish committed-byte parity. Earlier planning seals are preserved with explicit predecessor snapshots rather than overwritten to manufacture a pass.

## Bounded migration safety

The executor inventories real files with source/destination path, digest, size and regular-file kind, plus existing destination baseline. It does not classify tracked/ignored/untracked ownership; the separate development ledger does that scope review. It refuses unsafe/case-colliding/reparse/hard-linked/nonregular payloads, unreadable subtrees, stale or conflicting bytes and SQLite WAL/SHM sidecars. Copy/resume uses the same frozen source and destination identity. Migration publication follows complete verification and has no later fallible journal update. This publication records successful copying; canonical routing is already the default.

Stop the actual development writers before inventory/copying and close/checkpoint SQLite owners. The real cooperative OEOS lease excludes participating mutations only. `quiesced=True` records the caller's assertion rather than stopping processes or proving that arbitrary writers are absent. This prerequisite protects a consistent development snapshot; it is not a new production approval flow. Ordinary mutating tasks retain their existing checkout cleanliness contract, while the explicit migration claim permits inventoried dirty bytes without cleaning or repairing them.

`DurableIntelligenceCollector` event/work IDs and historical `source_locator` remain unchanged. Current canonical bundles receive canonical locators; migrated historical bundles use their bound old logical identity. Encrypted CAS envelopes and protector metadata move byte-for-byte; relocation grants no new decryption capability. No cross-user/machine portability claim follows from file parity.

## Integration, finite acceptance and dissent

Pair each current default writer with its actual reader. Woland persistence/runtime, SymbolGame recording, OEOS custody/control, collector/digestion discovery, harvest and pharmacy producers must use canonical paths. Native `omega_symbol_game/src/woland_host.rs` is an independent producer boundary and requires selected source/binary evidence. Caller-supplied custom paths retain established semantics unless separately changed. The governed receipt-output fence includes `_ic`; it remains a custody fence rather than admission.

**INVARIANT:** current defaults use `_ic` without a marker and old pins resolve to exact original bytes after relocation or mutable-journal changes. **BREAK:** no-marker legacy output, changed copied/snapshot bytes, foreign inventory, unreadable scan or interrupted copy. **WITNESS:** real producer/readback plus exact source/canonical/snapshot Git-blob crosswalk and refusal on unavailable historical bytes. **MUTATION:** bypass an actual default-route, digest, inventory or historical-snapshot guard, observe its behavioral control RED, restore exact bytes and observe GREEN.

Finite controls include canonical no-marker defaults, malformed-present-marker refusal, repeated migration/resume, real process interruption/reopen, stale source/conflicting destination, real junction/case/path controls, concurrent canonical lease exclusion, checkpointed SQLite reopen, unchanged event/work identity, portable read in a different checkout, changed current journal with intact original snapshot, snapshot tampering and original receipt replay. These do not establish power-loss durability, malicious-writer isolation, external exactly-once effects or native admission.

Koroviev's dissent remains: deterministic paths, a quiescence assertion and finite fixture success do not prove every future producer is correctly routed, eliminate duplicate ingestion or complete autonomous recovery. Full OEWAS007/009 automation/research and native-admission obligations stay `RESEARCH_HOLD`. This ceiling does not withhold the current authorized development cutover. Storage migration cannot promote a detector, issue a license witness or close immune enforcement.

The [runbook](../../../omega_engine_workflows_agents_skills/documentation/intelligence_migration_v1.md) supplies actual development plan/apply/resolve procedures. [Aggregate execution custody](../../../omega_engine_workflows_agents_skills/receipts/oewas007_20261010/) separates final source-matched controls from earlier scoped evidence. The [governance loader receipt](../../../omega_engine_workflows_agents_skills/receipts/oewas007_20261010/koroviev/receipt.json) binds schema ingress only.
