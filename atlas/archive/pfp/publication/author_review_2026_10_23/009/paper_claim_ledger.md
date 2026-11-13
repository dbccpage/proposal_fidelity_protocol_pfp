# Paper 009 claim ledger

Jeremy H. Carroll. Author-review revision, 2026-10-02, version 0.1.0. \
Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The [manuscript](paper.md) is a declared review protocol with inspectable
examples. Each row names its evidence and its limit. Executable rows name the
package test that checks them.

| ID | Claim | Evidence kind and source | Limit |
| --- | --- | --- | --- |
| G009-01 | A claim can be reviewed by connecting its statement, assumptions, implementation, probes, and evidence | Declared procedure in Sections 1–2 and 4–7 | Review method, not measured reviewer effectiveness |
| G009-02 | Subtracting the displayed potential differences preserves the triangle's cycle sum; replacing the claims by those differences gives cycle sum zero | Arithmetic and telescoping argument in Section 3; `test_triangle_cycle_sum.py::test_potential_subtraction_keeps_cycle_sum`; `test_triangle_cycle_sum.py::test_replacing_claims_by_differences_gives_zero_cycle_sum`; [companion notebook](jupyter_notebooks/009_triangle_cycle_sum.ipynb) | One declared triangle; the two operations are distinct |
| G009-03 | The semiotic-audit fixture compares two supplied strings | `test_009_adversarial_reality_gate.py::test_semiotic_sign_drift_detection` (`SemioticAudit`) | No code parsing or semantic-equivalence decision |
| G009-04 | The stagnation fixture checks a supplied count, gauge flag, and score | `test_009_adversarial_reality_gate.py::test_stagnation_review_trigger` (`StagnationRecord`) | No strategy or escape-frequency evidence |
| G009-05 | The toy verdict function branches on supplied scores and flags | `test_009_adversarial_reality_gate.py::test_terminal_reality_gate_verdicts` (`evaluate_terminal_reality_gate`) | Does not compute scores or verify flag provenance |
| G009-06 | Proposal constructors differ from the designated terminal constructor under the Lean definitions | `MSSN.Level15.theorem1_proposal_non_authority` in [Level15AuthorityCalculus.lean](lean4/Level15AuthorityCalculus.lean); [axiom report](lean4/axiom_report.txt) | Abstract state distinction; runtime correspondence needs separate evidence |
| G009-07 | The same agent state fails the formal unequal-hash independence predicate | `MSSN.Level15.theorem2_self_critique_non_verification` in [Level15AuthorityCalculus.lean](lean4/Level15AuthorityCalculus.lean) | No statistical independence claim for different models |
| G009-08 | A populated zero-budget trigger can have no licensed target | `PaperER007.exists_populated_zero_budget_trigger_without_license` in [TriggerNotLicense.lean](lean4/TriggerNotLicense.lean), with its imports `RuntimeLimits` and `SLevel` | Finite countermodel under declared lift-budget conditions |
| G009-09 | The terminal-routing source carries a warning that its declarations were not typechecked | Header comment of the repository file [lean4/TerminalizerPolicy.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/lean4/TerminalizerPolicy.lean); not copied into this package | No compiled theorem claimed |
| G009-10 | The review record format is a template awaiting observed results | Section 7 | No automatic harvester or execution receipt |
| G009-11 | In one retained run of 10 trials, the adversary challenged all 6 checker-refused proposals, challenged 2 of the 4 other proposals, and concurred with the remaining 2 | [Trace](https://github.com/dbccpage/the_symbol_game/blob/593230f7daba7aa04d7c41dd456dfbd00a39bcbd/atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_1790210039.jsonl) at `atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_1790210039.jsonl` (SHA-256 `329e29228b3278dc9172bc318d82c38876107175a64c834c386e60d98bd509d7`); `test_recorded_bout_counts.py::test_confusion_counts` | Labels are historical program-check labels, not physical ground truth; models as reported in the receipt; no rate for other models, lattices, or prompts; the bundled copy is recounted without model or native-checker execution |
| G009-12 | The trace field `adversary_caught_am` is true in all 10 records, including both concurrences, so counting it does not measure detection | Same trace; `test_recorded_bout_counts.py::test_caught_field_is_true_in_every_record` | Explains the withdrawn 10/10 figure |
| G009-13 | A later replay stored with the run refuses all 10 recorded proposals, including the 4 obstruction claims | [Receipt](https://github.com/dbccpage/the_symbol_game/blob/593230f7daba7aa04d7c41dd456dfbd00a39bcbd/atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_receipt.json) at `atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/results/demo2_r7_adversarial_debate_receipt.json`; `test_recorded_bout_counts.py::test_retained_replay_refuses_all_ten` | Retained replay report only; no fresh checker replay; its checker revision is not pinned; the bundled copy is recounted without model or native-checker execution |
| G009-14 | At the audited commit, the Adversary gate authorizes a proposal on a triangle whose cochain (1, 1, 1) has cycle sum 3, because Act IV replaces the cochain by zeros on a lifted carrier and Act II then scores the zeros | Replay F1 in the collection's `verification/adversary_gate_falsifiers.json`, produced by `tools/replay_adversary_gate_falsifiers.py` from commit `30609de2c3928238715375a9bac608256fa381d8`; source `adversary/use_cases/act_helpers.py` lines 480 to 498 and `use_cases/bout_service.py` lines 266 to 277 at that commit | One constructed input with the default scorer; the replay needs a repository checkout with that commit |
| G009-15 | At the audited commit, a critique blocks a candidate exactly when its text contains "DEFECT" or "FLAW": a stated counterexample without those words does not block, and "No defect found" does | Replays F2a and F2b in the same record; `act_helpers.py` line 642 | Two constructed replies |
| G009-16 | At the audited commit, with no critique the gate's evidence reference is the SHA-256 of the run key, and the obstruction receipt states `annihilates_coboundary: true` and `norm_bounded: true` as constants, including for a witness that is not balanced | Replay F3 in the same record; `act_helpers.py` lines 917 to 932 and 1008 to 1015 | One constructed Act VII input |
| G009-17 | The C012 challenge copy of the gate writes a narrative and step record that report full checker agreement, a respected budget, verified repairs on 46 cases and a repaired coboundary for a refused run with no cases | Replay F4 in the same record; `projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/governance/adversary_gate.py` lines 69 to 195 at the audited commit | One copy of 36; the fixed sentence about full agreement occurs verbatim in four copies |
| G009-18 | In the corrected gate a lift carries the input cochain and a lift that lowers the obstruction is refused; critiques are typed and an unparsable one blocks; receipts are stored and cited by digest; `AUTHORIZED` requires an `ACCEPTED` verdict from a checker bound to the candidate by digest; the challenge gate copies report reference runs as reference self-consistency with a stated scope | Commit [`a054c8ce1`](https://github.com/dbccpage/the_symbol_game/commit/a054c8ce17c3025ac5518aaeef29096a299519bb): `adversary/tests/test_honest_gate_falsifiers.py` (66 passed) and `adversary/tests/test_adversarial_m1_it2_1_challenger.py` (44 passed); commit [`e6fbc15cf`](https://github.com/dbccpage/the_symbol_game/commit/e6fbc15cf011121597a82a1d199626063bedf7c0): `projects/mssn_sn_symgam/challenges/harness_tests/test_harness_honesty.py` | Corrected code source-inspected; passing counts are historical, not fresh v0.1 tests; the falsifier record stays pinned to the audited commit |

## Claim hygiene

**Supports:** a reusable process for documenting bounded claims, checking likely
failure cases, and preserving the distinction between inspected and executed
evidence; exact arithmetic for one triangle; a recount of one retained ten-trial
run; five probes in four defect families that locate where one gate's verdicts came from at one
commit.

**Does not support:** guaranteed semantic truth, universal finite search
termination, proof of model independence, psychological effects, or a catch
rate for adversarial review in general.

**Narrowest defensible claim:** the stated review procedure can be applied to
the concrete source artifacts and finite examples identified in this guide.

**Next check:** independent reviewers apply the protocol to the revised papers,
record actionable discrepancies, and attach actual command outcomes where
execution is required. Any effectiveness claim needs a separate study with
independently checked labels.

## v0.1 deposit additions

The three retained records are bundled under `docs/historical_evidence/` with
byte identities and source paths. `test_review_counts.py` checks exact fractions,
negative controls, undefined denominators, the five-record/four-family census,
and every retained record digest. These checks establish recount consistency
and custody, not a new provider trial or execution of the historical gate.
The local quiz, guide, separate key, and `tools/review_capstone.py` teach those
evidence boundaries. Fresh validation is recorded in `docs/v01_review_2026_10_02.json`.

## 2026-10-23 harness extension

| Claim | Evidence | Limit |
| --- | --- | --- |
| New research mechanism | Paper 029 source manifest and focused checks | Implemented adaptation; historical evidence remains separately pinned |
| New model effects | Replayed campaign report | NOT_MEASURED; live campaign NOT_RUN |
| External AIDE2 findings | Versioned PDF and page-level source map | Attribution, not replication |
| Formal results above | Existing proofs and finite examples | No additional formal theorem or Lean claim |
