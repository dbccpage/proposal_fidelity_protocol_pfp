# PFP VI claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · First-publication
review

Baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`. The main
manuscript gives commit-pinned source links. "Source-inspected" records
what was read, not a fresh execution count. Package tests are named as
`file::function`; repository tests outside this package are named by
function and file path. Current execution results belong to the dated
review receipt. Identifiers P6-01 to P6-18 preserve the earlier review
history. P6-19 to P6-26 record the first-publication findings. Version
1.1.0 was an internal draft label; the current public candidate is
0.1.0. The fresh validation receipt binds the exercised code and current
publication assets.

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                                               Evidence                                                                                        Status and boundary
  ----------------- --------------------------------------------------- ----------------------------------------------------------------------------------------------- ---------------------------
  P6-01             The production sink records ordered refusal entries `pfp/infrastructure/persistence/cemetery_sink.py`                                  Source-inspected local
                    with predecessor digests and a count/head header.                                                                                                   storage

  P6-02             Restart verification checks entry shape, order,     Same source; `pfp/tests/test_cemetery_sink.py`                                     Finite positive and hostile
                    chain, count, and head.                                                                                                                             cases; no universal parser
                                                                                                                                                                        proof

  P6-03             Removing a tail while preserving the original       `test_006_worked_example.py::test_removed_final_entry_is_rejected_with_original_header`;        Depends on the unchanged
                    header is detectable.                               `test_cold_restart_tail_truncation_rejection` in the repository sink tests                      expected header; the
                                                                                                                                                                        package test needs the full
                                                                                                                                                                        repository

  P6-04             Rewriting both file and local header can preserve   `test_006_worked_example.py::test_consistent_shorter_file_passes_locally_but_not_the_anchor`;   Threat-model limitation;
                    local self-consistency.                             paper §§5--6                                                                                    the package test needs the
                                                                                                                                                                        full repository

  P6-05             A separately retained count/head compares the       `test_006_worked_example.py::test_section6_block_runs_as_printed`;                              Caller trust obligation;
                    ordered normalized-entry snapshot, excluding        `test_006_worked_example.py::test_numeric_and_string_reason_share_count_and_head`;              not automatic signed
                    raw-file and full-header identity.                  `emit_tail_receipt`                                                                             freshness

  P6-06             Physical writes replace the full serialized file    `CemeterySink._write_file`                                                                      Logical append only; no
                    through a temporary path.                                                                                                                           lock or explicit fsync

  P6-07             Sorted JSON in the historical sink does not         `_canonical_json_bytes` compared with RFC 8785                                                  Explicit standards boundary
                    establish complete RFC 8785 compliance; later
                    encoder changes have their own source identity.

  P6-08             Stored cochain and refusal fields are               `record_refusal` signature and normalization                                                    Storage integrity does not
                    caller-supplied evidence, not sink-computed native                                                                                                  verify event truth
                    results.

  P6-09             Invalid detector regex yields a typed refusal; a    `pfp/domain/immune/clonal_selection.py`;                                           Finite rule-maintenance
                    benign-panel match produces a kill-condition        `test_kill_condition_refuses_an_invalid_pattern_without_raising` in the repository regression   contract
                    record.                                             suite

  P6-10             The self panel has 40 distinct base contents among  `test_canonical_self_panel_has_forty_distinct_base_contents` in the repository regression suite Source-inspected corpus
                    1,000 rows.                                                                                                                                         assertion; no
                                                                                                                                                                        1,000-independent-example
                                                                                                                                                                        claim

  P6-11             The explicit toxicity threshold is inclusive at     `pfp/domain/immune/treg.py`; `test_treg_downgrades_at_exactly_tau`,                Exact policy arithmetic
                    1/5; the unlabelled-corpus score is 0 or 1.         `test_treg_keeps_a_detector_just_below_tau`, and                                                over supplied trigger
                                                                        `test_treg_prompt_corpus_toxicity_is_zero_or_one` in the repository regression suite            labels

  P6-12             Affinity decay is invariant to batching of the same `apply_half_life_decay`; `test_decay_does_not_depend_on_how_idle_runs_are_batched` in the       Finite implementation and
                    idle-run total at fixed tau, with a nonnegative     repository regression suite                                                                     elementary telescoping
                    initial score and no intervening reset/stimulation.                                                                                                 relation

  P6-13             Retention-to-detector admission needs replay,       Paper §§7--8                                                                                    Proposed integration method
                    provenance, near misses, and scope.

  P6-14             Paper-local toy classes do not verify production    `test_006_epistemic_immune.py::test_toy_chain_links_predecessor_digests`;                       Educational illustration
                    integration.                                        `test_006_epistemic_immune.py::test_danger_signal_threshold`; the module defines its own        only
                                                                        classes

  P6-15             The retained catalog                                The file at the baseline commit (Git blob `e4984047231091caca6e5b0b7810f20c705e4970`; SHA-256   Corrected in 1.1.0; counts
                    `_intelligence/_antibodies/pharmacy_catalog.json`   `b95ce7c1338867cc680abffcc3f2fb9da634c7a7ec2f4c00e0d67391e91b4acb`);                            describe the data file
                    holds 61 entries with 14 distinct `failure_class`   `test_006_catalog_file.py::test_catalog_entry_class_and_status_counts`;                         only, not reproduction,
                    values; 56 are marked `candidate` and 5 `active`.   `test_006_catalog_file.py::test_catalog_fields_and_placeholder_fixtures`; paper §7.1            coverage, or effectiveness;
                    Every entry has `negative_fixture`,                                                                                                                 the tests prefer the
                    `positive_fixture`, and `evidence_sha256`; 49                                                                                                       historical Git object and
                    entries carry placeholder fixtures.                                                                                                                 otherwise use an identical
                                                                                                                                                                        digest-bound package
                                                                                                                                                                        snapshot

  P6-16             Changing an entry payload while keeping its digest  `test_006_worked_example.py::test_changed_payload_is_rejected_on_reopen`;                       Finite hostile case; the
                    is rejected on reopen.                              `test_intermediate_bit_flip_tamper_detection` in the repository sink tests                      package test needs the full
                                                                                                                                                                        repository

  P6-17             The catalog does not record which bytes an          `test_006_catalog_file.py::test_evidence_digests_hash_identifiers_not_receipts`;                Comparison against an
                    `evidence_sha256` value covers. Both baseline       `adversary/domain/immune/seeder.py`;                                                  independently retained
                    harvesters hash short identifying strings, and 19   `operations/domain/symbol_game_bridge/pharmacy_seeder.py`                          anchor only; not
                    stored values are reproduced from a defect label                                                                                                    immutability or proof of
                    joined with run and task identifiers found in                                                                                                       reproduction
                    retained run records.

  P6-18             No code at the baseline matches proposals against   Source search at the baseline;                                                                  Negative finding of a
                    the catalog fixtures or derives a repair from a     `external_application/prompt_doctor/use_cases/repair_service.py`                   source search at one commit
                    positive fixture; the nearest consumer tests
                    `target_pattern` as a prompt substring.
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| P6-19 \| A tail receipt reports cached count/head and does not reread
  changed disk bytes. \| `emit_tail_receipt`;
  `test_006_worked_example.py::test_cached_receipt_does_not_verify_changed_disk_bytes`
  \| Source-bound exercised boundary; reopen or verify before disk
  comparison \|
| P6-20 \| Failed replacement can leave the unacknowledged append in
  memory while disk retains its old file. \| `record_refusal`;
  `test_006_worked_example.py::test_failed_replace_leaves_memory_ahead_of_the_persisted_file`
  \| Injected single failure, not crash/durability proof; reconcile
  before retry \|
| P6-21 \| Header schema/genesis and formatting can change while the
  tail anchor matches; a valid extension changes the head. \| Added
  header, whitespace, and prefix-extension cases in
  `test_006_worked_example.py` \| Normalized prefix comparison differs
  from raw identity and authentication \|
| P6-22 \| Normalization can merge caller types or mapping keys before
  hashing; nested mappings remain mutable. \| `_sanitize_for_cemetery`;
  exact worksheet;
  `test_mutable_nested_mapping_can_invalidate_a_later_snapshot` \| No
  injective original-value encoding or transitive immutability claim \|
| P6-23 \| Clonal and regulatory methods return decision records; they
  do not themselves establish host enforcement. \|
  `check_kill_condition`, `synthesize_treg`, paper §§7-8 \| Consumer
  integration and applied-action evidence required \|
| P6-24 \| Trigger-pair and corpus denominators differ; empty triggers
  give zero by convention. \| `evaluate_toxicity`; worksheet and
  baseline regression suite \| Supplied signal arithmetic, not an oracle
  population safety rate \|
| P6-25 \| Individual full-history rewrites have quadratic accumulated
  entry-byte cost under the stated equal/bounded-size model. \| Paper
  §4; worksheet's 100-record calculation \| Elementary accounting, not a
  measured performance result \|
| P6-26 \| The companion has 24 problems, a worked guide, a separate
  key, and exact replay. \| `_lev_examiner_theoretical_minimum_quiz/`;
  `code/examiner_worksheet.py` \| Original educational curriculum, not
  historical Examiner authority or measured gains \|

## Open obligations

Independent anchor custody, authenticated producers, concurrent writers,
power-failure persistence, a fully specified interoperable encoding,
complete host-decision binding, and integrated mining effectiveness
remain open. No empirical usefulness or broad neural error-prevention
result is claimed.

Formal proof files previously cited for Hodge decomposition and related
topics do not prove this storage implementation. This revision makes no
claim that any formal proof covers the storage code and removes that
inappropriate support from the ledger.

The 2026-09-27 revision stated, in P6-15 and paper §7.1, that the
catalog held 61 active antibodies mined from 107 multi-round transitions
(the paper added 134 empirical artifacts), and paper §7.1 stated that
matching proposals received a repair derived from the positive fixture.
Those statements are withdrawn; see the change log.

## 2026-10-23 harness extension

  -----------------------------------------------------------------------
  Claim                   Evidence                Limit
  ----------------------- ----------------------- -----------------------
  New research mechanism  Paper 029 source        Implemented adaptation;
                          manifest and focused    historical evidence
                          checks                  remains separately
                                                  pinned

  New model effects       Replayed campaign       NOT_MEASURED; live
                          report                  campaign NOT_RUN

  External AIDE2 findings Versioned PDF and       Attribution, not
                          page-level source map   replication

  Formal results above    Existing proofs and     No additional formal
                          finite examples         theorem or Lean claim
  -----------------------------------------------------------------------
