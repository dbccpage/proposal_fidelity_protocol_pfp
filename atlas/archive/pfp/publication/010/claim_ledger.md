# Claim ledger: PFP X (Paper 010)

Version 2.0.2, 2026-09-30. Code baseline
`a623568eb0f853b968bc419bf06dfc6af256ab02`.

Each row is a claim made in the manuscript, with the section that makes
it, its kind, and the evidence that supports it. Kinds are: *executable
check* (a named test in `code/tests/`), *formal proof* (a Lean
declaration in `lean4/`), *standard fact* (a cited reference), *retained
record* (a repository file, cited by path and commit), and *source
inspection* (reading a retained script), and *replay* (the collection's
`tools/replay_formal_math_baselines.py`, which runs the challenge
checkers from the cited commits on answers that need no mathematics; its
output is recorded in the collection's
`verification/formal_math_baselines.json`). Paths under
`projects/` are relative to the repository root; the C017
folder is
`projects/mssn_sn_symgam/challenges/b_cohomology/c017_nonabelian_lattice_holonomy/`
and the formal-mathematics folder is
`projects/mssn_sn_symgam/challenges/e_formal_math/`. Claims
withdrawn from the first release are listed in `paper_change_log.md`,
not here.

## The first release (Section 1)

  -----------------------------------------------------------------------------------------------------------------------------
  ID             Claim             Section        Kind           Evidence
  -------------- ----------------- -------------- -------------- --------------------------------------------------------------
  PFP10-00       In the first      1              Source         `paper.md` and
                 release's                        inspection     `code/tests/test_010_adversarial_refusals_and_decimation.py`
                 package, the five                               in this package folder at commit
                 prompt-filter                                   `35e3d7ba2e0e20904d17a79cc395980f50a1a0f1`; a search of the
                 stages were                                     repository finds the benchmark and effect statements only in
                 simple functions                                copies of the first-release paper. Engine components with
                 (a radius-one                                   similar names (an allosteric gate and a kinetic proofreader
                 neighbourhood                                   under `pfp/domain/`) are separate code,
                 split, a                                        and no run of them against model answers is recorded
                 list-membership
                 test, two
                 threshold
                 comparisons, an
                 ordered
                 four-label line
                 check, and a
                 count of five
                 listed symbols
                 compared with
                 three); no run,
                 runner or receipt
                 for the first
                 release's filter
                 benchmark or
                 effect sizes is
                 retained, and no
                 effect was
                 measured.

  -----------------------------------------------------------------------------------------------------------------------------

## Checker and mathematics (Section 2)

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID             Claim                  Section        Kind           Evidence
  -------------- ---------------------- -------------- -------------- ----------------------------------------------------------------------------------------------------
  PFP10-01       The package's $S_3$    2.1            Executable     `test_holonomy_checker.py::test_package_groups_are_nonabelian_of_orders_6_and_8`
                 (permutations of three                check
                 points) and $Q_8$
                 (integer unit
                 quaternions) tables
                 satisfy the group
                 axioms; they are
                 nonabelian of orders 6
                 and 8, and $Q_8$ has
                 one element of order
                 2.

  PFP10-02       A table that is not a  2.1, 2.2       Executable     `test_holonomy_checker.py::test_constructor_rejects_tables_that_are_not_groups`
                 group (two entries of                 check
                 a row swapped, a wrong
                 inverse, an entry that
                 is not an element) is
                 refused.

  PFP10-03       Lattices with too few  2.1            Executable     `test_holonomy_checker.py::test_lattice_rejects_degenerate_shapes`
                 rows or columns, or                   check
                 with non-integer
                 sizes, are refused; a
                 torus needs at least
                 three rows and
                 columns.

  PFP10-04       Link lists with an     2.2            Executable     `test_holonomy_checker.py::test_loader_refuses_inconsistent_or_incomplete_links`
                 inverse mismatch, a                   check
                 missing direction or
                 an edge outside the
                 lattice are refused.

  PFP10-05       Reversing a plaquette  2.1, 2.4       Executable     `test_holonomy_checker.py::test_orientation_reversal_inverts_plaquette_holonomy`; references 1 and 2
                 inverts its product;                  check;
                 changing the starting                 standard fact
                 vertex conjugates it;
                 some products differ
                 from their inverses in
                 $S_3$ and $Q_8$.

  PFP10-06       A gauge transformation 2.1            Executable     `test_holonomy_checker.py::test_gauge_transformation_conjugates_plaquette_holonomy`; references 1
                 conjugates each                       check;         and 2
                 plaquette product by                  standard fact
                 the gauge at the
                 plaquette's first
                 vertex.

  PFP10-07       A flat connection on   2.1            Standard fact  References 2 and 3; checked on finite families by PFP10-11 and PFP10-12
                 an open lattice is
                 gauge-trivial; on the
                 torus $A$ and $B$
                 commute, and the
                 connection is
                 gauge-trivial exactly
                 when $A = B = e$.

  PFP10-08       The trivial connection 2.4            Executable     `test_holonomy_checker.py::test_trivial_connection_is_flat_trivial`
                 is `FLAT_TRIVIAL` on                  check
                 open and periodic
                 lattices, and every
                 plaquette can be
                 skipped.

  PFP10-09       A gauge transformation 2.3, 2.4       Executable     `test_holonomy_checker.py::test_pure_gauge_connection_is_flat_trivial_with_no_identity_plaquettes`
                 of the trivial                        check
                 connection with no
                 plaquette of four
                 identity links is
                 `FLAT_TRIVIAL`; the
                 returned tree gauge
                 makes every link the
                 identity.

  PFP10-10       A single non-identity  2.4            Executable     `test_holonomy_checker.py::test_single_non_identity_link_is_not_flat`
                 link away from the                    check
                 boundary gives
                 `NOT_FLAT` with
                 exactly two non-flat
                 plaquettes.

  PFP10-11       A torus connection     2.4            Executable     `test_holonomy_checker.py::test_flat_nontrivial_torus_with_constant_holonomy_around_one_cycle`
                 with a constant                       check
                 non-identity product
                 around one cycle is
                 `FLAT_NONTRIVIAL`.

  PFP10-12       For every pair         2.4            Executable     `test_holonomy_checker.py::test_flat_cycle_holonomies_commute_on_every_seam_pair`
                 $(a, b)$ in                           check
                 $S_3 \times S_3$ and
                 $Q_8 \times Q_8$, the
                 $3 \times 4$ torus
                 connection with seam
                 links $a$ and $b$ is
                 flat exactly when
                 $ab = ba$; flat cases
                 have cycle products
                 $(a, b)$, conjugated
                 by one element after a
                 gauge transformation;
                 the non-flat plaquette
                 has product
                 $b a b^{-1} a^{-1}$.

  PFP10-13       Skipping plaquettes    2.3, 2.4       Executable     `test_holonomy_checker.py::test_identity_skipping_never_changes_the_result`
                 with four identity                    check
                 links never changes
                 the verdict, the
                 non-flat count, the
                 witness or the cycle
                 products.

  PFP10-14       The certificate check  2.2, 2.4       Executable     `test_holonomy_checker.py::test_verify_claim_checks_certificates_not_labels`
                 accepts a correct                     check
                 plaquette in either
                 orientation and
                 rejects a wrong
                 product, a flat
                 plaquette, a
                 four-cycle that is not
                 a plaquette, a wrong
                 gauge, an unparsed
                 answer and a
                 contractible loop.

PFP10-15       Lemma: four identity   2.3            Formal proof   `lean4/LatticeDecimation.lean`, `SymbolGame010.identity_links_give_identity_product`;
                 links give the                                       `lean4/axiom_report.txt` records no axioms
                 identity plaquette
                 product (identity law
                 and $e^{-1} = e$
                 only).
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## C017 pilot (Section 3)

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID             Claim                         Section        Kind           Evidence
  -------------- ----------------------------- -------------- -------------- ------------------------------------------------------------------------------------
  PFP10-16       The five files in             3.1            Executable     `code/data/c017/provenance.json`;
                 `code/data/c017/` are byte                   check;         `test_c017_replay.py::test_case_files_match_recorded_digests`
                 copies of the retained                       retained
                 challenge cases; their CRLF                  record
                 digests equal the challenge's
                 judge manifest.

  PFP10-17       Host verdicts, lattice sizes, 3.1            Executable     `test_c017_replay.py::test_host_verdicts_for_the_five_cases`;
                 plaquette counts and                         check          `test_c017_replay.py::test_retained_certificates_agree_with_recorded_outcomes`
                 skippable counts of Table 1;
                 they agree with the verdicts
                 the harness expected.

  PFP10-18       In `base_03`, $A$ = `r`, $B$  3.1, 3.2       Executable     `test_c017_replay.py::test_torus_case_has_ten_plaquettes_with_a_non_identity_link`
                 = `r2`, and exactly 10 of 30                 check
                 plaquettes contain a
                 non-identity link.

  PFP10-19       The case $S_3$ table is       3.1            Executable     `test_c017_replay.py::test_case_groups_are_s3_and_q8`
                 isomorphic to the permutation                check
                 group (six isomorphisms) and
                 the case $Q_8$ table equals
                 the package table.

  PFP10-20       Arm settings (prompt content, 3.1            Source         `eval_epistemic_immune_transfer.py` at `7e639a0be573f6affc4d84a2aacb5573da92bc79`;
                 model, temperature,                          inspection     `eval_arm5_hybrid.py` at `9e45ee501e6a48086aaabd2381632eef6f7ed7a2` and
                 completion limit).                                          `5327cfcb7ee3622e79f7d0cd884dfa37ef4eef56`; `eval_arm6_hierarchical_decimation.py`
                                                                             at `eb5fc971ae44320ff8183f09343d547f830d9d56` (all in the C017 folder)

  PFP10-21       Accepted certificates per     3.2            Retained       `results/immune_transfer_report.json` at `7e639a0be573f6affc4d84a2aacb5573da92bc79`;
                 run: 0, 0, 3, 3 and 4 of 5;                  record;        `results/arm5_hybrid_report.json` at `9e45ee501e6a48086aaabd2381632eef6f7ed7a2`;
                 verdict labels equal to the                  executable     `results/arm5_stealth_space_bunny_alpha_report.json` at
                 host: 4, 2, 3, 3 and 4 of 5                  check          `5327cfcb7ee3622e79f7d0cd884dfa37ef4eef56`;
                 (Table 2).                                                  `results/arm6_stealth_space_bunny_alpha_report.json` at
                                                                             `eb5fc971ae44320ff8183f09343d547f830d9d56`;
                                                                             `test_c017_replay.py::test_recorded_outcomes_for_arms_1_and_2`;
                                                                             `test_c017_replay.py::test_retained_certificates_agree_with_recorded_outcomes`

  PFP10-22       The package's certificate     3.2            Executable     `code/data/c017/model_claims.json`;
                 check agrees with the harness                check          `test_c017_replay.py::test_retained_certificates_agree_with_recorded_outcomes`
                 on all 15 certificates
                 retained in full (10
                 accepted, 5 rejected).

  PFP10-23       Three Arm 1 and two Arm 2     3.2            Retained       `results/immune_transfer_report.json` and `eval_epistemic_immune_transfer.py` at
                 answers were rejected because                record; source `7e639a0be573f6affc4d84a2aacb5573da92bc79`;
                 the plaquette was listed in                  inspection;    `test_c017_replay.py::test_recorded_outcomes_for_arms_1_and_2`
                 the reverse vertex order; the                executable
                 Arm 1 and Arm 2 prompts did                  check
                 not state the accepted order.

  PFP10-24       For `base_03`, the Arm 5      3.2            Retained       `results/arm5_stealth_space_bunny_alpha_report.json` and
                 reply of                                     record;        `results/arm6_stealth_space_bunny_alpha_report.json`;
                 `stealth/space-bunny-alpha`                  executable     `test_c017_replay.py::test_completion_lengths_recorded_for_the_torus_case`
                 stopped at 8,000 completion                  check
                 tokens with unfinished JSON;
                 the Arm 6 reply used 2,810
                 completion tokens and was
                 accepted.

  PFP10-25       The only retained             3.2            Retained       `results/immune_transfer_report.json`; `code/data/c017/model_claims.json`
                 `PURE_GAUGE` answer is the                   record
                 Arm 2 answer for `base_01`,
                 whose gauge fails on the edge
                 $(0,1) \to (0,2)$; the three
                 Arm 5 and Arm 6 answers for
                 `base_02` stated a flat
                 plaquette as non-flat.

  PFP10-26       Both C017 harness checkers    3.2            Source         `judge_packet/checkers/algebraic_holonomy_checker.py` and
                 import the plaquette list and                inspection     `judge_packet/checkers/independent_checker.py` import
                 path product from the                                       `reference_solver/lattice_holonomy.py` (C017 folder)
                 challenge's reference solver.

PFP10-27       Each C017 report's SHA-256    3.3            Retained       `results/receipt.json`, `results/receipt_arm5.json` (at
                 digest equals the digest in                  record         `9e45ee501e6a48086aaabd2381632eef6f7ed7a2`),
                 its receipt file.                                           `results/receipt_arm5_stealth_space_bunny_alpha.json`,
                                                                             `results/receipt_arm6_stealth_space_bunny_alpha.json` (C017 folder)
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------

## Formal-mathematics pilots (Section 4)

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID             Claim                         Section        Kind           Evidence
  -------------- ----------------------------- -------------- -------------- ---------------------------------------------------------------------------------------
  PFP10-28       Counts in Table 3, n = 10 per 4.1            Retained       `c045_knot_polynomials_from_pd/empirical_results/c045_space_bunny_matrix_report.json`
                 cell, one reply per case; a                  record         at `ea2b55d841bdbe283f2f6ac77abe8a1677cbf0f8`; the C046, C047, C048 and C049 panel B
                 pass required both checkers.                                reports (`*_space_bunny_matrix_report.json`) and the C049 panel A files
                 The counts are made under                                   (`results_*.json`) at `46bd1dec156260f073b77caa07d8a453f8efad30`; the C050 report at
                 leaked labels (PFP10-37) and                                `46bd1dec156260f073b77caa07d8a453f8efad30` (run 1) and
                 do not measure unaided                                      `5a256c6e8d088c612332362a8abc53138806ac7a` (run 2)
                 performance.

  PFP10-29       Completion limits,            4.1            Source         `run_c045_matrix.py` to `run_c050_matrix.py` in the challenge folders at the commits of
                 temperature 0 and panel                      inspection     PFP10-28
                 definitions set by the
                 runners; the C049 panel B
                 runner is not retained.

  PFP10-30       C050 was run twice with the   4.1            Retained       C050 report at `46bd1dec156260f073b77caa07d8a453f8efad30` and at
                 same runner and cases; start                 record         `5a256c6e8d088c612332362a8abc53138806ac7a`
                 times 98 seconds apart; five
                 of ten
                 `stealth/space-bunny-alpha`
                 outcomes changed, two through
                 API errors.

  PFP10-31       In C045 all 8 and in C046 5   4.2            Retained       C045 and C046 reports (PFP10-28); the extent of the second-checker defects is PFP10-39
                 of 6                                         record
                 `stealth/space-bunny-alpha`
                 failures returned no answer
                 object, at 4,751 to 4,845 and
                 4,624 to 4,747 recorded
                 tokens; the second checker
                 reported acceptance for these
                 empty answers.

  PFP10-32       In C047 case m06 the second   4.2            Retained       C047 report (PFP10-28); panel in `c047_sequence_law_discovery/run_c047_matrix.py`;
                 checker accepted an absence                  record; source `c047_sequence_law_discovery/judge_packet/exact_checker.py` uses a fraction-free
                 certificate that the exact                   inspection     determinant (reference 5)
                 checker rejected; on m07, m08
                 and m10 no model returned a
                 certificate both checkers
                 accepted.

  PFP10-33       C043 and C044 scoring         4.3            Retained       `c043_ramsey_vdw_constructions/commit_reveal/c043_l41_scoring_receipt.json` at
                 receipts record the reference                record         `50197478726e5ecb791e519760cee9a79af2af27`;
                 solver passing 64 of 64                                     `c044_finite_group_identification/commit_reveal/c044_l41_scoring_receipt.json` at
                 hidden cases with no checker                                `999b36c1afed0f905f634f83adc1c646da7b975e`; judge packet folders
                 disagreement and 48 of 48
                 mutations rejected; no
                 receipt is retained for C045
                 to C050; each judge packet
                 retains 64 cases and 48
                 mutations.

PFP10-34       The C043 and C044 model run   4.3            Source         `run_c043_matrix.py` writes to `_intelligence/symbol_game/runs/` inside the repository,
                 reports are not retained in                  inspection     which the repository ignores (`.gitignore`, pattern `runs/`); `run_c044_matrix.py`
                 the repository; the C044                                    (commit `999b36c1afed0f905f634f83adc1c646da7b975e`, lines 134, 153 and 204) reads ten
                 runner sent each example's                                  files `participant_packet/examples/c044_pub_*.json`, sends each whole, and writes its
                 `note`, which names the group                               report to `parents[6]`, outside the repository; no such report exists in the repository
                 or the expected verdict, and                                history; a file of that name outside the repository has SHA-256
                 the C043 prompts carried no                                 `5fecd63f08dc1b5b2094fe6b722c236f284567b52a9a140f62d4825e63e8648b`
                 note.
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Scope statements

  -------------------------------------------------------------------------------------------------------------------------------------------------------
  ID             Claim                         Section        Kind           Evidence
  -------------- ----------------------------- -------------- -------------- ----------------------------------------------------------------------------
  PFP10-35       `stealth/space-bunny-alpha`   3.1, 5         Scope          Model identifier in the retained reports; no provider, size or training
                 is a new free stealth model                  statement      record exists;
                 offered on OpenRouter as of                                 `projects/mssn_sn_symgam/challenges/01_challenge_protocol.md`
                 2026-09-28; the provider does                               §2
                 not disclose its identity,
                 size or training; its results
                 are exploratory, fall outside
                 SG-CP v1 §2, and may not be
                 reproducible after the
                 stealth period.

PFP10-36       No comparison between prompts 4.1, 5         Scope          Sections 4.1 and 5
                 or models is claimed; no                     statement
                 statistical test was run;
                 costs are not reported.
  -------------------------------------------------------------------------------------------------------------------------------------------------------

## Erratum of version 2.0.1 (Section 4)

  ---------------------------------------------------------------------------------------------------------------------------------------
  ID             Claim             Section        Kind           Evidence
  -------------- ----------------- -------------- -------------- ------------------------------------------------------------------------
  PFP10-37       Each C045 to C050 4.1            Source         Prompt lines `run_c045_matrix.py:219`, `run_c046_matrix.py:270`,
                 runner sent                      inspection;    `run_c047_matrix.py:221`, `run_c048_matrix.py:163`,
                 `Case ID: <id>`                  replay         `run_c049_matrix.py:264`, `run_c050_matrix.py:236` at the run commits of
                 before the case                                 PFP10-28 and at the code baseline; the panel identifiers, the notes and
                 data; for 36 of                                 the author's reading of each identifier are listed in
                 the 60 cases in                                 `verification/formal_math_baselines.json` (`prompt_lines`,
                 the six panels                                  `panel_case_ids`, `panel_cases_with_note`, `identifier_reading_ids`);
                 whose runner is                                 the reading is a judgment, recorded so that it can be disputed case by
                 retained the                                    case
                 identifier names
                 the expected
                 verdict or answer
                 (C045 7, C046 5,
                 C047 4, C048 10,
                 C049 panel A 5,
                 C050 5); the
                 C045, C046, C049
                 and C050 runners
                 sent the whole
                 case record,
                 including the
                 `note` of C049
                 m10 and C050 m09.

  PFP10-38       Under the         4.1            Replay         `verification/formal_math_baselines.json`, field
                 runners' pass                                   `best_trivial_both_accept` and the rows under `trivial_answers`
                 rule, the best
                 answer that needs
                 no mathematics
                 passes 10, 10, 0,
                 3, 2 and 1 of the
                 ten cases of
                 C045, C046, C047,
                 C048, C049 panel
                 A and C050; in
                 C045 and C046 it
                 is a refusal of
                 every case with
                 any listed
                 reason.

  PFP10-39       The C045 and C046 4.2            Replay; source `verification/formal_math_baselines.json`;
                 second checkers                  inspection     `c045_knot_polynomials_from_pd/judge_packet/checkers/exact_checker.py`
                 accept `{}`, a                                  lines 26 to 29 and
                 bare abstention                                 `c046_knuth_bendix_completion/judge_packet/checkers/exact_checker.py`
                 and any refusal                                 lines 28 to 31 at the run commits
                 with a reason and
                 a witness on all
                 ten cases; the
                 C047 second
                 checker accepts
                 an empty
                 coefficient list
                 and an empty list
                 of minor rows on
                 9 of 10; the C048
                 second checker
                 accepts any
                 out-of-scope
                 answer on all
                 ten; the C049
                 second checker
                 accepts a
                 constant "does
                 not exist" on 8
                 of 10; the C045
                 and C046 exact
                 checkers accept
                 any refusal that
                 carries a reason.

  PFP10-40       In C045 and C046  4.1            Retained       The `parsed_ans` fields of the C045 and C046 reports (PFP10-28)
                 the models'                      record
                 passes include
                 refusals only on
                 the cases whose
                 identifiers name
                 a refusal (C045
                 m09 and m10; C046
                 m08 to m10).

PFP10-41       After the runs,   4.2, 4.3       Source         The corrected runners and checkers at commits `e6fbc15cf` and
                 the harness was                  inspection;    `e2f7a3500`; the trivial answers of Section 4.2 replayed against them on
                 corrected: the                   replay         2026-09-29 (recorded in the collection's verification report)
                 C045 and C046
                 second checkers
                 recompute the
                 answer, so a
                 refusal of every
                 case, `{}` and an
                 empty answer fail
                 them; the C047
                 second checker
                 refuses empty
                 certificates; the
                 C048 second
                 checker accepts
                 an out-of-scope
                 answer only for a
                 non-integer
                 coefficient; the
                 runners use
                 opaque per-run
                 tokens; the C045
                 and C046 exact
                 checkers still
                 accept any
                 refusal.
  ---------------------------------------------------------------------------------------------------------------------------------------
