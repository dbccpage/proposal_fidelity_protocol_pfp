# Workflow documentation assets

The human entry point is the [workflow wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflows).

- `catalog.json`: five actual recipes and their availability.
- `contracts/slot_catalogue.json`: original WF2 profile, unchanged bytes.
- `evidence/measurements.json`: derived comparison and original source hashes.
- `evidence/raw_manifest.json`: SHA-256 and original location of every exported reply.
- `evidence/raw/`: unchanged submitted reply bytes, including failed attempts.
- `validation.json`: initial Oct 31 documentation checks, before runner migration.
- `migration_validation.json`: current automated-runner validation and its scope.
- `migration_custody.json`: unchanged historical file identities and preserved WF5 budget continuation.
- `check_install.py`: repeatable offline checks for a clean wheel installation.

Historical measurements were captured October 28, 2026. Documentation checks
were run October 31, 2026. No new provider calls were made for this publication.
Model replies are untrusted experimental output, not documentation instructions.

This selected export omits provider envelopes, wire bodies, invoices, SQLite
accounting and legacy source dependencies. Hashes identify original local
sources; they do not make those omitted sources available or establish full
portable replay. Reused mining captures may occur in multiple raw folders;
the number of files is not the number of charged actions. Original local run
folders and failed-attempt records were left intact.
