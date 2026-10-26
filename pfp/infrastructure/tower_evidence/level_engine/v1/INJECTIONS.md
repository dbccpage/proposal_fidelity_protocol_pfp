# Injection record

AuthorityEffect: None.

Written by `python tools/inject.py`. Each injection is a minimal edit on disk,
never committed. It must make the named command exit nonzero and print the
exact code; the edit is then reversed and the same command must pass. The
tree is checked clean before and after. Nothing is regenerated or repinned
while an injection is live.

| id | guard | injected defect | file | command | code | fired | recovered |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I1 | fixed claims | the candidate builder offers instances on claim forms (a claim-overwrite repair) | `engine/search.py` | `run_bootstrap.py --out _scratch/inj` | `CLAIM_FROZEN` | yes (exit 1) | yes (exit 0) |
| I2 | embargo | a challenge declares a four-item search bound | `payload/cell_orientation/spec.py` | `run_bootstrap.py --out _scratch/inj` | `GUARD_EMBARGO` | yes (exit 1) | yes (exit 0) |
| I3 | exact values | a fixture value is written as a JSON float | `payload/distance_form/instance.json` | `run_bootstrap.py --out _scratch/inj` | `RR-FLOAT` | yes (exit 1) | yes (exit 0) |
| I4 | fixture expectations | the own negative is replaced by the positive | `payload/edge_endpoints/instance.json` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I5 | intake | the own negative is deleted | `payload/edge_endpoints/instance.json` | `run_bootstrap.py --out _scratch/inj` | `MISSING_NEGATIVE` | yes (exit 1) | yes (exit 0) |
| I6 | intake | the positive is an empty payload | `payload/cell_faces/instance.json` | `run_bootstrap.py --out _scratch/inj` | `EMPTY_FIXTURE` | yes (exit 1) | yes (exit 0) |
| I7 | exhaustion | the enumeration stops one item count early | `engine/search.py` | `run_bootstrap.py --out _scratch/inj` | `RR-EXHAUSTION` | yes (exit 1) | yes (exit 0) |
| I8 | custody | one character of the pinned tree id changes | `PINS.json` | `tools/vendor.py --check` | `RR-PIN` | yes (exit 1) | yes (exit 0) |
| I9 | transport | the typed map drops the relations, so fixtures coincide | `outward/bundles.py` | `run_bootstrap.py --out _scratch/inj` | `RR-TRANSPORT-COLLAPSE` | yes (exit 1) | yes (exit 0) |
| I10 | hygiene | a watched word is appended to a payload restatement | `payload/cell_faces/RESTATEMENT.md` | `gate.py --step hygiene` | `watch=1` | yes (exit 1) | yes (exit 0) |
| I11 | agreement | the compile step drops the separation requirement (a lossy restatement) | `payload/edge_endpoints/spec.py` | `run_bootstrap.py --out _scratch/inj && tools/preflight_draft.py _scratch/inj L002 tests/checkers/arcs.py` | `DISAGREEMENT:near_protect` | yes (exit 1) | yes (exit 0) |
| I12 | clause census | a hosted challenge declares its answer native (type D) | `payload/distance_form/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `ANSWER_TYPE_DISAGREES` | yes (exit 1) | yes (exit 0) |
| I13 | descent | decoding gives a fresh datum an old meaning | `engine/encoding.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-NON-DESCENT` | yes (exit 1) | yes (exit 0) |
| I14 | binding | a ladder row digest is edited | `bindings/L003.json` | `tools/bind.py --check` | `ROW_DIGEST` | yes (exit 1) | yes (exit 0) |
| I15 | Lean tokens | a law's proof is replaced by a placeholder token | `engine/lean/ExactRat/Laws.lean` | `gate.py --step lean` | `FORBIDDEN TOKEN` | yes (exit 1) | yes (exit 0) |
| I16 | Lean axioms | a reported law is proved through Classical.choice | `engine/lean/ExactRat/Laws.lean` | `gate.py --step lean` | `RR-AXIOM` | yes (exit 1) | yes (exit 0) |
| I17 | Lean certificates | a generated certificate states the opposite verdict | `payload/distance_form/lean/DistanceForm.lean` | `gate.py --step lean` | `LEAN_BUILD_FAILED` | yes (exit 1) | yes (exit 0) |
| I18 | lift: certified survivor | the declared dual witness names two positions with different keys | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `NO_CERTIFIED_SURVIVOR` | yes (exit 1) | yes (exit 0) |
| I19 | lift: claims fixed | the proposal rewrites the demand's last entry | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `CLAIM_FROZEN` | yes (exit 1) | yes (exit 0) |
| I20 | lift: exhaustion | the enumeration never tries the halting choice | `engine/ladder.py` | `tools/lift_check.py` | `EXHAUSTION_NOT_CLOSED` | yes (exit 1) | yes (exit 0) |
| I21 | lift: context witness | the declared context pair is not collapsed at the source | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `NO_CONTEXT_WITNESS` | yes (exit 1) | yes (exit 0) |
| I22 | lift: class frozen | the extension class is edited after its pre-registration | `lifts/record_reading/CLASS.json` | `tools/lift_check.py` | `CLASS_NOT_PREREGISTERED` | yes (exit 1) | yes (exit 0) |
| I23 | lift: minimal, ties retained | the proposal drops one of the two tied minima | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `NOT_MINIMAL_OVER_A_CLASS` | yes (exit 1) | yes (exit 0) |
| I24 | lift: traceable | the new capability is declared at the active entry | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `UNTRACEABLE` | yes (exit 1) | yes (exit 0) |
| I25 | lift: resolved | one answer entry fires the climb instead of the constant map | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `NOT_RESOLVED` | yes (exit 1) | yes (exit 0) |
| I26 | lift: preservation | the embedding reads the oldest entries instead of ignoring them | `engine/ladder.py` | `tools/lift_check.py` | `NOT_PRESERVED` | yes (exit 1) | yes (exit 0) |
| I27 | lift: rollback | the carrier's down map reads the wrong record entry | `engine/ladder.py` | `tools/lift_check.py` | `RR-ROLLBACK` | yes (exit 1) | yes (exit 0) |
| I28 | lift: descent | the partial restriction gives a new term an old meaning | `engine/ladder.py` | `tools/lift_check.py` | `RR-NON-DESCENT` | yes (exit 1) | yes (exit 0) |
| I29 | lift: non-trivial, priced | the step is declared free | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `RR-TRIVIAL-LIFT` | yes (exit 1) | yes (exit 0) |
| I30 | lift: survival accounting | the old ceiling is declared preserved, not refined | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `SILENT_DRIFT` | yes (exit 1) | yes (exit 0) |
| I31 | lift: evidence only | a step carries an activation field | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `AUTHORITY_FIELD` | yes (exit 1) | yes (exit 0) |
| I32 | lift: budget | the last step spends no budget | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `BUDGET_NOT_DECREASING` | yes (exit 1) | yes (exit 0) |
| I33 | lift: replay | the exhibit pointer names another program's enablements | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `REPLAY_MISMATCH` | yes (exit 1) | yes (exit 0) |
| I34 | lift: chain | the second step starts from a budget the first did not leave | `lifts/record_reading/proposals.json` | `tools/lift_check.py` | `CHAIN_BROKEN` | yes (exit 1) | yes (exit 0) |
| I35 | reach records | the carrier half stops booking name-blindness in the loss ledger | `outward/reach.py` | `-m pytest -q -p no:cacheprovider tests/test_reach_records.py -k up_to_the_cap` | `TC-UNBOOKED-STANDING-ENTRY` | yes (exit 1) | yes (exit 0) |
| I36 | harness host | the carrier registry stops declaring 19L57G1's harness host | `../mssn_sn_tower/reach/registry/carriers.json` | `tools/reach_ledger_check.py` | `does not verify: RR-PRODUCER-VERDICT` | yes (exit 1) | yes (exit 0) |
| I37 | Lean certificates (a level's own module) | a generated certificate states the opposite verdict | `payload/scope_fence/lean/ScopeFence.lean` | `gate.py --step lean` | `LEAN_BUILD_FAILED` | yes (exit 1) | yes (exit 0) |
| I38 | Lean citations in a record | every certificate is looked up in one level's module | `outward/reach.py` | `-m pytest -q -p no:cacheprovider tests/test_reach_records.py -k working_tree and 10` | `RR-STATEMENT` | yes (exit 1) | yes (exit 0) |
| I39 | compatibility square | the unit square reads the counit on its left side | `bindings/adapters/L008.py` | `-m pytest -q -p no:cacheprovider tests/test_reach_records.py -k working_tree and 8` | `TC-CRITERION-MISSING` | yes (exit 1) | yes (exit 0) |
| I40 | ordered closure | a loop's closure is decided by its signed count of each turn | `payload/loop_products/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I41 | scope fence | the fence stops refusing a scope past the table | `payload/scope_fence/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:mut` | yes (exit 1) | yes (exit 0) |
| I42 | exact roots | a claimed root is accepted within a tolerance of 1/1000 | `payload/table_polynomial/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I43 | recomputed split | the split reads the load back instead of recomputing its parts | `payload/three_way_split/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_mark` | yes (exit 1) | yes (exit 0) |
| I44 | feasible flow | a zero gap certifies without the flow balancing | `payload/flow_certificate/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I45 | least span | any span dividing the length is accepted, not only the least | `payload/cycle_words/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I46 | freeze (imported round) | an expectation frozen in E0 is edited | `payload/edge_endpoints/expect.json` | `gate.py --step freeze` | `FROZEN FILE DIFFERS FROM THE SOURCE` | yes (exit 1) | yes (exit 0) |
| I47 | embargo list | rung seven's question is dropped from the embargo list | `engine/guards.py` | `gate.py --step embargo` | `EMBARGO LIST DRIFT` | yes (exit 1) | yes (exit 0) |
| I48 | Q-level registrations | a registered sealed theorem's name is misspelled | `bindings/qlevels.json` | `run_bootstrap.py --out _scratch/inj` | `RR-STATEMENT` | yes (exit 1) | yes (exit 0) |
| I49 | replayed steps | a stated step is taken without checking it is a sealed one-step reduct | `payload/positioned_join/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_absorb_one` | yes (exit 1) | yes (exit 0) |
| I50 | stages kept apart | a map is judged by injectivity alone, not by the target's classes | `payload/stage_chain/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I51 | sealed validity | the new stage is judged without the sealed validity check | `payload/conservative_embedding/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_invalid` | yes (exit 1) | yes (exit 0) |
| I52 | carried reversal | a dagger is accepted when it names any arrow, not the transposed one | `payload/carried_reversal/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_not_involution` | yes (exit 1) | yes (exit 0) |
| I53 | balanced witness | the closed route's witness is accepted without being a sealed boundary | `payload/route_replay/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_dual` | yes (exit 1) | yes (exit 0) |
| I54 | whole menu | the formula's domain is read from the claim, not from the sealed menu | `payload/bounded_mask/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_truncated` | yes (exit 1) | yes (exit 0) |
| I55 | host verifier | a terminal is accepted from any verifier | `payload/host_bound_verdict/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I56 | digest binding | container digests are not recomputed | `payload/tagged_digest/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_digest` | yes (exit 1) | yes (exit 0) |
| I57 | source equations | the chain's maps are not checked on source equations | `payload/stage_chain/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_equation` | yes (exit 1) | yes (exit 0) |
| I58 | axiom-free restatement | an axiom-free theorem is restated with a placeholder axiom | `outward/reach.py` | `-m pytest -q -p no:cacheprovider tests/test_reach_records.py -k restated_axiom_report` | `FAILED tests/test_reach_records.py::test_the_restated_axiom_report_keeps_every_line` | yes (exit 1) | yes (exit 0) |
| I59 | sealed boundary | the boundary maps are accepted when their composites vanish, whatever they are | `payload/boundary_chain/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_tail` | yes (exit 1) | yes (exit 0) |
| I60 | observed ledger | merges are counted only among protected pairs | `payload/observed_blocks/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_unrecorded` | yes (exit 1) | yes (exit 0) |
| I61 | computed effect rows | declared effect rows are trusted | `payload/granted_steps/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_understated` | yes (exit 1) | yes (exit 0) |
| I62 | named blockers | a Q-level is blocked by a reason that is neither an embargo item nor named | `bindings/qlevels.json` | `run_bootstrap.py --out _scratch/inj` | `UNKNOWN_BLOCKER` | yes (exit 1) | yes (exit 0) |
| I63 | row sums | a row is accepted when it sums to at most one | `payload/step_weights/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_negative` | yes (exit 1) | yes (exit 0) |
| I64 | positive evidence | an observation is accepted whatever its evidence | `payload/weighted_update/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_zero_later` | yes (exit 1) | yes (exit 0) |
| I65 | exact pair product | the product is taken slot by slot | `payload/mirror_pairs/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I66 | unit size | any nonzero size is accepted as a unit row | `payload/unit_rows/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I67 | computed rank | any positive claimed rank is accepted | `payload/joint_rank/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I68 | whole-table size keeping | size keeping is judged by sampling the probe rows | `payload/size_keeping/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I69 | one-signed rest | a rest of both signs is accepted | `payload/signed_totals/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I70 | table given | roots are accepted with no table | `payload/table_roots/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:near_no_table` | yes (exit 1) | yes (exit 0) |
| I71 | owned joint moves | a claim's joint move is not required to be made of the players' moves | `payload/joint_payoffs/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I72 | unilateral changes | the first player's changes of move are not tried | `payload/stable_profiles/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_gain` | yes (exit 1) | yes (exit 0) |
| I73 | witnessed proofs | a proved triple is not required to carry a witness | `payload/witnessed_triples/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I74 | every overlap | overlaps are checked only between neighbouring choices | `payload/overlap_choices/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I75 | commuting checks | the exchange count is not reduced modulo two | `payload/commuting_checks/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_anti` | yes (exit 1) | yes (exit 0) |
| I76 | map given | a match is claimed with no map required | `payload/step_squares/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_no_map` | yes (exit 1) | yes (exit 0) |
| I77 | no surrogate evidence | offered counts are not refused | `payload/answer_keeping/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_offered` | yes (exit 1) | yes (exit 0) |
| I78 | ordered face product | the product is compared as an unordered summary | `payload/face_products/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_order` | yes (exit 1) | yes (exit 0) |
| I79 | named frame | coordinates with no frame named are read in a default frame | `payload/named_frames/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I80 | recomputed total | the claimed total is read, not recomputed | `payload/two_party_bound/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:mut` | yes (exit 1) | yes (exit 0) |
| I81 | both ends | a change of labels is applied at a link's first end only | `payload/walk_transport/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I82 | trace one | a reduction's trace is not checked | `payload/side_reduction/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I83 | recomputed weights | reported weights are trusted | `payload/split_weights/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I84 | real eigenvalues | the discriminant is not checked | `payload/square_one/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I85 | far-choice blindness | near weights may move with the far choice | `payload/far_blind/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I86 | sequential weights | the joint weights are taken as products of the separate weights | `payload/ordered_splits/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I87 | outward enclosure | only the upper end of a claimed bound is checked | `payload/outward_bounds/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:mut` | yes (exit 1) | yes (exit 0) |
| I88 | checked rim | the declared rim edges are not checked | `payload/rim_cochains/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I89 | mutual wait | two endpoints both waiting to receive are not refused | `payload/dual_endpoints/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I90 | bounded jumps | a jump is not required to carry a loss bound | `payload/scale_steps/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I91 | same background | a counterfactual may draw its background again | `payload/same_background/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I92 | named sources | a payload module a spec imports is left out of the record's sources | `outward/bundles.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k named_source` | `UNNAMED_SOURCE` | yes (exit 1) | yes (exit 0) |
| I93 | carrier part of a registration | a harness record is read as a replay of sealed evidence | `outward/qlevels.py` | `run_bootstrap.py --out _scratch/inj` | `STALE_REGISTRATION` | yes (exit 1) | yes (exit 0) |
| I94 | ruling D4 framing | a record at an apparatus level is framed as a supplied challenge | `outward/reach.py` | `-m pytest -q -p no:cacheprovider tests/test_reach_records.py -k d4` | `D4_FRAMING` | yes (exit 1) | yes (exit 0) |
| I95 | carrier cap | the carrier cap reverts to 12 | `engine/structure.py` | `run_bootstrap.py --out _scratch/inj` | `SIZE_CAP` | yes (exit 1) | yes (exit 0) |
| I96 | declared class count | a class beyond the budget is enumerated instead of declared | `engine/search.py` | `-m pytest -q -p no:cacheprovider tests/test_kinds_search.py -k over_the_budget` | `class_over_budget` | yes (exit 1) | yes (exit 0) |
| I97 | digests as values | descent drops the hosted digests | `engine/encoding.py` | `run_bootstrap.py --out _scratch/inj` | `RR-NON-DESCENT` | yes (exit 1) | yes (exit 0) |
| I98 | induction certificate | the certificate no longer checks the value at the start | `engine/lean/ExactRat/Poly.lean` | `gate.py --step lean` | `LEAN_BUILD_FAILED` | yes (exit 1) | yes (exit 0) |
| I99 | no return | a listed cell is checked only for existing, not against earlier removals | `payload/filtered_pages/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:mut` | yes (exit 1) | yes (exit 0) |
| I100 | every representative | only the zero corner cochain is tried | `payload/class_operations/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I101 | ordered closure | closure is judged by the parity of the face values | `payload/closed_faces/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I102 | digest recomputed | the seal's digest is read, not recomputed from the axiom list | `payload/bound_axioms/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_digest` | yes (exit 1) | yes (exit 0) |
| I103 | external by digest | a confirmation counts as external when its evaluator is another element | `payload/confirmed_runs/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_self` | yes (exit 1) | yes (exit 0) |
| I104 | hinge incidence | a term is checked only for its number of patches | `payload/hinge_deficits/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I105 | one root | any positive drop in sign changes is accepted | `payload/isolated_roots/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I106 | every n | the bound is checked at the sample indices only | `payload/rated_limits/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_far` | yes (exit 1) | yes (exit 0) |
| I107 | every depth | the estimate is checked at the listed depths only | `payload/refined_sums/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_far` | yes (exit 1) | yes (exit 0) |
| I108 | right fibre | a reindexed term is required over the arrow's target, not its source | `payload/reindexed_fibres/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I109 | glue restricts | a glued value is compared with itself, not with the patches | `payload/glued_patches/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I110 | coherence | the pentagon sum is reduced modulo one | `payload/associator_tables/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I111 | forced value | a forced claim is checked for presence only | `payload/forced_differences/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_forced` | yes (exit 1) | yes (exit 0) |
| I112 | used at least once | an unused name is accepted | `payload/use_once_terms/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_unused` | yes (exit 1) | yes (exit 0) |
| I113 | answers recomputed | claimed answers are counted, not compared with the evaluated ones | `payload/typed_queries/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:mut` | yes (exit 1) | yes (exit 0) |
| I114 | patched within | a patched view row need not be in the new table | `payload/patched_views/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I115 | declared ends | an edge's ends need not be declared vertices | `payload/signed_cells/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `EXPECTATION_MISMATCH:own_neg` | yes (exit 1) | yes (exit 0) |
| I116 | strict writes | a write over another transaction's unfinished write is allowed | `payload/serial_receipts/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I117 | rising clocks | a parent's clock is not compared with its child's | `payload/ordered_log/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_clock` | yes (exit 1) | yes (exit 0) |
| I118 | idempotent merge | merging a state with itself is not required to give it back | `payload/merge_tables/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I119 | issued by authority | a grant's issuer need not be the authority | `payload/exact_grants/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I120 | within budget | a release that exceeds the remaining budget is allowed | `payload/budgeted_releases/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I121 | pins hold | a pin is checked for presence, not against its input's seal | `payload/lineage_pins/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_pin` | yes (exit 1) | yes (exit 0) |
| I122 | no expansion | a rooted handoff may widen the permissions it passes on | `payload/narrowing_handoffs/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I123 | mutants refused | a mutant the subject accepts is not refused | `payload/mutant_challenges/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I124 | exit recomputed | the captured exit kind is not compared with the replayed one | `payload/limited_runs/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_exit` | yes (exit 1) | yes (exit 0) |
| I125 | independence decided | sources assumed independent are never tested | `payload/composed_errors/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I126 | empty clause | a refutation need not end in the empty clause | `payload/resolution_claims/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_short` | yes (exit 1) | yes (exit 0) |
| I127 | both directions | a one-way flow is accepted | `payload/wired_handshakes/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:mut` | yes (exit 1) | yes (exit 0) |
| I128 | outputs recomputed | the recorded outputs are not compared with the two implementations | `payload/differential_pairs/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_output` | yes (exit 1) | yes (exit 0) |
| I129 | seed replayed | the recorded first list is not regenerated from the seed | `payload/seeded_shrinks/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_replay` | yes (exit 1) | yes (exit 0) |
| I130 | not self-certified | a self-certified release is refused only when it is also a frontier claim | `payload/scoped_release/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I131 | custody booked | a research-tree record stops booking its custody in the loss ledger | `outward/bundles.py` | `run_bootstrap.py --out _scratch/inj` | `UNBOOKED_CUSTODY` | yes (exit 1) | yes (exit 0) |
| I132 | retired blocker | a registration lists witness_not_sealed again after the ruling | `bindings/qlevels.json` | `run_bootstrap.py --out _scratch/inj` | `RULED_ADMISSIBLE` | yes (exit 1) | yes (exit 0) |
| I133 | tree custody | a research-tree replay also reads a sealed source | `payload/observer_glue/spec.py` | `run_bootstrap.py --out _scratch/inj` | `RR-TREE` | yes (exit 1) | yes (exit 0) |
| I134 | embargo list | rung eight's leftover candidate is dropped from the embargo list | `engine/guards.py` | `gate.py --step embargo` | `EMBARGO LIST DRIFT` | yes (exit 1) | yes (exit 0) |
| I135 | observer glue | a conflict on a shared locus is never looked at, and a failed glue is no objection | `payload/observer_glue/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I136 | shared labels | two contexts may give a shared item two labels | `payload/shared_labels/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_turned` | yes (exit 1) | yes (exit 0) |
| I137 | row margin | the total is read from its label, not recomputed from the rows | `payload/row_margin/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I138 | site checks | each check is compared with itself, not with the others | `payload/site_checks/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_odd` | yes (exit 1) | yes (exit 0) |
| I139 | walk relabels | a transport changed at one end only is also accepted | `payload/walk_relabels/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I140 | face walk products | a face need not end where it starts | `payload/face_walk_products/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I141 | register squares | a claim with no map is not refused for it | `payload/register_squares/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:near_no_map` | yes (exit 1) | yes (exit 0) |
| I142 | pairing certificates | a rest holding both signs is accepted | `payload/pairing_certificates/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I143 | chord square rim | a declared rim need only contain the recomputed rim | `payload/chord_square_rim/spec.py` | `-m pytest -q -p no:cacheprovider tests/test_levels.py -k frozen_expectations` | `RR-FIXTURE-PASSED:own_neg` | yes (exit 1) | yes (exit 0) |
| I144 | embargo list | rung nine's census rows are dropped from the embargo list | `engine/guards.py` | `gate.py --step embargo` | `EMBARGO LIST DRIFT` | yes (exit 1) | yes (exit 0) |

I10 appends a word from 19L57G1's prose watchlist; the word is assembled at run
time and is not written in this record or in the injector's source.

## Findings while proving the panel

- I1, first run: the claim-overwrite injection was caught, but by the count
  guard (`RR-EXHAUSTION`), because only validated deltas passed through the
  claims check. The engine now checks every enumerated delta, and I1 fires
  `CLAIM_FROZEN` by name.
- First run of the whole panel: most recoveries failed because the injector
  reused stale bytecode (a restored file can match the injected one in size
  and mtime second). The injector now clears bytecode and writes none. The
  gates themselves were not at fault.
- I4, first run: the code fired but pytest truncated it out of the message;
  the test now prints mismatches in full.

I15 to I17 run `lake build` and the axiom audit; nothing is repinned while they are live.

I18 to I34 each mutate one of record_reading's two proposed lifts (a proposal
field, the pre-registered extension class, or one line of the ladder mirror)
and run `tools/lift_check.py`. It recomputes every condition from the pinned
evidence and prints a refusal code only on a drift from the frozen
expectations, so each injection is seen by its own code. I35 runs the
test-only draft pipeline through the receiving side's `check_record`.

- I27 and I28, first run: both fired, but recovery was scored false, because
  the check's summary printed the failing codes the expectations already hold
  (R2.8 fails on both steps). The summary now names failing conditions, and
  only a drift row prints a code.
- I35, first run: it did not fire. The edit renamed the ledger row's key and
  left the row in place. It now drops the row.

I36 edits the receiving side's carrier registry, outside this directory. It
then runs that side's `ledger --check` in its default context: without the
declared harness host, the stored Mode E receipts no longer resolve.
- I36, first run: it was expected to fire `RR-PIN` and did not. The ledger
  verifies a stored receipt by recomputing it and comparing. When the sources
  do not resolve, the recomputed block differs, and the ledger names that
  difference, `RR-PRODUCER-VERDICT`, not the `RR-PIN` beneath it. The
  injection now expects the code the ledger actually prints.

I37 to I47 are round P3's. I37 runs the Lean step on a level's own
certificate module (the generator now renders one per level). I38 and I39 run
a level's record, completed on the working tree, through the receiving side's
`check_record`: a certificate cited from the wrong module (`RR-STATEMENT`),
and a compatibility square whose two sides differ (`TC-CRITERION-MISSING`).
I40 to I45 each weaken one band level's decisive clause to the defect the
level exists to refuse (a scalar summary for an ordered product, a fence that
reads the declared scope, a rounded root, a split read back instead of
recomputed, a zero gap without feasibility, a span that is not the least); the
level's own refused fixture is then accepted. I46 proves the E0 freeze check
after its repair, and I47 the embargo pin's new item. I48 proves that every
Q-level registration's sealed citation is checked against the pinned axiom
report, and I49 and I50 weaken the two replays of sealed evidence (a step
that is not a sealed reduct; a map judged by injectivity alone).

I51 to I58 prove the second P3 pull request's guards: each of the six new
replays of sealed evidence (006, 009, 013, 014, 015, 017) and the chain's
equation clause (016) is weakened to the defect it exists to refuse, and
I58 reintroduces a defect found while building 007's kernel module: the
restated axiom report wrote an axiom-free theorem with a placeholder
axiom, which the receiving side refused (`RR-AXIOM`). Its first run did not
fire: the record test reads the committed restatement, not a fresh one. It
now runs the test that restates the report afresh.

I59 to I64 are round P4's: the three new replays of sealed evidence (029, 032,
043) and the two harness levels (035, 036) are each weakened to the defect
they exist to refuse, and I62 names a Q-level blocker that is neither an
embargo item nor one of the two named non-embargo blockers.
- I64, first run: it did not fire. It divided zero evidence through as if it
  were one, but the evidence clause reads the evidence itself, so no verdict
  moved. It now drops the evidence clause.

I65 to I91 are round P5's: each of the twenty-seven new harness levels (047,
048, 054, 057, 066, 070, 039, 040, 044, 058, 060, 065, 067, 062, 049, 059,
061, 056, 051, 050, 055, 052, 068, 072, 042, 033 and 038, in the order they
were built) has its decisive clause weakened to the defect the level exists
to refuse, and the level's own refused fixture, or a near-miss, is then
accepted or refused for another reason. I92 leaves a payload module a spec
imports out of the record's sources (UNNAMED_SOURCE). I93 reads a harness
record at a blocked Q-level as a replay of sealed evidence
(STALE_REGISTRATION: the refusal round P5 predicted, G1, before the registry
read the carrier part). I94 frames the record at a ruling-D4 apparatus level
as a supplied challenge (D4_FRAMING).
- I72, first run: it did not fire. With the first player's changes untried,
  the own negative (a, x) is still refused, by the second player's change to
  y. The injection now expects near_gain, whose only profitable change is the
  first player's, to be accepted.

I95 to I130 are round P6's. I95 reverts the carrier cap to 12, and 031's
18-element structure is refused (SIZE_CAP). I96 enumerates a class beyond
the evaluation budget instead of declaring its count. I97 drops the hosted
digests in descent (RR-NON-DESCENT). I98 removes the start check from the
Lean induction certificate, and the level modules that cite it no longer
build. I99 to I130 weaken the decisive clause of each new harness level
(030, 031, 064, 045, 046, 063, 069, 071, 073, 022, 023, 027, 037, 041,
074 to 081, 083, 085, 087, 088, 089, 092, 094, 098, 099 and 100) to the
defect it exists to refuse; the level's refused fixture, or a near-miss, is
then accepted or refused for another reason.
- I114 and I115, first run: both exited nonzero, but not with the code
  expected. With the relational clause weakened, the own negative reached
  the decoded clauses and was refused there, for another reason. They now
  expect the expectation mismatch they print.
- I1, first run of this round: it did not fire. The declared-count guard
  (I96's capability) ran before the claims check, so the claim-overwrite
  repair was refused as `RR-EXHAUSTION`. The claims check now runs first on
  every enumerated delta, and I1 fires `CLAIM_FROZEN` by name again.

- The freeze step, first gate run of the round: it failed on every new
  payload, because it compared each payload's expectations with the E0 source
  repository, which holds only E0's. It now compares the files the source
  holds at its head; I46 shows it still bites on an E0 file.

I131 to I143 are round P7A's (research-tree witnesses, the author's ruling of
2026-09-25). I131 stops booking a tree record's custody in its loss ledger
(UNBOOKED_CUSTODY); I132 re-lists the retired blocker witness_not_sealed
(RULED_ADMISSIBLE); I133 makes a tree replay read a sealed source as well
(RR-TREE); I134 drops rung eight's leftover candidate from the embargo list,
and I144 rung nine's undecided census rows.
I135 to I143 weaken the decisive clause of each research-tree replay (023,
058, 059, 060, 061, 062, 065, 066, 072) to the defect its level refuses; the
level's refused fixture, or a near-miss, is then accepted.
- The first full panel of the round stopped at I62: its anchor named 023's
  retired blocker, and the injector raised on the missing anchor after an
  hour of injections. I62 now re-blocks 041, I93 targets the registry's new
  binding rule, and the injector checks every anchor before it runs any
  injection (STALE ANCHOR).

Covered by unit tests rather than on-disk injection: a trivial capability
failing condition 10 (`RR-TRIVIAL-LIFT`), a checker below the bar
(`CHECKER_BELOW_BAR`), a checker file off its pin (`RR-PIN`), growth, removal
and declared-responder capabilities (`GUARD_EMBARGO`), loading
second-derivation state (`GUARD_EMBARGO`), a request about symmetry along a
history or about the element count and succession (`GUARD_EMBARGO`), a
second mutation for most lift conditions
(`tests/test_ladder.py`), a skipped rung (`NOT_MINIMAL_OVER_A_CLASS` with
`UNTRACEABLE`), a reused residual and a misplaced stop (`CHAIN_BROKEN`), a
positive that is not the committed witness (`RR-PIN`) and a producer verdict
(`RR-PRODUCER-VERDICT`) in a completed level record.
