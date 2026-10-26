# Paper 009 claim ledger

Jeremy H. Carroll. Author-review revision, 2026-10-02, version 0.1.0.\
Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The [manuscript](paper.pdf) is a declared review protocol with
inspectable examples. Each row names its evidence and its limit.
Executable rows name the package test that checks them.

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                            Evidence kind and source                                                                                                                                                                                                                                         Limit
  ----------------- -------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------
  G009-01           A claim can be reviewed by       Declared procedure in Sections 1--2 and 4--7                                                                                                                                                                                                                     Review method, not
                    connecting its statement,                                                                                                                                                                                                                                                                         measured reviewer
                    assumptions, implementation,                                                                                                                                                                                                                                                                      effectiveness
                    probes, and evidence

  G009-02           Subtracting the displayed        Arithmetic and telescoping argument in Section 3; `test_triangle_cycle_sum.py::test_potential_subtraction_keeps_cycle_sum`; `test_triangle_cycle_sum.py::test_replacing_claims_by_differences_gives_zero_cycle_sum`; [companion                                  One declared triangle;
                    potential differences preserves  notebook](jupyter_notebooks/009_triangle_cycle_sum.ipynb)                                                                                                                                                                                                        the two operations are
                    the triangle's cycle sum;                                                                                                                                                                                                                                                                         distinct
                    replacing the claims by those
                    differences gives cycle sum zero

  G009-03           The semiotic-audit fixture       `test_009_adversarial_reality_gate.py::test_semiotic_sign_drift_detection` (`SemioticAudit`)                                                                                                                                                                     No code parsing or
                    compares two supplied strings                                                                                                                                                                                                                                                                     semantic-equivalence
                                                                                                                                                                                                                                                                                                                      decision

  G009-04           The stagnation fixture checks a  `test_009_adversarial_reality_gate.py::test_stagnation_review_trigger` (`StagnationRecord`)                                                                                                                                                                      No strategy or
                    supplied count, gauge flag, and                                                                                                                                                                                                                                                                   escape-frequency
                    score                                                                                                                                                                                                                                                                                             evidence

  G009-05           The toy verdict function         `test_009_adversarial_reality_gate.py::test_terminal_reality_gate_verdicts` (`evaluate_terminal_reality_gate`)                                                                                                                                                   Does not compute
                    branches on supplied scores and                                                                                                                                                                                                                                                                   scores or verify flag
                    flags                                                                                                                                                                                                                                                                                             provenance

  G009-06           Proposal constructors differ     `MSSN.Level15.theorem1_proposal_non_authority` in [Level15AuthorityCalculus.lean](lean4/Level15AuthorityCalculus.lean); [axiom report](lean4/axiom_report.txt)                                                                                                   Abstract state
                    from the designated terminal                                                                                                                                                                                                                                                                      distinction; runtime
                    constructor under the Lean                                                                                                                                                                                                                                                                        correspondence needs
                    definitions                                                                                                                                                                                                                                                                                       separate evidence

  G009-07           The same agent state fails the   `MSSN.Level15.theorem2_self_critique_non_verification` in [Level15AuthorityCalculus.lean](lean4/Level15AuthorityCalculus.lean)                                                                                                                                   No statistical
                    formal unequal-hash independence                                                                                                                                                                                                                                                                  independence claim for
                    predicate                                                                                                                                                                                                                                                                                         different models

  G009-08           A populated zero-budget trigger  `PaperER007.exists_populated_zero_budget_trigger_without_license` in [TriggerNotLicense.lean](lean4/TriggerNotLicense.lean), with its imports `RuntimeLimits` and `SLevel`                                                                                       Finite countermodel
                    can have no licensed target                                                                                                                                                                                                                                                                       under declared
                                                                                                                                                                                                                                                                                                                      lift-budget conditions

  G009-09           The terminal-routing source      Header comment of the repository file [lean4/TerminalizerPolicy.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/lean4/TerminalizerPolicy.lean); not copied into this package                                     No compiled theorem
                    carries a warning that its                                                                                                                                                                                                                                                                        claimed
                    declarations were not
                    typechecked

  G009-10           The review record format is a    Section 7                                                                                                                                                                                                                                                        No automatic harvester
                    template awaiting observed                                                                                                                                                                                                                                                                        or execution receipt
                    results

  G009-11           In one retained run of 10        [Trace](https://github.com/dbccpage/the_symbol_game/blob/593230f7daba7aa04d7c41dd456dfbd00a39bcbd/omega_engine_atlas/coda_atlas/omega_engine_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_1790210039.jsonl)   Labels are historical
                    trials, the adversary challenged at `omega_engine_atlas/coda_atlas/omega_engine_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_1790210039.jsonl` (SHA-256 `329e29228b3278dc9172bc318d82c38876107175a64c834c386e60d98bd509d7`);                   program-check labels,
                    all 6 checker-refused proposals, `test_recorded_bout_counts.py::test_confusion_counts`                                                                                                                                                                                                            not physical ground
                    challenged 2 of the 4 other                                                                                                                                                                                                                                                                       truth; models as
                    proposals, and concurred with                                                                                                                                                                                                                                                                     reported in the
                    the remaining 2                                                                                                                                                                                                                                                                                   receipt; no rate for
                                                                                                                                                                                                                                                                                                                      other models,
                                                                                                                                                                                                                                                                                                                      lattices, or prompts;
                                                                                                                                                                                                                                                                                                                      the bundled copy is
                                                                                                                                                                                                                                                                                                                      recounted without
                                                                                                                                                                                                                                                                                                                      model or
                                                                                                                                                                                                                                                                                                                      native-checker
                                                                                                                                                                                                                                                                                                                      execution

  G009-12           The trace field                  Same trace; `test_recorded_bout_counts.py::test_caught_field_is_true_in_every_record`                                                                                                                                                                            Explains the withdrawn
                    `adversary_caught_am` is true in                                                                                                                                                                                                                                                                  10/10 figure
                    all 10 records, including both
                    concurrences, so counting it
                    does not measure detection

  G009-13           A later replay stored with the   [Receipt](https://github.com/dbccpage/the_symbol_game/blob/593230f7daba7aa04d7c41dd456dfbd00a39bcbd/omega_engine_atlas/coda_atlas/omega_engine_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_receipt.json) at  Retained replay report
                    run refuses all 10 recorded      `omega_engine_atlas/coda_atlas/omega_engine_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_receipt.json`; `test_recorded_bout_counts.py::test_retained_replay_refuses_all_ten`                                  only; no fresh checker
                    proposals, including the 4                                                                                                                                                                                                                                                                        replay; its checker
                    obstruction claims                                                                                                                                                                                                                                                                                revision is not
                                                                                                                                                                                                                                                                                                                      pinned; the bundled
                                                                                                                                                                                                                                                                                                                      copy is recounted
                                                                                                                                                                                                                                                                                                                      without model or
                                                                                                                                                                                                                                                                                                                      native-checker
                                                                                                                                                                                                                                                                                                                      execution

  G009-14           At the audited commit, the       Replay F1 in the collection's `verification/woland_gate_falsifiers.json`, produced by `tools/replay_woland_gate_falsifiers.py` from commit `30609de2c3928238715375a9bac608256fa381d8`; source `omega_engine_woland/use_cases/act_helpers.py` lines 480 to 498    One constructed input
                    Woland gate authorizes a         and `use_cases/bout_service.py` lines 266 to 277 at that commit                                                                                                                                                                                                  with the default
                    proposal on a triangle whose                                                                                                                                                                                                                                                                      scorer; the replay
                    cochain (1, 1, 1) has cycle sum                                                                                                                                                                                                                                                                   needs a repository
                    3, because Act IV replaces the                                                                                                                                                                                                                                                                    checkout with that
                    cochain by zeros on a lifted                                                                                                                                                                                                                                                                      commit
                    carrier and Act II then scores
                    the zeros

  G009-15           At the audited commit, a         Replays F2a and F2b in the same record; `act_helpers.py` line 642                                                                                                                                                                                                Two constructed
                    critique blocks a candidate                                                                                                                                                                                                                                                                       replies
                    exactly when its text contains
                    "DEFECT" or "FLAW": a stated
                    counterexample without those
                    words does not block, and "No
                    defect found" does

  G009-16           At the audited commit, with no   Replay F3 in the same record; `act_helpers.py` lines 917 to 932 and 1008 to 1015                                                                                                                                                                                 One constructed Act
                    critique the gate's evidence                                                                                                                                                                                                                                                                      VII input
                    reference is the SHA-256 of the
                    run key, and the obstruction
                    receipt states
                    `annihilates_coboundary: true`
                    and `norm_bounded: true` as
                    constants, including for a
                    witness that is not balanced

  G009-17           The C012 challenge copy of the   Replay F4 in the same record; `omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/governance/woland_gate.py` lines 69 to 195 at the audited commit                                                                           One copy of 36; the
                    gate writes a narrative and step                                                                                                                                                                                                                                                                  fixed sentence about
                    record that report full checker                                                                                                                                                                                                                                                                   full agreement occurs
                    agreement, a respected budget,                                                                                                                                                                                                                                                                    verbatim in four
                    verified repairs on 46 cases and                                                                                                                                                                                                                                                                  copies
                    a repaired coboundary for a
                    refused run with no cases

  G009-18           In the corrected gate a lift     Commit [`a054c8ce1`](https://github.com/dbccpage/the_symbol_game/commit/a054c8ce17c3025ac5518aaeef29096a299519bb): `omega_engine_woland/tests/test_honest_gate_falsifiers.py` (66 passed) and                                                                    Corrected code
                    carries the input cochain and a  `omega_engine_woland/tests/test_adversarial_m1_it2_1_challenger.py` (44 passed); commit [`e6fbc15cf`](https://github.com/dbccpage/the_symbol_game/commit/e6fbc15cf011121597a82a1d199626063bedf7c0):                                                              source-inspected;
                    lift that lowers the obstruction `omega_engine_projects/mssn_sn_symgam/challenges/harness_tests/test_harness_honesty.py`                                                                                                                                                                          passing counts are
                    is refused; critiques are typed                                                                                                                                                                                                                                                                   historical, not fresh
                    and an unparsable one blocks;                                                                                                                                                                                                                                                                     v0.1 tests; the
                    receipts are stored and cited by                                                                                                                                                                                                                                                                  falsifier record stays
                    digest; `AUTHORIZED` requires an                                                                                                                                                                                                                                                                  pinned to the audited
                    `ACCEPTED` verdict from a                                                                                                                                                                                                                                                                         commit
                    checker bound to the candidate
                    by digest; the challenge gate
                    copies report reference runs as
                    reference self-consistency with
                    a stated scope
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Claim hygiene

**Supports:** a reusable process for documenting bounded claims,
checking likely failure cases, and preserving the distinction between
inspected and executed evidence; exact arithmetic for one triangle; a
recount of one retained ten-trial run; five probes in four defect
families that locate where one gate's verdicts came from at one commit.

**Does not support:** guaranteed semantic truth, universal finite search
termination, proof of model independence, psychological effects, or a
catch rate for adversarial review in general.

**Narrowest defensible claim:** the stated review procedure can be
applied to the concrete source artifacts and finite examples identified
in this guide.

**Next check:** independent reviewers apply the protocol to the revised
papers, record actionable discrepancies, and attach actual command
outcomes where execution is required. Any effectiveness claim needs a
separate study with independently checked labels.

## v0.1 deposit additions

The three retained records are bundled under `docs/historical_evidence/`
with byte identities and source paths. `test_review_counts.py` checks
exact fractions, negative controls, undefined denominators, the
five-record/four-family census, and every retained record digest. These
checks establish recount consistency and custody, not a new provider
trial or execution of the historical gate. The local quiz, guide,
separate key, and `tools/review_capstone.py` teach those evidence
boundaries. Fresh validation is recorded in
`docs/v01_review_2026_10_02.json`.

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
