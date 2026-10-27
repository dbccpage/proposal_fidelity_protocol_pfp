# Paper 009 claim ledger

Jeremy H. Carroll. Author-review revision, 2026-09-30, version 1.2.1.\
Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The [manuscript](paper.pdf) is a declared review protocol with
inspectable examples. Each row names its evidence and its limit.
Executable rows name the package test that checks them.

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                            Evidence kind and source                                                                                                                                                                                                                                                                       Limit
  ----------------- -------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------
  G009-01           A claim can be reviewed by       Declared procedure in Sections 1--2 and 4--7                                                                                                                                                                                                                                                   Review method, not
                    connecting its statement,                                                                                                                                                                                                                                                                                                       measured reviewer
                    assumptions, implementation,                                                                                                                                                                                                                                                                                                    effectiveness
                    probes, and evidence

  G009-02           Subtracting the displayed        Arithmetic and telescoping argument in Section 3; `test_triangle_cycle_sum.py::test_potential_subtraction_keeps_cycle_sum`; `test_triangle_cycle_sum.py::test_replacing_claims_by_differences_gives_zero_cycle_sum`; [companion                                                                One declared triangle;
                    potential differences preserves  notebook](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/jupyter_notebooks/009_triangle_cycle_sum.ipynb)               the two operations are
                    the triangle's cycle sum;                                                                                                                                                                                                                                                                                                       distinct
                    replacing the claims by those
                    differences gives cycle sum zero

  G009-03           The semiotic-audit fixture       `test_009_adversarial_reality_gate.py::test_semiotic_sign_drift_detection` (`SemioticAudit`)                                                                                                                                                                                                   No code parsing or
                    compares two supplied strings                                                                                                                                                                                                                                                                                                   semantic-equivalence
                                                                                                                                                                                                                                                                                                                                                    decision

  G009-04           The stagnation fixture checks a  `test_009_adversarial_reality_gate.py::test_stagnation_review_trigger` (`StagnationRecord`)                                                                                                                                                                                                    No strategy or
                    supplied count, gauge flag, and                                                                                                                                                                                                                                                                                                 escape-frequency
                    score                                                                                                                                                                                                                                                                                                                           evidence

  G009-05           The toy verdict function         `test_009_adversarial_reality_gate.py::test_terminal_reality_gate_verdicts` (`evaluate_terminal_reality_gate`)                                                                                                                                                                                 Does not compute
                    branches on supplied scores and                                                                                                                                                                                                                                                                                                 scores or verify flag
                    flags                                                                                                                                                                                                                                                                                                                           provenance

  G009-06           Proposal constructors differ     `MSSN.Level15.theorem1_proposal_non_authority` in                                                                                                                                                                                                                                              Abstract state
                    from the designated terminal     [Level15AuthorityCalculus.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/lean4/Level15AuthorityCalculus.lean);   distinction; runtime
                    constructor under the Lean       [axiom report](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/lean4/axiom_report.txt)                                  correspondence needs
                    definitions                                                                                                                                                                                                                                                                                                                     separate evidence

  G009-07           The same agent state fails the   `MSSN.Level15.theorem2_self_critique_non_verification` in                                                                                                                                                                                                                                      No statistical
                    formal unequal-hash independence [Level15AuthorityCalculus.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/lean4/Level15AuthorityCalculus.lean)    independence claim for
                    predicate                                                                                                                                                                                                                                                                                                                       different models

  G009-08           A populated zero-budget trigger  `PaperER007.exists_populated_zero_budget_trigger_without_license` in                                                                                                                                                                                                                           Finite countermodel
                    can have no licensed target      [TriggerNotLicense.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/lean4/TriggerNotLicense.lean), with its        under declared
                                                     imports `RuntimeLimits` and `SLevel`                                                                                                                                                                                                                                                           lift-budget conditions

  G009-09           The terminal-routing source      Header comment of the repository file [lean4/TerminalizerPolicy.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/lean4/TerminalizerPolicy.lean); not copied into this package                                                                   No compiled theorem
                    carries a warning that its                                                                                                                                                                                                                                                                                                      claimed
                    declarations were not
                    typechecked

  G009-10           The review record format is a    Section 7                                                                                                                                                                                                                                                                                      No automatic harvester
                    template awaiting observed                                                                                                                                                                                                                                                                                                      or execution receipt
                    results

  G009-11           In one retained run of 10        [Trace](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_1790210039.jsonl) at          Labels are historical
                    trials, the adversary challenged `atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_1790210039.jsonl` (SHA-256 `329e29228b3278dc9172bc318d82c38876107175a64c834c386e60d98bd509d7`);                                program-check labels,
                    all 6 checker-refused proposals, `test_recorded_bout_counts.py::test_confusion_counts`                                                                                                                                                                                                                                          not physical ground
                    challenged 2 of the 4 other                                                                                                                                                                                                                                                                                                     truth; models as
                    proposals, and concurred with                                                                                                                                                                                                                                                                                                   reported in the
                    the remaining 2                                                                                                                                                                                                                                                                                                                 receipt; no rate for
                                                                                                                                                                                                                                                                                                                                                    other models,
                                                                                                                                                                                                                                                                                                                                                    lattices, or prompts;
                                                                                                                                                                                                                                                                                                                                                    the test skips outside
                                                                                                                                                                                                                                                                                                                                                    the full repository

  G009-12           The trace field                  Same trace; `test_recorded_bout_counts.py::test_caught_field_is_true_in_every_record`                                                                                                                                                                                                          Explains the withdrawn
                    `adversary_caught_am` is true in                                                                                                                                                                                                                                                                                                10/10 figure
                    all 10 records, including both
                    concurrences, so counting it
                    does not measure detection

  G009-13           A later replay stored with the   [Receipt](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_receipt.json) at            Replay of stored
                    run refuses all 10 recorded      `atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_receipt.json`; `test_recorded_bout_counts.py::test_retained_replay_refuses_all_ten`                                            proposals only; no
                    proposals, including the 4                                                                                                                                                                                                                                                                                                      model was called; the
                    obstruction claims                                                                                                                                                                                                                                                                                                              test skips outside the
                                                                                                                                                                                                                                                                                                                                                    full repository

  G009-14           At the audited commit, the       Replay F1 in the collection's `verification/adversary_gate_falsifiers.json`, produced by `tools/replay_adversary_gate_falsifiers.py` from commit `30609de2c3928238715375a9bac608256fa381d8`; source `adversary/use_cases/act_helpers.py` lines 480 to 498 and `use_cases/bout_service.py`  One constructed input
                    Adversary gate authorizes a         lines 266 to 277 at that commit                                                                                                                                                                                                                                                                with the default
                    proposal on a triangle whose                                                                                                                                                                                                                                                                                                    scorer; the replay
                    cochain (1, 1, 1) has cycle sum                                                                                                                                                                                                                                                                                                 needs a repository
                    3, because Act IV replaces the                                                                                                                                                                                                                                                                                                  checkout with that
                    cochain by zeros on a lifted                                                                                                                                                                                                                                                                                                    commit
                    carrier and Act II then scores
                    the zeros

  G009-15           At the audited commit, a         Replays F2a and F2b in the same record; `act_helpers.py` line 642                                                                                                                                                                                                                              Two constructed
                    critique blocks a candidate                                                                                                                                                                                                                                                                                                     replies
                    exactly when its text contains
                    "DEFECT" or "FLAW": a stated
                    counterexample without those
                    words does not block, and "No
                    defect found" does

  G009-16           At the audited commit, with no   Replay F3 in the same record; `act_helpers.py` lines 917 to 932 and 1008 to 1015                                                                                                                                                                                                               One constructed Act
                    critique the gate's evidence                                                                                                                                                                                                                                                                                                    VII input
                    reference is the SHA-256 of the
                    run key, and the obstruction
                    receipt states
                    `annihilates_coboundary: true`
                    and `norm_bounded: true` as
                    constants, including for a
                    witness that is not balanced

  G009-17           The C012 challenge copy of the   Replay F4 in the same record; `projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/governance/adversary_gate.py` lines 69 to 195 at the audited commit                                                                                                         One copy of 36; the
                    gate writes a narrative and step                                                                                                                                                                                                                                                                                                fixed sentence about
                    record that report full checker                                                                                                                                                                                                                                                                                                 full agreement occurs
                    agreement, a respected budget,                                                                                                                                                                                                                                                                                                  verbatim in four
                    verified repairs on 46 cases and                                                                                                                                                                                                                                                                                                copies
                    a repaired coboundary for a
                    refused run with no cases

G009-18           In the corrected gate a lift     Commit `a054c8ce1`: `adversary/tests/test_honest_gate_falsifiers.py` (66 passed) and `adversary/tests/test_adversarial_m1_it2_1_challenger.py` (44 passed); commit `e6fbc15cf`: `projects/mssn_sn_symgam/challenges/harness_tests/test_harness_honesty.py`    Tests of the corrected
                    carries the input cochain and a                                                                                                                                                                                                                                                                                                 code at those commits;
                    lift that lowers the obstruction                                                                                                                                                                                                                                                                                                the falsifier replay
                    is refused; critiques are typed                                                                                                                                                                                                                                                                                                 itself stays pinned to
                    and an unparsable one blocks;                                                                                                                                                                                                                                                                                                   the audited commit
                    receipts are stored and cited by
                    digest; `AUTHORIZED` requires an
                    `ACCEPTED` verdict from a
                    checker bound to the candidate
                    by digest; the challenge gate
                    copies report reference runs as
                    reference self-consistency with
                    a stated scope
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Claim hygiene

**Supports:** a reusable process for documenting bounded claims,
checking likely failure cases, and preserving the distinction between
inspected and executed evidence; exact arithmetic for one triangle; a
recount of one retained ten-trial run; four falsifiers that locate where
one gate's verdicts came from at one commit.

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
