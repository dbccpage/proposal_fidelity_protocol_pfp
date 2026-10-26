# Canonical intelligence storage and development migration v1

**Default:** current writers use `_ic`; no opt-in activation gate.
**Scope:** repository development-data cutover with portable historical byte binding.
**AuthorityEffect:** None.

The user confirmed this repository is development work and directed all current use to `_ic`. The [decision](../../omega_engine_product_planning_office/plans/decisions/adr_20261010_oewas_intelligence_migration.md), [OEWAS007](../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md) and [OEWAS009](../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oewoland_plan.md) replace the earlier default-legacy/opt-in design. Full future-estate automation or native admission is not claimed. The [aggregate records](../receipts/oewas007_20261010/) and [development cutover records](../../receipts/oewas007_20261010/) own exact implemented source, binary and relocated-file scope.

## Defaults and custody

`intelligence_path(repo_root, legacy_relative)` maps current defaults to canonical agency paths even without checkout-local migration metadata. Present malformed metadata refuses. Whole Woland bundles use `_ic/darpa/woland`; OEOS control/packets remain distinct under ODNI; harvest remains together under NARA. Unknown safe namespaces use deterministic NARA legacy containment, not actor admission. `OMEGA_INTELLIGENCE_ROOT` still denotes a repository root.

The active writer lock is `_ic/odni/migration/checkout-writer.lock`. The old legacy lock, if inventoried, is historical payload at `_ic/odni/oeos_control/checkout-writer.lock`. Updated development workers use the canonical coordination domain. Stop the actual development writers before taking a consistent migration snapshot; continuing old-worker lock compatibility is not part of this cutover.

The real migration port is `IcMigration`: `plan`, `apply` and pinned historical resolution. These copy/verify/resume operations publish checked migration metadata but do not enable canonical defaults. A plan or copy alone does not claim the repository's tracked files were relocated; the development ledger and exact Git-blob crosswalk establish that scope.

Portable historical binding is `_ic/odni/migrations/oewas007/receipt.json` plus `inventory.json`. Exact original snapshots are `_ic/nara/historical/oewas007/<legacy suffix>`. Current canonical databases/journals may change; the reader verifies the requested original pin and falls back to its independently bound snapshot. Missing/checksum-mismatched evidence, a wrong explicit caller inventory pin or unavailable matching bytes refuses; the metadata is not independent cryptographic source authority. The portable binding is checkout-independent; absolute-root checkout-local activation/inventory/state under singular `migration` is ignored and must not be staged as universal metadata.

## Snapshot prerequisites and command environment

Use the reviewed development checkout, exact Git HEAD/origin and a separate external frozen-inventory path. Stop OEOS/Woland/woland/SymbolGame, collection/digestion/harvest/pharmacy and other identified writers while inventory/copy runs. The cooperative lease covers only participating OEOS mutations; `--quiesced` asserts actual stopped writers rather than stopping them. This is a consistent-snapshot procedure, not production permission.

Checkpoint and close all SQLite writers. WAL/SHM sidecars refuse rather than silently omitting live transactions. The example covers the existing collector only; other databases use their owner-specific stop/checkpoint/close procedure. Preserve encrypted CAS envelopes and protector identity. No database row, original receipt body or locator-derived ID is rewritten.

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

Compare `$reviewedHead` with the intended reviewed revision and retain it through plan/apply. Never refresh the pin after a refusal to manufacture a pass. No provider credentials are needed. The inventory command refuses an existing external inventory file.

For a known existing legacy collector database before cutover, checkpoint without creating a missing database:

```powershell
$dbPath = Join-Path $repoRoot '_intelligence/oeos/snapshots/intelligence_state.sqlite3'
& $uv @runtimeArgs python -X utf8 -c 'import sqlite3,sys; from pathlib import Path; p=Path(sys.argv[1]); c=sqlite3.connect(p.as_uri()+"?mode=rw",uri=True); r=c.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone(); c.close(); print(r); sys.exit(0 if r[0]==0 else 2)' $dbPath
```

After cutover that collector defaults under `_ic/odni/oeos`. Select the actual owning database, require a successful nonbusy checkpoint and close all connections. A missing database is not permission to create or repair one.

## Freeze, review, copy and resume

For a checkout whose legacy payload has not yet been moved:

```powershell
& $uv @runtimeArgs python -X utf8 -m omega_engine_operating_system.adapters.intelligence_custody.ic_migration plan --repo-root $repoRoot --repository dbccpage/the_symbol_game --head-sha $reviewedHead --inventory $inventoryPath --quiesced
$inventorySha = (Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
$inventorySha
& $uv @runtimeArgs python -X utf8 -m omega_engine_operating_system.adapters.intelligence_custody.ic_migration apply --repo-root $repoRoot --inventory $inventoryPath --inventory-sha256 $inventorySha --quiesced
```

Require exit 0 from each command and compare the printed inventory SHA with the independently computed digest before apply. Review every source/destination row, byte hash/size/kind, directory and existing destination baseline. The filesystem census does not classify tracked/ignored/untracked ownership. Separately review that Git scope. At the pinned base, 6,672 tracked legacy files provide context; use the actual ledger rather than assuming another checkout has that count.

The executor checks exact sources/destinations and lease identity, refuses changed or unreadable inventory, foreign pins, conflicts, unsafe/reparse/case paths, hard links/nonregular payloads and live SQLite sidecars, then publishes verified migration status. Resume uses the same frozen inventory/digest and rechecks real bytes. Do not overwrite the inventory or silently repin changed sources. A successful later idempotency report is not a fresh audit of mutable runtime output. Process interruption/reopen controls do not establish power-loss safety.

These copy/resume commands preserve source bytes. The PR's authorized tracked relocation and historical snapshot publication are additionally bound by `receipts/oewas007_20261010/development_cutover.json`, its inventory and source/canonical/snapshot Git-blob crosswalk. Review that actual result, not merely ACTIVATED wording or an empty directory walk. Canonical defaults do not wait for this marker; keep development writers stopped while the existing data snapshot is being relocated so they do not race the frozen baseline.

## Read a pinned historical file

Select a real original locator and its exact SHA-256 from the portable inventory or explicit local frozen inventory. Historical resolution validates source revision and requested bytes; it never substitutes a new current hash for an unavailable old one. It uses an available matching original/canonical copy, otherwise the verified immutable snapshot. Different-checkout reads must not depend on the old build worktree's absolute root.

The same `IcMigration.resolve_historical(origin, inventory_digest=..., sha256=...)` port reads checkout-local or portable bound history. For the portable CLI path, independently pin its actual inventory and substitute real row values:

```powershell
$inventoryPath = Join-Path $repoRoot '_ic/odni/migrations/oewas007/inventory.json'
$inventorySha = (Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
$origin = '_intelligence/_woland/runs/REPLACE_WITH_INVENTORIED_TASK/receipt.json'
$originalSha = 'REPLACE_WITH_THE_INVENTORY_ROW_64_HEX_SHA256'
& $uv @runtimeArgs python -X utf8 -m omega_engine_operating_system.adapters.intelligence_custody.ic_migration resolve --repo-root $repoRoot --inventory $inventoryPath --inventory-sha256 $inventorySha --origin $origin --sha256 $originalSha
```

The last command is a template. Compare `$inventorySha` with the independently retained intended cutover pin rather than trusting any substituted local receipt. `--inventory` remains required by CLI shape; resolve binds the explicit `--inventory-sha256` to loaded local/portable history. Capture binary stdout with a byte-preserving caller, not text-encoding PowerShell redirection. The [portable controls](../../omega_engine_operations/tests/packaging/test_ic_portable_history.py) exercise the actual reader in another checkout and after canonical mutation; exact executed source/cases are bound by the final aggregate evidence. `intelligence_source_locator` and `resolve_source_directory` retain historical collector identity/readback; new bundles receive canonical locators. Existing event/work IDs stay unchanged. Storage relocation does not admit antibodies or detectors.

## Verification and remaining work

Independently compare retained source pins with both canonical and original-snapshot file hashes and committed Git blobs. `_ic/** -text` plus retained nested attributes must preserve all evidence bytes through staging. Keep original receipt bodies, raw logs and earlier planning seals immutable. The exact development-data move is authorized; do not delete the historical snapshots or invent receipt rewrites as cleanup.

Run the updated producers and pair each actual writer with its reader. Native evidence binds the selected built source and binary SHA; Python-only tests do not establish native parity. Full future-estate migration automation, hostile-writer isolation, power-loss durability, universal duplicate-ingestion freedom and trusted native detector admission remain held. These research ceilings do not defer current canonical defaults or the repository cutover.

Focused test batches use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-o addopts='' -o filterwarnings=''` and a unique external `--basetemp`. Run at most three named files: governance schema files, `omega_engine_operations/tests/packaging/test_ic_migration_recovery_contract.py`, or `omega_engine_operations/tests/intelligence_digestion/test_ic_routed_producers.py` with their actual dependencies, and `omega_engine_operations/tests/packaging/test_ic_portable_history.py`. Exact executed commands/versions belong in receipts; this runbook is not an execution receipt.
