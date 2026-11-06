# Historical native run, 2026-09-28

These files are copies of records from the author run of 2026-09-28 EDT
(2026-09-29 UTC). The report bytes match the collection verification copy.
They are not a new run.

## What each file is

`report_second_revision_2026-09-28.md` is the retained native execution
record. Its Paper 004 paragraph records four Cargo targets:
`host_contract` (12 passed), `foundation_contract` (11), `invoke_contract`
(32), and `native_cli_intake` (9). Every command exited 0. The runner is
Rust 1.98.0 on Windows (`x86_64-pc-windows-msvc`). The reviewed commit is
`1c7092c3db2ab2fa65999cf2555aff7733b97b99`. The report says the
`core_symbol_game` crate source at that commit matches the code baseline
`52cb5457f6c485ba548cfd292f6012a941ed22cf`. The crate tree at both commits is
`75d77aa5e1f30dfc102f00c8f7cb6159418dec63`. The recorded window is 2026-09-29
02:02 to 02:06 UTC (2026-09-28, 22:02 to 22:06 EDT).

`004_run_all_receipt.json` and `004_republication_gate_receipt.json` are the
package review pipeline from the same window. The run-all file uses schema
`core.swarm_self_review.v1`, review id `SWARM_REV_20260929_020350`,
timestamp `2026-09-29T02:03:50.845858+00:00`, and overall status PASS. Those
two files record package pytest, ruff, and a Lean stage. They do not name
the four Cargo targets. They are not the native command log.

The report says raw receipts lived at
`_intelligence/core_paper_reviews/pfp_loop_final2_20260929_020235/`. The
Paper 004 folder there contains these two JSON files. No Cargo standard
output or standard error log for the four targets was found there. Skipped
counts as a separate number, and executable digests for those four targets,
were not retained.

The report also covers Papers 001 to 011. Its links to `residuals.md` and
`report_first_revision_2026-09-28.md` point at the collection verification
directory. Those siblings were not copied.

The two JSON files contain absolute paths from the machine that ran the
pipeline, and stage wording from that pipeline. That wording is the
pipeline's own record. It is not adopted here as a new claim about this
paper.

The 2026-10-02 package-local receipt does not record a fresh run of these
native targets. A checksum of this directory does not turn the historical
counts into an October measurement.

This note assigns no authorization and changes no jurisdiction.
