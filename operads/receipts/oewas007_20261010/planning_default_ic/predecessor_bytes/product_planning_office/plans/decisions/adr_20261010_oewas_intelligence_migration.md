# OEWAS007 intelligence migration: custody before activation

**Status:** `IMPLEMENTED_BOUNDED`; live operator activation and full epic scope remain `RESEARCH_HOLD`.
**Base:** `4d207641277ef3d3af16e11aafb411ada1ee10ed`.
**AuthorityEffect:** None.

This decision defines the bounded transition owned by [OEWAS007](../epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md) and the storage-routing dependency of [OEWAS009](../epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oeadversary_plan.md). The bounded source ports are implemented; exact execution claims are limited to the linked sealed evidence. This document does not activate a checkout or certify a live estate migration. Historical receipts and prior planning decisions retain their recorded versions.

## Decision and ownership

Reuse `AgencyCode`, the existing canonical YAML and `IntelligenceCommunity`; introduce no second agency registry. The existing [route adapter](../../../operating_system/adapters/intelligence_custody/ic_routing.py) and [migration executor](../../../operating_system/adapters/intelligence_custody/ic_migration.py) own the source/destination relation through one versioned deterministic mapping and a frozen inventory. The control directory is `_ic/odni/migration`, inside the canonical agency partition. The existing repository-root resolver keeps its meaning, including linked-worktree resolution to the main checkout and `CORE_INTELLIGENCE_ROOT` as a repository-root override.

Writer defaults remain under `_intelligence` until the selected checkout has a validated activation receipt. Migration is opt-in. Code deployment alone must not copy, retire, delete, or switch the user's shared live estate. The receipt attests a checked inventory and activation state; it supplies no actor admission, signature trust, security classification, or publication authority.

| Legacy namespace | Canonical destination | Containment decision |
| --- | --- | --- |
| `_intelligence/_adversary` | `_ic/darpa/adversary` | Keep each complete bout bundle and its sibling producer journals together. Current canon explicitly names Adversary bouts in DARPA's mission. |
| `_intelligence/_oeos` | `_ic/odni/oeos_control` | OEOS control-state namespace stays distinct from packet/turn custody. The existing legacy checkout lock remains the coordination anchor. |
| `_intelligence/oeos` | `_ic/odni/oeos` | Preserve this complete namespace, including collector state, as one resource family. |
| `_intelligence/harvest` | `_ic/nara/harvest` | Keep vault, indexes and sealed harvest resources together; current NARA definition includes sealed harvest vaults. |
| `_intelligence/archive` | `_ic/nara/_archive` | Preserve source-relative historical structure and refuse conflicting existing destination bytes. |
| `_intelligence/research` | `_ic/darpa/research` | Preserve the existing research namespace and its receipt relationships. |
| `_intelligence/antibodies` | `_ic/cdc/antibodies` | Preserve the existing pharmacy resource family and admission state. |
| Namespaces without another explicit route | `_ic/nara/legacy/<legacy namespace>` | Deterministic containment fallback preserves the original namespace. It is not writer admission or a historical-only filter. |

Other explicit routes preserve `core_paper_reviews` under INR; `code_reviews`, `coverage` and `documentation` under NRO; `omc_dags` under NGA; and `blackrod` under FBI. The map accepts safe legacy locators and contains fallback namespaces under NARA; it does not implement a separate producer-identity authorization registry. Agency placement is a containment taxonomy, not a new definition of confidentiality or execution permission. A whole Adversary bundle is not divided into CIA, NSA and CDC copies. Consumers needing another agency's view refer to the single stored bundle. Existing receipt and content-addressed identifiers do not change merely because physical storage moves.

## Custody and transition constraints

At this base `_intelligence` includes 6,672 tracked files, alongside possible ignored or untracked live output. The implemented inventory is a filesystem census recording source path, destination path, exact byte digest, size and file kind; it does not classify Git-tracked, ignored or untracked files. Git ownership and committed-byte custody require a separate reviewed rehearsal/ledger before any tracked-file relocation. Existing `_ic/nara/_archive` content is retained. Source/destination traversal, case-fold collisions, symlinks and Windows reparse-backed paths must be refused at the actual copy/activation boundary. Unknown, missing, stale or conflicting inventory entries cannot count as verified copies.

Copy before activation, independently verify destination bytes, and retain original files throughout recovery. Resume must recheck frozen source and destination identity; an interrupted copy is not an activation receipt. No automatic retirement or deletion is part of this increment. A failure before activation publication leaves previous routing defaults in force. Activation publication is the routing commit point; a later ancillary failure must not be misreported as an unactivated checkout. Activation follows complete verification, and post-activation apply is an idempotency report rather than a fresh audit of new runtime writes.

Root `.gitattributes` defaults to LF normalization and contains legacy path-specific `-text` exceptions. Equivalent destination exceptions and nested `.gitattributes` resources must preserve evidence bytes before staging. Filesystem parity alone is insufficient for tracked artifacts: compare the committed destination blob with its pinned source blob as well. Historical receipt bodies, raw logs and their hashes stay unchanged.

The OEOS checkout lease protects only its cooperating mutating tasks. Keeping its original lock path avoids splitting old/new lock domains; it does not stop Adversary, the city, SymbolGame or arbitrary filesystem writers. Activation therefore requires an explicit all-writers-quiesced declaration plus the actual existing lease boundary. This declaration is an operator prerequisite, not a machine proof that every possible writer has stopped.

`DurableIntelligenceCollector` uses WAL-backed SQLite with FULL synchronous mode. Live database copying is refused: stop its writers and checkpoint WAL before freezing and copying database bytes. Preserve event/work rows and their historical `source_locator`; these locators participate in stable hashes and idempotency. Historical resolution maps old locations to verified bytes without editing the old event payloads. The cutover must also account for SQLite sidecars and other live journals; a copied main database file alone is not a successful migration.

Encrypted OEOS CAS envelopes are copied byte-for-byte with their existing metadata and digests. Moving storage grants no new protector capability. Decryption still depends on the configured current-user protector; no cross-machine or cross-user portability claim follows from file parity.

## Reader and producer integration

A source inventory must name real owners and pair each changed writer with its reader. The bounded integration includes Adversary persistence, SymbolGame run recording, durable collection and digestion discovery/readback. Native `core_symbol_game/src/adversary_host.rs` independently chooses a Adversary output path; Python default changes alone cannot close that native route. Explicit caller-supplied output locations retain their established contracts unless a separately reviewed boundary changes them.

Historical resolution requires a pinned source identity and a verified mapping. Missing historical bytes or a digest mismatch refuses; current working bytes must not silently substitute for an unavailable recorded version. The existing Level Engine historical Git resolver is a reusable custody pattern, not evidence that intelligence receipt paths already use it. Migration must supply and exercise its own actual reader seam.

OEWAS's governed receipt-output fence must include `_ic` before default activation, preserving the existing protection of `_intelligence`. An arbitrary CLI `--out` is not a typed agency writer. Rules, skills and examples describing legacy defaults must distinguish pre-activation compatibility from activated routing; historical documentation remains historical.

## Finite acceptance and dissent

The theoretical minimum is: **INVARIANT** frozen source bytes resolve to the same verified destination bytes and only complete verified inventories activate; **BREAK** change one source or destination byte, substitute a foreign manifest, or interrupt before activation; **WITNESS** real writer/readback plus explicit refusal and unchanged old receipt hashes; **MUTATION** bypass the actual digest or activation guard and observe the corresponding test fail, then restore exact source bytes.

Required controls use temporary real files and bounded real public ports: unchanged legacy defaults, opted-in canonical writer/readback, repeated activation/resume, interruption before activation, stale source, conflicting destination, missing/foreign mapping, case/reparse/path escape, concurrent legacy-lock exclusion, SQLite reopen with retained event/work identity, and historical receipt replay. Recovery tests do not establish power-loss safety or external exactly-once effects. Selected native tests must distinguish a freshly built source-matched host from an older available executable.

Defect Hunter's retained dissent is that path classification, an operator declaration, and a successful finite fixture do not establish estate-wide quiescence, zero duplicate ingestion, or complete native parity. Full OEWAS007 and OEWAS009 scopes remain `RESEARCH_HOLD` until their remaining writer inventory, historical readers, cutover/recovery evidence and independent native/admission obligations are satisfied. Storage success cannot promote a detector, issue a license witness, or close immune enforcement.

The [operator runbook](../../../workflows_agents_skills/documentation/intelligence_migration_v1.md) gives actual plan/apply/resolve commands and prerequisites. [Migration execution evidence](../../../workflows_agents_skills/receipts/oewas007_20261010/) retains aggregate `receipt.json`/`review.md` as sealed, with specialist source/command/negative-control custody. The [governance-loader receipt](../../../workflows_agents_skills/receipts/oewas007_20261010/defect_hunter/receipt.json) separately binds canonical dictionary ingress and does not execute migration.
