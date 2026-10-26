# PFP VI claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · First-publication review

Baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
The main manuscript gives commit-pinned source links. “Source-inspected”
records what was read, not a fresh execution count. Package tests are named as
`file::function`; repository tests outside this package are named by function
and file path. Current execution results belong to the dated review receipt.
Identifiers P6-01 to P6-18 preserve the earlier review history. P6-19 to
P6-26 record the first-publication findings. Version 1.1.0 was an internal
draft label; the current public candidate is 0.1.0. The fresh validation
receipt binds the exercised code and current publication assets.

| ID | Claim | Evidence | Status and boundary |
| --- | --- | --- | --- |
| P6-01 | The production sink records ordered refusal entries with predecessor digests and a count/head header. | `omega_engine_pfp/infrastructure/persistence/cemetery_sink.py` | Source-inspected local storage |
| P6-02 | Restart verification checks entry shape, order, chain, count, and head. | Same source; `omega_engine_pfp/tests/test_cemetery_sink.py` | Finite positive and hostile cases; no universal parser proof |
| P6-03 | Removing a tail while preserving the original header is detectable. | `test_006_worked_example.py::test_removed_final_entry_is_rejected_with_original_header`; `test_cold_restart_tail_truncation_rejection` in the repository sink tests | Depends on the unchanged expected header; the package test needs the full repository |
| P6-04 | Rewriting both file and local header can preserve local self-consistency. | `test_006_worked_example.py::test_consistent_shorter_file_passes_locally_but_not_the_anchor`; paper §§5–6 | Threat-model limitation; the package test needs the full repository |
| P6-05 | A separately retained count/head compares the ordered normalized-entry snapshot, excluding raw-file and full-header identity. | `test_006_worked_example.py::test_section6_block_runs_as_printed`; `test_006_worked_example.py::test_numeric_and_string_reason_share_count_and_head`; `emit_tail_receipt` | Caller trust obligation; not automatic signed freshness |
| P6-06 | Physical writes replace the full serialized file through a temporary path. | `CemeterySink._write_file` | Logical append only; no lock or explicit fsync |
| P6-07 | Sorted JSON in the historical sink does not establish complete RFC 8785 compliance; later encoder changes have their own source identity. | `_canonical_json_bytes` compared with RFC 8785 | Explicit standards boundary |
| P6-08 | Stored cochain and refusal fields are caller-supplied evidence, not sink-computed native results. | `record_refusal` signature and normalization | Storage integrity does not verify event truth |
| P6-09 | Invalid detector regex yields a typed refusal; a benign-panel match produces a kill-condition record. | `omega_engine_pfp/domain/immune/clonal_selection.py`; `test_kill_condition_refuses_an_invalid_pattern_without_raising` in the repository regression suite | Finite rule-maintenance contract |
| P6-10 | The self panel has 40 distinct base contents among 1,000 rows. | `test_canonical_self_panel_has_forty_distinct_base_contents` in the repository regression suite | Source-inspected corpus assertion; no 1,000-independent-example claim |
| P6-11 | The explicit toxicity threshold is inclusive at 1/5; the unlabelled-corpus score is 0 or 1. | `omega_engine_pfp/domain/immune/treg.py`; `test_treg_downgrades_at_exactly_tau`, `test_treg_keeps_a_detector_just_below_tau`, and `test_treg_prompt_corpus_toxicity_is_zero_or_one` in the repository regression suite | Exact policy arithmetic over supplied trigger labels |
| P6-12 | Affinity decay is invariant to batching of the same idle-run total at fixed tau, with a nonnegative initial score and no intervening reset/stimulation. | `apply_half_life_decay`; `test_decay_does_not_depend_on_how_idle_runs_are_batched` in the repository regression suite | Finite implementation and elementary telescoping relation |
| P6-13 | Retention-to-detector admission needs replay, provenance, near misses, and scope. | Paper §§7–8 | Proposed integration method |
| P6-14 | Paper-local toy classes do not verify production integration. | `test_006_epistemic_immune.py::test_toy_chain_links_predecessor_digests`; `test_006_epistemic_immune.py::test_danger_signal_threshold`; the module defines its own classes | Educational illustration only |
| P6-15 | The retained catalog `_intelligence/_antibodies/pharmacy_catalog.json` holds 61 entries with 14 distinct `failure_class` values; 56 are marked `candidate` and 5 `active`. Every entry has `negative_fixture`, `positive_fixture`, and `evidence_sha256`; 49 entries carry placeholder fixtures. | The file at the baseline commit (Git blob `e4984047231091caca6e5b0b7810f20c705e4970`; SHA-256 `b95ce7c1338867cc680abffcc3f2fb9da634c7a7ec2f4c00e0d67391e91b4acb`); `test_006_catalog_file.py::test_catalog_entry_class_and_status_counts`; `test_006_catalog_file.py::test_catalog_fields_and_placeholder_fixtures`; paper §7.1 | Corrected in 1.1.0; counts describe the data file only, not reproduction, coverage, or effectiveness; the tests prefer the historical Git object and otherwise use an identical digest-bound package snapshot |
| P6-16 | Changing an entry payload while keeping its digest is rejected on reopen. | `test_006_worked_example.py::test_changed_payload_is_rejected_on_reopen`; `test_intermediate_bit_flip_tamper_detection` in the repository sink tests | Finite hostile case; the package test needs the full repository |
| P6-17 | The catalog does not record which bytes an `evidence_sha256` value covers. Both baseline harvesters hash short identifying strings, and 19 stored values are reproduced from a defect label joined with run and task identifiers found in retained run records. | `test_006_catalog_file.py::test_evidence_digests_hash_identifiers_not_receipts`; `omega_engine_woland/domain/immune/seeder.py`; `omega_engine_operations/domain/symbol_game_bridge/pharmacy_seeder.py` | Comparison against an independently retained anchor only; not immutability or proof of reproduction |
| P6-18 | No code at the baseline matches proposals against the catalog fixtures or derives a repair from a positive fixture; the nearest consumer tests `target_pattern` as a prompt substring. | Source search at the baseline; `omega_engine_external_application/prompt_doctor/use_cases/repair_service.py` | Negative finding of a source search at one commit |

| P6-19 | A tail receipt reports cached count/head and does not reread changed disk bytes. | `emit_tail_receipt`; `test_006_worked_example.py::test_cached_receipt_does_not_verify_changed_disk_bytes` | Source-bound exercised boundary; reopen or verify before disk comparison |
| P6-20 | Failed replacement can leave the unacknowledged append in memory while disk retains its old file. | `record_refusal`; `test_006_worked_example.py::test_failed_replace_leaves_memory_ahead_of_the_persisted_file` | Injected single failure, not crash/durability proof; reconcile before retry |
| P6-21 | Header schema/genesis and formatting can change while the tail anchor matches; a valid extension changes the head. | Added header, whitespace, and prefix-extension cases in `test_006_worked_example.py` | Normalized prefix comparison differs from raw identity and authentication |
| P6-22 | Normalization can merge caller types or mapping keys before hashing; nested mappings remain mutable. | `_sanitize_for_cemetery`; exact worksheet; `test_mutable_nested_mapping_can_invalidate_a_later_snapshot` | No injective original-value encoding or transitive immutability claim |
| P6-23 | Clonal and regulatory methods return decision records; they do not themselves establish host enforcement. | `check_kill_condition`, `synthesize_treg`, paper §§7-8 | Consumer integration and applied-action evidence required |
| P6-24 | Trigger-pair and corpus denominators differ; empty triggers give zero by convention. | `evaluate_toxicity`; worksheet and baseline regression suite | Supplied signal arithmetic, not an oracle population safety rate |
| P6-25 | Individual full-history rewrites have quadratic accumulated entry-byte cost under the stated equal/bounded-size model. | Paper §4; worksheet's 100-record calculation | Elementary accounting, not a measured performance result |
| P6-26 | The companion has 24 problems, a worked guide, a separate key, and exact replay. | `_lev_landau_theoretical_minimum_quiz/`; `code/landau_worksheet.py` | Original educational curriculum, not historical Landau authority or measured gains |

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

## 2026-10-23 harness extension

| Claim | Evidence | Limit |
| --- | --- | --- |
| New research mechanism | Paper 029 source manifest and focused checks | Implemented adaptation; historical evidence remains separately pinned |
| New model effects | Replayed campaign report | NOT_MEASURED; live campaign NOT_RUN |
| External AIDE2 findings | Versioned PDF and page-level source map | Attribution, not replication |
| Formal results above | Existing proofs and finite examples | No additional formal theorem or Lean claim |
