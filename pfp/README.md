# Proposal Fidelity Protocol and Symbol Game

AuthorityEffect: None.

This folder holds the symbol-game Python package. If you are new, do not
start here.

## Door 1 — what is this

Read the plain-language route:

[PFP and the Symbol Game learning route](../education/documentation/004_oepfp/README.md)

## Door 2 — verify the math

Read the paper register, in the order it already gives:

[Paper 001: S(n) and MSS-N](../atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/001_sn_mssn/README.md)

## Internal note

`CONTEXT.md` in this directory is the internal engineering definition and
is not the newcomer entry.

## What this page is not

It does not restate `CONTEXT.md`. It does not replace either door above.

## Native migration

The native host supports MCP directly with `core_symbol_game --mcp`.
See the [complete file map and migration roadmap](documentation/rust_migration/README.md)
and [executed validation](documentation/rust_migration/validation.md). Full Python
retirement remains open at the documented lifecycle and custody boundaries.

## Runtime ownership

Follow the [ordered migration and integration plan](documentation/pfp_migration_and_integration_plan.md)
for the remaining consumer cutover, local test waves and live-run exit gates.

`pfp` is the combined application. Shared prompt assembly, bounded
stage orchestration, provider/budget adapters, calculation/workpad contracts and
frozen-runtime replay belong to its domain, use-case and infrastructure layers.

| Responsibility | Canonical home |
| --- | --- |
| Exact calculation and certificate agreement | `domain/contracts/pfp_calculations.py` |
| Typed calculation/workpad output schemas | `use_cases/pfp_calculation_contracts.py` |
| Saved-source replay | `infrastructure/adapters/pfp_frozen_replay.py` |
| Task/dimension file catalogs | `infrastructure/catalogs/` |
| Normal-form executable code | `infrastructure/normal_forms/` |
| Normal-form YAML, SQL and JSON resources | `infrastructure/yaml/normal_forms/` |
| Named lesson/pilot dispatchers | `infrastructure/pilot_runners/` |
| Current braid tournament | `infrastructure/braid_tournament.py`; [bounded execution guide](documentation/braid_tournament.md) |
| Current graph retraction benchmark | `infrastructure/retraction_benchmark.py`; [conditions, commands and replay](../education/documentation/004_oepfp/docs/17_runtime_ownership_and_replay.md#current-paper-008-graph-benchmark) |
| Finite signed-graph workbench checker | `infrastructure/adapters/finite_gauge/`; [commands and scope](../education/documentation/004_oepfp/docs/17_runtime_ownership_and_replay.md#finite-signed-graph-workbench) |
| Relational spacetime research and independent judges | `../adversary/tests/pilots/relational_spacetime/` |
| Challenge compositions and packet audits | `../adversary/tests/pilots/challenge_suite/`, `../adversary/tests/pilots/judge_packet_audit/` |

Education retains teaching documents and papers. Remaining pilot recipes,
history and fixtures live under `adversary/tests/pilots`; `demo_004`
and pilots 0000000-0000005 remain under `pfp/tests`.

Paper numbers and recorded pilot IDs express provenance. They do not define
application packages. Research judges stay beside their experiments; reusable
contracts live in the engine. Python code does not live beneath the YAML assets.

The [type inventory](type_register/README.md) records unresolved semantic overlaps.
The [ownership and replay guide](../education/documentation/004_oepfp/docs/17_runtime_ownership_and_replay.md)
records evidence, version roles and the remaining lesson/dossier contract mismatch.

## v1.1RC architectural review

The [OEPFP v1.1RC specification](documentation/oepfp_v1_1_rc_specification.md)
contains the curriculum, pilot, Adversary and antibody audit, typed operad/DPO/quantum
contracts, and migration roadmap. Its
[execution receipt](documentation/oepfp_v1_1_rc_evidence/execution_receipt.json)
separates the focused reference checks from source-only estate evidence and
existing governance failures. The delivered models validate metadata; full
runtime migration and the stated research obligations remain open.
