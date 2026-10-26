# Epic: Typed intelligence routes and recoverable inventory-bound migration

**Epic ID:** `EPIC-OE-OEWAS-007`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Implementation slice:** `IMPLEMENTED_BOUNDED`; operator estate activation remains held.
**Reviewed:** 2026-10-10
**Owner:** OEOS custody/lease owners; governance canon owner; OEWAS009 producer/reader integration owners.

The [migration decision](../../decisions/adr_20261010_oewas_intelligence_migration.md) and [operator runbook](../../../../omega_engine_workflows_agents_skills/documentation/intelligence_migration_v1.md) govern this increment. Source delivery and finite fixture verification do not activate the user's live estate. Original receipts, earlier planning reviews and historical bytes retain their custody.

## Source inspection and delivered bounded behavior

Reuse [governance canon](../../../../omega_engine_governance/_types/intelligence_community.yaml), [AgencyCode/IntelligenceCommunity](../../../../omega_engine_governance/domain/intelligence_community.py) and the [public dictionary loader](../../../../omega_engine_governance/_types/types.py). The dictionary loader now delegates to the canonical model loader instead of independently coercing list-of-pairs or silently selecting duplicate declarations. The model's nested dictionary remains mutable; neither API is a filesystem capability or actor-admission boundary. Its separate [schema evidence](../../../../omega_engine_workflows_agents_skills/receipts/oewas007_20261010/koroviev/receipt.json) records genuine RED/minimal GREEN, 58 final focused controls and an actual bypass mutation with exact restoration.

The new [IcMigration executor](../../../../omega_engine_operating_system/adapters/intelligence_custody/ic_migration.py) implements `plan(repository, head_sha, quiesced=True)`, `apply(inventory, expected_digest=..., quiesced=True)` and `resolve_historical(origin, inventory_digest=..., sha256=...)`. It uses the real [CheckoutLeaseManager](../../../../omega_engine_operating_system/infrastructure/checkout_lease.py), a frozen inventory, copied destination bytes and independent SHA-256/size comparisons. States PLANNED, COPIED and VERIFIED precede atomic activation publication. An interrupted apply resumes against the same inventory and refuses changed sources, conflicting destinations or a different stored inventory. No retirement, deletion, receipt rewrite or automatic quiescing is implemented.

The [route adapter](../../../../omega_engine_operating_system/adapters/intelligence_custody/ic_routing.py) preserves legacy defaults until a valid activation exists. Activation binds repository root, source revision and exact canonical inventory bytes; malformed activation or inventory refuses instead of silently selecting a fallback. Its named sorted ASCII JSON profile is not RFC 8785. Control data resides inside `_ic/odni/migration`. Existing [OEOS composition](../../../../omega_engine_operating_system/composition.py) consumes the route, while the lock stays at `_intelligence/_oeos/checkout-writer.lock` to preserve a shared coordination domain with older cooperating writers.

Whole Woland bundles route to `_ic/darpa/woland`; OEOS control and packet namespaces remain distinct at `_ic/odni/oeos_control` and `_ic/odni/oeos`; harvest stays together under `_ic/nara/harvest`; archives map to `_ic/nara/_archive`. Other explicit routes and deterministic NARA legacy fallback are recorded in the ADR. Fallback is containment, not writer authorization. Complete bundles keep their internal files and receipt hashes; no new bundle schema is inferred from directory relocation.

## Bounded contract and dependency decisions

The filesystem inventory records source/destination paths, byte digest, size and regular-file kind plus existing destination baseline. It refuses unsafe relative paths, case-fold collisions, symlinks/reparse paths, hard-linked/nonregular payloads and SQLite WAL/SHM sidecars. It does not classify Git-tracked versus ignored/untracked bytes. The separate disposable estate rehearsal and committed-blob comparisons must establish that custody claim; filesystem hashing alone cannot do so.

`apply` requires an exact inventory digest and the existing repository/HEAD lease checks. The migration claim permits dirty working bytes and never cleans or repairs them; ordinary mutating task claims retain their clean-checkout requirement. `quiesced=True` is an explicit operator assertion that all direct producers have stopped and SQLite writers have checkpointed and closed. The lease excludes only cooperative OEOS writers. It cannot prove all estate writers stopped or prevent a hostile concurrent path replacement. Live shared-checkout activation remains an operator-owned operation with a reviewed frozen inventory.

`resolve_historical` binds the explicit active inventory pin, original locator and expected file digest, preferring retained originals and verifying whichever copy it reads. Missing or tampered bytes refuse. `intelligence_source_locator` preserves historical collector identities only for byte-verified inventoried directories; new canonical outputs receive canonical locators. `resolve_source_directory` supplies the missing-original directory reader seam. Existing SQLite event/work payloads and locator-derived IDs are retained. OEWAS009 owns their actual writer/readback integration and native producer closure.

Repository-root resolution keeps its established meaning: linked worktrees target the main checkout, and `OMEGA_INTELLIGENCE_ROOT` names a repository root. Explicit caller output paths retain their existing contracts. `_ic/** -text` destination attributes preserve historical bytes through Git staging; retain source-specific/nested attributes and compare destination blobs with pinned source blobs before claiming tracked-byte parity.

## Obstruction review and TDD test plan

**Independent oracle:** original file bytes and independently computed SHA-256/size; unchanged old receipt bodies and locator-derived IDs; no activation file before complete verification; actual public writer path and reader result after activation. The [execution evidence directory](../../../../omega_engine_workflows_agents_skills/receipts/oewas007_20261010/) contains the aggregate `receipt.json`/`review.md` and specialist records as they are sealed. Final claims must use the source and test versions bound there; a test's presence alone is not execution evidence.

1. **RED → minimal GREEN:** the public dictionary loader must refuse a pair-list inner container. This missing guard was observed and repaired through canonical-loader reuse. Valid metadata, fresh dictionaries, existing merge semantics, duplicate/escaped keys and deliberate malformed-root refusal are bounded controls. The real delegation bypass made the controls RED, followed by exact source restoration and GREEN; the sealed schema receipt owns the counts and commands.
2. **RED → minimal GREEN:** [test_ic_migration_recovery_contract.py](../../../../omega_engine_operations/tests/packaging/test_ic_migration_recovery_contract.py) exercises the real executor and real temporary Git checkout/lease. Inventory and apply retain originals, copy exact CRLF/binary bytes, activate only after verification, and replay an original receipt after its source is absent. Interruption after one copy, changed-source resume, conflicting/foreign pins, destination baseline changes, unsafe/case-colliding paths, a real junction and live SQLite sidecars are negative controls. The matching-digest malformed-inventory control binds the strict activation-reader repair. Recovery interruption here is injected at the real copy seam; it is not a process-crash or power-loss proof.
3. **RED → minimal GREEN:** actual producer tests under [test_ic_routed_producers.py](../../../../omega_engine_operations/tests/intelligence_digestion/test_ic_routed_producers.py) must pair route selection with consumer readback and unchanged identity. Historical database reopening, duplicate completion notification and missing-source resolution must preserve existing event/work IDs. Native host evidence must identify its actual built source and selected binary. Refactor only with these real boundaries intact; do not replace missing native coverage with a test-local writer.

| Theoretical minimum | Obligation and mutation target |
| --- | --- |
| INVARIANT | Only exact frozen source/destination bytes activate; legacy identities and receipt bodies remain bound. |
| BREAK | Change one source/destination byte, substitute foreign or malformed inventory, or interrupt before activation. |
| WITNESS | Actual port refuses without activation; valid copy/readback yields original bytes and existing identities. |
| MUTATION | The actual public-loader delegation, executor `_verify_source`/`_verify_destinations`, `apply` digest/quiescence checks and route activation guards are production targets. Only a sealed actual mutation record counts as executed; bypass must make its behavioral control RED and exact restoration GREEN. |

Landau controls are complete canon/valid copy (1), malformed roots and stale bytes (2), foreign inventory/transplanted binding (3), interrupted recovery/competing legacy lease (4), and real production bypass/restore (5). Schema success is not zero-loss rollout or all-producer parity.

Run one to three named Python files per batch using the cached isolated interpreter/dependencies and external unique basetemp described in the runbook. The explicitly invoked [ext-mattpocock-tdd skill](../../../../.agents/skills/ext-mattpocock-tdd/SKILL.md) remains a minimal Code-to-Code stub; these concrete RED/GREEN/refactor methods are local acceptance requirements. Already-GREEN behavior is reuse. No second framework, provider call or broad native build is required for schema/executor fixtures.

Four-stage route: DOC_MGR/Yaroslava pin bytes/links; DEV_MGR/Hella/Azazello bind public ports; QA_MGR/Soviet Inspector run bounded batches and retain failures; BUILDER checks the theoretical minimum before Woland records the bounded outcome. Koroviev's dissent remains visible. SoftwareQaReceiptV1 requires its actual schema/writer; this plan is not one.

## Claim discipline and retained residuals

- Supports: implemented opt-in inventory/copy/verify/resume/activation/historical-resolution ports, canonical-loader reuse and selected producer integration, with exact evidence scope owned by sealed receipts.
- Does not support: live-estate cutover, automatic retirement/deletion, cryptographic actor admission, malicious-writer isolation, power-loss recovery, zero duplicate ingestion or complete estate/native producer parity.
- Narrowest claim: this checkout delivers a bounded transition that retains original bytes and gates new defaults on validated activation metadata; operational activation is separate.
- Next evidence: review the disposable full-estate inventory and Git-blob rehearsal, reconcile remaining producer/reader coverage, pin native binary/source evidence, then obtain the operator's actual stopped-writers/checkpointed-database activation receipt. Full scope stays RESEARCH_HOLD until that evidence exists.

The [shared ownership decision](../../decisions/adr_20261010_epic_integration_ownership.md) retains OEOS custody ownership and OEWAS009 integration responsibility. Historical planning receipts are preserved through explicitly pinned successor copies; their earlier proposed-test wording remains historical.
