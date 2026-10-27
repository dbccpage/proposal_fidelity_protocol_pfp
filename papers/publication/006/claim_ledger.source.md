# PFP VI claim ledger

Jeremy H. Carroll · 2026-09-28 · Version 1.1.0 · Author-review revision

Baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
The main manuscript gives commit-pinned source links. “Source-inspected”
records what was read, not a fresh execution count. Package tests are named as
`file::function`; repository tests outside this package are named by function
and file path. Current execution results belong to the dated review receipt.
Identifiers P6-01 to P6-15 keep their earlier meaning; P6-15 is corrected in
this revision, and P6-16 to P6-18 are new.

| ID | Claim | Evidence | Status and boundary |
| --- | --- | --- | --- |
| P6-01 | The production sink records ordered refusal entries with predecessor digests and a count/head header. | `pfp/infrastructure/persistence/cemetery_sink.py` | Source-inspected local storage |
| P6-02 | Restart verification checks entry shape, order, chain, count, and head. | Same source; `pfp/tests/test_cemetery_sink.py` | Finite positive and hostile cases; no universal parser proof |
| P6-03 | Removing a tail while preserving the original header is detectable. | `test_006_worked_example.py::test_removed_final_entry_is_rejected_with_original_header`; `test_cold_restart_tail_truncation_rejection` in the repository sink tests | Depends on the unchanged expected header; the package test needs the full repository |
| P6-04 | Rewriting both file and local header can preserve local self-consistency. | `test_006_worked_example.py::test_consistent_shorter_file_passes_locally_but_not_the_anchor`; paper §§5–6 | Threat-model limitation; the package test needs the full repository |
| P6-05 | A separately retained count/head compares the ordered normalized-entry snapshot, excluding raw-file and full-header identity. | `test_006_worked_example.py::test_section6_block_runs_as_printed`; `test_006_worked_example.py::test_numeric_and_string_reason_share_count_and_head`; `emit_tail_receipt` | Caller trust obligation; not automatic signed freshness |
| P6-06 | Physical writes replace the full serialized file through a temporary path. | `CemeterySink._write_file` | Logical append only; no lock or explicit fsync |
| P6-07 | Sorted JSON in this sink does not establish complete RFC 8785 compliance. | `_canonical_json_bytes` compared with RFC 8785 | Explicit standards boundary |
| P6-08 | Stored cochain and refusal fields are caller-supplied evidence, not sink-computed native results. | `record_refusal` signature and normalization | Storage integrity does not verify event truth |
| P6-09 | Invalid detector regex yields a typed refusal; a benign-panel match produces a kill-condition record. | `pfp/domain/immune/clonal_selection.py`; `test_kill_condition_refuses_an_invalid_pattern_without_raising` in the repository regression suite | Finite rule-maintenance contract |
| P6-10 | The self panel has 40 distinct base contents among 1,000 rows. | `test_canonical_self_panel_has_forty_distinct_base_contents` in the repository regression suite | Source-inspected corpus assertion; no 1,000-independent-example claim |
| P6-11 | The explicit toxicity threshold is inclusive at 1/5; the unlabelled-corpus score is 0 or 1. | `pfp/domain/immune/treg.py`; `test_treg_downgrades_at_exactly_tau`, `test_treg_keeps_a_detector_just_below_tau`, and `test_treg_prompt_corpus_toxicity_is_zero_or_one` in the repository regression suite | Exact policy arithmetic over supplied trigger labels |
| P6-12 | Affinity decay is invariant to batching of the same idle-run total at fixed tau. | `apply_half_life_decay`; `test_decay_does_not_depend_on_how_idle_runs_are_batched` in the repository regression suite | Finite implementation and elementary telescoping relation |
| P6-13 | Retention-to-detector admission needs replay, provenance, near misses, and scope. | Paper §§7–8 | Proposed integration method |
| P6-14 | Paper-local toy classes do not verify production integration. | `test_006_epistemic_immune.py::test_toy_chain_links_predecessor_digests`; `test_006_epistemic_immune.py::test_danger_signal_threshold`; the module defines its own classes | Educational illustration only |
| P6-15 | The retained catalog `_intelligence/_antibodies/pharmacy_catalog.json` holds 61 entries with 14 distinct `failure_class` values; 56 are marked `candidate` and 5 `active`. Every entry has `negative_fixture`, `positive_fixture`, and `evidence_sha256`; 49 entries carry placeholder fixtures. | The file at the baseline commit (Git blob `e4984047231091caca6e5b0b7810f20c705e4970`; SHA-256 `b95ce7c1338867cc680abffcc3f2fb9da634c7a7ec2f4c00e0d67391e91b4acb`); `test_006_catalog_file.py::test_catalog_entry_class_and_status_counts`; `test_006_catalog_file.py::test_catalog_fields_and_placeholder_fixtures`; paper §7.1 | Corrected in 1.1.0; counts describe the data file only, not reproduction, coverage, or effectiveness; the tests need the full repository with Git |
| P6-16 | Changing an entry payload while keeping its digest is rejected on reopen. | `test_006_worked_example.py::test_changed_payload_is_rejected_on_reopen`; `test_intermediate_bit_flip_tamper_detection` in the repository sink tests | Finite hostile case; the package test needs the full repository |
| P6-17 | The catalog does not record which bytes an `evidence_sha256` value covers. Both baseline harvesters hash short identifying strings, and 19 stored values are reproduced from a defect label joined with run and task identifiers found in retained run records. | `test_006_catalog_file.py::test_evidence_digests_hash_identifiers_not_receipts`; `adversary/domain/immune/seeder.py`; `operations/domain/symbol_game_bridge/pharmacy_seeder.py` | Comparison against an independently retained anchor only; not immutability or proof of reproduction |
| P6-18 | No code at the baseline matches proposals against the catalog fixtures or derives a repair from a positive fixture; the nearest consumer tests `target_pattern` as a prompt substring. | Source search at the baseline; `external_application/prompt_doctor/use_cases/repair_service.py` | Negative finding of a source search at one commit |

## Open obligations

Independent anchor custody, authenticated producers, concurrent writers,
power-failure persistence, a fully specified interoperable encoding, complete
host-decision binding, and integrated mining effectiveness remain open.
No empirical usefulness or broad neural error-prevention result is claimed.

Formal proof files previously cited for Hodge decomposition and related topics
do not prove this storage implementation. This revision makes no claim that any
formal proof covers the storage code and removes that inappropriate support
from the ledger.

The 2026-09-27 revision stated, in P6-15 and paper §7.1, that the catalog held
61 active antibodies mined from 107 multi-round transitions (the paper added
134 empirical artifacts), and paper §7.1 stated that matching proposals
received a repair derived from the positive fixture. Those statements are
withdrawn; see the change log.
