# PFP III claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · First-publication
candidate

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
"Source-inspected" means the branch and associated assertion were read
at the baseline; it does not report a fresh executed result. Repository
paths are identifiers at the baseline; the paper's references give
commit-pinned links. A "package test" is a test in this deposit's
`code/tests/`; it exercises the package re-implementation of paper
Section 4.1, not the canonical host. Current execution results belong to
`docs/first_publication_validation_2026_10_02.json`. Historical
correction counts in P3-23 to P3-25 identify the earlier report and are
not fresh execution.

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                            Evidence                                                                                                     Status and ceiling
  ----------------- -------------------------------- ------------------------------------------------------------------------------------------------------------ -------------------------------------------------------------------------------------
  P3-01             The baseline Demo 3 host charges Repository `pfp/use_cases/mssn_sn_demos/demo_3/host.py`; repository test                        Source-inspected at the baseline
                    one unit of fuel for each        `test_poisoned_batch_rolls_covered_elements_back` in `pfp/tests/mssn_sn_demos/test_demo_3.py`
                    processed batch before applying
                    it, restores covered elements,
                    witness, and phase when the
                    batch is refused, and does not
                    return the fuel.

  P3-02             Every nonempty declared route    Repository `verify_route`; repository tests                                                                  Unavailable route verification; no accepted witness claimed
                    yields `NO_NATIVE_PORT` at the   `test_verify_route_returns_missing_port_without_judging_a_witness` and
                    baseline, so no witness is       `test_odd_and_cochain_routes_use_the_same_refusal` in the same file
                    certified.

  P3-03             At the baseline, a move after    Repository host source; repository tests `test_move_after_verify_rolls_the_whole_batch_back`,                Source-inspected; the empty-batch and twelfth-batch cases are read from source, not
                    `VERIFY` or a malformed element  `test_malformed_element_ids_do_not_commit`, and `test_fuel_exhaustion_and_bool_fuel_are_refused` in the same asserted by a baseline test
                    identifier is refused and rolled file
                    back; an empty batch is charged
                    and recorded as `ACCEPTED`; once
                    fuel is zero the next batch is
                    recorded as `FUEL_EXHAUSTED` and
                    the host enters `TERMINAL`.

  P3-04             The baseline receipt verifier    Repository `verify_receipt_bytes`; repository test                                                           Source-inspected; digest-chain consistency only, no key and no producer
                    recomputes each cell's digest    `test_packaged_matrix_receipt_verifies_without_a_certificate` in the same file (positive case only)          authentication
                    chain from its initial digest,
                    checks fuel and the scripted arm
                    decisions over the 30-cell
                    matrix, and refuses `{}`, schema
                    changes, chain discontinuities,
                    and certificate claims.

  P3-05             The package re-implementation    `test_demo_3_host.py::test_known_gauge_witness_still_refuses_and_rolls_back`                                 Package test; not evidence about the canonical host
                    refuses the worked-example batch
                    with `NO_NATIVE_PORT`, rolls it
                    back, and leaves 11 of 12 fuel
                    units.

  P3-06             In the package                   `test_demo_3_host.py::test_move_after_verify_rolls_the_whole_batch_back`;                                    Package tests on finite cases; no general transaction proof
                    re-implementation, a move after  `test_demo_3_host.py::test_empty_batch_consumes_fuel_and_rolls_back`;
                    `VERIFY`, an empty batch, and a  `test_demo_3_host.py::test_malformed_element_ids_do_not_commit`;
                    malformed element identifier are `test_demo_3_host.py::test_repeated_refusals_consume_fuel_and_exhaust`
                    refused, rolled back, and
                    charged; repeated refusals
                    exhaust the fuel and end in
                    `TERMINAL` with
                    `FUEL_EXHAUSTED`.

  P3-07             The package receipt verifier     `test_demo_3_host.py::test_verify_receipt_bytes_rejects_forgeries_and_empty`;                                Package tests; an edited receipt with recomputed digests and no certificate label
                    refuses empty input, `{}`,       `test_demo_3_host.py::test_packaged_matrix_receipt_verifies_without_a_certificate`; `code/host_engine.py`    passes
                    certificate labels, non-hex
                    event bytes, and digest edits
                    that were not recomputed; it
                    does not check fuel or arm
                    scripts.

  P3-08             In the two-signal table, Signal  Repository `pfp/domain/immune/danger_gate.py` (source-inspected);                               Decision table over supplied signals; signal truth and provenance are separate
                    1 alone is diagnostic, a low or  `test_danger_gate.py::test_gate_signal1_alone_is_diagnostic`;
                    medium Signal 2 alone is         `test_danger_gate.py::test_gate_signal2_alone_critical_refuses`;
                    diagnostic, a high or critical   `test_danger_gate.py::test_gate_both_signals_refuse`
                    Signal 2 alone refuses, and both
                    signals refuse.

  P3-09             The repository self panel at the Repository test `test_canonical_self_panel_has_forty_distinct_base_contents` in                              Source-inspected corpus assertion; the package's synthetic panel only has the same
                    baseline has 1,000 rows and 40   `pfp/tests/test_immune_defect_regressions.py`                                                   shape
                    distinct base contents, ten per                                                                                                               (`test_demo_3_host.py::test_synthetic_self_panel_has_forty_distinct_base_contents`)
                    category.

  P3-10             The four package phrase          `test_demo_3_host.py::test_canaries_fire_on_constructed_fixtures_and_not_on_clean_controls`;                 Behavior of fixed phrase lists on these sentences; no accuracy, sensitivity, or
                    detectors flag their constructed `test_danger_gate.py::test_attractive_u_true_statement_is_not_flagged`                                       false-suppression rate; detectors unadmitted
                    fixture sentences and not three
                    clean controls, including a true
                    attractive-U statement that the
                    previous phrase list would have
                    flagged.

  P3-11             A phrase match cannot see        `test_danger_gate.py::test_phrase_match_does_not_see_negation`                                               One constructed example
                    negation.

  P3-12             The earlier harvest behind the   Repository `research/mssn_sn_tower/demos/antimorphism_farm/harvest/antimorphism_harvest.jsonl`,              Provenance of identifiers only; not a measurement of model error rates or detector
                    detector identifiers has 112     `eis/infrastructure/mssn_domains.py`, and                                   accuracy
                    rows: 102 author-written         `eis/infrastructure/mssn_classifier.py` (identical at the baseline and at
                    scripted responses and 10        this revision)
                    responses from one model
                    (`qwen/qwen-2.5-7b-instruct`),
                    labelled by a prompt-specific
                    rule set without an independent
                    checker.

  P3-13             The Rust port of the table and   `test_danger_gate.py::test_native_port_matches_python_reference`                                             Runs only with a built binary; skipped otherwise
                    detectors gives the same outputs
                    as the Python reference on the
                    tested cases.

  P3-14             Detector admission requires a    Paper Section 3                                                                                              Proposed method; no detector is admitted here
                    reproduced defect, valid near
                    misses, a declared scope, and
                    frozen identities.

  P3-15             D versus R is the principal      Paper Section 6                                                                                              Prespecified design; no live effect estimate
                    policy-plus-feedback comparison.

  P3-16             Route-specific false suppression Paper Section 7                                                                                              Proposed safety gate; no achieved bound
                    and false terminal outcomes
                    require independent
                    verification.

  P3-17             Zero failures in n independent   Elementary derivation in paper Section 7                                                                     Conditional calculation; dependence invalidates direct use
                    Bernoulli trials give the upper
                    bound `1-0.05^(1/n)`.

  P3-18             The historical manifest disables `demos/demo_3/experiment_manifest.yaml`                                                                      Historical configuration, separate from any pilot
                    the planned live experiment.

  P3-19             The stored pilot cannot          `demos/demo_3/results/live_openrouter_trial_receipt.json`; paper Section 8                                   Historical descriptive record; its terminal certificates came from an earlier runner
                    establish the frozen randomized
                    study.

  P3-20             Lemma A: if Signal 2 is a        Proof in Appendix A.2;                                                                                       Proved; exhaustive check on the stated finite domain
                    function of the match count, the `test_two_signals_one_detector.py::test_derived_signal2_exhaustive_over_every_function_of_the_match_count`
                    decision depends on the count    (all 28,561 functions from counts 0 to 3 to 13 Signal 2 values);
                    alone; `DIAGNOSTIC_ONLY` is      `::test_audited_derivation_reaches_only_tolerated_or_quarantined`;
                    reachable exactly when a match   `::test_independent_signals_reach_all_four_decisions`;
                    has no positive derived defect,  `::test_package_gate_collapses_the_same_way_under_a_derived_signal2`
                    or zero matches have a
                    LOW/MEDIUM derived defect; if
                    Signal 2 is present exactly with
                    Signal 1 at one severity, only
                    `TOLERATED` and one refusal are
                    reachable.

  P3-21             Lemma B: the Hill-type gate      Proof in Appendix A.3;                                                                                       Proved; exact check for integer $n$ from 1 to 4 (1 to 6 at $t = 1/2$) over 400 signal
                    activates exactly when the       `test_two_signals_one_detector.py::test_hill_rule_equals_sum_threshold_on_the_whole_domain`,                 vectors; non-integer $n$ by the proof only
                    positive signals sum to at least `::test_half_threshold_decision_does_not_depend_on_the_hill_coefficient`,
                    $K (t/(1-t))^{1/n}$; at          `::test_decision_depends_only_on_the_positive_sum_and_is_monotone`,
                    $t = 1/2$ the threshold is $K$   `::test_one_sensor_alone_can_activate_every_threshold`,
                    for every $n$; one sensor can    `::test_agent_count_follows_only_from_a_per_sensor_bound`,
                    activate it; a minimum number of `::test_threshold_zero_activates_without_any_signal_and_one_never_activates`
                    contributing sensors follows
                    only from a per-sensor bound;
                    $t = 0$ activates with no signal
                    and $t = 1$ never activates.

  P3-22             Lemma C: screening against a     Proof in Appendix A.4;                                                                                       Proved; exhaustive on the stated universe
                    self panel is sound for every    `test_two_signals_one_detector.py::test_screening_is_sound_for_every_panel_iff_executed_implies_screened`
                    panel exactly when the executed  (all 4,096 predicate pairs and 63 panels on a six-element universe);
                    predicate implies the screened   `::test_pattern_ignoring_matcher_is_admitted_and_fires_on_a_self_fixture`;
                    one, and rejects no harmless     `::test_screening_the_executed_predicate_rejects_that_rule`
                    rule exactly when the converse
                    holds.

  P3-23             At commit `30609de2c`, the       `eis/use_cases/demos/demo_4e_cogsci_autopoiesis/run_packaged_immune.py`     Source-inspected at the audited commit; line 178 is corrected in commit `fdc0035a8`
                    packaged immune demonstration    line 178; `infrastructure/mssn_ports.py` lines 27 to 39                                                      (Signal 2 from host checks, `TWO_SIGNAL_COLLAPSE` refusal;
                    computes Signal 2 for its 24                                                                                                                  `eis/tests/unit/test_two_signal_independence.py`, 18
                    controls as a high-severity                                                                                                                   passed)
                    defect counting the matches, so
                    Lemma A(3) applies whenever the
                    screen admits every rule.

  P3-24             At commit `30609de2c`, the       `eis/domain/allostery.py` lines 68 and 74 to 79; `domain/value_objects.py`  Source-inspected at the audited commit; corrected in commit `fdc0035a8` (exact gate,
                    allostery gate is the sum        (`HillParameters.calculate_cooperativity`)                                                                   per-sensor cap 1, minimum quorum 2 at the defaults;
                    threshold of Lemma B in floating                                                                                                              `tests/unit/test_allostery_exact.py`, 32 passed)
                    point; at its defaults it
                    activates at a positive sum of 2
                    and with a single sensor; its
                    comment's two-signal requirement
                    is not enforced; $t = 0$
                    activates on an empty list.

  P3-25             At commit `30609de2c`, the       `eis/domain/thymus.py` lines 77 to 99; `infrastructure/mssn_ports.py` lines Source-inspected at the audited commit; corrected in commit `fdc0035a8` (rules bind
                    screen tests each rule's regular 17 to 24 (the one matcher that executes the pattern) and 80 to 166;                                          their matcher and the screen runs it;
                    expression, while three of four  `use_cases/demos/demo_4e_cogsci_autopoiesis/run_packaged_immune.py` lines 118 to 122                         `tests/unit/test_thymus_binds_executed_matcher.py`, 22 passed)
                    matchers behind the same port
                    never execute it; for the
                    pharmacy rules the screened
                    expression is the failure-class
                    name.

  P3-26             Anti-skill V2 states the         `workflows_agents_skills/domain/anti_skill/anti_skill_v2.py`;                                   Source-inspected at the audited commit; describes a record format, not an effect
                    admission record of Section 3 as `application/anti_skill/anti_skill_v2.py` lines 140 to 148; `application/anti_skill_admission/verifier.py`
                    types: a closed predicate        lines 25 to 45; `.agents/anti_skills/admitted/registry.json` (empty) and
                    language of at most 16 atoms     `.agents/anti_skills/admitted/truth_boundary_v2/`
                    over eight fields, positive and
                    negative controls from at least
                    two contexts, receipts whose
                    outcome is derived, and a closed
                    human decision bound to the
                    specification and receipt; its
                    admission verifier and loader
                    are retired, and no detector is
                    active through it.

  P3-27             Fuel bounds charged processed    Baseline host `_blocked` and `_commit`; paper Sections 4 and 9                                               Source-inspected bound; global resource limits remain caller obligations
                    batches, not post-terminal
                    receipts, batch bytes, or total
                    elapsed time.

  P3-28             A cap on signal magnitude bounds Appendix A.3-A.4                                                                                             Mathematical scope clarification; no empirical guarantee
                    positive entries, not
                    independent agents; matching
                    screened and executed predicates
                    does not guarantee coverage of
                    all valid inputs.

  P3-29             Exact threshold and panel        New input-boundary tests in `code/tests/test_two_signals_one_detector.py`                                    Package validation only; not a full runtime input audit
                    helpers reject Boolean/inexact
                    coefficients or masks and
                    predicate bits outside the
                    declared universe.

  P3-30             The Examiner companion contains 24 `_lev_examiner_theoretical_minimum_quiz/`; current worksheet replay receipt                                    Educational artifact; no learner-outcome study
                    scoped problems, worked study
                    material, and a separate
                    instructor key.
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Withdrawn in the retained internal revision

The previous ledger entry P3-13 stated that a retrospective analysis of
28 adversarial probe runs isolated four recurring failure modes, with 13
detections and 15 grounded witnesses. It is withdrawn. Those 28 rows of
the harvest are 18 author-written scripted responses and 10 responses
from one model, labelled by the prompt-specific rule set; the labels
were not independently checked. The two detections on model responses
fire on sentences that deny or conditionally mention the targeted claim,
and one row counted as grounded is an author-written false claim that
the rules did not flag. The previous P3-11 described the package receipt
check as cryptographic verification that rejects forged certificates
"even after digest recomputation"; it is narrowed to P3-07.

## Excluded promotions

The paper does not claim a general immunity result, a causal treatment
effect, controlled model transfer, a physical Hamiltonian bridge,
arbitrary tower extension, or correspondence between the implementation
and any formal proof-assistant model. Retaining a refusal does not
authorize retaining every raw field.

Earlier ledgers are available in Git history at the baseline. Historical
passing counts are not copied into this current ledger.

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
