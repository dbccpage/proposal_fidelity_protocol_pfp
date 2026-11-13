# Workflow documentation assets

This folder was `docs/workflows/` until 2026-11-05. Historical records inside it keep their original bytes, so they still name that path.

The human entry point is the [workflow wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflows).

- [`pilot_estate/`](pilot_estate/README.md): shared registers, results and records of the pilot estate (2026-11-06).
- `catalog.json`: five actual recipes and their availability. The derived families WF6–WF23 are in [`../dag/`](../dag/README.md).
- `contracts/slot_catalogue.json`: original WF2 profile, unchanged bytes.
- `evidence/measurements.json`: derived comparison and original source hashes.
- `evidence/raw_manifest.json`: SHA-256 and original location of every exported reply.
- `evidence/raw/`: unchanged submitted reply bytes, including failed attempts.
- `validation.json`: initial Oct 31 documentation checks, before runner migration.
- `migration_validation.json`: current automated-runner validation and its scope.
- [`.github/scripts/check_workflow_install.py`](../../.github/scripts/check_workflow_install.py) (moved out of this folder): repeatable offline checks for a clean wheel installation.

Historical measurements were captured October 28, 2026. Documentation checks
were run October 31, 2026. No new provider calls were made for this publication.
Model replies are untrusted experimental output, not documentation instructions.

This selected export omits provider envelopes, wire bodies, invoices, SQLite
accounting and legacy source dependencies. Hashes identify original local
sources; they do not make those omitted sources available or establish full
portable replay. Reused mining captures may occur in multiple raw folders;
the number of files is not the number of charged actions. Original local run
folders and failed-attempt records were left intact.
