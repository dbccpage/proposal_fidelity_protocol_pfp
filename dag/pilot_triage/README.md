# Imported pilot triage

The original Anomalon corpus moved into `pilots/anomalon_woland/` with a SHA-256 custody manifest in `../migrations/anomalon_pilots_move.json`. Source-removal PR #1572 is merged. Incoming history is a separate scope from the original PFP inventory.

`catalog.json` combines the four numbered-pilot reports and the shared-owner reports. All 204 numbered pilots have an initial mechanism assessment. This is not a claim that every historical transcript, generated case or archived runtime was substantively read. Every report states its reading and execution limits.

The first retirement plan selects only the 131 reviewed stubs and seven trivial demonstrations. `retained_lessons.json` preserves their useful cautions, candidate mechanisms, workflow mappings and source references. These lessons are not executable adapters or successful benchmark results. Other verdicts remain separate consolidation work.

`retirement_plan.json` is frozen. `retirement_receipt.json` is authoritative for completed removals; a plan alone does not mean deletion happened. The receipt records a durable intent before each removal and a completed entry afterward. An interrupted receipt needs inspected recovery; the removal script deliberately refuses a blind rerun.

Every selected file was checked against both migration custody and the recovery ZIP before removal. The Windows preflight rejects changed/unknown files, directory drift, links and non-default NTFS data streams. The bounded independent review is in `retirement_review.json`; it does not establish power-loss durability or protection from simultaneous writers.

The recovery ZIP is outside this checkout. Its exact location and SHA-256 are in `../migrations/pilot_recovery_archive.json`. Keep that archive: the retired source files are not duplicated in this repository. Archive entries use paths such as `pilot_0000002/README.md`, and `_migration_manifest.json` preserves the original directory/file inventory. The archive is a recovery copy, not a new proof or benchmark dataset.

`retirement_custody.EvidenceStore` reads current files first, and reads missing retired files from the verified archive only when the removal receipt authorizes that exact source path. It refuses unexplained missing evidence, changed archives and changed retained lessons. `build_catalog.py` uses this reader to keep historical source pins checkable after removal.

To rebuild the catalog and evidence graphs, from the repository root:

```powershell
.venv\Scripts\python.exe -B -X utf8 dag\pilot_triage\build_catalog.py
.venv\Scripts\python.exe -B -X utf8 dag\reviews\build_coverage.py
.venv\Scripts\python.exe -B -X utf8 dag\build_dags.py
```

The graphs retain retired pilot assessment nodes with explicit deletion status and archive references. They do not count those nodes as new workflow families or as admitted executable compositions.
