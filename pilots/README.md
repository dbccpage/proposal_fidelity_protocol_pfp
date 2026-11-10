# Imported pilots under review

`anomalon_woland/` is the exact directory moved from
`anomalon/omega_engine_woland/tests/pilots/` on 2026-11-10 UTC.

The move preserved all 25,330 files (223,481,649 bytes), including 9,962 Git-tracked
files and 15,368 local ignored files. Every file's SHA-256 and every directory path
were verified after the move. The source directory was removed by the move.
The custody manifest is `dag/migrations/anomalon_pilots_move.json`, relative to
this repository's root. It pins source commit
`16f3247e4415f8301d722f41ef1443d5504ad084` and each tracked Git blob separately
from the exact local bytes.

These are historical pilot inputs, code, outputs and local artifacts, not newly
validated workflows. Their contents were not rewritten during relocation.
Legacy import paths, assumptions, model names, budgets and success claims remain
historical source assertions. No pilot was executed during the move.

The review records reusable mechanisms, existing canonical workflow owners,
stubs, repetitions, trivial examples and overly domain-specific tasks in
`dag/pilot_triage/catalog.json`. Its counts are authoritative as review proceeds.
An initial mechanism assessment does not imply that every historical transcript
or supporting file was substantively verified. No quality-based deletion has
occurred yet.

Anomalon deletion PR #1572 is merged at
`84102f4e5eb02ff64f4d91c21e4b7c4892d8b3b8`. Follow-up PR #1573 isolates the
default PFP demo runner from the removed catalog; other pilot-dependent consumers
remain a separate migration obligation. The destination import is still local.

Before culling, all 25,330 incoming files were preserved in an external recovery
ZIP and verified again against current bytes and the original custody hashes,
with zero drift. `dag/migrations/pilot_recovery_archive.json` records its path,
size and SHA-256. This archive preserves historical evidence while allowing
reviewed redundant or unusable pilot directories to be removed from this tree.

The frozen QM benchmark and its private answer key remain separate. Historical
pilot answer keys and expected outputs must never be mistaken for an independent
blind evaluation of that benchmark.
