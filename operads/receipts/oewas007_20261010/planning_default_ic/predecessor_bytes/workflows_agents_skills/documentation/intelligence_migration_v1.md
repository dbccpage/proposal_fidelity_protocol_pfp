# Intelligence migration v1 operator runbook

**Implementation:** bounded opt-in filesystem migration and activation-gated routing.
**Operational activation:** not performed by publishing this code or document.
**AuthorityEffect:** None.

The [decision record](../../product_planning_office/plans/decisions/adr_20261010_oewas_intelligence_migration.md), [OEWAS007](../../product_planning_office/plans/epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md) and [OEWAS009](../../product_planning_office/plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oeadversary_plan.md) distinguish source delivery, finite evidence and a live rollout. [Execution records](../receipts/oewas007_20261010/) bind the selected source, commands and binary evidence; `receipt.json` and `review.md` are the aggregate records. Do not infer all-producer/native parity from a selected fixture batch.

## Scope and prerequisites

The real port is `operating_system.adapters.intelligence_custody.ic_migration.IcMigration`; its CLI has `plan`, `apply` and `resolve` actions. `plan` freezes the current filesystem census, `apply` copies/verifies/resumes against its explicit digest, and `resolve` reads a historical file with the active inventory and original file pin. No action deletes, retires or rewrites original receipt bodies. Control data is `_ic/odni/migration`; legacy checkout locking stays at `_intelligence/_oeos/checkout-writer.lock`.

Use a reviewed deployed checkout, its exact Git HEAD and origin, sufficient free disk space for retained originals plus copied payloads, and a separate external directory for the frozen inventory. The executor permits dirty working bytes without repairing them, so independently classify unrelated dirty/tracked/untracked content before live rollout. Its filesystem inventory does not perform that Git ownership review.

Stop all actual writers first: OEOS daemon/control tasks, Adversary/adversary/SymbolGame producers, collection/digestion/harvest processes and any other writer identified in the source inventory. The cooperative OEOS lease excludes participating mutation tasks only. `--quiesced` records the operator assertion; it does not stop processes, prove their absence or sandbox a hostile concurrent writer. Do not use it as a substitute for stopping them.

Checkpoint and close every SQLite writer before inventory. WAL/SHM sidecars cause refusal rather than an incomplete database copy. The checkpoint example below covers the existing collector database only; other databases require their owning adapter's stop/checkpoint/close procedure. Preserve encrypted CAS envelopes and existing protector identity; copy parity does not provide a new user's decryption capability.

## Prepare the pinned command environment

Run PowerShell. These variables name existing user-workstation tools and a repository; `CORE_INTELLIGENCE_ROOT`, if used by producers, continues to mean a repository root. Select an external inventory path outside both `_intelligence` and `_ic`; the plan command refuses an existing inventory file.

```powershell
$repoRoot = (Resolve-Path -LiteralPath 'C:/Users/a343o/source/repos/the_symbol_game').Path
$reviewedHead = (& git -C $repoRoot rev-parse --verify HEAD).Trim()
$inventoryPath = 'C:/Users/a343o/ic-migration-review/inventory.json'
$uv = 'C:/Users/a343o/.local/bin/uv.exe'
$pythonRuntime = 'C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe'
$runtimeArgs = @('run', '--offline', '--no-project', '--python', $pythonRuntime,
                 '--with', 'pyyaml==6.0.3', '--with', 'pydantic==2.13.5')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $inventoryPath) | Out-Null
Set-Location -LiteralPath $repoRoot
```

Compare `$reviewedHead` with the intended reviewed deployed revision and retain it unchanged through plan/apply. The checkout lease checks exact HEAD and origin again; do not silently refresh the snapshot or inventory digest after a refusal. No provider credentials are needed for the migration executor.

After stopping collector writers, checkpoint the existing database through a connection that refuses a missing file:

```powershell
$dbPath = Join-Path $repoRoot '_intelligence/oeos/snapshots/intelligence_state.sqlite3'
& $uv @runtimeArgs python -X utf8 -c 'import sqlite3,sys; from pathlib import Path; p=Path(sys.argv[1]); c=sqlite3.connect(p.as_uri()+"?mode=rw",uri=True); r=c.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone(); c.close(); print(r); sys.exit(0 if r[0]==0 else 2)' $dbPath
```

A busy checkpoint or missing database is a refusal to investigate, not permission to create or repair one. Close all owning connections. The executor does not checkpoint or repair databases itself.

## Freeze and review the inventory

```powershell
& $uv @runtimeArgs python -X utf8 -m operating_system.adapters.intelligence_custody.ic_migration plan --repo-root $repoRoot --repository dbccpage/the_symbol_game --head-sha $reviewedHead --inventory $inventoryPath --quiesced
$inventorySha = (Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
$inventorySha
```

Require exit 0 before continuing. Retain the exact printed inventory digest and compare it with `$inventorySha`. Review every source/destination row, byte digest/size/file kind, directory and existing destination baseline. Whole Adversary bundles map to DARPA, OEOS control and packet custody remain distinct under ODNI, sealed harvest resources remain together under NARA, and unknown safe namespaces use deterministic NARA legacy containment. This map is not producer admission or a confidentiality classification.

The reviewed base contains 6,672 tracked legacy files and existing IC archive resources. That historical count is context, not a required count for another checkout. The actual frozen census and separate Git-blob rehearsal establish the selected checkout's scope. `_ic/** -text` and retained nested/source-specific attributes must preserve committed bytes; compare source/destination blobs before claiming tracked-evidence parity.

## Apply or resume the same inventory

```powershell
& $uv @runtimeArgs python -X utf8 -m operating_system.adapters.intelligence_custody.ic_migration apply --repo-root $repoRoot --inventory $inventoryPath --inventory-sha256 $inventorySha --quiesced
```

Require exit 0 and an ACTIVATED result. Before activation, the executor independently rechecks source inventory, existing destination baseline and every copied file. It refuses changed sources, foreign roots/pins, conflicting destinations, unsafe or reparse-backed paths, case collisions, nonregular/hard-linked files and live SQLite sidecars. PLANNED/COPIED/VERIFIED records do not switch defaults; only validated activation does. Malformed matching-digest inventory cannot activate a route.

If interrupted before activation, keep writers stopped and retain the same external inventory/digest. Run the same apply command after investigating the failure. Resume rechecks source and copied bytes and does not silently repin. A changed source requires restoring the reviewed bytes or a separately reviewed new transition; never overwrite the frozen inventory to manufacture a pass. Originals remain available. These process-level copy semantics do not establish power-loss durability.

After activation, an idempotent apply reports the existing matching activation without recopying. New runtime outputs are permitted, so this report is not a fresh full-estate byte audit. Keep the exact activation and inventory bytes in the rollout evidence, together with independently checked retained-original and destination hashes and the operator's actual writer-quiescence/checkpoint record.

## Read a pinned historical file

Select a real original locator and its SHA-256 from the frozen inventory. Do not substitute a current file's hash for a missing historical pin. The resolve action requires the inventory argument for CLI compatibility and uses the explicitly pinned active inventory; its stdout is the exact recovered payload.

```powershell
$origin = '_intelligence/_adversary/runs/REPLACE_WITH_INVENTORIED_TASK/receipt.json'
$originalSha = 'REPLACE_WITH_THE_INVENTORY_ROW_64_HEX_SHA256'
& $uv @runtimeArgs python -X utf8 -m operating_system.adapters.intelligence_custody.ic_migration resolve --repo-root $repoRoot --inventory $inventoryPath --inventory-sha256 $inventorySha --origin $origin --sha256 $originalSha
```

The command above is a template: replace both row values before use. Binary output must be captured as bytes by a byte-preserving caller, not through a text-encoding PowerShell redirection. The port prefers retained originals and verifies their bytes; when the original is absent it reads the inventoried destination and verifies the same hash and size. Missing mappings, wrong pins or tampering refuse. This mechanism does not rewrite older receipt paths or SQLite event/work IDs.

Historical directory identity is separately checked by `intelligence_source_locator` and `resolve_source_directory`: inventoried relocated bundles retain their original collector locator only when their complete bytes match. New canonical bundles use new canonical locators. Selected integration tests exercise existing collector idempotency and reader recovery; storage migration does not change antibody or detector admission.

## Post-activation ownership and held work

Resume only the reviewed producer versions and pair each real writer with its real reader. A stale native executable can still have a legacy default; the native handoff must bind selected host SHA and source snapshot. Explicit caller-supplied paths retain their established contracts. Do not claim all-producer parity until the remaining caller inventory and failure paths have evidence.

There is no automatic rollback, retirement, cleanup or deletion command. Removing activation metadata after new writes could split old/new state; do not improvise that recovery. Retained originals provide custody, while a later operational reversal needs an explicit reconciliation of post-activation writes. Full OEWAS007/009 scope stays RESEARCH_HOLD until live operator activation, historical-readback coverage and remaining native/admission obligations are independently evidenced.

For focused verification, use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-o addopts='' -o filterwarnings=''` and a unique writable external `--basetemp`. Run at most three named files per batch: the governance schema files, `operations/tests/packaging/test_ic_migration_recovery_contract.py`, or `operations/tests/intelligence_digestion/test_ic_routed_producers.py` with their appropriate dependencies. Exact executed commands and versions belong in the receipts; this runbook is not an execution receipt.
