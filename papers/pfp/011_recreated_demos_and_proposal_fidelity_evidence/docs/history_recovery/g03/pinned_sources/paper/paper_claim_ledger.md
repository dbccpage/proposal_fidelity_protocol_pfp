# Claim ledger

Field key — **ID**: stable identifier. **Statement**: exact claim.
**Class**: one of declared metatheory / definition / finite computation /
theorem / bounded theorem / conjecture / counterexample / unresolved.
**Deps**: claims this one depends on. **Assumptions**: declared metatheory
it rests on. **Python**: evidence (artifact key and/or test).
**Lean**: theorem name(s) in `lean4/Derivation/`. **Axioms**: from
`artifacts/lean_axioms.txt` (`--` = no Lean formalization).
**Falsifier / boundary**: what would refute it, or the boundary that
survives.

Shared assumptions for every claim: the metatheory of `paper.md`
sections 2-3 (regimes, events, replay, contexts, profiles, declared
separability), and — where marked *bounded* — the declared bounds of
section 1.  Lean evidence is stated in the token-erased abstraction,
connected to the token-aware semantics by the proved simulation
CL-TOKEN-ERASURE; Lean is never claimed to literally mirror the Python
implementation.

---

### CL-0-INERTIA
- **Statement**: With nothing admitted, nothing is derivable and no
  successor state is internally forced; a bare supply never changes the
  admitted state.  The forcing clause is structural: the declared model
  has no transition machinery besides event-indexed admission, no forcing
  predicate is defined, and nothing here excludes a successor in an
  extension of the language; the class below covers the derivability and
  bare-supply clauses, the forcing clause being that structural
  observation (scope stated 2026-09-08).
- **Class**: theorem.
- **Deps**: none. **Assumptions**: shared only.
- **Python**: `challenges.json:challenge0`; `test_challenge0_inertia`,
  `test_supply_is_not_admission`.
- **Lean**: `supply_no_op`, `genesis_underivable`, `underivable_of_empty`.
- **Axioms**: `propext` (supply_no_op); none (the other two).
- **Falsifier / boundary**: a derivation or state change from the empty
  regime without an admission event.  None exists in the model; the
  boundary is the model itself (transitions are event-indexed by
  construction).

### CL-0-NO-PROPOSAL-MUTATION
- **Statement**: A proposed transition cannot alter admitted state without
  a separate admission event; ill-formed admissions are rejected.
- **Class**: theorem (model-scoped).
- **Deps**: CL-0-INERTIA. **Assumptions**: shared.
- **Python**: `test_model.py` (rejection of every ill-formed event kind);
  `test_replay_certify_and_tamper_detection`.
- **Lean**: `stepE` totality with `Option` rejection; `supply_no_op`.
- **Axioms**: `propext`.
- **Falsifier / boundary**: a state change reachable without an event.

### CL-1-SUPPLY-NOT-ADMISSION
- **Statement**: The Challenge 1 supply of `<a>` is a new external
  presentation and not an admission; no internal observable distinction
  arises.
- **Class**: theorem.
- **Deps**: CL-0-INERTIA. **Assumptions**: shared.
- **Python**: `challenges.json:challenge1`;
  `test_challenge1_supply_vs_admission_and_convergence`.
- **Lean**: `supply_no_op`, `collapsed_of_no_insts`.
- **Axioms**: `propext`; `propext` (per `artifacts/lean_axioms.txt`; an
  earlier version recorded the second as axiom-free, which the artifact
  refutes — corrected 2026-08-18).
- **Falsifier / boundary**: an internal test distinguishing anything at
  Challenge 1.

### CL-1-READING-CONVERGENCE
- **Statement**: The two Challenge 1 sub-readings (admit `<a>` on supply /
  do not) converge to the same regime at Challenge 2 close.
- **Class**: finite computation.
- **Deps**: CL-1-SUPPLY-NOT-ADMISSION. **Assumptions**: shared +
  presentation-identity dedup of admissions (declared).
- **Python**: `challenges.json:challenge1.sub_readings_converge_at_
  challenge2 = true`; same test.
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: differing replays of the two extended
  histories.

### CL-2-COLLAPSED
- **Statement**: After Challenge 2 both readings admit externally distinct
  tokens whose every pair is observationally collapsed.
- **Class**: theorem.
- **Deps**: CL-0-INERTIA. **Assumptions**: shared.
- **Python**: `challenges.json:challenge2` (observational classes = 1);
  `test_challenge2_collapse_and_no_expressive_increase`.
- **Lean**: `R2L_collapsed`, `R2F_collapsed`, `historyL_replays`,
  `historyF_replays`.
- **Axioms**: `propext`; `propext`; `propext`; `propext` (all four per
  `artifacts/lean_axioms.txt` — the collapse theorems instantiate
  `collapsed_of_no_insts`, which carries `propext`; an earlier version
  recorded the first two as axiom-free — corrected 2026-08-18).
- **Falsifier / boundary**: a well-formed context separating any pair in
  the Challenge 2 regime.

### CL-2-NONINCREASE
- **Statement**: A new external inscription does not necessarily increase
  internal expressive power: admitting a fresh datum changes the state but
  leaves the collapsed pair collapsed.
- **Class**: counterexample (to the necessity claim).
- **Deps**: CL-2-COLLAPSED. **Assumptions**: shared.
- **Python**: `challenges.json:challenge2.*.expressive_increase_over_
  challenge0 = false`.
- **Lean**: `admission_without_expressive_increase`.
- **Axioms**: `propext`.
- **Falsifier / boundary**: n/a (a counterexample refutes the general
  necessity claim; the boundary is that *some* inscriptions plus
  judgments do increase power — Challenge 3).

### CL-3-FAIL-CURRENT
- **Statement**: The Challenge 2 regime does not satisfy the declared
  internal separability of `<a>` and `<ab>` in either reading.
- **Class**: theorem.
- **Deps**: CL-2-COLLAPSED. **Assumptions**: shared + declared
  separability (definition 3.5).
- **Python**: `claims.json:CL-3-FAIL-CURRENT = {L: false, F: false}`;
  `test_challenge3_reading_l_classes`.
- **Lean**: `R2L_collapsed`, `R2F_collapsed` with
  `separable_not_collapsed`.
- **Axioms**: `propext`; `propext`; `propext` (per-theorem, matching
  `artifacts/lean_axioms.txt`; an earlier version recorded all three as
  axiom-free — corrected 2026-08-18, the fourth entry of the same class
  and the one the walk's sweep missed).
- **Falsifier / boundary**: a witness context in the unaugmented regime.

### CL-3-COST1-IMPOSSIBLE
- **Statement**: No delta of at most one item is a valid response to the
  Challenge 3 requirement, in either reading.  *Bounds: none — absolute
  over the item grammar (any arity, any argument tuple). Measure: mu1.*
- **Class**: theorem.
- **Deps**: CL-3-FAIL-CURRENT. **Assumptions**: shared + candidate grammar
  (definition 3.6).
- **Python**: `test_c3_cost1_all_fail_and_min_is_two` (exhaustive over the
  bounded slice, consistent with the grammar-wide theorem).
- **Lean**: `cost1_insufficient_general`, `cost1_insufficient`,
  `cost1_insufficient_F`.
- **Axioms**: `propext`.
- **Falsifier / boundary**: a single admissible item separating the pair.

### CL-3-MIN-TWO
- **Statement**: The minimum valid response cost at Challenge 3 is exactly
  two items in both readings.  *Bounds: none. Measure: mu1. Uniqueness:
  see CL-3-NONUNIQUE-MU1.*
- **Class**: theorem.
- **Deps**: CL-3-COST1-IMPOSSIBLE. **Assumptions**: shared.
- **Python**: `challenges.json:challenge3.*.mu1.minimum_cost = [2, -1]`.
- **Lean**: existence — `deltaU0_valid`, `deltaU0F_valid`; floor —
  CL-3-COST1-IMPOSSIBLE.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a valid one-item response (excluded) or
  failure of the two-item witnesses (machine-checked).

### CL-3-NONUNIQUE-MU1
- **Statement**: Under mu1 the minimum corrective augmentation is not
  unique: the unary mark and the binary link are both minimum valid
  responses with non-isomorphic results.  *Bounds: none. Measure: mu1.
  Uniqueness: refuted absolutely — in reading L; reading F
  non-uniqueness rests on the Lean cost floor plus the bounded
  enumeration (see Class).*
- **Class**: theorem for reading L (the cited Lean is stated over
  `R2L`); for reading F, finite computation — the {F: 5} count is the
  bounded enumeration of CL-3-TIE-CLASSES, and no reading-F
  non-isomorphism theorem exists in Lean (scope made explicit
  2026-08-18; the entry was previously reading-silent).
- **Deps**: CL-3-MIN-TWO. **Assumptions**: shared + implemented
  isomorphism (definition 3.8).
- **Python**: `claims.json:CL-3-NONUNIQUE-MU1 = {L: 3, F: 5}`.
- **Lean**: `mu1_minimum_not_unique`, `U0_not_iso_BL` (both reading L).
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: an isomorphism between the mark and the link
  (excluded: arity is an invariant).

### CL-3-TIE-CLASSES
- **Statement**: The tied mu1 minima at Challenge 3 form exactly 3
  isomorphism classes in reading L (unary mark, binary link, binary
  self-loop) and exactly 5 in reading F (adding link-to and link-from the
  genesis datum).  *Bounds: max_items 2, max_arity 2. Measure: mu1.
  Uniqueness: class counts complete only within these bounds.*
- **Class**: bounded theorem.
- **Deps**: CL-3-NONUNIQUE-MU1, CL-PRUNE-RULE, CL-PRUNE-STRUCTURAL,
  CL-ISO-SOUND. **Assumptions**: shared + bounds.
- **Python**: `challenges.json:challenge3` iso_classes; cross-check
  against the unpruned space
  (`test_pruned_cost2_contains_every_valid_full_delta` — its base
  regimes are the reading-L base and mixed regimes, not the reading-F
  base, so the unpruned certification covers reading L only);
  `test_challenge3_reading_f_has_five_classes`.
- **Lean**: class distinctness — `U0_not_iso_BL`, `U0_not_iso_BD`,
  `BL_not_iso_BD`; class collapse — `isoU1U0`.  All four are stated
  over the reading-L regimes; no Lean theorem distinguishes the five
  reading-F classes, whose count rests on the pruned enumeration
  quotiented by the implemented isomorphism (CL-ISO-SOUND).  Scope made
  explicit 2026-08-18.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a valid bounded delta outside the listed
  classes, or a missed isomorphism.  Boundary: arity > 2 candidates exist
  and are tied (CL-3-INFINITE-TIES).

### CL-3-INFINITE-TIES
- **Statement**: For every arity k >= 1 the k-ary mark is a two-item
  minimum valid response in reading L, and distinct arities give
  non-isomorphic results: the reading-L mu1 tie class is countably
  infinite.  *Bounds: none.  Measure: mu1.  Reading: L — every cited
  Lean theorem is stated over the reading-L regime, and no F-side
  analogue of the k-ary family is formalized (scope made explicit
  2026-08-18; the entry was previously reading-silent).*
- **Class**: theorem (reading L).
- **Deps**: CL-3-COST1-IMPOSSIBLE. **Assumptions**: shared.
- **Python**: consistent bounded slice (arities 1, 2 both appear).
- **Lean**: `deltaK_valid`, `deltaK_length`, `markK_pairwise_noniso`,
  `deltaK_applies`, `markK_separable`.
- **Axioms**: `propext, Quot.sound` (`propext` only for the non-iso).
- **Falsifier / boundary**: an isomorphism between marks of different
  arity.

### CL-3-UNIQUE-MU2-L
- **Statement**: Under mu2, every valid two-item response with new-form
  arity sum <= 1 in reading L produces a regime isomorphic to the unary
  mark; with the cost floor this makes the mu2-minimum unique up to
  isomorphism.  *Bounds: item grammar-wide. Measure: mu2. Uniqueness:
  absolute over the grammar, up to the implemented isomorphism.*
- **Class**: theorem.
- **Deps**: CL-3-MIN-TWO. **Assumptions**: shared.
- **Python**: `claims.json:CL-3-UNIQUE-MU2.L = 1`;
  `test_c3_mu2_minimum_is_unary_mark`.
- **Lean**: `mu2_unique` (with `isoRefl`, `isoU1U0`).
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a valid (2, <=1) delta with a non-mark result.

### CL-3-UNIQUE-MU2-F
- **Statement**: Under mu2 reading F has exactly one minimum class (the
  unary mark on a required datum): every valid two-item response with
  new-form arity sum <= 1 produces a regime isomorphic to `U0F`.
  *Measure: mu2. Uniqueness: grammar-wide, same scope as the L twin.*
- **Class**: theorem (grammar-wide, 2026-08-18); the engine enumeration
  within the declared bounds is retained as independent evidence.
- **Deps**: CL-3-UNIQUE-MU2-L (method), CL-ISO-SOUND.
- **Python**: `claims.json:CL-3-UNIQUE-MU2.F = 1`.
- **Lean**: `mu2_unique_F`, with `genesis_mark_not_separable` closing
  the one case reading F adds over reading L — the mark on the genesis
  datum, killed by the R3 mention lemma
  (`collapsed_append_unmentioning`): its instance mentions neither
  required datum, so the pair stays collapsed and validity fails.
  `isoU2F_U0F` collapses the two required-datum marks to one class;
  `cost1_insufficient_F` and `deltaU0F_valid` were already in place.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a valid two-item arity-<=1 response in
  reading F not isomorphic to `U0F`.

### CL-PRUNE-RULE
- **Statement**: (i) Separation witnesses never inhabit uniformly ruled
  forms, so shrinking the final rule set preserves every separation —
  proved.  (ii) The delta-level corollary "a delta containing a
  uniform-rule item is never a minimum valid response" additionally needs
  the bridge that rule items commute out of a delta leaving the same
  regime with a smaller rule set — proved (`applyDelta_dropRules`,
  2026-08-18; this statement still said "computational" until
  2026-09-08, while the class below already said theorem).
- **Class**: (i) theorem; (ii) theorem (bridge proved 2026-08-18); the
  full-space computational check is retained as independent evidence.
- **Deps**: none. **Assumptions**: shared.
- **Python**: `test_rule_never_appears_in_minimum_responses` (full-space
  check on a mixed regime: every valid rule-bearing delta has a valid
  rule-free sub-delta).
- **Lean**: (i) `separable_of_subrules`; (ii) `applyDelta_dropRules`
  (rule items commute out of a delta over ANY replacement rule field —
  the bridge is definitional: no `applyItem` guard reads the rule
  field, and only `newRuleAll` writes it), `validResponse_dropRules`,
  `rule_item_never_minimal` (valid, strictly shorter, arity sum
  unchanged: never a minimum under either declared measure), with
  `applyDelta_rules_mono`, `dropRules_length_lt`, `aritySum_dropRules`
  as the supporting steps.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a minimum valid response containing a rule.

### CL-PRUNE-STRUCTURAL
- **Statement**: In the cost-2 enumeration, unreferenced fresh data and
  unreferenced fresh forms never affect validity, and an instance-only
  delta changes the target pair's separability only if some instance
  mentions a target datum; the pruned enumeration therefore contains every
  minimum.  *Bounds: cost <= 2 deltas over the declared grammar slice.*
- **Class**: bounded theorem.
- **Deps**: none. **Assumptions**: shared + bounds.
- **Python**: `test_pruned_cost2_contains_every_valid_full_delta` (every
  valid excluded delta has a valid strict sub-delta), plus
  `test_new_datum_alone_never_separates`,
  `test_fast_equals_naive_on_full_space`.
- **Lean**: the three irrelevance facts are now proved —
  `collapsed_fresh_datum` (R1), `collapsed_fresh_form` (R2),
  `collapsed_append_unmentioning` (R3), with `mem_plug_of_hole`,
  `not_mem_of_arg_out_of_range`, `exists_out_of_range_slot` and
  `getD_append_left` as the supporting steps (2026-08-17).
- **Axioms**: `propext, Quot.sound`.
- **Scope, exactly**: the Lean proves each irrelevance fact as an `iff`
  about `collapsed` for a pair that already exists.  It does NOT prove
  the enclosing statement "the pruned enumeration therefore contains
  every minimum", which quantifies over the declared cost-2 grammar
  slice and remains the bounded computational result certified by
  `test_pruned_cost2_contains_every_valid_full_delta`.  The class stays
  **bounded theorem** for that reason: three of its inputs became
  theorems, the enumeration claim did not.
- **Falsifier / boundary**: a valid full-space delta absent from the
  pruned space with no valid sub-delta.  Boundary: certified
  computationally on bare, marked, and mixed base regimes; Lean proof
  outstanding.

### CL-PROGRESS
- **Statement**: On any well-formed regime whose imposed requirements are
  all separated, every *supplied* separation demand has a valid response
  (fresh unary form + one mark) that keeps every imposed requirement
  separated.  Scope: response existence only — this claim does not
  assert autonomous demand generation and does not assert an unbounded
  tower.  (An earlier version said "preserves every existing
  separation"; the proved preservation conjunct of validity quantifies
  over the imposed requirements only — narrowed 2026-08-18.)
- **Class**: theorem.
- **Deps**: none. **Assumptions**: shared.
- **Python**: engine assertion (no `terminal_no_response` node in any
  run); `test_min_responses_cost1_path` and tree runs.
- **Lean**: `mark_progress` (with `derivable_extend`,
  `getD_concat_self`, `getD_append_lt`).
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a challenged accepted regime with no valid
  bounded response.

### CL-CLOSURE-POLICY
- **Statement**: No object-language endogenous demand generator was
  derived: a collapsed pair is not an active obstruction unless
  separation is required, and the requirement pattern originates
  externally.  What is declared instead is the *pair-separation closure
  policy*: reissue the admitted requirement pattern on collapsed pairs,
  one challenge branch per automorphism orbit — token-blind, no fresh
  data, no new goal kind, isomorphism-equivariant.
- **Class**: declared metatheory + finite computation (token-blindness
  and equivariance); the Lean model even lacks the vocabulary for glyph
  inspection (regimes carry no tokens).
- **Deps**: CL-2-COLLAPSED, CL-TRANSITION-EQUIVARIANCE.
  **Assumptions**: shared + the declared policy itself.
- **Python**: `closure_challenge_orbits`;
  `test_closure_policy_is_token_blind`, `test_closure_policy_fixpoint`.
- **Lean**: token-freeness by construction of `Regime`.
- **Axioms**: n/a.
- **Falsifier / boundary**: any dependence of the challenge orbits on
  token renaming or representative labeling.  Selection of this policy
  among conceivable ones is a declared-metatheory judgment.

### CL-CLOSURE-TERMINATION
- **Statement**: Pair-separation closure terminates: with the external
  policy disabled, every maximal branch ends at the all-pairs-separated
  fixpoint within n(n-1)/2 rounds (L: 1 round, 3 terminal branches, 0
  guard-cut, 0 round-cut, 0 open; F: 3 rounds, 16 terminal branches,
  0/0/0).  *Bounds: declared engine bounds, closed-system runs under
  measure mu1 only (both exported baselines fix mu1; no mu2 closed run
  is exported — scope made explicit 2026-08-18); the counting laws are
  grammar-wide but conditional (see Lean field).*
- **Class**: bounded theorem.
- **Deps**: CL-CLOSURE-POLICY, CL-PROGRESS. **Assumptions**: shared +
  bounds.
- **Python**: `claims.json:CL-CLOSURE-TERMINATION` (branch reports over
  *all* maximal branches, `every_maximal_branch_terminates = true`,
  `within_bound = true`);
  `test_no_supply_variant_terminates_within_pair_bound`,
  `test_closed_system_terminal_at_round_boundary`.
- **Lean**: `index_le_strict_mono`, `strict_bounded_length`,
  `no_supply_round_bound`, `allPairs_length`; and, 2026-08-18, the
  hypotheses discharged for the transition system itself: under the
  declared round shape (`ClosedRun`: impose a FRESH target, respond
  with a delta admitting NO fresh datum) each round grows the
  requirement count by exactly one (`round_reqs_succ`) over a fixed
  datum count (`round_data_eq`), requirements stay ordered, bounded and
  duplicate-free, and `closedRun_round_bound_from_empty` proves
  2 *rounds <= n* (n - 1) — the division-free form of the
  n(n-1)/2 bound — by choice-free subset counting into `allPairs`
  (`nodup_subset_length`).  What remains computational is narrowed to
  exactly this: that each EXPORTED round has the declared syntactic
  shape.  Discharging the freshness condition from the closure policy
  itself would need collapsed-pair selection and acceptance semantics
  formalized, which this row does not claim.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a closed-system branch that is guard-cut,
  round-cut, open, or exceeds the pair bound.

### CL-CLOSURE-FIXPOINT
- **Statement**: Beyond the fixpoint the closure policy yields nothing:
  the requirement language of n data has exactly n(n-1)/2 elements, all
  exhausted at the fixpoint; any further requirement needs a fresh datum
  (external supply) or a new requirement kind (external goal).  Further
  continuation requires the declared external continuation policy.
- **Class**: theorem (language-size law) + declared metatheory (policy
  boundary).
- **Deps**: CL-CLOSURE-TERMINATION. **Assumptions**: shared + the
  admitted requirement language (separation over admitted data).
- **Python**: `test_closure_policy_fixpoint`.
- **Lean**: `allPairs_length`.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: an admitted-structure-only challenge issuable
  at the fixpoint.

### CL-TRANSITION-EQUIVARIANCE
- **Statement**: The quotiented transition is well defined: expanding a
  regime by one challenge per automorphism orbit of collapsed pairs (all
  non-isomorphic challenge orbits retained) commutes with renaming — for
  every datum bijection (identity on forms: the space both the Lean
  transport and the exhaustive test cover; a general isomorphism here is
  a PAIR of bijections, and the form component is not exercised), the
  renamed regime expands to exactly the same set of child isomorphism
  classes.  Raw least-pair selection violates this:
  on the regression regime (four data, one unary form, marks on data 2
  and 3, collapsed pairs (0,1) and (2,3), renaming (2,3,0,1)) the
  canonical keys agree while the same-index least-pair challenges produce
  non-isomorphic children.
- **Class**: theorem (relation-level transport, 2026-08-18) + finite
  computation (the child-CLASS-set formulation, below) + counterexample
  (against the old policy).  The general transports — candidates, costs,
  validity, steps and children under a datum renaming — are now proved
  at the relation level; the conversion from "children correspond under
  the explicit padded renaming" to "equal canonical-key class sets"
  remains with CL-ISO-SOUND on the Python side.
- **Deps**: CL-ISO-SOUND. **Assumptions**: shared.
- **Python**: `tests/test_equivariance.py` (regression, orbit
  distinctness, exhaustive congruence, orbit coverage);
  `claims.json:CL-TRANSITION-EQUIVARIANCE` (policy record and
  multi-orbit statistics: 0 in every exported run — the repaired defect
  was latent within the explored bounds); every merge edge in every
  export carries an explicitly verified isomorphism certificate
  (CL-REPLAY).
- **Lean**: `transStep_rename_fwd` (every step maps to a step of the
  renamed regime, children corresponding under the padded renaming) and
  `transStep_image_total` (every step of the renamed regime is such an
  image: the renamed relation is EXACTLY the image, not a superset),
  over `renameRegimeR` (the action extended to requirements, since the
  transition — unlike collapse — reads them) with `respond_rename`,
  `validResponse_rename`, `stepE_impose_rename`, `applyDelta_rename` as
  the chain; `validCount_rename` + `mapItem_length` + `formAritySum_map`
  carry minima and counts of both declared measures;
  `least_pair_selection_not_congruent` witnesses the boundary in Lean on
  the regression regime.  Deliberately NOT an equality-form iff over an
  arbitrary child: `mapReq` renormalizes pairs, so the action is not
  injective on disordered-requirement regimes, and mapping plus image
  totality is the honest packaging.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a regime and bijection whose expansions
  yield different child class sets; boundary: the class-SET statement
  stays computational (sampled regimes, full symmetric groups); the
  relation-level statement is grammar-wide.

### CL-BRANCH-REPORTS
- **Statement**: Per-tree branch evidence — terminal, guard-cutoff,
  round-cutoff, and open branch counts with the
  every-maximal-branch-terminates flag — as tabulated in paper
  section 8.3/8.4.
- **Class**: finite computation.
- **Deps**: CL-REPLAY. **Assumptions**: shared + bounds.
- **Python**: `claims.json:CL-BRANCH-REPORTS`;
  `test_run_main_produces_all_artifacts`.
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: recount from the exported trees.

### CL-TREE-MU2-COMPLETE
- **Statement**: The isomorphism-quotient trees under mu2 are enumerated
  in full, within the declared bounds, to the requested depth of 15
  transition steps with zero guard cutoff: 963 nodes / 1022 edges (L),
  1847 / 1960 (F); all leaves are round-cut.  A transition step is a
  separation response or an external supply; each completed leaf carries
  10 to 12 separation responses (`CL-TRANSITION-STEPS-VS-RESPONSE-ROUNDS`;
  an earlier version said "fully enumerated to the requested 15 rounds"
  — narrowed 2026-09-08).
  *Bounds: declared bounds; completeness is of the quotient tree within
  them, and is conditional on the orbit challenge policy losing no
  child classes — the class-set form of CL-TRANSITION-EQUIVARIANCE,
  which is computational (dependency made explicit 2026-08-18).*
- **Class**: bounded theorem.
- **Deps**: CL-ISO-SOUND, CL-PRUNE-STRUCTURAL, CL-REPLAY,
  CL-TRANSITION-EQUIVARIANCE.
- **Python**: `tree_L_mu2_summary.json` / `full/tree_L_mu2.json.gz` and
  the F analogues; stats in
  `claims.json:CL-TREE-SUMMARY`.
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: a reachable bounded node missing from the
  export.

### CL-TREE-MU1-FRONTIER
- **Statement**: The mu1 trees are guard-bounded at the 1200-node
  pre-expansion guard with exact exported frontiers across two levels:
  first cut at depth 6 (L) / 5 (F), maximum depth 7 / 6; L carries 47
  guard-cut nodes at depth 6 and 880 at depth 7 (927), F 303 at depth 5
  and 583 at depth 6 (886).  The expanded subgraph is complete within the
  bounds; not every node at the maximum depth was reached or expanded.
  (An earlier version said "depth 7 with 927 frontier leaves (L), depth 6
  with 886 (F)", the maximum depths, for the cut — corrected 2026-09-08;
  `test_mu1_first_guard_cut_below_maximum_depth` recounts.)
- **Class**: finite computation.
- **Deps**: as CL-TREE-MU2-COMPLETE.
- **Python**: `tree_L_mu1_summary.json`, `tree_F_mu1_summary.json`;
  full exports `full/tree_L_mu1.json.gz`, `full/tree_F_mu1.json.gz`.
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: the frontier is the boundary, exported
  exactly for continuation.

### CL-REACHES-REQUESTED-DEPTH-WITH-EXTERNAL-SUPPLY
- **Statement**: With the external continuation policy, the process
  reaches the requested depth in the mu2 trees (15 of 15 transition
  steps, of which 10 to 12 on each completed leaf are separation
  responses and the rest external supply; mu1 trees reach maximum depth
  7 / 6 with first guard cuts at 6 / 5).  Reaching a
  finite requested
  depth is not a proof of unboundedness; no unboundedness claim is made,
  and the behavior beyond the exported depths is unresolved.
- **Class**: finite computation.
- **Deps**: CL-PROGRESS (response existence only). **Assumptions**:
  shared + bounds.
- **Python**:
  `claims.json:CL-REACHES-REQUESTED-DEPTH-WITH-EXTERNAL-SUPPLY`.
- **Lean**: supporting core — `mark_progress` (response existence for a
  supplied demand; not demand generation, not a tower).  **Axioms**:
  `propext, Quot.sound`.
- **Falsifier / boundary**: recount from exports; the boundary is the
  exported depth itself.

### CL-CLOSURE-VS-EXTERNAL
- **Statement**: Side-by-side comparison of the closed-system towers
  (4 / 20 nodes, all branches terminal) with the external-policy trees
  (963-1847 node complete mu2 quotients; 1200-node mu1 frontiers).
- **Class**: finite computation.
- **Deps**: CL-CLOSURE-TERMINATION, CL-TREE-MU2-COMPLETE.
- **Python**: `claims.json:CL-CLOSURE-VS-EXTERNAL`.
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: recount from exports.

### CL-ROLES
- **Statement**: The recurring transition roles that emerge are supply,
  discrimination (one instance), innovation (fresh form + instance), and
  rare double discrimination (6 edges, F mu2 only); the enumerated
  auxiliary-witness shape never appears among accepted minima in the
  observed runs.
- **Class**: finite computation.
- **Deps**: CL-TREE-MU2-COMPLETE, CL-TREE-MU1-FRONTIER.
- **Python**: role counts in `claims.json:CL-TREE-SUMMARY`;
  `test_role_classification_of_rare_response_shapes`.
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: bounded to the observed runs; deeper or
  wider bounds could surface the auxiliary-witness role.

### CL-TOKEN-ERASURE
- **Statement**: The Lean development is a token-erased abstraction of
  the token-aware admission semantics, connected by **two** proved
  components — never by duplicate-admission idempotence alone:
  (i) the erasure simulation: one token-aware step followed by erasure
  equals one erased step of the erased event (a duplicate datum
  admission erases to a bare supply, a proved no-op), and the same for
  whole histories; (ii) membership extensionality: Python's admitted
  collections are sets, Lean's are deduplicated lists, and under the
  proved relation `RegimeExt` every observable transports — derivability,
  context well-formedness, collapse, separability, item/delta
  application, response validity — so no claim stated in terms of these
  observables depends on list order or representation.  (An earlier
  version said "no exported claim"; claims stated at the representation
  level — the concrete replay equalities — are covered only up to
  `RegimeExt`, and nothing proves every exported claim factors through
  the listed observables — narrowed 2026-08-18.)  Both components relate
  the two Lean models; the Python implementation is connected to the
  token-aware model by the executable checks named under Python, not by
  any proof over the Python source (endpoints stated 2026-09-08).
- **Class**: theorem.
- **Deps**: CL-0-INERTIA (`supply_no_op` makes the duplicate case a
  no-op). **Assumptions**: shared.
- **Python**: set semantics of the admitted collections (frozensets in
  `model.py`); `test_admit_datum_dedups_on_presentation_identity`.
- **Lean**: `insertNew` (+ `mem_insertNew`, `insertNew_of_not_mem`,
  `insertNew_of_mem`), `erase_step`, `erase_replay` (with
  `replayT_cons`, `replayE_cons`) in `Derivation/Erasure.lean`;
  `derivable_ext`, `wfCtx_ext`, `collapsed_ext`, `separable_ext`,
  `applyItem_ext`, `applyDelta_ext`, `validResponse_ext` in
  `Derivation/Ext.lean`.
- **Axioms**: `propext, Quot.sound` (simulation); the extensionality
  family reports per-theorem in `artifacts/lean_axioms.txt`.
- **Falsifier / boundary**: a repeated admission of any event kind on
  which the two sides disagree; two membership-equal list
  representations supporting different claims; or a token-aware history
  whose erased replay differs from its replayed erasure.  Boundary:
  Python-side structures beyond events (token strings vs numbers) are
  related by the declared opaque-token reading.

### CL-REPLAY
- **Statement**: Every certified regime equals the replay of its recorded
  history from genesis; replay is compositional; tampering is detected.
  The normalized DAG exports certify **every edge**, not only one
  creation edge per node: a creation edge must replay from its parent to
  the exact stored child (hash equality), and a merge edge carries
  explicit datum/form bijections, computed and re-verified at attach
  time, that `verify_full_export` independently checks to map the
  replayed result exactly onto the stored child representative.  A single
  invalid merge edge is rejected even when every node retains a valid
  creation path.
- **Class**: theorem (compositionality) + finite computation
  (certification of all 5240 exported nodes and all 5498 exported edges,
  in-engine and again from the exports).
- **Deps**: none. **Assumptions**: shared.
- **Python**: `all_certified = true` in every tree;
  `test_replay_certify_and_tamper_detection`,
  `test_replay_from_base_composes`,
  `test_full_export_replays_and_verifies`,
  `test_verify_full_export_detects_tampering`,
  `test_every_edge_is_certified_including_merges`,
  `test_verify_rejects_invalid_merge_edge_despite_valid_creation_paths`;
  `test_run_main_produces_all_artifacts` verifies every exported tree.
- **Lean**: `replayE_append`, `historyL_replays`, `historyF_replays`.
- **Axioms**: `propext, Quot.sound`; `propext`; `propext`.
- **Falsifier / boundary**: a certified node whose history replays
  elsewhere, or an edge whose certificate fails independent re-checking.

### CL-QUOT-BARRIER
- **Statement**: If an abstraction identifies two cases, no operation
  defined only on the abstraction recovers the distinction: every function
  out of the quotient is constant on identified elements; instantiated at
  the Challenge 2 collapse.
- **Class**: theorem.
- **Deps**: CL-2-COLLAPSED. **Assumptions**: shared.
- **Python**: n/a (purely logical).
- **Lean**: `quotient_barrier`, `quot_barrier`, `barrier_R2L`.
- **Axioms**: `Quot.sound`; `Quot.sound`; `propext, Quot.sound`
  (per-theorem, matching the artifact; the instantiation at the
  Challenge 2 collapse inherits `propext` through
  `collapsed_of_no_insts`).
- **Falsifier / boundary**: none within the model; recovering the
  distinction requires changing the abstraction (which is what
  Challenge 3 forces).

### CL-ISO-SOUND
- **Statement**: The implemented canonical form decides exactly the
  declared isomorphism relation: equality of refined canonical keys agrees
  with equality of brute-force keys, and the key is invariant under every
  bijection pair.  The automorphism search (used by the closure policy's
  orbit decomposition) enumerates within isomorphism-invariant color
  classes and is budget-guarded like canonicalization.  *Bounds: verified
  exhaustively on the Challenge 3 class representatives and mixed
  regimes; budget-guarded in general.*
- **Class**: finite computation.
- **Deps**: none. **Assumptions**: shared.
- **Python**: `test_agreement_with_bruteforce_on_pairs`,
  `test_canonical_invariant_under_rename`, `test_perm_budget_error`,
  `test_regression_orbits_are_distinct_and_both_retained`,
  `test_orbit_representatives_cover_all_collapsed_pairs`.
- **Lean**: -- (unresolved). **Axioms**: --.
- **Falsifier / boundary**: a pair of regimes on which refined and
  brute-force equality disagree, or an orbit decomposition that misses or
  double-counts a collapsed pair.

### CL-COUNT-INVARIANCE
- **Statement**: The unresolved-requirement count (collapsed pairs) is
  invariant under token renaming and index bijections.
- **Class**: theorem for datum-index bijections (the Lean transport,
  over a caller-supplied candidate list); token renaming and form-index
  bijections remain finite computation — presentation tokens do not
  exist in the Lean model (`data : Nat`), so token blindness is
  inexpressible there, and `renameRegime` maps datum indices only
  (split made explicit 2026-08-18; an earlier version read as if the
  whole conjunction were Lean-proved).  The exhaustive Python
  certification over the Challenge 3 classes and mixed regimes covers
  all three conjuncts and is retained as independent evidence.
- **Deps**: CL-ISO-SOUND. **Assumptions**: shared.
- **Python**: canonical-invariance tests
  (`test_canonical_invariant_under_rename`; an earlier version said the
  count is a component of the canonical key — false, `serialize` in
  `iso.py` carries the data count, forms, instances, rules and
  requirements, and the invariance fixtures have one form, so their form
  permutation loop exercises only the identity — withdrawn 2026-09-08);
  `test_closure_policy_is_token_blind`.
- **Lean**: `collapsed_rename` (observational collapse transports under a
  datum renaming) and `collapsedCount_rename` (the count over any
  candidate pair list is preserved), with `plug_mapCtx`,
  `derivable_rename`, `wfCtx_rename` as the supporting steps; language-size
  law `allPairs_length` as before.  Under the full two-bijection
  isomorphism, collapse transport is proved by `collapsed_transport`
  (in `lean4/Derivation/IsoCollapse.lean`) and `collapsed_renameForms`,
  `collapsed_renameDataForm` (in `lean4/Derivation/FormTransport.lean`);
  the executable count and the pair enumeration stay computational
  (credited 2026-09-08).
- **Axioms**: `propext, Quot.sound`.
- **Scope, exactly**: `collapsed_rename` is unconditional in the renaming's
  bounds — it needs only bijectivity. The bound fields are used solely by
  `wfCtx_rename`. `collapsedCount_rename` takes the decision procedure as
  a parameter with a proof that it tracks `collapsed`: nothing here decides
  `collapsed`, whose quantifier ranges over the infinite type `Ctx`. The
  requirement conjunct of `Regime.wf` is NOT claimed to transport — a
  bijection need not preserve the `q.1 < q.2` ordering — and does not need
  to, because `collapsed` reads only `forms`, `data`, `insts` and `rules`.
- **Falsifier / boundary**: a renaming changing the collapsed-pair count.

### CL-DETERMINISM
- **Statement**: The entire artifact set is byte-identical across
  independent runs on one platform; across the two platforms exercised
  (Windows locally, Linux in CI) the JSON artifacts are byte-identical
  and the compressed full exports are content-identical and hash-pinned
  by the committed summaries.  (An earlier version said "across
  platforms" without naming them; no third platform is exercised —
  scope made explicit 2026-08-18.)
- **Class**: finite computation.
- **Deps**: none. **Assumptions**: shared.
- **Python**: `test_run_main_is_deterministic`,
  `test_write_json_and_gz_are_deterministic`,
  `test_build_tree_small_deterministic_and_certified`;
  `ci/compare_artifacts.py` (regeneration gate, run locally and in CI).
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: any content difference across runs.

### CL-READING-UNDERDETERMINATION
- **Statement**: The challenge text underdetermines admission semantics;
  readings L and F both survive the full derivation and no internal fact
  separates them.
- **Class**: unresolved (deliberately retained branches; the Challenge 1
  sub-reading convergence is finite computation, CL-1-READING-CONVERGENCE).
- **Deps**: all Challenge results (computed for both readings).
- **Python**: every artifact is produced per reading.
- **Lean**: both `R2L` and `R2F` variants where formalized.
- **Axioms**: as per constituent claims.
- **Falsifier / boundary**: an internal criterion selecting a reading
  (none exists: the difference is a metatheoretic fact about the
  challenge text).

### CL-NO-UNIVERSAL-PROPERTY
- **Statement**: The final process is minimal or initial among a defined
  class of finite processes satisfying the same challenges.
- **Class**: unresolved — **claim refused**.  No universal property was
  proved; per the discipline, the word "minimal" for the whole process is
  therefore not used.
- **Deps**: n/a. **Python / Lean / Axioms**: --.
- **Falsifier / boundary**: what survives instead: per-stage minimality
  with declared scope (CL-3-*), engine determinism (CL-DETERMINISM), and
  bounded completeness (CL-TREE-MU2-COMPLETE).

---

## Frontier Run 006 claims (refusal, reflection, the remaining bridge)

Full statements, dependencies, and boundaries:
`paper/refusal_as_difference.md`; evidence:
`artifacts/refusal_frontier.json` and
`lean4/Derivation/RefusalFrontier.lean`.

### CL-FR6-TERMINAL
- **Statement**: split by target (per PR #7 verdict; supersedes the
  earlier single-line MULTIPLE_MINIMUM_BRIDGES, which conflated three
  bridge targets): FREE_REFUSAL_BRIDGE_FAILS (the free fragment reaches
  nothing); UNIQUE_MINIMUM_WITNESSED_BRIDGE_IN_CLASS (one minimum
  protocol — datum retention + relation rule, no tag, singleton
  algebra, one token — for witnessed_relation and
  witnessed_irreflexive, identical under both cost orders);
  MULTIPLE_MINIMUM_WEAKER_BRIDGES (three ties for two_carrier and two
  ties for separable/oriented pair under order A, with order B
  selecting different winners).  Irreflexivity as a law is not reached
  and remains separately declared.
- **Class**: bounded theorem (exhaustive in class) + theorem (cores).
- **Python**: `refusal_frontier.json` (minimum_table, normal_form).
- **Lean**: the CL-FR6-T* theorems, incl.
  `min_witnessed_route_closes`.  **Axioms**: within
  {propext, Quot.sound}.
- **Falsifier**: an in-class route with no listed purchase; a second
  minimum protocol at a witnessed milestone under either order; or a
  weaker-milestone tie eliminated under both orders.

### CL-FR6-T1-INERTIA
- **Statement**: horizon-free silent-refusal inertia under arbitrary
  repetition.  **Class**: theorem.
- **Lean**: `RefusalFrontier.silent_repetition_inert`.

### CL-FR6-T2-TRACE
- **Statement**: result streams never feed back (per-event, every
  state); metatheoretically distinct histories — one vs two
  presentations of one token — erase to one object state (the collapse
  theorem is that single witness pair, not a universal over histories;
  narrowed 2026-08-18).  **Class**: theorem.
- **Lean**: `trace_erasure`, `histories_collapse`.

### CL-FR6-T3-CONSTRUCTORS
- **Statement**: constructor-channel dependency (singleton algebras are
  monochrome, swap-invariant, and — by the refusal translation —
  collapsed); the search scopes the three
  import channels *by target* — constructors are required for
  result-outcome distinction, tags or relations for carrier-pair
  separability, relations for witnessed relations.  Result codes never
  enter carrier profiles; no target-independent interchangeability of
  the channels is claimed.
- **Class**: theorem + bounded computation.
- **Lean**: `singleton_algebra_monochrome`, `mono_code_swap_invariant`,
  `distinct_code_not_swap_invariant`,
  `distinction_needs_two_constructors`; `histories_collapse` (the
  collapse half, shared with CL-FR6-T2-TRACE — cited here 2026-08-18,
  previously the collapsed adjective was uncovered by this entry's
  list).
- **Python**: matrix cell `separable_pair -> two_result_constructors`
  refuted (recorded countermodel: the relation route — datum retention
  plus relation rule under a singleton algebra; an earlier version said
  "tag-route countermodel", but the artifact's recorded countermodel
  for this cell is the relation route, the tag route also refuting it
  in class — corrected 2026-08-18); target-relative checks
  `separable_without_tag_or_relation`,
  `oriented_without_tag_or_relation`,
  `result_distinction_without_binary_algebra` all empty in class.

### CL-FR6-T4-CARRIER
- **Statement**: refusal-to-carrier per variant; judgment mode gives a
  second judgment, never a datum (horizon-free carrier bound).
- **Class**: theorem + bounded computation.
- **Lean**: `judgment_variant_second_judgment_not_datum`,
  `judgment_carrier_bound`.

### CL-FR6-T5-BRIDGE
- **Statement**: a sufficient non-minimum bridge closes (`stepP`:
  occurrence-style reification + tag + relation; no result store —
  witnessed, irreflexive-as-fact, oriented from one token in two
  presentations); and the unique minimum witnessed route (datum
  retention + relation rule only, on a state with no tag store and no
  result store) closes in Lean, matching the search's single minimum
  under both cost orders.  The tag/relation tie and the order
  disagreement live at the weaker milestones (separable/oriented pair),
  not at the witnessed milestones.
- **Class**: theorem + bounded computation (ties).
- **Lean**: `priced_bridge_closes`, `priced_bridge_oriented`,
  `min_witnessed_route_closes`.

### CL-FR6-T6-LAW
- **Statement**: bridge facts do not entail the irreflexivity law; in
  class every refusal link is born off-diagonal (receipts fresh).
- **Class**: theorem (first clause) + bounded computation (the in-class
  clause).
- **Lean**: `bridge_facts_not_law` (first clause only).
- **Python**: `test_refusal_links_are_born_irreflexive_in_class`
  (exhaustive over the class at the declared event bound — the named
  evidence for the in-class clause; named 2026-08-18, previously the
  clause rested on a Lean theorem that does not cover it).

### CL-FR6-T7-CEILING
- **Statement**: the invariance ceiling, general form: equivariant
  constructions fix outputs of symmetry-fixed states; the bypass is
  exhibited — the bridge state is not a fixed point of the swap.
- **Class**: theorem (general lemma) + exhibited bypass (one state).
  An earlier version said tagged/relational states bypass the ceiling
  "by never being fixed points"; the cited Lean proves non-fixedness of
  the one exemplar, not a universal over the class — narrowed
  2026-08-18.
- **Lean**: `equivariant_output_invariant`; bypass
  `priced_bridge_oriented` (the bridge exemplar).

### CL-FR6-T8-DYNAMICS
- **Statement**: reflective dynamics classified — fixpoint, two-cycle,
  horizon-free growth; the *declared* reflective semantics realizes a
  successor chain for every n (carrier `range (n+1)`, relation
  successor, every link irreflexive).  Realization by declaration, not
  derivation: `stepRefl` itself appends the current length and inserts
  the predecessor edge; refusal alone derives no numerals.  Initiality
  is open (F4).
- **Class**: theorem.
- **Lean**: `untyped_reflect_fixpoint`, `toggle_two_cycle`,
  `reflective_chain_growth`, `reflective_chain_is_initial_segment`,
  `reflective_chain_successor_relation`,
  `reflective_chain_irreflexive_facts`.

### CL-FR6-T9-PRICES
- **Statement**: minimum-price table under two cost orders with all
  ties, split by target: three tied purchases for two-ness under order
  A (order B selects occurrence); tag vs relation routes tied for
  separability under order A (order B selects the tag route); a unique,
  order-independent minimum (the relation route) for witnessed_relation
  and witnessed_irreflexive.  The order disagreement concerns the
  weaker milestones only.
- **Class**: finite computation (exhaustive in class).
- **Python**: `minimum_table`.

### CL-FR6-T10-NORMAL-FORM
- **Statement**: target-relative provenance dependencies, each checked
  exhaustively over the 44 protocols at the declared 6-event horizon
  (carrier cap 4; bounds declared in the FR6 write-up — "reacher" is
  horizon-relative), claims matching checks one-for-one: every witnessed-irreflexive reacher makes a declared
  purchase (zero violations); witnessed relations require the relation
  rule; one-token carrier growth requires reification or occurrence
  retention; separable and oriented pairs require a tag or a relation;
  result-outcome distinction requires the binary algebra.
  `normal_form_holds_in_class` is the conjunction of exactly these
  checks.  The class-general Lean form is the named unresolved
  obligation.
- **Class**: bounded theorem (exhaustive in class).
- **Python**: `normal_form_check`.

## F5 claims (the composite generator)

Full statements, dependencies, and boundaries:
`paper/endogenous_generator.md`; evidence: `artifacts/generator.json`
and `lean4/Derivation/Generator.lean`.

### CL-G-TERMINAL
- **Statement**: split by claim — ENDOGENOUS_GENERATION_PROVED (the
  composite of reflective growth and pair-separation closure has a
  live obstruction at every round from the third on, horizon-free,
  with no per-round external act: the first horizon-free generator
  exhibited here, without a minimality or uniqueness claim, and not
  genesis from `<>`); OBJECT_LANGUAGE_GENERATOR_NOT_IN_SCOPE (the theorem
  is demand persistence for a declared reflective chain and declared
  closure policy, not an object-language demand generator);
  ENDOGENOUS_REPAIR_FAILS_IN_DECLARED_CLASS (over the five declared
  strategies and 15-round computation, the
  fires-repairs-never-imports class is empty);
  GENERATION_REPAIR_EXCLUSION_IN_CLASS (within those declared bounds,
  no strategy both fires, clears every firing round, and avoids
  recurring imports; valued marking prevents rather than repairs a
  fired demand).
- **Class**: theorem (generation; depth-1 strategy cores) + bounded
  computation (exclusion over the declared class; depth-2 leg
  instance-backed and bounded) + open conjecture (general depth-d,
  G2).
- **Lean**: `generation_never_dries` and the CL-G-* theorems below.
  **Axioms**: within {propext, Quot.sound}.
- **Python**: `generator.json` (trajectories, classification table,
  `endogenous_cycle_found: false`, Lean agreement checks).
- **Falsifier**: within the declared bound, a declared strategy
  classified `endogenous_cycle`; or a round ≥ 3 with no obstruction
  under the bare composite.

### CL-G-GENERATION
- **Statement**: for every chain length ≥ 3, elements 1 and 2 are
  distinct carrier elements with equal depth-1 profiles; the only
  event consumed is the internally enabled reflection.  **Class**:
  theorem (horizon-free).
- **Lean**: `generation_never_dries`; regime characterizations
  `reflective_chain_tags`, `chain_tagged_iff`, `chain_hasIn_iff`,
  `chain_hasOut_iff`.

### CL-G-OBSTRUCTIONS-EXACT
- **Statement**: at depth 1 the obstruction set of the bare chain is
  exactly the interior pairs — an iff, for distinct elements within
  the carrier; profile classes seed/interior/tip are pairwise
  distinct.  **Class**: theorem.
- **Lean**: `depth1_obstructions_are_exactly_middle_pairs`,
  `middle_profile`, `endpoint0_profile`, `endpointN_profile`.
- **Python**: agreement check over lengths 1..15.

### CL-G-REPAIR-FATES
- **Statement**: presence automark is vacuous (receipts are already
  tagged; the interior still collapses); every finite marking is
  outgrown, so per-pair repair recurs forever with a fresh import per
  repair; valued automark separates every pair and kills generation —
  its price is an unbounded observable alphabet (presentation identity
  made observable).  **Class**: theorem (each horizon-free).
- **Lean**: `automark_presence_vacuous`, `le_foldr_max`,
  `finite_marks_outrun`, `valued_marks_collapse_generation`.
- **Python**: bounded trajectories; per-pair imports at every firing
  round within the bound.

### CL-G-DEPTH2
- **Statement**: raising the regime to depth 2 separates the near-end
  pair (1, 3) at length 4 and is outrun by the deep-interior pair
  (2, 3) at length 5; within the 15-round bound the depth-2 branch
  fires unrepaired from length 5.  The general depth-d statement is
  open (G2).  **Class**: theorem (decidable instances) + bounded
  computation + open conjecture.
- **Lean**: `depth2_separates_near_ends_n4`, `depth2_obstruction_n5`.

### CL-G-DIRECT-SWAP
- **Statement**: directly transposing interior points 1 and 2 does not
  preserve the successor relation.  This distinguishes the example
  from the earlier branch where that swap is an admitted symmetry.
  It does not quantify over all automorphisms or prove full directed-
  chain rigidity.  **Class**: theorem plus explicit nonclaim.
- **Lean**: `middle_swap_not_relation_preserving`; contrast
  `equivariant_output_invariant`,
  `PrimDiff.symmetric_no_equivariant_classifier`.

### CL-G-EXCLUSION
- **Statement**: over the declared five-strategy class within the
  15-round bound, no strategy fires, repairs, and never imports
  (`endogenous_cycle_found: false`); classification per strategy:
  bare/presence/depth-2 fire unrepaired, per-pair repairs with
  recurring imports, valued is generation-dead.  Depth-1 fates are
  horizon-free theorems; the depth-2 fate is instance-backed and
  bounded.  **Class**: exhaustive finite computation over the declared
  class and bound + theorem cores.
- **Python**: `exclusion_check`.

### CL-G-OPEN
- **Statement**: G1 (no non-identity repair channel, class-general),
  G2 (general depth-d outrun; named single best next theorem target),
  G3 (repair-power = generation-poison as a conservation law), G4
  (the sealed engine as the import branch), F4 carried (chain
  initiality).  **Class**: open conjectures / carried obligations.

## Native primitive-difference interface claims

Full statements, boundaries, and the delivery table:
`paper/difference_interface.md`; evidence:
`lean4/Derivation/DiffInterface.lean` (core-only imports, 35 exported
theorems) and `artifacts/diff_interface.json`.  Externally imposed
challenge (caller request, 2026-08-12); the caller's independent
adapter is external evidence, assumed nowhere.

### CL-DI-EQUIVALENCE
- **Statement**: for every admitted difference observer
  (`δ : X → X → R`, `Zero : R → Prop` with the three laws),
  `ZeroRel x y := Zero (δ x y)` is an equivalence relation; the
  quotient realization is constructible only downstream of this proof
  (it consumes the `Setoid` built from it), and identifies exactly
  the zero-pairs in the sound direction.
- **Class**: theorem.  **Lean**: `zeroRel_equivalence`,
  `obsQuotient_eq_of_zero`; kernel observers inherit the laws from
  `kernelObs` once.

### CL-DI-OBSTRUCTION
- **Statement**: retained / observer-zero / protected are independent
  fields; an active obstruction is exactly their conjunction.  The
  blocking lemmas prove that absence of any conjunct prevents activity.
  The five finite examples specifically exhibit feature-bearing,
  observer-zero pairs in unprotected stages; they do not enumerate every
  proper subset of the conjunction.
- **Class**: definition + theorems.  **Lean**: `ActiveObstruction`,
  `no_guard_no_obstruction`, `unretained_not_active`,
  `distinguished_not_active`.

### CL-DI-REFLECTION
- **Statement**: a bare reflection step (embedding + retraction,
  a point outside the old live image, declared parent, old structure preserved on
  the live region, retained + protected parent/new pair, pre-closure
  zero) certifies an active obstruction on a distinct pair.  The active
  conclusion uses the three declared pair fields and is not derived
  from freshness alone.
- **Class**: theorem.  **Lean**: `BareReflection`,
  `bare_reflection_certifies_active_obstruction`; concrete instance
  `towerReflection`/`tower_obstruction`.

### CL-DI-CLOSURE
- **Statement**: abstract demands are predicates, and closure selects no
  preferred pair; closure steps discharge map-saturated demand sets
  under declared structure-preserving maps, without assuming inverses
  or composition.  `demand_offdiag` makes every demand off-diagonal;
  every step preserves old distinctions, kills every demanded pair,
  and creates no new active obstruction.  The concrete declared
  measure (count of retained, protected, observer-zero ordered pairs)
  strictly decreases (positive before, zero after).
- **Class**: theorem.  **Lean**: `MapSaturated`, `StageMaps`, `ClosureStep`,
  `closure_preserves_old_distinctions`, `closure_kills_demanded`,
  `closure_adds_no_obstruction`, `mem_activePairs`,
  `closed_measure_zero`, `preclose_measure_pos`,
  `towerNext_decrease`.

### CL-DI-PROPOSAL
- **Statement**: when discharge needs new carrier or observer
  structure, `ExtensionProposal` represents request data carrying the
  request kind and demanded set; no stage is ever constructed from a
  proposal in this package.  In the Boolean-view grammar over three
  protected points, every replacement view leaves an active obstruction
  (pigeonhole), so no view in the grammar closes the stage; checked
  exhaustively (8 views) in Python.  `boolProposal` is separately
  available data; no decision theorem forces its selection.
- **Class**: theorem (no closed grammar view) + exhaustive computation;
  proposal selection unresolved.
- **Lean**: `bool_view_pigeonhole`, `bool_grammar_obstruction`,
  `no_bool_view_is_closed`, `boolProposal`.

### CL-DI-TERMINATION
- **Statement**: with fuel exceeding the declared measure, the driver
  reaches `closed` or `proposal` (never out-of-fuel), given strict
  per-step decrease and instantiated for the tower.  Separately, the
  concrete demand enumerator has fixed size 2.  At every `n`, a bare
  reflection and map-saturated closure step are available whose
  application is definitionally the next closed stage; this is a
  pointwise successor-step family, not a formal trace object or a
  finite-prefix induction theorem.  Old distinctions persist to every
  later horizon.
- **Class**: theorem.  **Lean**: `drive_terminates`,
  `tower_fuel_terminates`, `tower_demand_bound`,
  `tower_demand_characterized`, `tower_successor_step`,
  `tower_step_composes`, `cview_distinct_mono`, `tower_closed`.

### CL-DI-COUNTERMODELS
- **Statement**: freshness, tagging, an edge, a new hash, and
  repetition each fail, alone, to produce observer-visible difference
  — and, unprotected, fail to produce an active obstruction.
- **Class**: countermodels (concrete finite instances).
- **Lean**: `cm_freshness`, `cm_tagging`, `cm_edge`, `cm_hash`,
  `cm_repetition`.  **Python**: countermodel table in the artifact.

### CL-DI-BOUNDARIES
- **Statement**: the package imports core Lean only and assumes
  nothing about downstream consumers; `zero_preserved`/`zero_pres`
  are live-region-scoped; the abstract termination theorem is
  conditional on the declared measure decrease; axioms of all 35
  exported theorems within {propext, Quot.sound}.
- **Class**: boundary record.  **Falsifier**: an import of any
  development module or external vocabulary into
  `DiffInterface.lean`; an exported theorem outside the axiom set.

## Represented-progress claims (the kernel without an outside)

Full statements and the exact ceiling:
`paper/represented_progress.md`; evidence:
`lean4/Derivation/Represented.lean` (native, core-only, 48 exported
theorems) and `artifacts/represented.json`.  Externally imposed
challenge (caller assignment, 2026-08-12).

### CL-RP-TERMINAL
- **Statement**: scoped to a fixed kernel constitution.  The
  constitution — event grammar, sep/sat laws, response menu,
  acceptance predicates, history producer — is fixed metatheory.
  Relative to that fixed `step` semantics:
  REPRESENTED_KERNEL_EXISTS (every *runtime* input — evaluator,
  requirement, scheduler, tie-break, fresh-name source, fuel,
  authorization, stopping condition — occurs in the represented state
  or history, and the eight target theorems hold in their declared
  scopes); HIDDEN_INPUT_CLASSES_REFUTED (four hidden-runtime-input
  countermodels, plus four neighboring semantic/inference failures,
  split and machine-checked);
  CERTIFICATION_BOUNDED_BY_PANEL_QUOTIENT (internal certification is
  exactly the panel's joint quotient, never correspondence).  The
  constitution does not derive itself.
- **Class**: theorem (kernel-scoped) + countermodels + bounded
  computation.  **Axioms**: within {propext, Quot.sound}.
- **Falsifier**: a runtime input changing a kernel result without
  occurring in `supp`/history; a countermodel failing its exhibited
  divergence; a certified claim exceeding the panel's joint separation
  power.

### CL-RP-DEFINITIONS
- **Statement**: the ten required notions defined natively —
  representation (`World`), admitted transformation (guarded `step`),
  history/replay, recorded requirement, obstruction (recorded
  requirement + exhaustive menu failure, never lookalikeness),
  same-structure repair, structure-creating augmentation, represented
  support (`supp`), internally determined successor family
  (`repairFamily`, all ties kept), replay-equivalence (`WEquiv`).
- **Class**: definition.

### CL-RP-REPLAY
- **Statement**: replay determinism (definitional for the kernel — the
  step type admits no unrepresented argument) and composition
  (`Represented.replay_append`).  **Class**: theorem.
- **Lean**: `Represented.replay_deterministic`, `replay_nil`,
  `Represented.replay_append`.

### CL-RP-SUPPORT
- **Statement**: operational-support factorization — the step factors
  through the `supp` projection: support-agreeing worlds have
  support-equal successors for every event; contrapositively, runs
  whose successor supports differ already differ in represented
  support.  A factorization theorem, not a claim of per-datum result
  causation.  The inert notes field is provably inert.
- **Class**: theorem.
- **Lean**: `support_determines`, `internal_support`, `notes_inert`.

### CL-RP-NO-HIDDEN-CHOICE
- **Statement**: scoped to `repairFamily` — the same-structure
  successor family is the complete set of accepted responses with all
  ties retained (sound + complete filter, no selector);
  replay-equivalent worlds step to replay-equivalent worlds with
  membership-identical successor families.  The progress theorem's
  structural branch exhibits the canonical augmentation `[i]`, whose
  orientation is supplied by the ordered, recorded requirement — a
  represented datum and a stated scoping; augmentation candidates are
  not gathered into a retained family, and this claim does not extend
  to them.  **Class**: theorem (scoped).
- **Lean**: `repairFamily_sound`, `repairFamily_complete`,
  `repairFamily_retains_ties`, `equiv_step`, `equiv_replay`,
  `equiv_repairFamily`.

### CL-RP-REPAIR-AUG
- **Statement**: accepted repairs discharge a recorded violation and
  preserve every previously satisfied requirement; accepted
  augmentations satisfy the exact positive-satisfaction delta equation
  (`satB_aug`) and preserve every satisfied positive requirement
  (`aug_preserves_satisfied`) while verifiably adding expressive
  capacity.  Old *non-separation* judgments are not preserved —
  changing them is the licensed content of augmentation; the earlier
  word "conservativity" is withdrawn as an overclaim.
- **Class**: theorem.
- **Lean**: `mark_discharges`, `mark_preserves`, `step_mark_sound`,
  `satB_aug`, `aug_preserves_satisfied`, `aug_increases`.

### CL-RP-PROGRESS
- **Statement**: under replay well-formedness (an invariant) and a
  recorded violation, the repair family is non-empty or the violation
  is a certified obstruction whose canonical singleton augmentation is
  accepted and discharges it; the isolated remaining hypotheses are
  the represented budget and license.  Refusal records verified
  same-level exhaustion and is non-absorbing: it certifies, it does
  not terminalize; ending a bounded run belongs to the metatheoretic
  history producer, and no terminalization-in-refusal is claimed.
- **Class**: theorem.
- **Lean**: `represented_progress`, `wf_genesis`, `wf_step`,
  `wf_replay`, `progress_needs_budget`, `progress_needs_license`,
  `refusal_needs_certificate`, `refusals_are_represented`.
- **Python**: the pigeonhole story (violation → empty family →
  obstruction certificate → accepted augmentation → discharge →
  quiescence).

### CL-RP-CLOSURE
- **Statement**: new violations arise only from represented `require`
  events; quiescent worlds stay quiescent under every non-`require`
  event.  **Class**: theorem.
- **Lean**: `violation_only_from_require`, `quiescent_stable`.

### CL-RP-PRODUCTIVITY
- **Statement**: one prefix-compatible unbounded run under an
  *explicitly supplied* event stream (the history producer is
  metatheory, never called endogenous), with carrier literally
  `range (k+1)` reached through the acceptance-guarded kernel;
  per-event acceptance and per-stage quiescence verified exhaustively
  to the 15-round bound (Python) with a Lean quiescence instance at
  k = 3; productivity is separated by proof from per-length witnessing
  (the represented König failure: witnesses at every length, no
  compatible infinite source).  **Class**: theorem + finite
  computation.
- **Lean**: `histUpTo_prefix`, `admit_data_fresh` (spelled
  `admitTok`), `worldAt_data`, `worldAt_growth`, `productive_run`,
  `worldAt_three_quiescent`, `wit_all_lengths`, `wit_no_infinite`.

### CL-RP-CERTIFICATION
- **Statement**: internal certification by represented evaluators is
  exactly joint separation by the panel's own columns; it is not
  correspondence (a unanimous panel certifies an equivalence an
  outside column refutes) and not monotone under panel extension.
  Classification: the panel is an explicit certification argument —
  represented data by type but not carried in `World` or admitted by
  events; certification is not replay-integrated in this kernel.
- **Class**: theorem + countermodels.
- **Lean**: `cert_scope`, `cert_not_correspondence`,
  `cert_panel_relative`.

### CL-RP-COUNTERMODELS
- **Statement**: eight small (not proved minimal) machine-checked
  witnesses, split by class.  Hidden runtime inputs (an input in neither state nor
  history): unrecorded scheduler, unrecorded fresh-name source, hidden
  evaluator, order-sensitive tie-break.  Neighboring
  semantic/inference failures (no hidden input; a wrong definition or
  reading): incomplete search (false obstruction), destructive rewrite
  (vs append-only augmentation), repetition-as-progress, per-length
  witnesses without a compatible infinite history.
- **Class**: countermodels.
- **Lean**: `scheduler_hidden`, `gensym_hidden`, `oracle_hidden`,
  `incomplete_search_false_alarm`,
  `augmentation_destroys_old_replay`, `repetition_not_progress`,
  `order_sensitivity_splits_equivalents`.
- **Python**: countermodel table; mutation tests (every single-event
  mutation of the story history changes the replay).

### CL-RP-CEILING
- **Statement**: representability of runtime inputs is proved relative
  to the fixed constitution (which does not derive itself); uniqueness
  is not proved (policies are represented choices); progress is
  conditional on represented budget/license, with refusal
  non-absorbing; certification never exceeds the panel quotient and is
  not replay-integrated; admission order is semantic (occurrence
  identity) while view/requirement/refusal order is provably not; the
  carrier is the naturals in both formalisms (negative inputs rejected
  in the mirror, matching Lean's `Nat` exactly); the two standing
  rules are proved consistent and sufficient for this kernel within
  bounds — their general forms remain conjectures.
- **Class**: boundary record + conjecture (general forms).

## Ultra-closure claims (the completed native derivation)

Full statements: `paper/native_derivation_completion.md`; bridge
table: `paper/native_derivation_map.md`; machine evidence: the five
`completion_*.json` artifacts; Lean:
`Completion/NoOutside/Constitution/Initiality` (57 new exported
theorems; 291 total, all within {propext, Quot.sound}).

### CL-NC-TERMINALS
- **Statement**: RELATIVE_REPLAY_CLOSURE_ONLY;
  EVENT_SOURCE_INTERNALIZED_RELATIVE_TO_FIXED_INTERPRETER;
  KERNEL_CONSTITUTION_INTERNALIZED_RELATIVE_TO_FIXED_INTERPRETER;
  KERNEL_CONSTITUTION_REMAINS_META (outermost layer — the single OPEN
  edge in the declared graph, which does not claim to exhaust every
  possible bridge);
  UNIQUE_PROBE_COMPLIANT_DESCRIPTOR_IN_DECLARED_TOGGLE_CLASS;
  ABSOLUTE_NO_OUTSIDE_UNFORMULABLE.  FULL_NATIVE_COMPOSITION is not
  claimed; categorical initiality is not claimed.
- **Class**: theorem (relative closures) + boundary record (the OPEN
  bridge and the unformulable absolute).
- **Falsifier**: a represented member of the constitution family that
  executes its own family interpreter; a kernel result changed by an
  input outside represented support/history/constitution; a second
  compliant member of the declared class.

### CL-NC-COMMON-STATE
- **Statement**: one common native state carries the do-not-erase
  distinctions as separate fields, with retention, protection, and
  observer-zero as three independent obstruction conditions
  (`obstC_conditions_independent`; the kernel transport instantiates
  retention and protection from one store — a stated identification);
  the kernel, the reflective chain, the two-element difference
  objects, and the early collapse checkpoint transport with
  preservation theorems; S2 symmetry is scoped to the relation store
  (`s2_state_not_swap_invariant` for the whole-state boundary);
  witness does not transport to separation, separation does not
  transport to witness, and metatheoretic inequality is operationally
  inert.
- **Class**: definition + theorem + countermodels.
- **Lean**: `ofWorld_sep`, `ofWorld_obstruction`, `ofWorld_quiescent`,
  `obstC_conditions_independent`, `chain_transport`,
  `d2_transport_oriented`, `s2_transport_symmetric`,
  `s2_state_not_swap_invariant`, `witness_not_separation`,
  `separation_not_witness`, `meta_distinctness_inert`,
  `early_collapse_transports`.

### CL-NC-RULE1
- **Statement**: Rule 1's strongest forms — the operational
  dichotomy (repair family versus exhaustion-plus-extension family)
  with tie-retained extension family (both orientations proved
  accepted); refusal a parallel, non-absorbing record, proved
  object-inert and outside the binary action algebra
  (preserve-presentation / change-presentation, by the signature
  measure); budget/license execution a separate represented gate; the
  fidelity reduction (no protected requirement, no obstruction); the
  retraction countermodel bounding the preservation law to what the
  acceptance guard buys.  Classification: derived for the fixed
  kernel, fidelity-relative in general, primitive nowhere.
- **Class**: conditional theorem + countermodels.
- **Lean**: `rule1_repair_or_extension`, `augFamily_retains_ties`,
  `refusal_recordable`, `Completion.refusal_object_inert`,
  `refusal_non_absorbing`, `action_dichotomy`, `rule1_needs_fidelity`,
  `retraction_breaks_preservation`.

### CL-NC-RULE2
- **Statement**: Rule 2's strongest forms — support factorization
  extended to histories, successor families, certificates, and
  verdicts; the effectual-outside dichotomy (operational,
  constitution-relative; the absolute form is unformulable in this
  calculus); the family-valued invariance ceiling; the certification
  panel replay-integrated by a conservative extension, with
  panel-induced non-separation proved an equivalence and the
  certificate proved equal to joint-quotient membership for a non-empty
  panel (the empty panel certifies nothing while its joint quotient is
  vacuously total — non-emptiness scope made explicit 2026-08-18).
- **Class**: theorem + boundary record.
- **Lean**: `support_replay`, `support_repairFamily`,
  `support_obstructed`, `support_quiescent`,
  `effectual_outside_dichotomy`, `equivariant_family_invariant`,
  `stepC_conservative`, `admitEvaluator_base_inert`, `panel_equiv`,
  `certNeg_iff_panelEquiv`, `certC_ceiling`.

### CL-NC-EVENT-SOURCE
- **Statement**: the event source is internalized relative to the
  fixed interpreter, under metatheoretic iteration: the policy is
  represented data; the generator invokes the next-family interpreter
  on the replayed state and appends the unique family member
  (state-derived, prefix-compatible generation — no internal-trigger
  claim: no represented transition invokes the interpreter); the
  interpreter emits complete tied families (singleton for the tower —
  proved; both augmentation orientations for closure); fresh names
  are canonical numerals, fresh on the tower invariant
  (`freshName_fresh_on_tower`) and not in general
  (`freshName_not_fresh_generally`) — a recorded arithmetic/ordering
  import; budget replenishment is an emitted represented event; the
  stop outcome is the represented empty family; and the generator
  reproduces the previously supplied tower stream exactly
  (`driver_reproduces_tower`).
- **Class**: theorem (relative) + declared policy (the generation
  policy itself).
- **Lean**: `nextFamily_tower_singleton`,
  `closeBlocks_complete_repair`, `closeBlocks_complete_aug`,
  `nextFamily_stop`, `towerBlock_eq`, `driver_reproduces_tower`,
  `nextFamily_complete`, `budget_replenishment_represented`,
  `gen_growth`, `gen_three_quiescent`.
- **Python**: `completion_protocols.json` (reproduction and
  acceptance exhaustive to the 15-round bound).

### CL-NC-AUTONOMY
- **Statement**: autonomy separated from iterability by the
  nine-level ladder, assessed for the tower generation: levels 1-3
  and 5-9 proved (steps, prefix compatibility, interpreter-computed
  families, selection-freeness, represented replenishment, lawfulness
  across extension, explicit productivity); level 4 (internal
  trigger) explicitly NOT attained — the iteration is metatheoretic.
  Arbitrary iterability is levels 1-2 only.  Level 8 (lawfulness) is
  carried by the Horizon module at every stage, not only at stage 3:
  the generated world's complete record is characterized by induction
  (`worldAt_spec`), quiescence and well-formedness hold at every
  horizon (`gen_quiescent`, `gen_wf`), and every emitted event of
  every block is accepted (`block_all_accepted`,
  `genesis_accepted`).  PR #12 correction C6: the prior version of
  this entry cited `tower_driver_autonomy` alone for "lawfulness
  across extension", but that theorem has no lawfulness conjunct —
  the only Lean lawfulness fact was the stage-3 instance
  `gen_three_quiescent`.  The gap is closed upward, not rescoped.
- **Class**: theorem (relative).
- **Lean**: `tower_driver_autonomy`, `Horizon.worldAt_spec`,
  `Horizon.gen_quiescent`, `Horizon.gen_wf`,
  `Horizon.block_all_accepted`, `Horizon.genesis_accepted`.

### CL-NC-CONSTITUTION
- **Statement**: the kernel constitution is represented as data
  within a completely enumerated 64-member family; the fixed family
  interpreter executes any description; the kernel's own description
  executes to exactly the sealed step (verified self-description).
  Quotation, executable description, and verified self-description
  are distinct definitions.  The outermost interpretation relation
  remains metatheoretic — the named irreducible obligation and the
  graph's single OPEN bridge.
- **Class**: theorem (family-relative) + OPEN (absolute).
- **Lean**: `interp_describe`, `allDescs_length`, `allDescs_complete`.

### CL-NC-INITIALITY
- **Statement**: in the declared 64-member class under the declared
  probe battery: every guard is load-bearing (six concrete
  separations); the sealed kernel's description is the unique
  probe-compliant member; both declared cost orders agree on the
  singleton; and the panel extension retracts onto the kernel (split
  retract).  Categorical initiality is NOT claimed — a six-probe
  singleton and one split retract do not establish it.  Scope:
  class-relative; "most primitive engine" is underdetermined as an
  absolute claim and proved as this class-relative one.
- **Class**: theorem (class-scoped) + bounded computation (the
  64-member compliance table).
- **Lean**: `dedup_load_bearing`, `require_guard_load_bearing`,
  `accept_guard_load_bearing`, `budget_gate_load_bearing`,
  `license_gate_load_bearing`, `refusal_certificate_load_bearing`,
  `unique_compliant`, `minimum_unique_in_class`, `extension_retract`,
  `extension_retract_replay`, `retract_section`.
- **Python**: `completion_minimality.json`.

### CL-NC-INVENTORY
- **Statement**: the theorem inventory is source-derived (names and
  axiom sets from the axiom artifact; statements extracted from
  sources; consumers and citing claims by search) and pinned by test
  to exactly the exported estate; the dependency graph classifies all
  thirty bridges with resolving evidence; exactly one bridge is OPEN.
- **Class**: finite computation + declared metadata (kind/role
  labels).
- **Python**: `completion_dependency_graph.json`,
  `completion_countermodels.json`, `completion_receipt.json`.


## PR #12 — Primitive Difference contact and passage

### CL-PD2-HORIZON
- **Statement**: the generated run's complete record is characterized
  at every stage by induction; quiescence, well-formedness, and
  per-event acceptance hold at every horizon; the family
  interpreter's budget semantics is pinned as a trichotomy (unchanged
  / saturating decrement / explicit set) for every descriptor and
  event, and the Python mirror asserts the identical facts on the same
  declared finite basis (all 64 descriptors over the probe worlds and
  events — the module header's own wording, restored here 2026-08-18).
- **Class**: theorem (horizon-free) + refuted-and-repaired prior
  claim (see change log, PR #12 Phase I).
- **Lean**: `Horizon.worldAt_spec`, `Horizon.worldAt_quiescent`,
  `Horizon.worldAt_wf`, `Horizon.block_all_accepted`,
  `Horizon.genesis_accepted`, `Horizon.gen_quiescent`,
  `Horizon.gen_wf`, `Horizon.interp_budget_bound`,
  `Horizon.budget_saturation_noop`,
  `Horizon.mark_saturation_all_descs`.
- **Python**: `test_budget_saturation_matches_lean_nat`,
  `test_budget_trichotomy_every_descriptor_event`.

### CL-PD2-MATRIX
- **Statement**: nine candidate readings of primitive difference over
  one signature; all 72 ordered implication cells settled: 17
  implications proved, 51 finite countermodels compiled (minimum
  carrier proved where cited), 4
  located cells OPEN with exact metatheoretic scope (every decidable
  relation is located; no internal countermodel can exist).
  Cotransitivity is automatic on the two-element carrier, making the
  three-element countermodels minimum-carrier.
- **Class**: theorem + countermodel + OPEN (scoped), cross-verified
  by exhaustive finite computation.
- **Lean**: `PrimitiveCore.matrixCells`, the 68 `imp_*`/`nimp_*`
  theorems, `PrimitiveCore.cotrans_auto_on_two`,
  `PrimitiveCore.located_of_decidable`, `PrimitiveCore.D_iff_ne`,
  `PrimitiveCore.e_empty_iff_d`.
- **Python**: `primitive_candidates.json`,
  `primitive_implication_matrix.json` (expected_equals_computed).

### CL-PD2-INITIALITY
- **Statement**: the oriented two-element realization is initial in
  the category of ALL pointed witnessed relations (true universal
  property, category laws proved).  Scope (review pass): `PtdRel`
  carries no irreflexivity, so this initiality characterizes the
  bare-witness reading W — the free pointed object on one witnessed
  arrow — and restricts to the irreflexive subcategory
  (`d2_initial_irrefl`); initiality does not itself select
  irreflexivity, whose independent justification is `imp_a_d`
  against `nimp_w_d`.  The symmetric realization is initial exactly
  in the symmetric subcategory and not weakly initial in the full
  one; initiality is unique up to isomorphism only, distinct from
  presentation identity and from minimum cardinality; pointed
  automorphisms are trivial for both realizations — orientation
  lives in the pointing.
- **Class**: theorem.
- **Lean**: `PrimitiveCats.d2_initial`,
  `PrimitiveCats.d2_initial_irrefl`, `PrimitiveCats.s2_initial_sym`,
  `PrimitiveCats.s2_not_weakly_initial`, `PrimitiveCats.initials_iso`,
  `PrimitiveCats.two_initials_not_identical`,
  `PrimitiveCats.larger_not_initial`, `PrimitiveCats.pointed_rigid`.

### CL-PD2-BRANCHING
- **Statement**: the faithful-presentation category of a
  three-occurrence source has no weakly terminal object: the maximal
  observer cuts are incomparable and both retained.  On the two-point
  source the cut-branching vanishes but unrestricted terminality
  fails anyway, constructively (`no_terminal_pres2`, review-pass
  closure of the former OPEN cell: the free-point presentation gives
  every target two distinct commuting maps); the positive fragment
  is uniqueness against surjective presentations (no classical
  choice used).  Cut census on carriers 2-4: 1, 2, 4 (Lean); carrier
  5: 8 (finite computation — the Lean census theorem stops at carrier
  4, and the carrier-5 value was previously uncited; evidence named
  2026-08-18).
- **Class**: theorem + OPEN (scoped) + finite computation.
- **Lean**: `PrimitiveCats.no_terminal_pres`,
  `PrimitiveCats.no_phom_mergeA_mergeB`,
  `PrimitiveCats.no_phom_mergeB_mergeA` (the B-to-A half of
  incomparability, previously uncited — added 2026-08-18),
  `PrimitiveCats.no_terminal_pres2`,
  `PrimitiveCats.phom2_unique_of_epi`;
  `HigherStructure.cut_census_growth` (carriers 2-4 only).
- **Python**: `primitive_passage.json:cells.invariants.cut_census`
  (carriers 2-5: 1, 2, 4, 8), `test_cut_census`.

### CL-PD2-APARTNESS
- **Statement**: positive apartness (irreflexive, symmetric,
  cotransitive) makes indistinguishability an equivalence, with each
  law spent at exactly one clause; omissions are refuted by minimal
  finite countermodels (carriers 1, 2, 3; minimality proved).  Both
  orientations of the two-point relation generate the same apartness
  and the same indistinguishability while remaining distinct data;
  the oriented-witness preservers are exactly the identity, the
  apartness preservers exactly the identity and the swap, constants
  preserve neither; the closure of any admitted family preserves the
  oriented witness iff every generator does.
- **Class**: theorem + countermodel, exhaustively mirrored to
  carrier 3 with preservation censuses to carrier 4.
- **Lean**: `Apartness.indist_equivalence`,
  `Apartness.bare_breaks_refl`, `Apartness.irrefl_alone_breaks_symm`,
  `Apartness.subsingleton_indist_total`,
  `Apartness.symm_without_cotrans_breaks_trans`,
  `Apartness.two_point_indist_trans`, `Apartness.s2_isApart`,
  `Apartness.orientations_same_apartness`,
  `Apartness.orientations_differ`,
  `Apartness.oriented_preserver_unique`,
  `Apartness.apart_preserver_pair`, `Apartness.clos_oriented_iff`,
  `Apartness.oriented_family_trivial`.
- **Python**: `apartness.json`.

### CL-PD2-CONTACT
- **Statement**: the declared contact package is absent at
  blind-native-base and at completion; the contact phases terminate
  CONTACT_INPUT_ABSENT; no contents invented; the native kernel
  interface any future contact must meet is committed (kernel
  binding, universal status, orientation fork, branching, matrix).
- **Class**: declared protocol outcome + runtime check.
- **Lean**: `PrimitiveContact.native_kernel_initial`.
- **Python**: `primitive_contact.json`.
- **Scope note (2026-08-13)**: true at its run and unchanged as
  stated — the package WAS absent at `blind-native-base` and at
  completion, and the interface committed there was met, not revised.
  The package has since arrived and the collision has been executed
  against exactly that interface; the pre-contact terminal is
  preserved as sealed history (`PrimitiveContact.contactStatus`,
  `contactStatusHistory[0]`, `primitive_contact.json:history[0]`, and
  the receipt's CONTACT_INPUT_ABSENT entry with its sealed-history
  scope field), and the current status is
  CONTACT_PROCESSED_LEAN_ONLY.  The new content is claimed in
  CL-PD2-CONTACT-RECONSTRUCTION, -BRIDGE, -COUNTERMODELS,
  -DICTIONARY, -KERNEL, -ENTRY and -VERDICT below; nothing in this
  entry is withdrawn.

### CL-PD2-PASSAGE
- **Statement**: each of the thirteen arrows of the passage chain
  has exactly one status with executable evidence.  Review-pass
  composition repair: the passage now carries a separate ASSERTED
  store — `assertWit` supplies the positive witness, `admitWit`
  retains an asserted difference — so a pre-retention Primitive
  Difference state exists (`assertion_not_retained`), retention
  demonstrably requires assertion (`retention_requires_assertion`),
  and candidate A transports into the passage as a theorem
  (`assert_transport` on every replayed state via the off-diagonal
  invariant `asserted_offdiag`; named instance
  `kernel_enters_preretained` — previously "canonical instance", a
  restricted word with no uniqueness or minimality proof for that
  state; narrowed 2026-08-18).  Active obstruction has three written
  factors, with four gates in the proved factorization (retained,
  protected, observation DECLARED, observer-zero) and every maximal
  proper gate subset refuted;
  primitive difference precedes observation as a theorem
  (`wit_independent_of_obs` — definitional field separation: states
  differing only in observation keep the same witnesses); ZeroRel is
  an equivalence before quotienting; THE TWO-RULE THEOREM, exactly
  scoped: under the DECLARED singleton-column extension universe
  (which contains a separator for every well-formed pair — the
  obstruction identifies one, it does not manufacture the
  constructor) and the declared same-level menu, an active
  obstruction with an in-bounds protected pair has a nonempty repair
  family or certified exhaustion plus a nonempty extension family;
  `setBudget 1` in emitted blocks is a declared self-funding policy;
  refusal is an inert record, the terminal absorbs, proposal is not
  execution; the represented next-family has
  stop/nonempty/completeness theorems and its iteration remains
  metatheoretic (stated).
- **Class**: theorem (+ declarations priced as admission events with
  countermodels).
- **Lean**: `PrimitivePassage.assert_transport`,
  `PrimitivePassage.kernel_enters_preretained`,
  `PrimitivePassage.assertion_not_retained`,
  `PrimitivePassage.retention_requires_assertion`,
  `PrimitivePassage.asserted_offdiag`,
  `PrimitivePassage.retained_sub_asserted`,
  `PrimitivePassage.wit_independent_of_obs`,
  `PrimitivePassage.obst_requires_observation`,
  `PrimitivePassage.obst_conditions_independent`,
  `PrimitivePassage.zero_refl`, `PrimitivePassage.zero_symm`,
  `PrimitivePassage.zero_trans`, `PrimitivePassage.menu_complete`,
  `PrimitivePassage.extension_always_available`,
  `PrimitivePassage.two_rule`,
  `PrimitivePassage.proposal_not_execution`,
  `PrimitivePassage.budget_gates_execution`,
  `PrimitivePassage.refusal_object_inert`,
  `PrimitivePassage.terminal_absorbing`,
  `PrimitivePassage.extension_resolves`,
  `PrimitivePassage.nextFamilyP_stop`,
  `PrimitivePassage.nextFamilyP_nonempty`,
  `PrimitivePassage.nextFamilyP_complete_repair`,
  `PrimitivePassage.nextFamilyP_complete_ext` (the precedence and
  completeness citations were previously asserted in the Statement
  but unnamed here — added 2026-08-18).
- **Python**: `primitive_passage.json` (arrows + growth reports).

### CL-PD2-GROWTH
- **Statement**: the growth driver iterates the passage; the grown
  state at every stage is exactly the path graph with per-edge
  protection and one observation column per resolved obstruction
  (characterized by induction); each round's obstruction, nonempty
  response family, resolution, and creation record are theorems;
  quiescence is restored after every round; the connectivity residue
  is 1 at every stage (the path form itself is `graphAt_spec`; the
  residue alone proves neither connectedness nor acyclicity).
  Provenance, exact: the DRIVER supplies the graph data (occurrence,
  assertion, retention, protection); the OBSTRUCTION creates the
  observation column that resolves it.
- **Class**: theorem (horizon-free), mirrored to 15 rounds.
- **Lean**: `HigherStructure.graphAt_spec`,
  `HigherStructure.round_obstruction`,
  `HigherStructure.round_two_rule`,
  `HigherStructure.round_resolution`,
  `HigherStructure.round_creation_record`,
  `HigherStructure.graph_growth`,
  `HigherStructure.graphAt_quiescent`,
  `HigherStructure.path_connectivity_residue`.

### CL-PD2-LADDER
- **Statement**: the declared cell calculus admits a k+1-cell exactly
  over a complete unfilled boundary of k-cells — the shell guards
  `shell1/2/3` (complete boundaries, deliberately NOT simplicial
  horns, which omit a face).  The ladder recurrence — the two-rule
  shape one dimension up — is PROVED at dimensions 2 and 3
  (`ladder_dim2`, `ladder_dim3`); recurrence at every dimension is a
  frontier conjecture.  Shell guards are load-bearing and the shell
  does not fill itself (higher structure admitted, never forced);
  the four-occurrence demonstration grows 0-, 1-, 2-, 3-simplices in
  replayable creation order with the 1-skeleton equal to the passage
  witness store; the alternating cell-count statistic runs 4, -2, 2,
  1 along the stages (a statistic, not an invariant); with declared
  integer coefficients and boundaries the composite boundary
  vanishes on every demonstration cell, and two distinct conventions
  both work — the convention is declared content.
- **Class**: theorem + finite computation; non-forcing by
  countermodel.
- **Lean**: `HigherStructure.ladder_dim2`,
  `HigherStructure.ladder_dim3`,
  `HigherStructure.shell_guard_load_bearing`,
  `HigherStructure.filling_not_forced`, `HigherStructure.k4_builds`,
  `HigherStructure.k4_skeleton_agrees`,
  `HigherStructure.altNum_stages`,
  `HigherStructure.d2_zero_triangles`, `HigherStructure.d2_zero_tet`,
  `HigherStructure.boundary_not_forced`.

### CL-PD2-CONTROLLER
- **Statement**: in the declared 1024-member variable-event-grammar
  class, response-liveness is exactly the two-rule support (all 128
  live members execute the resolution at the certified obstruction;
  each response kind load-bearing by countermodel); the live family
  is essentially non-unique (full vs no-refuse agree on every
  refusal-free event, differ at a certified obstruction) — the sealed
  six-toggle uniqueness is class-relative; the simulation category
  has proved laws, every ordered pair is connected by constant
  simulations, and initiality is refuted everywhere (including the
  live subcategory); the strict refinement excludes constants yet
  global uniqueness still fails by an invariant-twist countermodel;
  uniqueness holds exactly on the genesis-reachable orbit — proved for
  the exhibited hom-set (the all-on controller into the refusal-free
  controller, the same pair carrying the twist countermodel); no other
  ordered pair is claimed (pair scope made explicit 2026-08-18).
- **Class**: theorem + countermodel + finite computation.
- **Lean**: `ControllerCategory.allKinds_complete`,
  `ControllerCategory.interpK_full`,
  `ControllerCategory.live_census`,
  `ControllerCategory.tworule_executable_of_live`,
  `ControllerCategory.dead_without_addcol`,
  `ControllerCategory.dead_without_budget`,
  `ControllerCategory.dead_without_refine`,
  `ControllerCategory.nonrefuse_agree`,
  `ControllerCategory.refuse_distinguishes`,
  `ControllerCategory.erase_sim`,
  `ControllerCategory.every_pair_connected`,
  `ControllerCategory.no_initial_ctrl`,
  `ControllerCategory.no_initial_live_ctrl`,
  `ControllerCategory.const_not_strict`,
  `ControllerCategory.strict_not_unique`,
  `ControllerCategory.strict_agree_on_reachable`.
- **Python**: `primitive_controller_category.json`.

### CL-PD2-INTERPRETER
- **Statement** (review-pass scope): every finite code list under
  any evaluation map is missed by a same-type function — FINITE
  extensional incompleteness, via a diagonal that differs only at
  the operationally inert notes field; NOT a self-interpretation
  impossibility, NOT "the evaluator cannot be coded", NOT a semantic
  tower theorem.  The declared 64-family has an exact universal
  code/evaluator, scoped; one typed-refusal extension is defined, with
  no theorem that partiality is forced or total evaluation impossible;
  `family_missed` proves finite image non-exhaustion only.  A DECLARED model of the
  description/interpreter boundary satisfies candidates A and F with
  obstructed collapse; its relation/retention/protection are
  inserted by definition, and no theorem links the uncoded
  occurrence to the missed function.  The identification of the
  boundary with a Primitive Difference is a FRONTIER CONJECTURE
  whose missing theorem (denotational/operational grounding) is
  stated in the receipt.  Absolute no-outside not claimed.
- **Class**: theorem + countermodel + finite computation +
  CONJECTURE (boundary identification) + OPEN (absolute closure).
- **Lean**: `InterpreterBoundary.tower_persists`,
  `InterpreterBoundary.i2_universal_in_class`,
  `InterpreterBoundary.i3_refusal_code_returns_none`,
  `InterpreterBoundary.i3_coded_member_returns_some`,
  `InterpreterBoundary.family_missed`,
  `InterpreterBoundary.i5_boundary_is_A`,
  `InterpreterBoundary.i5_boundary_is_F`,
  `InterpreterBoundary.i5_collapse_obstructed`,
  `InterpreterBoundary.i5_family_not_extensionally_complete`
  (audit repair: renamed from the earlier i5_difference_grounded, whose
  statement is `family_missed` and mentions neither the
  boundary pair nor the uncoded occurrence;
  `InterpreterBoundary.arbitrary_uncoded_assignment` proves a freely
  chosen carrier interpretation is vacuous, and the denotational
  bridge is only an OPEN obligation label in
  `InterpreterBoundary.openDenotationalBridge`).
- **Python**: `primitive_interpreter.json`.

### CL-PD2-RECEIPT
- **Statement**: the completion receipt binds base commit, contact
  status, prompt hashes, toolchain pins, the axiom-report hash, all
  declared finite bounds, ten terminal claims each mapped to theorem
  or countermodel evidence, five open obligations, the twenty-attack
  adversarial record, and the two withdrawn-or-repaired claims.
- **Class**: finite computation (deterministic generator).
- **Python**: `primitive_completion_receipt.json`,
  `run_primitive_receipt.py`.
- **Scope note (2026-08-18)**: the ten/five/twenty counts above are
  the PR #12 close figures.  The receipt has since been extended in
  place (its extensions list has twelve entries): the committed
  artifact now binds thirteen terminal claims, eight open obligations,
  and a twenty-one-entry adversarial record — recounted from the
  artifact this date; the two withdrawn-or-repaired claims stand.

### CL-PD2-ATTACHMENT (repaired, final pass)
- **Statement**: one-edge attachment (a fresh walking edge glued
  along a represented parent: assert, retain, protect) is lawful at
  every stage for every LAWFUL policy — a `LawfulPolicy` carries
  the proof that each chosen parent is represented; NO CLAMPING
  occurs anywhere (the retired clamp survives only as the recorded
  countermodel `clamp_rewrote_input`, and an illegal choice meets
  the typed refusal `AttachOutcome.refusedParent`, never a
  rewrite).  Occurrence identity is resolved: `occ` stores TOKENS
  in admission order, POSITIONS are the identities used by every
  relational store; the canonical fresh token is one past the
  maximum, fresh on EVERY carrier (`freshTok_fresh`), while
  length-as-token fails on non-initial carriers
  (`length_not_fresh_countermodel`); on canonical tree states
  tokens and positions provably coincide and the tree block IS the
  Up block (`freshTok_treeState`, `attachBlock_is_upBlock`).
  Completeness is REGISTRY-RELATIVE and an iff:
  `b ∈ Up(s) ↔ LegalOneEdgeExtension s b` (`up_iff_legal`), for the
  exact declared one-edge grammar and nothing else; every Up block
  executes to a strict legal extension on live store-bounded states
  (`up_exec_eq`, `up_executes`), and tree states are store-bounded
  (`treeState_wf`).  Presentation invariance is a genuine
  positional renaming ACTION: blocks and the family transport along
  it and replay commutes with it on the supply fragment
  (`upBlock_transport`, `upFamily_transport`, `act_up_comm`);
  the old length-equality survives only as grammar uniformity over
  an IDENTICAL carrier (`upFamily_grammar_uniform`) — equal-size
  states with literally equal families need not be related by any
  renaming (`equal_size_not_renaming_related`).  Every lawful
  policy produces a tree — unique ascending parent, root
  reachability, V−E=1 (`treeAt_spec`, `all_reach`,
  `attach_residue`); global shape is NOT forced
  (`path4_star4_not_isomorphic`), and two legal equal-cost
  extensions genuinely diverge
  (`equal_cost_non_isomorphic_extensions`) — the complete family
  never selects.  Orbit-valued choices where symmetry remains (star
  leaves one orbit; the ORIENTED path rigid — the orientation
  residue at work).  The unique map out of the two-element kernel
  is injective into every irreflexive target and provably not so
  without irreflexivity.  Imported inputs stated: fresh token
  supply, protection, observer transport, budget, activation.
- **Class**: theorem + countermodel + finite computation.
- **Lean**: `Attachment.up_iff_legal`, `Attachment.up_exec_eq`,
  `Attachment.up_executes`, `Attachment.attachChecked_refuses`,
  `Attachment.unlawful_refused`, `Attachment.clamp_rewrote_input`,
  `Attachment.freshTok_fresh`,
  `Attachment.length_not_fresh_countermodel`,
  `Attachment.freshTok_treeState`,
  `Attachment.attachBlock_is_upBlock`, `Attachment.treeState_wf`,
  `Attachment.upBlock_transport`, `Attachment.upFamily_transport`,
  `Attachment.act_up_comm`, `Attachment.upFamily_grammar_uniform`,
  `Attachment.equal_size_not_renaming_related`,
  `Attachment.equal_cost_non_isomorphic_extensions`,
  `Attachment.treeAt_spec`, `Attachment.attach_residue`,
  `Attachment.parent_lt`, `Attachment.parent_unique`,
  `Attachment.parent_exists`, `Attachment.all_reach`,
  `Attachment.path4_star4_not_isomorphic`,
  `Attachment.star_orbit_swap`, `Attachment.path_oriented_rigid`,
  `Attachment.path_center_separate`,
  `Attachment.halted_up_inert`,
  `PrimitiveCats.d2_map_injective`,
  `PrimitiveCats.d2_map_not_injective_without_irrefl`.
- **Python**: `attachment_ladder.json` (lawful policies to 15
  rounds; registry iff; renaming commutation over the full
  permutation group on the sample carriers; both countermodels;
  orbit computation via store automorphisms).

### CL-PD2-LADDER-GENERAL (repaired and reconciled with
CL-PD2-LADDER)
- **Statement**: the dimension-indexed declared cell calculus
  carries ONE well-formed shell guard uniform in the dimension —
  exact arity, STRICT ASCENT (the legacy guard admitted the
  repeated-vertex pseudo-cell `[0, 0]`;
  `pseudo_cell_countermodel`), complete unfilled boundary — and
  the UNIFORM GUARDED FILLER THEOREM (`uniform_guarded_filler`,
  renamed and NARROWED from the former "general ladder theorem"):
  at every dimension a complete well-formed unfilled boundary
  admits its filler and the admission strictly extends the
  complex.  This is a theorem about the declared guarded step, NOT
  a homology claim.  Reconciliation with CL-PD2-LADDER: the
  hard-coded `ladder_dim2/dim3` are the dimension-2/3 instances of
  the two-rule shape inside the PASSAGE-ADJACENT calculus of
  `HigherStructure`; `uniform_guarded_filler` is its
  dimension-uniform generalization in the standalone generalized
  calculus, and the review-pass conjecture
  GENERAL_DIMENSIONAL_LADDER is settled ONLY in this narrowed
  filler sense.  Well-formedness is a replayed invariant
  (`wf_nreplay`, `d4_wf`); guards are load-bearing and shells
  never self-fill; the dimension-4 demonstration replays
  completely (5/10/10/5/1); the older dimension-2–5 computations are
  retained as spot-checks.  The GENERAL coefficientwise composite
  vanishing is now proved in `BoundaryCancellation.d2_zero_unrestricted`
  (see CL-PD2-BOUNDARY-CANCELLATION); it is declaration-relative to the
  alternating signs and integer chain calculus and is not a consequence
  of the filler guard.
- **Class**: theorem (uniform guarded filler; wf invariant) +
  countermodel (pseudo-cell; guard load-bearing) + finite
  computation (dims 2–5).  The separate general boundary theorem is
  classified under CL-PD2-BOUNDARY-CANCELLATION.
- **Lean**: `LadderGeneral.uniform_guarded_filler`,
  `LadderGeneral.shell_refuses_general`,
  `LadderGeneral.shell_no_self_fill`,
  `LadderGeneral.pseudo_cell_countermodel`,
  `LadderGeneral.wf_nreplay`, `LadderGeneral.d4_demo`,
  `LadderGeneral.d4_wf`, `LadderGeneral.d4_guard_load_bearing`,
  `LadderGeneral.d2_zero_dims_2_3_4`.
- **Python**: `attachment_ladder.json` (dims 2–5; repaired guard;
  pseudo-cell countermodel; wf invariant).

### CL-PD2-COMPRESSION
- **Statement** (target-relative presentation compression; all
  notions relative to a DECLARED finite domain `D` and DECLARED
  represented question family `Q`): (A) a presentation map factors
  through the Q-signature exactly when it is constant on
  Q-signature fibers over `D` (`factors_iff_fiberConstant`); the
  factoring map is unique ON THE IMAGE of `D` and provably not
  unique off it (`factor_unique_on_image`,
  `factor_not_unique_off_image`).  (B) the signature quotient `pQ`
  is exact, Q-adequate, and COARSEST among Q-adequate
  presentations, with the universal property scoped to the image
  (`pQ_exact`, `pQ_adequate`, `pQ_coarsest`,
  `pQ_unique_on_image`) — no claim off-image or for undeclared
  families.  (C) every descent failure — two points merged by the
  compression yet separated by some declared question — is
  witnessed by an explicit separator (`descent_witness`).  (D)
  enlarging the family refines the agreement relation, and a class
  SPLITS exactly when the enlargement contains a NEW separator for
  previously agreeing points (`enlarge_refines`,
  `splits_iff_new_separator`).  (E) there is NO absolute adequacy
  without a declared family: adequacy for every family is exactly
  injectivity on `D` — no compression at all
  (`absolute_adequacy_iff_injective`, forward by indicator
  questions).  (F) repetition, digests/hashes, and replay records
  are functions of the old signature and separate nothing new
  (`dup_no_refine`, `postcompose_no_refine`,
  `refine_requires_separator`) — what makes replay EVIDENTIAL is
  a new separating question, never re-presentation.  Iteration is
  bounded by the declared domain: on a NONEMPTY domain — the
  positivity and chain bounds carry the hypothesis that `D` is
  nonempty, and on the empty domain the class count is zero (scope
  made explicit 2026-08-18) — class counts are positive,
  bounded by `|D|`, strictly increase on splits, and any strict
  refinement chain has fewer than `|D|` steps (`refine_bounded`,
  `classCount_pos`, `strict_split_increases`, `chain_bounded`,
  `strict_steps_lt`).  Repaired-attachment connection tested and
  bounded by countermodel: refinement is NOT unique and ties are
  retained (`refinement_not_unique`, `refinement_tie`) — no
  unique-minimum refinement, no endogenous selection, no unlimited
  iteration.
- **Class**: theorem + countermodel + finite computation
  (exhaustive within declared bounds n ≤ 3, m ≤ 3, |Q| ≤ 2).
- **Lean**: `Compression.factors_iff_fiberConstant`,
  `Compression.factor_unique_on_image`,
  `Compression.factor_not_unique_off_image`,
  `Compression.pQ_exact`, `Compression.pQ_adequate`,
  `Compression.pQ_coarsest`, `Compression.pQ_unique_on_image`,
  `Compression.descent_witness`, `Compression.enlarge_refines`,
  `Compression.splits_iff_new_separator`,
  `Compression.absolute_adequacy_iff_injective`,
  `Compression.dup_no_refine`, `Compression.postcompose_no_refine`,
  `Compression.refine_requires_separator`,
  `Compression.refinement_not_unique`,
  `Compression.refinement_tie`, `Compression.refine_bounded`,
  `Compression.classCount_pos`,
  `Compression.strict_split_increases`,
  `Compression.chain_bounded`, `Compression.strict_steps_lt`,
  `Compression.sigEq_iff_sigList`.
- **Python**: `compression.json` (757 families per size pair up to
  (3,3); 37736 witnessed descent instances; 10006 split instances;
  digest quantification over all signature functions).

### CL-PD2-RECEIPT-BYTES
- **Statement**: the completion receipt generator is deterministic
  under the declared CRLF→LF canonicalization and fixed generated
  inputs.  For the current tracked inputs, those canonical hashes
  equal the checked Git blob hashes.  The original supplied CRLF
  rendering of the seed prompt is recorded alongside as
  provenance.  The blob/checkout distinction is tested against
  `git show HEAD:...`; content mutation detection is spot-tested (a
  flipped content byte and an appended byte each move the canonical
  hash; a pure line-ending re-rendering does not — it is the same
  canonical content).  An earlier version said "any content byte
  change moves the canonical hash" as tested, and a later one called
  the universal "a property of the hash construction"; neither is
  established by these tests and neither is claimed — a fixed-size
  digest is not an injective encoding of arbitrary content, and what
  stands is the two observed mutations and the canonicalization
  convention (narrowed 2026-08-18 and again 2026-09-08).
- **Class**: finite computation + tests.
- **Python**: `run_primitive_receipt.py` (`canonical_sha256`),
  `tests/test_primitive_receipt.py` (blob/checkout distinction,
  mutation detection, dual seed hashes).

### CL-PD2-TRACE-STABILITY (audit repair; supersedes the withdrawn CL-PD2-STABLE-CONTENT)
- **WITHDRAWN CLAIM**: the review draft asserted "stable content is
  exactly protected separation".  The word *exactly* was an
  OVERCLAIM: only sufficiency was proved, and the converse is FALSE.
  The claim is withdrawn and replaced by the following; every body,
  receipt, and docstring site was weakened to match.
- **Statement** (native scope: the declared event grammar of the
  passage calculus).  Trace stability is now DEFINED, not assumed:
  `TraceStableSep s i j` says the pair stays separated by the
  declared observation after EVERY replay; `RestrictedStableSep` is
  the same over a syntactically restricted fragment omitting
  occurrence admission, budget setting, and license setting.  No
  ownership claim is made; generated blocks may contain `setBudget`.
  (i) **SUFFICIENCY (theorem)**: protected AND separated implies
  trace stable (`protSep_trace_stable`, via `protSep_persists` /
  `protSep_replays`) - supply events do not touch observation, new
  columns only add separators, and same-level refinement is guarded
  by precisely the monotone preservation of protected separations.
  (ii) **THE CONVERSE IS FALSE - one full-trace countermodel, plus one
  restricted-fragment example.**  On an
  ABSORBED (halted) state every replay is inert, so an UNPROTECTED
  separation is trace stable (`halted_stable_not_protected`).  On a
  LIVE but UNFUNDED state no event in the restricted fragment can
  change the observation, so an UNPROTECTED separation is stable only
  for that fragment
  (`unfunded_restricted_stable_not_protected`).  The latter is not a
  second countermodel to full trace stability.  Neither pair is protected.
  (iii) **INSTABILITY GIVEN A WITNESS (theorem)**: a concrete
  breaking witness - a funded, accepted refinement routed through the
  separating column - destroys an unprotected separation in one step
  (`separation_breakable`), instantiated concretely by
  `unprotected_separation_unstable`.  Whether every destruction
  requires such a witness is unproved and belongs to the OPEN
  characterization in (iv); protection is load-bearing against
  witnesses.  (An earlier version read "destroyed only when a
  concrete breaking witness exists" - the necessity direction, which
  no cited theorem proves; narrowed to the proved sufficiency
  2026-08-18.)
  (iv) **OPEN**: sufficiency and witness-borne instability sandwich
  the truth WITHOUT meeting.  Whether trace stability implies
  protected separation on the live, funded class is OPEN and is
  recorded as a Prop, never as a theorem
  (`openExactStabilityCharacterization`).
  (v) **Quiescence** (unchanged, and NOT a stability claim): on a
  declared state, no pair is actively obstructed exactly when every
  retained protected pair is protected-separated
  (`quiescent_iff_protected_separated`,
  `quiescence_is_protected_separation`).  The corollary that does
  follow is `quiescent_retained_protected_trace_stable`.
- **Class**: theorem (sufficiency; instability given a witness;
  quiescence iff) + countermodel (full converse, once) + restricted
  example + OPEN (exact characterization) + finite computation.
- **Lean**: `StableContent.protSep_trace_stable`,
  `StableContent.protSep_persists`,
  `StableContent.protSep_replays`,
  `StableContent.trace_stable_restricted_stable`,
  `StableContent.sep_preserved`, `StableContent.prot_mono`,
  `StableContent.sepP_refine`, `StableContent.replay_halted`,
  `StableContent.halted_stable_not_protected`,
  `StableContent.restricted_step_inert_unfunded`,
  `StableContent.restricted_replay_inert_unfunded`,
  `StableContent.unfunded_restricted_stable_not_protected`,
  `StableContent.separation_breakable`,
  `StableContent.unprotected_separation_unstable`,
  `StableContent.quiescent_iff_protected_separated`,
  `StableContent.quiescence_is_protected_separation`,
  `StableContent.quiescent_retained_protected_trace_stable`;
  OPEN statement `StableContent.openExactStabilityCharacterization`.
- **Python**: `primitive_passage.json` (`stable_content` section:
  single-step and bounded-trace sufficiency, the full-converse
  countermodel, the restricted-fragment example, the witness-borne
  instability countermodel, the
  quiescence coincidence, and the recorded open gap; declared
  bounds: carrier 3, trace depth 2, breadth 24).

### CL-PD2-RENAMING-STRUCTURE (Goal 1)
- **Statement**: the renaming structure around `Up` is completed and
  its laws proved, and only afterwards is the vocabulary
  "equivariant" used.  (i) `Renaming n` carries IDENTITY (`idRen`),
  INVERSE (`invRen`) and COMPOSITION (`compRen`) satisfying the group
  laws `RenamingStructure.comp_id`, `RenamingStructure.id_comp`,
  `RenamingStructure.comp_assoc`, `inv_comp`, `comp_inv`,
  `inv_inv`, proved through a componentwise extensionality principle
  (`Renaming.ext`: the two remaining fields are propositions, so a
  renaming is its function pair).  (ii) `act` is an ACTION:
  `act_id` holds UNCONDITIONALLY, and `act_comp` holds on the exact
  scope `n <= s.occ.length` — the scope in which positional
  re-indexing of the carrier is meaningful, and deliberately weaker
  than equality so that the EXTENDED state (length `n+1`) is covered
  too; `act_inv` follows.  (iii) block and family transport respect
  identity and composition (`upBlock_id`, `upBlock_comp`,
  `upFamily_id`, `upFamily_comp`, `upFamily_transport_id`,
  `upFamily_transport_comp`).  (iv) COHERENCE: replay of an `Up`
  block commutes with a COMPOSED renaming and the composite route
  equals the two-step route (`act_up_comm_comp`,
  `act_up_comm_twostep`) — the naturality square closes under
  composition.  (v) NO SELECTED REPRESENTATIVE: the family is closed
  under the action, carries the whole orbit, and has exactly one
  block per represented parent (`upFamily_orbit_closed`,
  `star_orbit_both_present`, `upFamily_length`).
  (vi) COUNTERMODELS — weaker data does not supply this structure: an
  arbitrary NON-BIJECTIVE map has no left inverse
  (`collapse_not_a_renaming`) and its pushforward turns an
  irreflexive store into self-pairs that the well-formedness guard
  refuses (`collapse_pushforward_ill_formed`).  This excludes that map
  from `Renaming` and from the inverse/group-action and equivariance
  theorems here; it does not deny that non-bijective maps can compose
  in a different monoid action.  Equal carrier size supplies no
  relatedness (`equal_size_supplies_no_law`), and equal cost supplies
  no identification (`equal_cost_supplies_no_law`).
- **Scope of the earned vocabulary** (`equivariance_summary`): the
  supply fragment of the declared one-edge grammar, on live
  store-bounded states.  NOT the observation calculus, NOT
  multi-edge or relational extensions, NOT any map that is not a
  renaming.
- **Class**: theorem + countermodel + finite computation.
- **Lean**: `RenamingStructure.Renaming.ext`,
  `RenamingStructure.comp_id`, `RenamingStructure.id_comp`,
  `RenamingStructure.comp_assoc`, `.inv_comp`, `.comp_inv`, `.inv_inv`,
  `.map_getD_range`, `.act_id`, `.act_comp`, `.act_inv`,
  `.upBlock_id`, `.upBlock_comp`, `.upFamily_id`, `.upFamily_comp`,
  `.upFamily_transport_id`, `.upFamily_transport_comp`, `.wf_act`,
  `.act_up_comm_comp`, `.act_up_comm_twostep`,
  `.upFamily_orbit_closed`, `.star_orbit_both_present`,
  `.upFamily_length`, `.collapse_not_a_renaming`,
  `.collapse_pushforward_ill_formed`, `.equal_size_supplies_no_law`,
  `.equal_cost_supplies_no_law`, `.equivariance_summary`.
- **Python**: `renaming_structure.json` — exhaustive over the whole
  symmetric group at carrier 3 (216 associativity triples, all 6
  permutations against both sample states for every action,
  transport, and coherence law) plus all three countermodels.

### CL-PD2-GRAPH-GENESIS (Goal 5)
- **Statement, part 1 (the negative theorems)**: in the declared
  calculus, graph growth is SUPPLIED, not generated by the represented
  `nextFamilyP` response semantics.
  `refineCol` and `addCol` provably leave seven state fields
  unchanged - occurrences, asserted, retained, protected, refusals,
  license, halted - so only observation and budget are even
  candidates for change (`refineCol_only_obs`, `addCol_only_obs`).
  The internal response family ranges over columns on EXISTING
  occurrences only (`extensionProposals_range_over_existing`,
  `repairFamily_range_over_existing`), and has exactly two block
  shapes, with no third (`nextFamilyP_block_shape`,
  `nextFamilyP_range_over_existing`).  Along EVERY internal trace the
  four graph stores are fixed
  (`internal_family_cannot_grow_carrier`).  The corollary states it
  in one line: growth comes from the external driver or the `Up`
  grammar, never from `nextFamilyP`
  (`graph_growth_is_supplied`).
- **Statement, part 2 (an explicit sufficient proposal schema)**:
  `ProposalRecord s` carries exactly - one NAMED member of the COMPLETE
  `Up` family with its membership proof (not a canonical or unique
  representative); an old-position embedding with its retraction and
  the retraction law; fresh-token evidence; preservation of every old
  asserted, retained, protected and separated item; the new pair with
  its provenance (parent position, fresh position); and a declared
  cost.  It carries NO license, execution, or activation field, and
  `proposal_confers_no_execution` witnesses that a proposal on a
  terminal state moves nothing.  The family transports under renaming
  within exactly `act_up_comm`'s scope (`proposal_transports`) and
  retains equal-cost non-isomorphic branches
  (`proposal_family_retains_ties`).
- **Statement, part 3 (the verdict)**: `nextFamilyP` does NOT request
  the carrier-changing lift at an active obstruction.  On the blind pair - all four
  obstruction conditions satisfied - the complete internal family is
  nonempty, every member discharges the obstruction, and every member
  leaves the graph stores fixed; and no state anywhere admits an
  internal family member that grows the carrier
  (`family_never_grows_carrier`).  Generalized:
  `obstruction_resolved_in_carrier` answers every obstruction meeting
  the kernel's own hypotheses inside the existing carrier.  Therefore
  the growth demand is a SEPARATELY DECLARED PREMISE, not entailed by
  the represented `nextFamilyP` semantics
  (`growth_demand_not_obstruction_consequence`).  No minimality or
  universal property is proved for `ProposalRecord`.
- **Scope limits, stated**: the field-invariance theorems prove
  invariance of the other seven fields only and do not claim that
  observation or budget do change (guards may refuse).
  `repairFamily_range_over_existing` bounds the NEW point only; points
  already inside a declared column are not bounded by any kernel
  invariant on hand-built states.  `proposal_transports` covers
  exactly the supply fragment on store-bounded live states.  Part 3
  covers the family the kernel computes (`nextFamilyP`); it does NOT
  exclude that some other declared family could grow the carrier -
  that remains OPEN.  On a terminal state the obstruction persists
  because nothing moves at all, so the resolution theorem is an
  implication and not a blanket claim.  "The record carries no
  authority" is structural (there is no such field), not a theorem.
- **Class**: theorem + countermodel + finite computation + OPEN
  (other response families).
- **Lean**: `GraphGenesis.refineCol_only_obs`, `.addCol_only_obs`,
  `.extensionProposals_range_over_existing`,
  `.repairFamily_range_over_existing`, `.nextFamilyP_block_shape`,
  `.nextFamilyP_range_over_existing`, `.IsInternal_exact`,
  `.internal_family_cannot_grow_carrier`,
  `.response_replay_fixes_graph`, `.nextFamilyP_block_fixes_graph`,
  `.graph_growth_is_supplied`, `.proposal_confers_no_execution`,
  `.upProposal_executes`, `.proposal_transports`,
  `.proposal_family_retains_ties`,
  `.obstruction_resolved_in_carrier`, `.family_never_grows_carrier`,
  `.growth_demand_not_obstruction_consequence`,
  `.blindPair_resolution_keeps_carrier`.
- **Python**: `graph_genesis.json` - 8 sample states, 600 battery
  checks (probing one past the carrier), 11104 internal traces of
  length at most 2, the full symmetric group at carrier 3 for
  transport, tie carrier 4; bounds recorded in the artifact.

### CL-PD2-BOUNDARY-CANCELLATION (Goal 4; supersedes the dimension-2-to-5 computation and closes the standing conjecture)
- **Statement**: the coefficientwise composite boundary vanishes.
  For EVERY finite list of vertices and EVERY face,
  `coeffN tau (pushN (bdN sigma)) = 0` (`d2_zero_unrestricted`); the
  declared form with strict ascent and list length at least two (cell
  dimension at least one) is `d2_zero_general`, whose hypotheses are
  recorded and discharged from the stronger theorem.  The proof is a
  PAIRING, not a
  computation: for each unordered pair of deleted positions the two
  deletion orders are matched by `eraseIdx_swap`
  (`(l.eraseIdx b).eraseIdx a = (l.eraseIdx a).eraseIdx (b-1)` for
  `a < b`), their signs cancel by `sgn_cancel`
  (`sgn b * sgn a + sgn a * sgn (b-1) = 0`), the double sum is
  rearranged by `coeff_rect` and `tri_transpose`, and `rect_zero`
  closes it.
- **A premise of the task was false, and is recorded as false.**
  Strict ascent is NOT load-bearing for the vanishing: the
  deletion-order involution cancels each pair whether or not a third
  term lands in the same slot, so the theorem holds for
  repeated-vertex lists too (`illformed_countermodel` confirms the
  pseudo-cell composite is still zero at every face).  What ascent IS
  load-bearing for is DISTINCTNESS of the codimension-two faces:
  `eraseIdx_inj_of_asc` and `codim2_distinct` are both false for
  `[0, 0, 1]`.  The ill-formed exhibit is therefore a distinctness
  countermodel plus a boundary-degeneracy exhibit, not a cancellation
  countermodel.
- **Connected to replay**: every cell of every complex replayed from
  the empty complex satisfies the vanishing (`d2_zero_replayed`, via
  `LadderGeneral.wf_nreplay`), including the dimension-4
  demonstration (`d2_zero_d4`).
- **Renaming independence**: for strictly monotone renamings ascent
  is preserved and the vanishing transports (`eraseIdx_map`,
  `ascB_map`, `d2_zero_renamed`, `d2_zero_shift`).  For injective but
  NON-monotone renamings ascent can be destroyed; the vanishing still
  holds, but only via the unrestricted theorem - stated exactly.
- **The signs and coefficients remain DECLARED**: in the declared
  integer calculus, replacing all signs by `1` makes the composite
  nonzero (`signless_countermodel`, `signless_countermodel_dim3`).
  Nothing here claims the filler rule forced them, or that the same
  countermodel works in every coefficient system; the orientation
  convention is declared content.
- **Not formalized**: the quantitative statement that every
  codimension-two face of an ascending cell collects exactly two of
  the ordered pairs.  It follows from `codim2_distinct` by counting;
  the count is checked exhaustively in the Python mirror and decided
  on the exhibits, but is not a Lean theorem.  Recorded, not claimed.
- **Class**: theorem (general) + countermodel (signless; ill-formed
  distinctness) + finite computation (mirror).
- **Lean**: `BoundaryCancellation.d2_zero_unrestricted`,
  `.d2_zero_general`, `.d2_zero_facets`, `.d2_zero_replayed`,
  `.d2_zero_d4`, `.eraseIdx_swap`, `.eraseIdx_eraseIdx_succ`,
  `.sgn_succ`, `.sgn_cancel`, `.dterm_cancel`, `.coeff_rect`,
  `.rect_zero`, `.tri_transpose`, `.eraseIdx_inj_of_asc`,
  `.codim2_distinct`, `.eraseIdx_map`, `.ascB_map`,
  `.d2_zero_renamed`, `.d2_zero_shift`, `.signless_countermodel`,
  `.signless_countermodel_dim3`, `.illformed_countermodel`.
- **Python**: `boundary_cancellation.json` - 218 cells (all ascending
  cells over the first 8 numerals, dimensions 2 to 6), 3124
  coefficient checks, sign alternation over all pairs below 64, and
  the involution report (bijection, involution, fixed-point-free,
  sign-reversing) per dimension; bounds recorded in the artifact.

### CL-PD2-WEIGHT-PROFILE (corrected contact ceiling)

- **Statement**: this is finite natural/integer weight-profile algebra, not a
  lift to an inner-product space. Carrier-facing lists are duplicate-free; raw list totals count
  repetitions with multiplicity. On the positive-total domain `SameProfile`
  is an equivalence, positive natural scaling preserves that domain, and
  profile equality is exactly common positive cross-multiplication. Zero
  scaling satisfies the raw equation but exits the domain. Support and order
  are preserved and the total weight is forgotten.
- **Presentation result**: a valid duplicate-free decorated presentation
  reproduces the declared weight profile. Unsigned square presentations of the
  same weights are carrierwise equal. Separately, two valid integer-square
  presentations `(1, 1)` and `(1, -1)` of weights `(1, 1)` are distinguished
  by the declared two-input read-out `(x+y)^2`. This is a scoped sign-shadow
  witness, not a general capacity or dynamics claim.
- **Descent result**: for the declared two-coordinate integer linear read-out
  followed by squaring, descent through coordinate-square fibers holds exactly
  when one coefficient vanishes.
- **Climb audit**: the former decorated-carrier existential is trivially
  inhabited; append additivity is a theorem of `total`; the displayed read-out
  uniqueness schema is false by the zero read-out. The invalid `eB` witness did
  not present the weights and has been removed. No priced representation climb
  remains.
- **Class**: theorem + scoped counterexample + finite computation + refuted
  overclaim.
- **Lean**: `WeightProfile.CarrierList`, `.duplicate_list_not_carrier`,
  `.total_append`, `.profile_equivalence_positive`,
  `.profile_scale_positive`, `.zero_scale_boundary`, `.profile_iff_ray`,
  `.profile_support`, `.profile_order`, `.profile_forgets_total`,
  `.presentation_profile_redundant`, `.presentations_agree_on_profile`,
  `.sq_injective`, `.unsigned_decoration_determined`,
  `.signed_square_presentations_split`, `.presentation_scope`, `.sq_add_sub`,
  `.descent_iff_subsingleton_support`, `.decoratedCarrierShape_exists`,
  `.claimedReadOutUniqueness_false`, and `.finite_scope_summary`.
- **Python**: `weight_profile.json` checks carrier 2, weights/decorations to 3,
  coefficients to 3, and inputs to 2. It mirrors the zero-scale boundary,
  duplicate policy, signed fixture, descent classification, and failed-climb
  dispositions. Bounds remain explicit.

### CL-PD2-TRANSITION-CODEBOOK (Goal 2, repaired)
- **Statement**: the PR declares a finite one-step signature and proves
  that every accepted transition in `WFClass` has exactly one of its
  thirteen codes (`sig_eq_classSig`, `classSig_inj`,
  `exists_unique_class`).  Erasing the guard leaves twelve declared
  code values (`declared_codebook_size`,
  `guard_erased_codebook_size`).  These are image sizes of this exact
  event grammar and projection; they are not a native alphabet or a
  quotient of histories.
- **Load-bearing negative theorem**: code equality is not a right
  congruence.  At genesis, `admitOcc 0` and `admitOcc 2` have the same
  code, yet a common suffix `admitOcc 0` separates their results.
  Likewise, two budget writes have one code but a following extension
  distinguishes them (`classSig_not_right_congruent_occurrence`,
  `classSig_not_right_congruent_budget`).  Codes must therefore never
  replace raw events or states in replay.
- **What the finite computation says**: over the declared 6,144-state,
  18-event battery there are 21 full accepted profiles, 13 projected
  signatures, and 12 guard-erased signatures.  All thirteen declared
  codes occur in that finite well-formed space.  This does not prove
  that every code is genesis-reachable or invariant under a different
  presentation.
- **Policy labels, not provenance**: the legacy `Origin` field is a
  constructor classification.  It is not evidence of issuer,
  capability, or causal origin: `nextFamilyP` itself emits
  `setBudget 1`, classified as `environment`.  The exact emission and
  non-emission theorems are retained, but no ownership conclusion is
  drawn from the label.
- **Scope limits**: no contextual quotient, renaming invariance,
  presentation-independent cardinality, or DDA correspondence is
  claimed.  Witness minimality is only exhaustive computation within
  the declared finite space, not a Lean theorem or a reachable-state
  theorem.
- **Class**: declared projection + coverage theorem + countermodels +
  bounded computation.
- **Lean**: `TransitionAlphabet.accepted_eq_guardHolds`,
  `.halted_accepts_nothing`, `.sig_eq_classSig`, `.classSig_inj`,
  `.exists_unique_class`, `.wf_of_replay`,
  `.declared_codebook_size`, `.guard_erased_codebook_size`,
  `.classSig_not_right_congruent_occurrence`,
  `.classSig_not_right_congruent_budget`,
  `.refine_addCol_effect_merge`, `.refine_addCol_domain_countermodel`,
  `.internal_family_emits_budget_write`,
  `.internal_family_env_only_unit_funding`.
- **Python**: `transition_alphabet.json` records all bounds, the three
  image sizes, and both common-suffix countermodels.

### CL-PD2-TRACE-ALGEBRA (Goal 3)
- **Statement**: a typed transition record binds pre-state, event,
  discharged guard, post-state, effect class, resource delta, and the
  complete computed profile;
  legal traces are aligned chains of well-formed records; and replay
  ERASES typed traces back to the existing semantics
  (`replay_erases`, `legal_trace_replays`).  From there the laws are
  DERIVED, not assumed.
  (i) Inertness is exact: a step is inert iff its guard fails
  (`inert_iff_guard_fails`).  (ii) The terminal absorbs
  (`terminal_absorbs`, `trace_absorbs`).  (iii) IDEMPOTENCE IS
  UNIVERSAL, which is stronger than expected: `step_idem` holds for
  EVERY event at EVERY state - the funded events are idempotent
  because a refined column leaves the menu and a created column is
  already present.  (iv) Three sufficient FRAME families are proved,
  not a necessary or exhaustive classification: `frame_licS`,
  `frame_budS` and `frame_occS` over declared insensitivity predicates give
  `comm_setLicense`, `comm_setBudget`, `comm_setBudget_setLicense`,
  `comm_admitOcc`.  (v) FIVE non-commutation countermodels
  (`noncomm_license_extension`, `noncomm_budget_extension`,
  `noncomm_terminal`, `noncomm_supply_retention`,
  `noncomm_same_store`), with `same_store_observationally_equal`
  keeping presentation identity apart from observational agreement.
  (vi) Traces restricted by the declared policy classifier preserve
  occurrence and license (`internal_trace_preserves_occ`,
  `internal_trace_preserves_license`); this is a syntactic fragment,
  not an issuer-provenance theorem.  (vii) Refusal records are
  append-only under every event and every trace and cannot be erased
  as inert syntax (`refusal_persists_step`, `refusal_persists_replay`,
  `refusal_not_erasable`).  (viii) Replay equivalence is SCOPED:
  `replay_eqv_scoped` holds on a declared start class while
  `replay_eqv_not_unscoped` refutes the unscoped form.
- **The rewrite system, and exactly where it is sound**: a two-rule
  state-independent system on event lists - adjacent idempotence and
  post-terminal absorption, closed under context.  Proved SOUND at
  every start state (`rw_sound`, `rwStar_sound`), TERMINATING by
  strict length decrease (`rw_length`), and CONFLUENT with unique
  normal forms (`rw_confluent`, `nf_unique`, `nf_noRedex`,
  `noRedex_nf_eq`).
- **Not claimed: completeness of this rewrite system.**
  `rewrite_not_complete` exhibits two lists that replay identically from
  every state but receive different `nf` values. This refutes completeness
  of this two-rule normalizer only; it does not prove impossibility of a richer
  canonicalizer for universal or start-scoped replay equivalence. Commutation
  reordering was not added because same-store writes need not commute, and
  inert deletion is state-dependent.
- **Scope limits, stated**: there is no general "disjoint support
  implies commutes" theorem, and it is false, because guards read
  fields their step never writes; only the three frame families are
  theorems, and the remaining entries of the 153-pair commutation
  matrix (91 commuting, 62 not) are battery computations.  Tightness
  of the insensitivity predicates is checked, not characterized -
  and three exclusions involving the terminal hold one-sidedly, which
  is recorded as an explanation rather than a theorem.  Observational
  equivalence is never converted into equality and no quotient is
  claimed to be a congruence.
- **Class**: theorem + countermodel + finite computation + explicit
  incompleteness.
- **Lean**: `TraceAlgebra.replay_erases`, `.legal_trace_replays`,
  `.inert_iff_guard_fails`, `.terminal_absorbs`, `.trace_absorbs`,
  `.step_idem`, `.frame_licS`, `.frame_budS`, `.frame_occS`,
  `.comm_setLicense`, `.comm_setBudget`,
  `.comm_setBudget_setLicense`, `.comm_admitOcc`,
  `.noncomm_license_extension`, `.noncomm_budget_extension`,
  `.noncomm_terminal`, `.noncomm_supply_retention`,
  `.noncomm_same_store`, `.same_store_observationally_equal`,
  `.internal_trace_preserves_occ`,
  `.internal_trace_preserves_license`,
  `.internal_blocks_cannot_supply_or_license`,
  `.refusal_persists_step`, `.refusal_persists_replay`,
  `.refusal_not_erasable`, `.replay_eqv_scoped`,
  `.replay_eqv_not_unscoped`, `.rw_sound`, `.rwStar_sound`,
  `.rw_length`, `.rw_confluent`, `.nf_unique`, `.nf_sound`,
  `.rewrite_not_complete`.
- **Python**: `trace_algebra.json` - declared bounds recorded there
  (rewrite alphabet of 4 events, lists to length 3, 12 named
  soundness states, the 153-pair commutation matrix).

### CL-PD2-CONTACT-RECONSTRUCTION (executed collision, 2026-08-13)
- **Statement**: the arriving development's quotient-descent layer had
  no counterpart in the sealed corpus and is reconstructed in native
  vocabulary as `ObsDescent`, over the sealed observer interface, with
  no new type-level structure.  Exactness: the observer quotient
  identifies exactly the zero-related pairs and its projection is
  surjective (`obsQuotient_exact`, `obsQuotient_mk_eq_iff`,
  `obsQuotient_mk_surjective`).  Descent: a view descends iff it is
  class-constant, any two descents agree, and one zero-related pair
  with distinct values blocks descent outright (`descend_exists_iff`,
  `descend_unique`, `descend_blocked_of_witness`); the same three
  statements hold for the difference map itself
  (`deltaDescend_exists_iff`, `deltaDescend_unique`,
  `deltaDescend_blocked_of_witness`).  Pairing splits componentwise
  (`classConstant_pair_iff`, `pair_descend_exists_iff`), and the
  flagship shape is exact: a class-constant view descends while its
  pairing with a blocked component does not
  (`view_descends_pair_blocked`).  The whole mod-setoid family
  collapses to the equality layer at `Quotient.mk S ∘ f`
  (`classConstant_comp_mk_iff`, with `descendMod_exists_iff`,
  `deltaDescendMod_exists_iff`, `descendMod_exists_of_coarsen`,
  `coarsenMap`, `pairSetoid`, `pairSetoid_mk_eq_iff`).  The arriving
  integer tail never instantiates its own core structure; it is
  subsumed by one native instance plus five one-line lemmas, and
  `value_orientation_survives` records the residue exactly: the value
  channel carries orientation, the zero relation cannot.
- **Class**: theorem + definition + countermodel.  Evidence classes:
  DERIVED_THEOREM (the descent, exactness, pairing and mod-layer
  statements), DEFINITION (`ClassConstant`, `descend`,
  `DeltaConstant`, `deltaDescend`, `coarsenMap`, `pairSetoid`,
  `intDiffObs`, `collapseAllObs`), COUNTERMODEL ×4 (the all-zero
  observer on `Bool`).
- **Deps**: CL-DI-EQUIVALENCE (the sealed observer interface and its
  quotient), CL-PD2-CONTACT (the interface the collision was executed
  against).  **Assumptions**: shared.
- **Lean**: `ObsDescent.obsQuotient_exact`, `.obsQuotient_mk_eq_iff`,
  `.obsQuotient_mk_surjective`, `.ClassConstant`, `.descend`,
  `.descend_mk`, `.descend_exists_iff`, `.descend_unique`,
  `.descend_blocked_of_witness`, `.DeltaConstant`, `.deltaDescend`,
  `.deltaDescend_mk`, `.deltaDescend_exists_iff`,
  `.deltaDescend_unique`, `.deltaDescend_blocked_of_witness`,
  `.classConstant_pair_iff`, `.pair_descend_exists_iff`,
  `.view_descends_pair_blocked`, `.coarsenMap`, `.coarsenMap_mk`,
  `.classConstant_comp_mk_iff`, `.descendMod_exists_iff`,
  `.deltaDescendMod_exists_iff`, `.pairSetoid`,
  `.pairSetoid_mk_eq_iff`, `.descendMod_exists_of_coarsen`,
  `.tag_view_zeroRel`, `.intDiffObs`, `.intDiffObs_zeroRel`,
  `.int_sub_ne_zero_iff`, `.int_sub_ne_zero_of_gt`,
  `.int_shift_cancel`, `.int_two_mul_eq_zero_iff`,
  `.int_add_sub_cancel`, `.value_orientation_survives`,
  `.collapseAllObs`, `.collapseAllObs_all_zero`,
  `.collapseAllObs_not_deltaConstant`,
  `.collapseAllObs_no_delta_descend`,
  `.collapseAllObs_id_not_classConstant`,
  `.collapseAllObs_no_view_descend`.
- **Axioms**: every report of the three collision modules lies within
  {propext, Quot.sound} (`artifacts/lean_axioms.txt` as run on
  2026-08-13, 1184 reports then; 1530 reports at `f12a498e` — the figure
  is bound to that dated run, not to the mutable artifact path;
  `ci/check_axiom_report.py`).
- **Python**: `primitive_contact.json:enumerations.E3_descent_dictionary`
  (64 combinations, 28 descending, 36 fixed-domain divergences) and
  `E4_flagship_census` (120 triples of a 512-triple universe);
  `tests/test_primitive_contact.py::test_enum_descent_dictionary_pinned`,
  `::test_enum_flagship_and_value_fork_pinned`.
- **Falsifier / boundary**: a descending view without class-constancy,
  or two descents of one view that differ.  Boundary: the
  reconstruction is NEW native content, not a sealed-corpus claim -
  every strictly-stronger reading must be stated against the enlarged
  corpus (recorded as a CONJECTURE in
  `primitive_contact.json:verdict.frontier_conjecture`).

### CL-PD2-CONTACT-BRIDGE (executed collision, 2026-08-13)
- **Statement**: difference in the arriving sense is exactly negation
  of the zero relation, and identifying that with the native asserted
  relation is a bridge whose every further native law is priced.
  `obsApart O := ¬ ZeroRel O` is irreflexive, symmetric
  and double-negation stable for FREE (from the three observer law
  fields), and, GIVEN a chosen apart pair as hypothesis, the induced
  setting satisfies the native candidate readings W, A, Bs and D with
  no further admission, E at the empty operation family only (a
  nonempty admitted merger family kills it — the sealed
  `merger_erases`), and Bc and Bl UNDER pointwise decidability of the
  zero relation (`obsSetting_bc`, `obsSetting_bl`: sufficiency, one
  direction; necessity for a fixed observer is NOT proved — what the
  pricing theorems below establish is the price of the schema
  quantified over all observers, which is a different statement).  In
  the other direction a native apartness becomes an observer
  (`apartObs`), and the two round trips return matching relations —
  but under TWO different admissions, one per direction, not
  interchangeable: apartness → observer carries
  `[∀ x y, Decidable (r x y)]` on the ASSERTED APARTNESS
  (`apartObs_roundtrip`, `isApart_repr`), observer → apartness
  carries `[∀ x y, Decidable (ZeroRel O x y)]` on the ZERO relation
  (`obsApart_isApart`, `indist_obsApart_iff`).  Neither yields the
  other: for `apartObs r h` the zero relation is `¬ r`, and
  `Decidable (¬ P)` does not return `Decidable P` constructively —
  precisely the gap `stability_schema_iff_dne` prices at DNE.  The
  dropped hypotheses are priced exactly,
  as schema equivalences with classical principles: the unconditional
  cotransitivity schema IS the weak law of excluded middle
  (`cotrans_schema_iff_wlem`), the unconditional stability schema IS
  double-negation elimination (`stability_schema_iff_dne`), and the
  unconditional locatedness schema implies the weak law
  (`located_schema_implies_wlem`; converse OPEN, and it would need a
  function-comprehension principle beyond the weak law).  Placement:
  what the arriving side ADMITS as three law fields, the native side
  PROVES equality-grade at the passage's declared observation stage
  (`declared_zero_as_view`, `observation_stage_realizes_observer`), so
  the arriving stratum is an admitted observer at the zero-relation
  stage, not a pre-observational witness; with no retention and no
  guarding nothing obstructs there (`kernelStage`,
  `kernel_stage_no_obstruction`).
- **Class**: theorem + bounded theorem (decidability-conditional) +
  unresolved.  Evidence classes: DERIVED_THEOREM (the free laws, the
  W/A/Bs/D/E cells, the three pricing theorems, the placement
  theorems), CONDITIONAL_THEOREM (`obsApart_cotrans`,
  `obsSetting_bc`, `obsSetting_bl`, `apartObs_roundtrip`,
  `isApart_repr`, `obsApart_isApart`, `indist_obsApart_iff` - all on
  a hypothesized `Decidable` instance, never on excluded middle),
  DEFINITION (`obsApart`, `obsSetting`, `apartObs`, `kernelStage`,
  `colView`, `wlemZero`), OPEN ×2 (`open_bridge_cotrans`,
  `open_bridge_located` — both registered as open obligations in
  `artifacts/primitive_completion_receipt.json:open_obligations`,
  each with its price; the converse of `located_schema_implies_wlem`
  is additionally registered under `frontier_conjectures` as
  LOCATEDNESS_SCHEMA_EQUALS_WLEM).
- **Deps**: CL-PD2-MATRIX (the nine candidate readings),
  CL-PD2-APARTNESS (`IsApart`, `Indist`), CL-PD2-PASSAGE (the
  declared observation stage), CL-DI-EQUIVALENCE.
  **Assumptions**: shared.
- **Lean**: `ContactBridge.obsApart`, `.obsApart_irrefl`,
  `.obsApart_symm`, `.obsApart_stable`, `.zeroRel_indist`,
  `.obsSetting`, `.obsSetting_w`, `.obsSetting_a`, `.obsSetting_bs`,
  `.obsApart_cotrans`, `.obsSetting_bc`, `.obsSetting_bl`,
  `.obsSetting_d`, `.obsSetting_e`, `.apartObs`, `.apartObs_zeroRel`,
  `.apartObs_roundtrip`, `.isApart_repr`, `.obsApart_isApart`,
  `.indist_obsApart_iff`, `.cotrans_schema_iff_wlem`,
  `.stability_schema_iff_dne`, `.located_schema_implies_wlem`,
  `.open_bridge_cotrans`, `.open_bridge_located`, `.colView`,
  `.declared_zero_as_view`, `.observation_stage_realizes_observer`,
  `.kernelStage`, `.kernel_stage_no_obstruction`,
  `.pair_blocked_is_collapse_collision`,
  `.collapse_collision_is_pair_blocked`,
  `.pair_blocked_iff_collapse_collision`.
- **Axioms**: within {propext, Quot.sound}; the classical principles
  occur only as quantified STATEMENTS inside the pricing theorems,
  never as proof steps.
- **Python**: `primitive_contact.json:collision_cells` rows
  `Obs_to_Bs`, `Obs_to_Bc`, `Obs_to_Bl`, `meet_roundtrip`,
  `stability_price`, `observer_placement (H1)`;
  `enumerations.E2_settings_kernels.cotrans_equals_complement_transitivity`
  (true on the finite decidable carriers 1-3, exactly as the pricing
  predicts); `tests/test_primitive_contact.py::test_enum_settings_kernels_pinned`.
- **Falsifier / boundary**: an observer whose complement fails
  cotransitivity while its zero relation is pointwise decidable; or a
  proof of either unconditional schema inside the ambient theory
  (which would prove the corresponding classical principle).
  Boundary: the two unconditional schemas admit NO internal
  countermodel - each is classically true - so they stay OPEN with
  their price, mirroring the sealed located-cell discipline.

### CL-PD2-CONTACT-COUNTERMODELS (executed collision, 2026-08-13)
- **Statement**: the native side is NOT representable in the arriving
  signature, and the failure is characterized rather than sampled.
  The crown, FOR PROP-VALUED OBSERVERS: a relation is the
  zero-complement of some `DiffObs X Prop` exactly when its
  complement is an equivalence and the relation is double-negation
  stable (`obsApart_repr_iff`, both directions constructive, both
  sides of the biconditional quantifying `∃ O : DiffObs X Prop`; at
  other value types only the forward direction is available, from
  `obsApart_stable` and the sealed `zeroRel_equivalence`).  All
  statements in this block quantify over `Type` (universe 0), while
  the arriving structure is universe-polymorphic.  The instances: the
  total one-point relation fails for Prop-valued observers (carrier
  1, `unit_total_not_repr`, which refutes `∃ O : DiffObs Unit Prop`
  only); the ORIENTED two-element
  witness fails over ANY value type (carrier 2,
  `d2_not_obs_complement`) - orientation cannot arrive through a
  difference-map presentation, and this is re-exported at the sealed
  interface as `PrimitiveContact.native_interface_not_representable`;
  the symmetric three-point relation fails (carrier 3,
  `triSym_not_obs_complement`), minimally, because on `Bool` witness
  plus irreflexivity plus symmetry already force representability
  with no decidability (`bool_bs_repr`); and an endpoint witness over
  the empty relation fails (carrier 2, `d_not_witnessed_repr`).
  Protection and retention are never derivable from an observer
  (`obsSetting_not_c`, `obsSetting_not_f`,
  `kernel_prot_independent`; the kernel-side echoes are
  `kernel_not_c`, `kernel_not_f`); the operation family is empty by
  construction in both translations — a definitional fact, not a
  separate non-derivability theorem (an earlier version listed
  "operations" under the same theorem citations; split made explicit
  2026-08-18).  The
  pair boundary is exact: same-data kernel inhabitation is equivalent
  to a non-zero pair (`kernel_from_obs_iff_pair`), the collapsed
  observer supplies no such pair (`kernel_no_witness_from_collapse`),
  and an inhabited observer does not determine a unique same-data
  kernel presentation (`kernel_not_unique_of_pair`).  The two
  arriving law fields are exactly the admissions separating observer
  from kernel, priced at carriers 2 and 3
  (`kernel_not_observer`, `kernel_not_bs`, `kernel_zero_not_trans`,
  `kernel_not_bc`).
- **Class**: countermodel (compiled, concrete, minimum carrier where
  claimed) + theorem (the characterization).  Evidence classes:
  COUNTERMODEL (the refutations named below, compiled finite models
  at the stated carriers), CONDITIONAL_THEOREM
  (`no_kernel_on_subsingleton`, on a `Subsingleton` carrier),
  DERIVED_THEOREM (`obsApart_repr_iff`, `bool_bs_repr`, and the
  never-derivable rows `kernel_not_c` / `kernel_not_f`),
  FINITE_COMPUTATION (the enumerated mirrors E1 and E2).
- **Deps**: CL-PD2-CONTACT-BRIDGE, CL-PD2-MATRIX,
  CL-PD2-APARTNESS.  **Assumptions**: shared.
- **Lean**: `ContactBridge.obsApart_repr_iff`,
  `.unit_total_not_repr`, `.d2_not_obs_complement`,
  `.triSym_not_obs_complement`, `.bool_bs_repr`,
  `.d_not_witnessed_repr`, `.obsSetting_not_c`, `.obsSetting_not_f`,
  `.kernel_prot_independent`;
  `ContactKernel.kernel_not_observer`, `.kernel_not_bs`,
  `.kernel_zero_not_trans`, `.kernel_not_bc`, `.kernel_not_c`,
  `.kernel_not_f`, `.no_kernel_on_subsingleton`,
  `.no_kernel_over_allzero`, `.kernel_not_e_merged`,
  `.kernel_from_obs_iff_pair`, `.kernel_not_unique_of_pair`,
  `.kernel_no_witness_from_collapse`;
  `PrimitiveContact.native_interface_not_representable`.
- **Axioms**: within {propext, Quot.sound}.
- **Python**: `primitive_contact.json:enumerations.E1_bool_observers`
  - over all 16 difference tables x 4 zero predicates on `Bool`, 24
  diagonal-zero holders, 20 full observer-law holders, 8 witnessed
  kernel quadruples, and ZERO observers whose complement is the
  oriented table (the finite mirror of `d2_not_obs_complement`);
  `E2_settings_kernels` - carriers 1-3, relation counts 2/16/512,
  candidate-A settings [0, 4, 192] matching exact-apartness kernels
  [0, 4, 192], representable relations [1, 2, 5] (the Bell numbers,
  as the crown predicts), witnessed representable [0, 1, 3];
  `contact/analysis/contact_countermodels.json:countermodel_table`
  (19 rows) and `candidate_reading_countermodel_sizes`;
  `tests/test_primitive_contact.py::test_enum_bool_observers_pinned`,
  `::test_enum_settings_kernels_pinned`.
- **Falsifier / boundary**: any observer, over any value type, whose
  zero-complement is the oriented two-element witness.  Boundary: the
  countermodels refute REPRESENTABILITY in the arriving signature;
  they say nothing about what a differently signed structure could
  do, and nothing about the arriving side's own theorems, all of
  which are reconstructed above.  Minimality boundary: of the nine
  candidate readings, CARRIER MINIMALITY is proved for Bs only (at
  3, by the positive `bool_bs_repr` at 2).  The other listed sizes
  are the least carrier at which the reading can be posed —
  METATHEORY, not a proved minimum — and
  `contact/analysis/lean_theorem_transport.md` records minimality as
  explicitly unclaimed for `d_not_witnessed_repr` and
  `no_kernel_over_allzero`; Bc, Bl and F carry no separate
  countermodel and fail through the A-conjunct models.

### CL-PD2-CONTACT-DICTIONARY (executed collision, 2026-08-13)
- **Statement**: global quotient descent and the sealed
  target-relative factorization are the SAME third notion, at exactly
  measurable distance.  Scope of the identification: kernel observers
  on the carrier `Nat` with `Nat`-valued views (`p q : Nat → Nat`,
  the typing forced by the sealed `Compression` layer's
  `D : List Nat`) — for such an observer, a view descends to the
  observer quotient iff it factors through the presentation at EVERY
  represented domain (`descend_iff_factorsOn_all`, via
  `classConstant_iff_fiberConstant_all`).  Kernel observers at other
  carriers or view types are outside the proved statements.  Per
  FIXED domain the
  native notion is strictly weaker: over the empty domain every
  question is vacuously fiber-constant while the identity view over a
  constant presentation is not class-constant, so the `∀ D`
  quantifier is not removable
  (`fiberConstant_fixed_D_not_classConstant`).  The pairing law has
  the same two forms (`classConstant_pair_iff` and the question-family
  `sigEq_append_iff`).  The uniqueness-scope difference is exactly
  codomain coverage by the projection: the arriving uniqueness is
  global because quotient projections are epi by induction
  (`obsQuotient_mk_surjective`), while native presentation uniqueness
  is image-scoped with an off-image countermodel
  (`Compression.factor_unique_on_image`, `.factor_not_unique_off_image`,
  `PrimitiveCats.phom2_unique_of_epi`).  The sealed raw-quotient
  barrier stays strictly more general than anything the arriving
  SETOID-BASED machinery can state (`Derivation.quot_barrier`) —
  METATHEORY, a citation-only comparison of two signatures with no
  transport theorem in either direction — and the arriving descent
  obstruction is collapse-collision at the projection, proved in BOTH
  directions (`pair_blocked_is_collapse_collision`,
  `collapse_collision_is_pair_blocked`, packaged as
  `pair_blocked_iff_collapse_collision`), and strictly coarser than
  the four-condition passage obstruction — METATHEORY, like the
  quot_barrier note: `obstP` conjoins retention, protection and
  declaration gates proved mutually independent within the passage
  (`PrimitivePassage.obst_conditions_independent`), but no transport
  theorem relates collapse-collision to `obstP` in either direction,
  and the comparison is recorded only as the `flagship_vs_obstP`
  collision row (flagged METATHEORY 2026-08-18; the clause previously
  read as a proved comparison).
- **Class**: theorem + countermodel + declared metatheory (the scope
  reconciliation).  Evidence classes: DERIVED_THEOREM (the
  dictionary, its class-constancy form, the pairing form, and
  surjectivity of the projection), COUNTERMODEL (fixed domain, the
  empty represented domain), METATHEORY (the
  uniqueness-scope and flagship-vs-branching notes, recorded as rows
  in `contact/analysis/contact_countermodels.json:metatheory_scope_notes`;
  and, added to this class 2026-08-18, the coarseness comparison
  against the passage obstruction, recorded only as the
  `flagship_vs_obstP` collision row).
- **Deps**: CL-PD2-COMPRESSION, CL-PD2-CONTACT-RECONSTRUCTION,
  CL-PD2-BRANCHING.  **Assumptions**: shared.
- **Lean**: `ObsDescent.descend_iff_factorsOn_all`,
  `.classConstant_iff_fiberConstant_all`,
  `.fiberConstant_fixed_D_not_classConstant`, `.sigEq_append_iff`,
  `.obsQuotient_mk_surjective`;
  `ContactBridge.pair_blocked_is_collapse_collision`,
  `.collapse_collision_is_pair_blocked`,
  `.pair_blocked_iff_collapse_collision`.
- **Axioms**: within {propext, Quot.sound}.
- **Python**: `primitive_contact.json:collision_cells` rows
  `descent_vs_factorsOn`, `fixed_D_strict`, `uniqueness_scope`,
  `quot_barrier`, `pairing_dict`, `flagship_vs_obstP`;
  `enumerations.E3_descent_dictionary` (36 fixed-domain divergences
  of 64 combinations).
- **Falsifier / boundary**: a view factoring at every represented
  domain that does not descend, or a descending view failing to
  factor at some domain.  Boundary: the two realizations are NOT
  identified in cost - the arriving side pays `Quot.sound` gluing,
  the native side pays representedness and first-match selection;
  the flagship obstruction is NOT identified with the sealed
  no-terminal-presentation results.

### CL-PD2-CONTACT-KERNEL (executed collision, 2026-08-13)
- **Statement**: a common replacement kernel exists, is CONSTRUCTED,
  and is realized from both sides.  `WitnessedDiff` is the meet:
  valued difference presentation, designated endpoints, a
  diagonal-zero law, and a refutation-grade non-zero witness at the
  designated pair - no symmetry, no transitivity, no retention, no
  protection, no operation family.  Its induced apartness is
  irreflexive and its endpoints are provably distinct
  (`kernelApart_irrefl`, `kernel_endpoints_ne`), and no kernel exists
  on a subsingleton carrier (`no_kernel_on_subsingleton`).  It is
  realized from any native candidate-A setting (`ofSetting`; exactly,
  under pointwise decidability OF THE ASSERTED RELATION `S.r`
  (`[∀ x y, Decidable (S.r x y)]`) — NOT of any zero relation; the two
  decidability admissions of this run are not interchangeable — by
  `ofSetting_exact`, the residual double-negation gap recorded OPEN in
  `open_kernel_grade`) and from
  any arriving-shape observer PLUS a chosen non-zero pair
  (`ofDiffObs`), with exact inhabitation boundary
  (`kernel_from_obs_iff_pair`) and a collapsed-observer failure
  (`kernel_no_witness_from_collapse`).  Whenever that boundary is
  inhabited, the same-data kernel presentation is non-unique
  (`kernel_not_unique_of_pair`).  It
  meets the sealed pre-contact interface by construction
  (`toNativeKernel : WitnessedDiff X R → PrimitiveContact.NativeKernel`,
  via `toSetting_A`) and is blind to retention, protection and
  operations (`ofSetting_ret_irrelevant`).  Universal status: the
  initial gateway is INHERITED, unconditionally, from the sealed
  `PrimitiveCats.d2_initial` (`kernel_gateway_unique`,
  `kernel_gateway_injective`, `boolKernel_apart_iff`), the gateway
  object is pinned only up to isomorphism — the oppositely pointed
  canonical kernel is a different presentation
  (`kernel_gateways_not_identical`, the kernel echo of the sealed
  `two_initials_not_identical`) — there is
  provably no terminal collector AT THE INDUCED-APARTNESS MORPHISM
  GRADE (`kernel_no_terminal`, `kernel_no_terminal_collector`: both
  quantify over `PrimitiveCats.Hom (apartObj K) (apartObj K')`,
  morphisms of the induced pointed-relation presentations, which
  discard the value data; nothing is proved about terminality in the
  valued morphism category `VHom`), and observer-derived kernels land
  in the symmetric subcategory (`apartObj_sym_of_observer`).  Value
  grade is presentation: two kernels with different value data induce
  the same apartness (`value_presentation_fork`), morphisms are not
  determined by their carrier component (`vhom_not_unique`), and
  uniqueness is restored UNDER surjectivity of the difference map
  (`vhom_unique_of_onto` — sufficiency, with `vhom_not_unique` as the
  one non-onto countermodel; no equivalence is proved, so
  delta-surjectivity is not claimed necessary).  In the reverse
  direction of the realization, the kernel TOGETHER WITH the two
  omitted law declarations is the observer record itself,
  field-for-field and losslessly (`toDiffObs`, with
  `toDiffObs_fields` proving the fields are carried unchanged and the
  kernel recovered from the result, and `toDiffObs_apart` proving the
  relations match) — a record identity at DEFINITION grade, not a
  derivation, with the two declarations priced separately at carriers
  two and three (`kernel_not_observer`, `kernel_zero_not_trans`).
- **Class**: definition + theorem + countermodel + unresolved.
  Evidence classes: DEFINITION (`WitnessedDiff`, `kernelApart`,
  `toSetting`, `toNativeKernel`, `ofSetting`, `ofDiffObs`,
  `toDiffObs` with its two identity theorems `toDiffObs_fields` and
  `toDiffObs_apart` — the record identity is definitional,
  `rfl`-proved, and is NOT claimed as a derivation,
  `apartObj`, `VHom`, `DeltaOnto`, `boolKernel`, `boolKernelSwap`,
  `freeKernel`, `unitValKernel`, `twoValKernel`), DERIVED_THEOREM
  (the realizations, the inherited gateway, the non-collector),
  CONDITIONAL_THEOREM (`ofSetting_exact`, `kernel_located_of_decidable`,
  `vhom_unique_of_onto`, `no_kernel_on_subsingleton`,
  `kernel_two_point_presentation`), COUNTERMODEL
  (`value_presentation_fork`, `vhom_not_unique`, and the
  admission-pricing models of CL-PD2-CONTACT-COUNTERMODELS), OPEN ×2
  (`open_kernel_grade`, `open_kernel_bl` — both registered as open
  obligations in
  `artifacts/primitive_completion_receipt.json:open_obligations`,
  each with its price).
- **Deps**: CL-PD2-CONTACT (the interface met), CL-PD2-INITIALITY
  (the inherited gateway), CL-PD2-MATRIX, CL-PD2-CONTACT-BRIDGE.
  **Assumptions**: shared.
- **Lean**: `ContactKernel.WitnessedDiff`, `.kernelApart`,
  `.kernelApart_irrefl`, `.kernel_endpoints_ne`,
  `.no_kernel_on_subsingleton`, `.boolKernel`, `.toSetting`,
  `.toSetting_A`, `.toNativeKernel`, `.ofSetting`, `.ofSetting_exact`,
  `.open_kernel_grade`, `.ofSetting_ret_irrelevant`, `.ofDiffObs`,
  `.kernel_from_obs_iff_pair`, `.kernel_not_unique_of_pair`,
  `.kernel_no_witness_from_collapse`,
  `.toDiffObs`, `.toDiffObs_fields`, `.toDiffObs_apart`,
  `.kernel_located_of_decidable`, `.open_kernel_bl`, `.kernel_to_w`,
  `.kernel_to_d`, `.kernel_to_e_empty`, `.unitValKernel`,
  `.twoValKernel`, `.value_presentation_fork`, `.VHom`,
  `.vhom_not_unique`, `.DeltaOnto`, `.vhom_unique_of_onto`,
  `.boolKernel_apart_iff`, `.apartObj`, `.apartObj_irrefl`,
  `.apartObj_sym_of_observer`, `.kernel_gateway_unique`,
  `.kernel_gateway_injective`, `.boolKernelSwap`,
  `.kernel_gateways_not_identical`, `.freeKernel`,
  `.kernel_no_terminal`, `.kernel_no_terminal_collector`.
- **Axioms**: within {propext, Quot.sound}.
- **Python**: `primitive_contact.json:verdict.kernel` (structure,
  both realizations, interface, gateway, no-collector, value
  rigidity), `collision_cells` rows `K_to_*` / `*_to_K` (18 of the 37),
  `enumerations.E2_settings_kernels` (candidate-A settings and exact
  kernels agree in count at carriers 1-3: [0, 4, 192]) and
  `E5_value_fork` (81 tables, 2 oriented class presentations);
  `tests/test_primitive_contact.py::test_verdict_block`,
  `::test_collision_cells_mirror_lean_literal`.
- **Falsifier / boundary**: a candidate-A setting or an
  observer-plus-pair that admits no kernel, or a second morphism from
  the sealed initial object into some kernel's presented object.
  Boundary: "replaces both" is scoped to the OVERLAP.  The kernel
  does not carry orientation beyond the pointing, retention,
  protection, operations, or any passage dynamics - all native-only
  surplus - and gateway uniqueness is initiality up to isomorphism,
  never a minimality or constitution-class claim.

### CL-PD2-CONTACT-ENTRY (executed collision, 2026-08-13)
- **Statement**: the common kernel enters the passage at the same
  station the sealed record fixed, and not before the pair's
  assertion — at definition grade: the candidate-A witness conjunct
  at the induced setting is membership in the asserted store, empty
  before `assertWit` (an earlier version said "and no earlier", a
  minimality-flavored clause no cited theorem carries; narrowed to
  this definitional ground 2026-08-18).  Every kernel has
  distinct endpoints, the sealed pre-retention state satisfies
  candidate A, and the retention store there is still empty
  (`kernel_licenses_entry`, reusing
  `PrimitivePassage.kernel_enters_preretained` rather than re-proving
  it); at that state protection is empty, no observation is declared,
  and the four-condition obstruction is false
  (`entry_pre_observation`, the third conjunct discharged by the
  sealed `obst_requires_observation`).  Entry into the passage and
  entry into every kernel factor through ONE initial presentation
  (`passage_gateway_unique`, `kernel_gateway_unique`, both
  instantiations of the sealed `PrimitiveCats.d2_initial`).  A TOTAL
  two-point presentation of the endpoints costs decidable equality of
  the carrier (`kernel_two_point_presentation`) — SUFFICIENCY ONLY:
  the theorem is `[DecidableEq X] (K : WitnessedDiff X R) : ∃ p, …`,
  one direction, and no converse is proved, so necessity is NOT
  claimed; without it only the licensing form is claimed.
- **Class**: theorem + bounded theorem.  Evidence classes:
  DERIVED_THEOREM (`kernel_licenses_entry`, `passage_gateway_unique`),
  FINITE_COMPUTATION (`entry_pre_observation`, decided on the sealed
  pre-retention state), CONDITIONAL_THEOREM
  (`kernel_two_point_presentation`, on `DecidableEq`), DEFINITION
  (`passageObj`).
- **Deps**: CL-PD2-PASSAGE (arrows 1-4 and the obstruction
  conditions), CL-PD2-CONTACT-KERNEL, CL-PD2-INITIALITY.
  **Assumptions**: shared.
- **Lean**: `ContactKernel.passageObj`, `.passage_gateway_unique`,
  `.kernel_licenses_entry`, `.entry_pre_observation`,
  `.kernel_two_point_presentation`;
  `ContactBridge.kernelStage`, `.kernel_stage_no_obstruction`,
  `.declared_zero_as_view`, `.observation_stage_realizes_observer`.
- **Axioms**: within {propext, Quot.sound}.
- **Python**: `primitive_contact.json:collision_cells` row
  `observer_placement (H1)`; the passage arrows themselves remain in
  `primitive_passage.json` and are unchanged.
- **Falsifier / boundary**: an obstruction active at the
  pre-retention entry state, or a kernel whose endpoints coincide.
  Boundary: entry is LICENSED, not forced - retention, protection and
  observation each remain separately priced admission events exactly
  as in the sealed thirteen-arrow chain, and nothing here shortens
  that chain.  Sharper: of the three conjuncts of
  `kernel_licenses_entry` only the FIRST mentions the kernel
  (endpoint distinctness).  The second and third are sealed constants
  about `PrimitivePassage.preRetained` that hold with or without any
  kernel, and no map from an arbitrary kernel into the passage state
  is constructed or claimed - "licenses" is exactly this conjunction,
  not a transport theorem.

### CL-PD2-CONTACT-VERDICT (executed collision, 2026-08-13)
- **Statement**: the contact status is CONTACT_PROCESSED_LEAN_ONLY
  (Lean content only; PROSE_INPUT_ABSENT), and three terminals are
  issued, each only because its evidence bundle compiled.  PRIMARY -
  CONTACT_INCOMPARABLE_WITH_COUNTERMODELS: as supplied, the two
  developments are incomparable, and the incomparability is
  asymmetric IN KIND - the native -> arriving direction is refuted at
  signature level and permanently (the countermodels of
  CL-PD2-CONTACT-COUNTERMODELS), while the arriving -> native gap was
  content-level and is closed this run by the reconstruction under
  the identical axiom budget.  The `WITH_COUNTERMODELS` half of the
  code therefore covers ONE direction: the arriving -> native half is
  an ABSENCE claim about what the sealed corpus contains (METATHEORY
  plus a finite computation over the corpus text), not a refutation,
  and the notion in question is in fact derivable natively at the
  `Nat` scope of the dictionary (`descend_iff_factorsOn_all`) - which
  is precisely why NATIVE_STRICTLY_STRONGER is not issued.
  COMMON_PRIMITIVE_KERNEL_REPLACES_BOTH,
  scoped to the overlap only.
  CONTACT_EQUIVALENT_UNDER_DECIDABLE_ZERO_PLUS_APARTNESS_ADMISSIONS,
  on the relational core only, with every dropped hypothesis priced,
  and with the decidability premise counted as TWO admissions (one
  per direction, not interchangeable - see CL-PD2-CONTACT-BRIDGE).
  NOT issued, with recorded reasons: CONTACT_STRICTLY_STRONGER
  (refuted) and NATIVE_STRICTLY_STRONGER (it would launder this run's
  reconstruction into the sealed record).  The pre-contact terminal
  CONTACT_INPUT_ABSENT is preserved as sealed history, not deleted.
  The collision is recorded as 37 cells with their statuses and
  evidence names; what is machine-checked there is the COUNT
  (`contactCells_length = 37`) and the byte-level agreement of the
  Lean literal with its artifact mirror - each row's status and size
  annotation is a declared label naming the theorem that carries it,
  and that theorem, not the row, is the evidence.  The collision also
  ADDS unresolved obligations: its four OPEN cells and two
  conjectures are registered in the receipt, taking `open_obligations`
  from four entries to eight and `frontier_conjectures` from three to
  five.
- **Class**: declared protocol outcome + theorem-backed terminal
  codes + finite computation.  Evidence classes: DECLARED_POLICY (the
  status and verdict strings, `contactStatusHistory`,
  `contactStatusCurrent`, `contactVerdictPrimary`),
  FINITE_COMPUTATION (`contact_status_count`, `contactCells_length`
  and the E1-E5 enumerations), DERIVED_THEOREM and COUNTERMODEL (the
  bundles cited by each terminal's scope), CONJECTURE (the
  enlarged-corpus containment and the converse of
  `located_schema_implies_wlem`, both registered in
  `primitive_completion_receipt.json:frontier_conjectures`), OPEN
  (the four collision cells `open_bridge_cotrans`,
  `open_bridge_located`, `open_kernel_grade`, `open_kernel_bl`, all
  registered with their prices in the same file's
  `open_obligations`), REFUSED (the arriving comment-borne
  physics and authority claims, dispositions G1-G20).
- **Deps**: CL-PD2-CONTACT-RECONSTRUCTION, -BRIDGE, -COUNTERMODELS,
  -DICTIONARY, -KERNEL, -ENTRY; CL-PD2-CONTACT (the sealed
  pre-contact record).  **Assumptions**: shared.
- **Lean**: `PrimitiveContact.contactStatusHistory`,
  `.contactStatusCurrent`, `.contactVerdictPrimary`,
  `.contact_status_count`, `.native_interface_not_representable`;
  `ContactKernel.contactCells`, `.contactCells_length`.
- **Axioms**: within {propext, Quot.sound}; the declared strings
  carry no report.
- **Python**: `primitive_contact.json` (`status`, `history`,
  `manifest_sha256`, `external_file_sha256_per_manifest`,
  `prose_status`, `verdict` with the full terminal scopes and the
  not-issued reasons, `collision_cells`, `enumerations`);
  `primitive_completion_receipt.json` (thirteen terminals, the
  sealed-history scope on CONTACT_INPUT_ABSENT, the contact block and
  bounds, the twenty-first adversarial attack);
  the four collision-run files of `contact/analysis/` —
  `contact_dictionary.md`,
  `contact_countermodels.json`, `lean_definition_map.md`,
  `lean_theorem_transport.md` (SUPPLIED_INPUT throughout; 103
  declaration rows, G1-G20 dispositions, the per-declaration map and
  the transport tables; the directory, not any two of its files, is
  the permitted quotation location — the directory has since gained
  `separation_capacity_open.md`, so the four-file count is the
  collision-run set, not an exhaustive census; scoped 2026-08-18);
  `tests/test_primitive_contact.py::test_contact_processed_state`,
  `::test_verdict_block`, `::test_status_branches`,
  `::test_collision_cells_mirror_lean_literal`,
  `::test_runner_byte_stable`,
  `::test_equivalence_scope_splits_the_two_decidability_admissions`,
  `::test_incomparable_scope_bounds_minimality_and_absence`,
  `::test_kernel_scope_states_grades_and_record_identity`;
  `tests/test_primitive_receipt.py::test_receipt_binds_everything`
  (which pins the eight open obligations, the four registered
  collision cells with their prices, and the two collision
  conjectures).
- **Falsifier / boundary**: a failed bundle - any listed theorem not
  compiling, any report outside {propext, Quot.sound}, or any
  enumeration disagreeing with the Lean literal (the generator raises
  and blocks regeneration).  Boundary: the verdict compares the
  SEALED corpus at `a5caee2` with the arriving file's Lean statements
  only; comments are never evidence, no prose stage was supplied, and
  any future strictly-stronger reading must be stated against the
  enlarged corpus, never the sealed one.

### CL-PD2-PACKET-02 (pair-choice necessity, 2026-08-14)
- **Statement**: a kernel that carries an observer's difference map
  and zero predicate exists if and only if a non-zero pair exists
  (`kernel_from_obs_iff_pair`).  Any such kernel equals `ofDiffObs`
  at its own endpoints (`eq_ofDiffObs_of_fields`).  The pair is
  therefore necessary data for the observer→kernel map.  This does
  NOT claim uniqueness of the pair or of the kernel
  (`kernel_not_unique_of_pair`) and does NOT claim every observer
  yields a pair (`kernel_no_witness_from_collapse`).
- **Class**: DERIVED_THEOREM.
- **Evidence**: `ContactKernel.kernel_from_obs_iff_pair`,
  `ContactKernel.eq_ofDiffObs_of_fields`; both `#print axioms` in
  `lean4/Derivation.lean`.
- **Deps**: CL-PD2-CONTACT-KERNEL.
- **Lean**: the two theorems above.
- **Axioms**: expected empty (definitional + structure cases).
- **Falsifier**: treating the iff as uniqueness; closing
  `open_kernel_grade` from this lemma.
- **Correction 2026-08-14**: this entry cited
  `pair_choice_load_bearing` as the non-uniqueness witness.  It is
  not one — see CL-PD2-PACKET-02R.  The iff itself is unaffected.

### CL-PD2-PACKET-02R (pair choice: correspondence, presentation non-uniqueness, fixed-action obstruction, 2026-08-14)
- **Withdrawn claim**: "`pair_choice_load_bearing` is
  non-uniqueness."  FALSE as stated.  That theorem exhibits one
  admissible pair and one inadmissible pair at one observer; it says
  an arbitrary pair may fail the side condition.  It exhibits no two
  valid choices, no two distinct kernels, and no obstruction to an
  equivariant pair-valued map.  Its docstring has been rewritten to
  the weak claim it carries.
- **Statement 1 — correspondence (the honest upgrade of the iff)**:
  for a FIXED observer, admissible pairs and same-data kernels
  correspond one for one.  `toPair` and `ofPair` between
  `NonZeroPair O` and `SameDataKernel O`, with BOTH round trips
  proved (`toPair_ofPair`, `ofPair_toPair`) and injectivity
  (`ofPair_injective`).  This replaces the inhabitation equivalence
  `kernel_from_obs_iff_pair` with a bijection: the pair choice IS
  the kernel choice.
- **Statement 2 — non-uniqueness, generally**: whenever an observer
  has an admissible pair at all, it has at least two distinct
  same-data kernels (`kernel_not_unique_of_pair`, via
  `transpose_kernel_ne`).  No carrier bound, no value-type bound.
  Concretely `pair_choice_not_unique` and
  `two_kernels_from_one_observer` exhibit `(false, true)` and
  `(true, false)` over `boolEqObs`.
- **Statement 3 — the fixed-action obstruction, scoped**: no total
  pair-valued map on `DiffObs Bool Bool` satisfies the Bool-negation
  equivariance law (`no_equivariant_pair_valued_map`); the
  contradiction already occurs at `boolEqObs`, a fixed point of the
  action (`swapObs_boolEqObs`), where negation fixes no pair.
- **Class**: DERIVED_THEOREM (13 new reported theorems; supporting
  definitions and abbreviations are counted separately).
- **Scope, stated exactly**: Statement 2 is PRESENTATION GRADE — the
  two kernels carry the same difference map and zero predicate and
  induce the SAME `kernelApart`; they differ only in the designated
  endpoints.  Nothing is claimed up to isomorphism, up to `VHom`, or
  up to observational equivalence.  Statement 2 rests on the
  ADMITTED `zero_symm` field, priced at carrier two
  (`kernel_not_observer`); the corresponding statement fails for a
  bare `WitnessedDiff`, which carries no symmetry.  Statement 3 is
  scoped to total maps `DiffObs Bool Bool → Bool × Bool`
  satisfying the Bool-negation equivariance law at `boolEqObs`;
  nothing is claimed about other carriers, actions, or
  non-equivariant maps.  The same obstruction is already native at
  the relation stratum (`Bridge.no_swap_fixed_offdiag_pair`,
  `Bridge.equivariant_not_D2`); this transports it to the observer
  stratum and claims no priority over it.
- **Axioms**: Statements 1–2 axiom-free; Statement 3 is reported
  within {Quot.sound} because Lean core realizes the function
  extensionality step through `Quot.sound`.  No quotient object occurs
  in the proposition or construction; that statement-level fact must
  not be confused with an axiom-free report.
- **Falsifier**: citing `pair_choice_load_bearing` for any of the
  three statements; reading Statement 2 as distinctness up to
  isomorphism; extending Statement 3 to other carriers, actions, or
  non-equivariant maps.

### CL-PD2-PACKET-05 (obstruction independence audit, 2026-08-14)
- **Status**: **WITHDRAWN 2026-08-14** and replaced by
  CL-PD2-PACKET-05R.  The withdrawn statement read: "`obst_
  conditions_independent` already proves each of the four `obstP`
  conjuncts (retained, protected, declared, zero) is necessary and
  that all four together suffice, by five concrete states."  That
  was false as stated.  `obstP` as written has THREE factors, the
  third being a single `obs`-reading match; and the theorem cited
  was five `obstP … = false/true` atoms, which assert nothing about
  any conjunct, gate, or subset.  The four-way reading lived only
  in the doc-comment, and CLAUDE.md forbids comments as evidence.
- **Falsifier that fired**: reading a table of verdicts as a
  factorization theorem.

### CL-PD2-PACKET-05R (four obstruction gates, proved, 2026-08-14)
- **Statement**: there are four gates in the proved factorization:
  `obstP` is EQUAL, at every state and every pair, to the conjunction
  of the four TOTAL `Bool` gates `retainedP`, `protectedP`,
  `declaredP`, `zeroDeclP` (`obstP_factors`), with both directions
  named (`obst_of_gates`, `gates_of_obst`); and no one of the four
  gates follows from the conjunction of the other three, nor does
  any maximal proper subset of them entail obstruction
  (`gate_zero_independent`, `gate_declared_independent`,
  `gate_protection_independent`, `gate_retention_independent`, each
  a pair of `¬ ∀` statements quantified over ALL states and pairs).
- **Class**: DERIVED_THEOREM (12 new reported theorems cited here;
  14 across this entry and CL-PD2-PACKET-05P, whose two policy
  theorems are classed DECLARED_POLICY there — count scoped
  2026-08-18; supporting definitions are counted separately).
- **Scope, stated exactly**: independence means non-entailment, and
  nothing more.  It is NOT claimed that all sixteen gate valuations
  occur — `obs_gates_not_both_false` proves they do not, gates 3 and
  4 both reading `obs`.  It is NOT claimed that four is the only
  decomposition of this predicate, nor that no other activation
  signature exists.  `obstP` itself has the three written factors
  recorded by `obstP_strict_factors`; `obstP_factors` alone is
  near-definitional (any `Bool` splits as `true && c`); it is the four
  independence
  theorems that carry the content, and the two must be cited
  together.
- **Declared convention**: `zeroDeclP` answers `true` on
  pre-observational states.  That value is a DECLARED CONVENTION,
  exhibited by `undeclared_gates`, priced by
  `obs_gates_not_both_false`, and shown load-bearing by
  `strict_gate_entails_declared` (under the rival `none => false`
  convention gate 4 would entail gate 3, and the omission witness
  would be unavailable).
- **Evidence**: the named gate definitions and theorems above plus
  `obstP_strict_factors` (the three written factors, by `rfl`) and
  `obstP_reads_three_stores` (at most `wit`, `prot`, `obs` are
  read); `#print axioms` for each in `lean4/Derivation.lean`.
- **Axioms**: within {propext, Quot.sound}.
- **Falsifier**: citing `obstP_factors` alone as a four-way
  independence result; claiming all sixteen valuations occur;
  claiming necessity of the gates for any notion of obstruction
  other than this predicate.

### CL-PD2-PACKET-05P (the pre-observational policy, priced, 2026-08-14)
- **Statement**: the `none => false` branch of `obstP` is a selected
  semantics, not a derived necessity.  `obst_requires_observation`
  unfolds that branch and proves nothing about whether it had to be
  chosen.  The rival reading — treat `none` as an observation
  declaring no columns — is now NAMED (`obstEmptyObs`).  The policies
  agree on every declared state (`obst_policies_agree_when_declared`)
  and differ at one named undeclared state (`obst_policies_differ`).
  A complete characterization of their divergence remains OPEN.
- **Class**: DECLARED_POLICY, with a proved divergence.
- **Supersedes**: the prior claim that declared observation "is not
  a convention", which is WITHDRAWN.  What is licensed instead: the
  selected passage semantics makes declaration an explicit gate, and
  it differs from treating `none` as an empty observer — provably,
  at a named state.  What is NOT licensed: that the selected branch
  was forced.
- **Note on the older witness**: `obst_diverges_when_undeclared` does
  NOT carry this content.  Its first conjunct writes the lists out
  rather than projecting them from the state, so it is a closed
  truth mentioning no state at all; only its second conjunct is
  about the state.  It is retained as the historical witness and is
  not evidence of divergence.
- **Evidence**: `PrimitivePassage.obstEmptyObs`,
  `obst_policies_agree_when_declared`, `obst_policies_differ`.
- **Falsifier**: asserting the branch is forced; citing
  `obst_requires_observation` as evidence about the choice; reading
  the named witness as an iff characterization of divergence.

### CL-PN-NATURAL-SELECTION (naturality obstruction across presentations, 2026-08-14)
- **Statement**: selecting an admissible pair can be obstructed by
  NATURALITY alone.  A presentation isomorphism (`PresIso`) is a
  bijection of carriers and of residual values transporting `delta`
  and `Zero`; `zeroRel_transport` proves the induced zero relation
  transports, and `PresIso.mapPair` transports the admissible-pair
  bundle.  Over the declared one-object family generated by a
  presentation automorphism (`autoFamily`), a section of that bundle
  is natural when it commutes with the automorphism.  **The general
  theorem** (`no_natural_section_of_fixed_point_free`): if the
  automorphism fixes the observer but fixes no admissible pair of it,
  no natural section exists.
- **Class**: theorem (general), with one negative and one positive
  finite fixture.
- **Weight, recorded honestly**: over a one-object family `IsNatural`
  unfolds to "the selected pair is fixed", so
  `no_natural_section_of_fixed_point_free` is NEAR-DEFINITIONAL and its
  proof is one line.  It must be cited WITH the transport machinery
  (`zeroRel_transport`, `PresIso.mapPair`, `viable_transport`), which
  is what makes natural selection a well-typed question across
  presentations, and WITH the positive boundary
  (`card4_has_natural_section`), which is not definitional.  Citing the
  obstruction alone, as though the one-line proof were the substance,
  is a misuse of this entry.
- **Instance**: at the sealed `ContactKernel.boolEqObs` with negation
  as the presentation automorphism, no admissible pair is fixed
  (`negIso_fixed_point_free`), so no natural section exists
  (`no_natural_section_boolEq`).
- **Both boundaries are proved**, so the theorem is neither vacuous
  nor a universal refusal:
  - `selection_is_possible_naturality_is_not` — over the very family
    with no natural section, a raw section is exhibited explicitly.
    Selection is possible; natural selection is not.
  - `card4_has_natural_section` — a four-element presentation whose
    declared automorphism transposes two elements and fixes two;
    the fixed pair is admissible, so a natural section DOES exist.
  - `naturality_separates_presentations` states the two together.
- **Supersedes nothing.**  `ContactKernel.no_equivariant_pair_valued_map`
  stands unchanged at its own scope.
- **Exact non-claims**:
  - No categorical structure.  `PresIso.refl`, `.symm`, `.trans` are
    given with pointwise component laws only (`refl_car`, `trans_car`,
    `symm_car_left`, `symm_car_right`, `symm_symm_car`).  No groupoid,
    category, or functor is asserted anywhere, and no `PresIso`
    equality is proved.
  - The obstruction is RELATIVE to the declared family.  `autoFamily`
    lists exactly one object and one isomorphism.  Nothing is claimed
    about families not constructed here.
  - Everything proved is over ONE-OBJECT families, including both
    fixtures.  They separate two one-object situations, not two
    presentation theories.  `Family` requires neither composition nor
    inverses, so naturality is with respect to exactly the arrows
    listed.  Multi-object families, naturality under a generating set,
    and coherence of `mapPair` with `trans`/`symm` beyond the
    one-object case are FUTURE WORK, not results.
  - This entry does NOT subsume
    `ContactKernel.no_equivariant_pair_valued_map` and must not be
    described as the general form of it.  Describing it that way was an
    earlier framing, now WITHDRAWN: the OPEN derivation below denies
    exactly that subsumption.
  - No claim that selection is impossible in any sense, and no choice
    principle is claimed, used, or refuted — every theorem in the
    module except the co-statement is axiom-free.
  - No quotient, homology, probability, inner-product-space, or non-commutative-observable
    conclusion is claimed or licensed.
  - `bool_obstruction_and_sealed_selector` is a CO-STATEMENT, not a
    derivation: it asserts this module's obstruction and the sealed
    selector theorem together, and obtains neither from the other.
    They quantify over different objects — maps out of the observer
    type, versus sections of the admissible-pair bundle.
- **OPEN**: deriving `ContactKernel.no_equivariant_pair_valued_map`
  from `no_natural_section_of_fixed_point_free`.  Until that is
  proved, the sealed Bool theorem is NOT licensed as an instance of
  the general obstruction.
- **Evidence (Lean)**: `PresentationNaturality.zeroRel_transport`,
  `.Bij.fwd_injective`, `.refl_car`, `.trans_car`, `.symm_car_left`,
  `.symm_car_right`, `.symm_symm_car`, `.viable_transport`,
  `.no_natural_section_of_fixed_point_free`,
  `.fixed_pair_of_natural_section`, `.negIso_fixed_point_free`,
  `.no_natural_section_boolEq`,
  `.selection_is_possible_naturality_is_not`, `.tw_involutive`,
  `.card4_natural_section`, `.card4_has_natural_section`,
  `.naturality_separates_presentations`,
  `.bool_obstruction_and_sealed_selector`.
- **Python evidence**: none.  This claim is Lean-only by construction;
  it introduces no new runner and no new artifact.
- **Falsifier**: exhibiting a natural section over `autoFamily
  boolEqObs negIso`; exhibiting a fixed admissible pair of `negIso`;
  reading the theorem as "no selector exists" rather than "no natural
  selector exists"; citing it as a categorical or groupoid statement;
  citing the co-statement as a derivation.

### CL-PN-HETEROGENEOUS-TRANSPORT (many objects, indexed carriers, 2026-08-14)
- **Narrows**: the one-object bound recorded in
  CL-PN-NATURAL-SELECTION.  That entry stands as the record of what was
  proved at the time; this entry records what is proved now.
- **Root cause of the old bound**: `Family` declared its arrows as a
  flat `Arr` with `src`/`tgt` functions, which forced ONE carrier `X`
  and ONE residual type `R` across every object, and made an
  endomorphism a propositional condition (`src f = tgt f`) rather than
  a typed one.  `HFamily` indexes arrows as `Hom a b`, so an
  endomorphism is definitionally an inhabitant of `Hom a a`, and the
  carrier and residual type become object-indexed (`car`, `res`).  No
  dependent transport appears anywhere in the new development.
- **Statement**: `no_natural_section_of_endo` — a declared
  endomorphism at ANY object of a heterogeneous family, fixing no
  admissible pair there, already rules out a natural section of the
  whole family.  The carrier and residual type may differ from object
  to object.
- **Coherence of the transported bundle**: `mapPair_refl`,
  `mapPair_trans`, `mapPair_symm_left`, `mapPair_symm_right`.  These
  are the bundle-level companions of the §3 component laws.  They are
  statements about `mapPair` and `PresIso`, NOT about `HFamily`, and
  they still assert no categorical structure.
- **Both boundaries, over a genuinely heterogeneous two-object
  family** (`Bool`/`boolEqObs` and `Card4`/`card4Obs`, different
  carriers and different residual types):
  - `twoFamilyNeg_no_section` — negation at the `Bool` object fixes no
    admissible pair, so the WHOLE family has no natural section, even
    though its `Card4` component alone does.
  - `twoFamilyPos_has_section` — replacing only that automorphism by
    the identity yields a natural section.
  - `heterogeneous_naturality_separates` states both.  Same objects,
    same carriers, same admissible pairs: only the declared
    automorphism differs, so the obstruction is carried by the
    declared arrows and not by heterogeneity.
- **Bridge**: `hAuto_iff_auto` — over ONE object, a natural section
  exists for the flat `autoFamily` exactly when one exists for the
  indexed `hAutoFamily`.  Both endpoint structures are named.
- **Still OPEN, exactly**:
  - A general embedding of `Family` into `HFamily`.  `hAuto_iff_auto`
    covers the one-object case only; `Family` is RETAINED and is not
    superseded.
  - Naturality under arrows that genuinely CROSS objects with
    different carriers.  The two-object fixtures declare no arrow
    between their objects, so that case is not exercised.
  - `HFamily` still assumes NO closure: no composition, no inverses,
    no identities.  `Hom a b` is a list of declared isomorphisms, not
    a hom-set of a category.  No categorical structure is claimed.
  - Deriving `ContactKernel.no_equivariant_pair_valued_map` remains
    OPEN and untouched by this entry.
- **Evidence (Lean)**: `PresentationNaturality.mapPair_refl`,
  `.mapPair_trans`, `.mapPair_symm_left`, `.mapPair_symm_right`,
  `.no_natural_section_of_endo`, `.hAuto_iff_auto`,
  `.twIso_fixes_card4Pair`, `.twoFamilyNeg_no_section`,
  `.twoFamilyPos_natural`, `.twoFamilyPos_has_section`,
  `.heterogeneous_naturality_separates`.  All eleven are axiom-free.
- **Python evidence**: none; Lean-only, no new runner or artifact.
- **Falsifier**: exhibiting a natural section over `twoFamilyNeg`;
  exhibiting a heterogeneous family where the endo obstruction fails;
  citing `HFamily` as a category or its `Hom` as a hom-set; citing the
  one-object bridge as a general embedding.

### CL-CAP-BOUND (the coloured separation-capacity bound, 2026-08-14)
- **Closes**: the OPEN residual recorded in
  `contact/analysis/separation_capacity_open.md` §2 and §3.  That
  document's §2 previously said the capacity bound was "not in this
  repository" and that "the pigeonhole is the blocker"; both statements
  are WITHDRAWN there, at their original site.
- **Statement** (`CapacityBound.capacity_bound`): let `colour` take
  values below `k`, and let `v` factor through the radius-`d` colour
  ball (`CapacityBound.ViewLocal`).  Then once
  `n ≥ k ^ (2d + 1) + 2d + 2`, the deep interior of `reflState n` holds
  two distinct points that `v` does not separate.  This is exactly the
  form the residual document stated as the target,
  `n ≥ B + 2d + 2`, with `B = k ^ (2d + 1)`.
- **Why it is a capacity statement and not global pigeonhole**: `B` is
  DERIVED, not assumed.  It counts the colourings of a radius-`d` ball,
  so it depends on the radius and the alphabet and NOT on `n`.  The
  deep interior holds `n - 2d - 1` points, so the threshold is exactly
  where that interior first holds `B + 1` points.  Without `ViewLocal`
  the radius is inert and the statement degenerates — which is the trap
  §4 of the residual document names, and `ViewLocal` is what meets it.
- **Class**: theorem, with two exhibited boundary fixtures.
- **Supporting**: `encode`/`encode_lt`/`encode_inj` carry bounded
  colour lists into `Nat` and back injectively at fixed length;
  `Pigeonhole.pigeonhole` supplies the counting; its enumerated report
  is choice-free and lies within `{propext, Quot.sound}`.
- **Non-vacuity, exhibited not assumed**: `capacity_at_one_colour` is
  the degenerate end (one colour, constant view);
  `local_view_can_separate` fixes `k = 2`, `d = 0`, and `n = 3`, proves
  that indices `1` and `2` are deep and that `3` lies strictly below
  the threshold `4`, and exhibits a local parity view that separates
  every distinct deep pair (including `1` and `2`). Thus the existential
  forced-collision conclusion is false at this below-threshold instance,
  rather than merely false for one selected pair.
- **Exact non-claims**:
  - `k ^ (2d + 1)` is an UPPER bound on the number of distinguishable
    balls.  No matching lower bound is proved; no tightness is claimed.
  - Nothing is claimed for views that do not factor through the ball.
  - `colour` is an arbitrary bounded colouring.  Nothing is claimed
    about the sealed `Generator.profile2` colouring in particular, and
    nothing here relates the two.
  - The general-`n` radius correspondence and a repair-strategy-class
    consequence are the two OPEN residuals of this investigation.  Their
    restricted forms are discharged later in this ledger by the local
    finite-alphabet G1 entries (`CL-G1-CAPACITY-APPLICATION`,
    `CL-G1-CLASS-EXCLUSION`); the unrestricted forms stay open (forward
    pointer added 2026-09-08).
  - Identity-grade observation, absolute interior, and any "no outside"
    result are outside this investigation's statement language. This
    entry does not license any of them.
- **Evidence (Lean)**: `CapacityBound.capacity_bound`, `.ViewLocal`,
  `.local_view_blind`, `.encode_lt`, `.encode_inj`,
  `.colourBall_length`, `.colourBall_bounded`,
  `.capacity_at_one_colour`, `.local_view_can_separate`;
  `Pigeonhole.nodup_length_le`, `.pigeonhole`, `.map_nodup_of_inj`,
  `.nodup_filter_eq_le_one`, `.filter_nodup`, `.length_filter_split`,
  `.upto_length`, `.upto_mem`. Their enumerated reports are all within
  `{propext, Quot.sound}` and contain no `Classical.choice`.
- **Python evidence**: none; Lean-only, no new runner or artifact.
- **Falsifier**: a local view over a `k`-colour alphabet separating
  every deep pair at some `n ≥ k ^ (2d + 1) + 2d + 2`; citing the
  bound for a view without the `ViewLocal` hypothesis; citing
  `k ^ (2d + 1)` as tight; reading the bound as a statement about the
  sealed profile colouring.

### CL-PREL-RELATIVE-IDENTITY (presentation-relative identity and comparison-forced refinement, 2026-08-14)
- **Statement, relative identity**: on a supplied finite list `D`,
  `PresentationIdentityOn D p q` is mutual `FactorsOn`.
  `presentationIdentity_iff_fiberIdentity` proves that this is exactly
  equality of the two induced fiber relations on represented pairs;
  `presentationIdentity_iff_residualEmpty` proves that it is exactly
  absence of a `DirectionalResidual` in either direction.
  `presentationIdentity_equivalence` proves that this relation is
  reflexive, symmetric, and transitive.
  `self_comparison_has_empty_residual` is the exact self-comparison
  corollary, not a self-certification theorem.
- **Question-family form**: `identityRelativeToQuestions_iff`
  identifies relative identity with the fibers of the supplied ordered
  first-match signature `pQ D Q`. For `x ∈ D`,
  `splitsAt_iff_directionalResidualAt` proves that
  `SplitsAt D Q Q' x` is exactly an old-family identification separated
  by the new family at `x`. If `Q'` contains `Q`,
  `family_enlargement_split_is_strict` combines the refinement
  direction with failure of mutual factorization.
- **Comparison-forced refinement**: if the supplied `q` fails to factor
  through `p` on `D`, `forced_split_of_factorization_failure` returns
  represented `x,y` with `p x = p y` and `q x ≠ q y`; every `r`
  carrying both `p` and `q` separates that pair and satisfies
  `classCount D [p] < classCount D [r]`.
  `directionalResidual_of_factorization_failure` packages the witness.
  `jointPresentation_strict_of_factorization_failure` exhibits one
  adequate refinement, `pQ D [p,q]`, whose left and right factorization
  laws are proved separately. Its ordered first-match encoding is
  declared; no naturality or preference follows.
- **Operational witnesses**: within the seven-field `World` schema,
  `supportNotesView` is injective while `supp` can identify records that
  the larger view separates; changing only `notes` preserves the
  enumerated kernel results. Under evaluator admission, panel
  equivalence refines and enlarged-panel negative certification implies
  source certification for a nonempty source panel; a fixed panel
  fixture shows the converse can fail without changing the stored
  world. The generator fixture supplies `id` as an identity-grade
  comparison and instantiates the forced-refinement theorem for every
  `n ≥ 3`.
- **Ambient diagnostic only**:
  `PresentationRelativity.Metatheory.attempted_absolute_identification_collapses_to_equality`
  and
  `PresentationRelativity.Metatheory.attempted_absolute_polarities_are_refuted`
  quantify over ambient Lean functions. They diagnose an attempted
  all-view quantifier; they do not admit such views to `World`,
  `CWorld`, or replay.
- **Class**: finite common-carrier theorems, plus one concrete panel
  fixture and three horizon-free generator consequences.
- **Exact non-claims**:
  - The comparison `q` is supplied. No first presentation,
    continuation policy, physical time, cosmological origin, or
    distinguished external fact is generated.
  - No capital-T truth object is defined. “Identity relative to
    questions” is the typed mutual-factorization relation above.
  - No heterogeneous-carrier version of the forced-split/class-count
    theorem is proved.
  - A forced split does not make a complete refinement unique, natural,
    canonical, or preferred.
  - `supportNotesView` is complete only for the declared `World` fields;
    no observer-complete view or all-view survey is claimed.
  - No general evaluator self-certification, self-cutting, or endogenous
    comparison-demand theorem is present.
  - `ABSOLUTE_NO_OUTSIDE_UNFORMULABLE` remains unchanged. Inside/outside
    predicates are absent from these object-level statements; their
    ontological nonexistence is not asserted as a theorem.
  - The generator instance uses the supplied identity comparison and
    therefore does not close G1's non-identity repair-channel
    obligation.
- **Evidence (Lean)**: all 32 `PresentationRelativity.*` theorem reports
  enumerated by `lean4/Derivation.lean`; in particular the four identity
  equivalences, the split/refinement spine, the joint-presentation laws,
  the two `Metatheory` diagnostics, the support/panel laws, and the three
  declared-generator results.
- **Python evidence**: inventory and receipt binding only; no new
  solver, runner, or computed mathematical evidence.
- **Falsifier**: a represented pair on which mutual factorization holds
  but fiber identity fails; a directional factorization failure with no
  residual pair; an `r` carrying both supplied maps but not splitting
  the witness or not increasing class count; or any citation of the
  joint presentation as natural/preferred or of the common-carrier
  theorem as heterogeneous.

### CL-CLOSURE-SYMMETRY (failed closure as internal symmetry loss, 2026-08-14)
- **Statement**: for two internal faces `p,q : Nat → Nat` of one
  attempted closure on represented finite domain `D`, failure of
  `FactorsOn D p q` is equivalent to the existence of a represented
  involution `σ` that preserves `D` and `p` but under which `q` is not
  invariant at a represented point. A `DirectionalResidual D p q`
  constructs `σ` as the transposition of its two points; conversely the
  non-invariant point reconstructs the residual.
- **Exact equivalence**:
  `closure_failure_iff_internal_symmetry_break` proves
  `¬ FactorsOn D p q ↔ Nonempty (InternalSymmetryBreak D p q)`.
  `residual_nonempty_iff_internal_symmetry_break_nonempty` identifies
  the residual and symmetry-break forms directly.
  `residual_refutes_factorization` is the one-directional closure
  obstruction used by the reverse implication.
- **Internality**: `p`, `q`, `σ`, the represented domain, and the
  residual pair are fields or arguments of the same typed attempt.
  Neither `p` nor `q` is an evaluator, subject, truth source, inside,
  outside, or observer from nowhere.
- **Class**: finite common-carrier equivalence and explicit
  transposition construction.
- **Exact non-claims**:
  - No replacement face, repair, continuation, or comparison demand is
    selected or authorized.
  - No face is preferred, canonical, more true, or externally
    certified.
  - No heterogeneous-carrier or infinite-domain theorem is claimed.
  - The result does not prove an ontological absence of inside/outside;
    those predicates do not occur in the object language.
  - No self-evaluator, self-certifier, or claim that a knife literally
    acts on itself is formalized. The proved content is invariance and
    factorization of one represented closure attempt.
- **Evidence (Lean)**: the seven `ClosureSymmetry.*` theorem reports
  enumerated by `lean4/Derivation.lean`; strongest axiom surface
  `{propext, Quot.sound}`.
- **Python evidence**: inventory and receipt binding only.
- **Falsifier**: a failed factorization with no represented internal
  symmetry break; a residual whose transposition does not preserve
  `p`; or an internal symmetry break that does not refute
  factorization.

### CL-FIDELITY-DESCENT (heterogeneous index erasure, 2026-08-14)
- **Statement**: for supplied carrier types `P,Q` and a supplied scoped
  `TranslationAttempt`, `TranslationGap` blocks exactly a totalization that must
  preserve the declared translation equation. For a total pair,
  `faithful_descent_iff_round_trip_coherent` proves equivalence between
  two-sided round-trip closure and an independently defined common carrier
  with injective embeddings satisfying the two declared identification
  equations that bind them to the totalized translations; coincident
  images of the two embeddings is a derived consequence
  (`faithful_common_descent_has_coincident_images`), not a defining
  condition.  (An earlier version described the right-hand side as
  "injective embeddings and coincident images", omitting the
  load-bearing identification equations — corrected 2026-08-18.)
- **Residual**: `CoherenceResidual` is failure of one of the two declared
  round trips. `residual_forces_index_retention` says that this declared pair
  does not faithfully erase its two indices.
- **Exact non-claims**: failure of one pair does not rule out every other
  equivalence; undefinedness alone does not rule out arbitrary extensions;
  disjoint union is not called descent; no observer, evaluator, metric, or
  authority is present.
- **Evidence**: the seven `PresentationDescent.*` theorem reports in the
  aggregate axiom artifact.

### CL-QUOTIENT-RETENTION (multiplicity survives failed collapse, 2026-08-14)
- **Statement**: for arbitrary carrier `I` and supplied setoids `fine,coarse`,
  refinement induces a surjective collapse map. An identification made by
  `coarse` but refused by `fine` yields two distinct fine classes with one
  coarse image and therefore makes the collapse non-injective. The collapse
  is injective exactly when the reverse refinement also holds.
- **Interpretation**: failed descent creates no object; it prevents an
  attempted identification from erasing an already supplied index.
- **Exact non-claims**: no finite carrier, count, observer, canonical
  representative, or ontology is derived.
- **Evidence**: the nine `QuotientRetention.*` theorem reports.

### CL-FIDELITY-CLOSURE (coherent paths and descent residuals, 2026-08-14)
- **Statement**: a `TranslationNetwork` supplies heterogeneous carriers and
  attempted translation pairs. `FidelityPath` freely closes only total,
  round-trip-coherent steps under identity, reversal, and composition. Its
  induced setoid identifies exactly path-connected indices. Missing paths
  retain distinct quotient classes. Holonomy and coherent label disagreement
  separately refuse faithful network or label descent.
- **Scope fence**: one failed endomorphism does not refute self-fidelity;
  reachability of indices is not a proof of path-independent global carrier
  data.
- **Evidence**: the eleven `FidelityClosure.*` theorem reports.

### CL-ENDOGENOUS-FIDELITY-GENERATOR (least closure, 2026-08-14)
- **Statement**: `fidelity_is_least_equivalence_containing_admitted_steps`
  proves that fidelity is the least equivalence relation containing the
  admitted coherent translation steps. `generated_structure_is_failed_erasure`
  compares its quotient with the attempted indiscrete collapse: if no coherent
  path joins two supplied indices, they survive as distinct generated classes
  although the universal collapse identifies their images.
- **Operational witness**: `NoOutsideFidelity` proves that the existing support
  projection cannot participate in a coherent round trip with any proposed
  backward map because a notes fiber contains distinct `World` values; the
  notes field remains operationally authority-inert.
- **Exact non-claims**: the network, initial indices, attempts, and admission
  criterion are supplied. No first presentation, self-certification,
  strategy, physical time, ontological inside/outside theorem, or authority
  effect is generated. `AuthorityEffect: None`.
- **Evidence**: six `EndogenousFidelityGenerator.*`, six
  `NoOutsideFidelity.*`, and seven `ResidualClosure.*` theorem reports.
- **Falsifier**: an admitted coherent step absent from fidelity; an
  equivalence containing every admitted step that fails to contain fidelity;
  a missing coherent path whose indices nevertheless have equal fidelity
  classes; or a faithful support descent preserving the exact projection.

## Local finite-alphabet G1 class claims (2026-08-26)

These entries supersede `CL-G-OPEN` only for the exact T5 and declared-class
T6 residuals named below. They do not withdraw unrestricted G1 or discharge
the closure-policy obligation. Full exact quotes, per-theorem reports, and
finite bounds are bound by `artifacts/g1_class_receipt.json`.

### CL-G1-LOCAL-CLASS

- **Statement**: `LocalStrategy d` consists of one fixed import discipline,
  colouring and repair view, with the view factored through a radius-`d`
  colour ball at every length. `FiniteDeclaration k S` uses one alphabet
  bound independent of chain length. `Fires`, `Clears`, `RecurringImport`,
  and `IdentityGrade` are distinct predicates.
- **Class**: declared metatheory.
- **Deps**: none; this entry declares the strategy-class vocabulary.
- **Assumptions**: one fixed radius and one fixed alphabet bound independent
  of chain length, with the view factored through the declared colour ball.
- **Python**: `code/derivation/local_strategy.py`; negative fiber test
  `test_unconstrained_view_fails_locality_fiber_check`.
- **Lean**: exact definitions `LocalFiniteAlphabet.LocalStrategy`,
  `LocalFiniteAlphabet.FiniteDeclaration`,
  `LocalFiniteAlphabet.RecurringImport`, `LocalFiniteAlphabet.Fires`,
  `LocalFiniteAlphabet.Clears`, and `LocalFiniteAlphabet.IdentityGrade`; the
  receipt quotes them byte-for-text.
- **Axioms**: definitions are not claimed axiom-clean. Every cited theorem
  below has an inventory report within `{propext, Quot.sound}`.
- **Falsifier / boundary**: equal radius balls with unequal views falsify
  locality; an alphabet growing with length falsifies `FiniteDeclaration`.
  Such strategies are outside the class, not disproved.

### CL-G1-T5-GENERAL

- **Statement**: for every chain length and every pair of interior indices,
  sealed depth-two profile equality is equivalent to radius-one structural
  profile equality.
- **Class**: theorem.
- **Deps**: `CL-G-DEPTH2`, `CL-CAP-BOUND`.
- **Assumptions**: both indices are interior points of the same finite
  reflective chain; radius is one. This withdraws the earlier general-`n`
  OPEN sentence.
- **Lean**: `SeparationCapacity.radius_one_agrees_with_sealed_depth2`, with
  `filter_range_decide_eq`, `filter_range_succ_eq`, `filter_range_eq`,
  `incoming_edges_interior`, `outgoing_edges_interior`,
  `profile2_interior`, and `profileD_radius_one`.
- **Axioms**: each of the eight reports is exactly
  `{propext, Quot.sound}`.
- **Python**: `code/derivation/g1_class_receipt.py` resolves and binds the
  eight exact T5/helper reports; the earlier length-4/5 computations remain
  witnesses, not the general proof.
- **Falsifier / boundary**: an interior pair on which the two equality
  relations disagree. The theorem is radius one and is not the class
  exclusion.

### CL-G1-CAPACITY-APPLICATION

- **Statement**: every member with `FiniteDeclaration k S` has a distinct
  deep equal-view pair once
  `k ^ (2 * d + 1) + 2 * d + 2 <= n`; therefore it cannot clear every
  inherited depth-one obstruction. The capacity `k ^ (2*d+1)` is derived,
  not assumed.
- **Class**: theorem.
- **Deps**: `CL-CAP-BOUND`, `CL-G-GENERATION`.
- **Assumptions**: `S` satisfies the quoted locality factorization and
  `FiniteDeclaration k S`; the displayed threshold holds.
- **Lean**: `LocalFiniteAlphabet.strategy_capacity_collision`,
  `finite_local_not_clears`, and `finite_local_not_identityGrade`.
- **Axioms**: each report is within `{propext, Quot.sound}`.
- **Python**: `artifacts/local_strategy.json`, concrete thresholds 10, 10,
  and 516 for bare, presence, and depth-two.
- **Falsifier / boundary**: a class member satisfying the hypotheses whose
  view separates every deep pair at the displayed threshold. No claim is
  made for a nonlocal view or an unbounded alphabet.

### CL-G1-CLASS-EXCLUSION

- **Statement**: every finite declared local member fires on the inherited
  reflective family, fails to clear every chain length, and cannot satisfy
  `Fires S and Clears S and not RecurringImport S`.
- **Class**: theorem.
- **Deps**: `CL-G1-LOCAL-CLASS`, `CL-G1-CAPACITY-APPLICATION`,
  `CL-G-GENERATION`.
- **Assumptions**: `S` is a member of the declared class and satisfies one
  fixed `FiniteDeclaration k S`; no finite horizon is assumed.
- **Lean**: `LocalFiniteAlphabet.fires_every_strategy`,
  `g1_local_finite_alphabet_class`,
  `G1Class.local_strategy_cycle_impossible`, and
  `G1Class.g1_class_exclusion`.
- **Axioms**: each report is exactly `{propext, Quot.sound}`.
- **Python**: `artifacts/local_strategy.json` supplies bounded witnesses and
  five concrete rows only.
- **Falsifier / boundary**: a member of the exact quoted class satisfying the
  full cycle. This theorem does not range over every repair channel:
  `OB1_UNCHANGED`; `OBJECT_LANGUAGE_GENERATOR_NOT_IN_SCOPE`.

### CL-G1-FIVE-STRATEGIES

- **Statement**: bare, presence, and depth-two are finite members that fire
  and fail to clear globally; per-pair fresh marking is recurring and not
  finite; valued marking is one-time identity-grade, clearing, and not
  finite. Presence equals bare, while depth-two clears length 4.
- **Class**: theorem.
- **Deps**: `CL-G1-LOCAL-CLASS`, `CL-G1-CLASS-EXCLUSION`,
  `CL-G-REPAIR-FATES`.
- **Assumptions**: the five strategy definitions are exactly those named in
  `Derivation.LocalStrategy`; the Python mirror uses check bound 15 only for
  its concrete rows.
- **Lean**: `profileCode_lt_eight`, `bare_finite`, `presence_finite`,
  `presence_eq_bare`, `depthTwo_finite`, `depthTwo_clears_n4`,
  `perPair_recurring`, `perPair_identityGrade`, `perPair_not_finite`,
  `valued_oneTimeIdentity`, `valued_not_finite`, `valued_clears`,
  `class_nonvacuity`, `bare_not_identityGrade`, and the three
  classification theorems `bare_classification`,
  `presence_classification`, and `depthTwo_classification`.
- **Axioms**: every named report lies within
  `{propext, Quot.sound}`; `profileCode_lt_eight` has none.
- **Python**: `artifacts/local_strategy.json`, five strategies through chain
  length 15; its classification is not used to prove the general theorem.
- **Falsifier / boundary**: disagreement between a row and its proposition,
  or acceptance of the constant-colour/index-view negative locality probe.

### CL-G1-G3-COUNTEREXAMPLE

- **Statement**: `Clears S` does not imply `not Fires S` under the current
  definitions. The valued strategy witnesses both, so G3 needs an additional
  state-transition hypothesis relating repair to future demand production.
- **Class**: counterexample.
- **Deps**: `CL-G1-LOCAL-CLASS`, `CL-G1-FIVE-STRATEGIES`.
- **Assumptions**: `Fires` retains its inherited pre-repair meaning and
  `Clears` its proposed post-repair meaning. G3 remains conjectural.
- **Lean**: `G1Class.clears_does_not_imply_not_fires`.
- **Axioms**: exactly `{propext, Quot.sound}`.
- **Python**: the valued row in `artifacts/local_strategy.json` is a bounded
  mirror only.
- **Falsifier / boundary**: a derivation of the proposed implication from the
  present predicates. No unrestricted conservation law is claimed.

### CL-G1-G4-FINITE

- **Statement**: **WITHDRAWN** — the former statement said that all 455
  depth-one chain obstructions were passed through the Challenge-3 engine.
  The loop never supplied its chain pair to `min_responses`; it repeated the
  four fixed Challenge-3 catalogs. No finite chain correspondence was
  computed, so G4 remains a conjecture. The surviving Challenge-3 facts are
  the already registered L/F `mu1` tie counts and the single `mu2`
  isomorphism class under the declared candidate bounds.
- **Class**: conjecture.
- **Deps**: `CL-3-MIN-TWO`, `CL-3-TIE-CLASSES`,
  `CL-3-UNIQUE-MU2-L`, `CL-3-UNIQUE-MU2-F`, `CL-G-GENERATION`.
- **Assumptions**: the surviving computation concerns only the sealed
  Challenge-3 targets, readings L/F, measures mu1/mu2, `max_items=2`,
  `max_arity=2`, and the implemented regime isomorphism quotient. No
  chain-to-regime adapter is assumed.
- **Python**: `code/derivation/engine.py`, `tests/test_engine.py`, and
  `artifacts/challenges.json`; `test_challenge3_reading_l_classes` and
  `test_challenge3_reading_f_has_five_classes` check the surviving catalogs.
- **Lean**: no Lean theorem is claimed for G4.
- **Axioms**: not applicable to the surviving finite computation.
- **Falsifier / boundary**: a declared collapse-preserving adapter that passes
  each actual chain pair to the engine, followed by a replayable finite run.
  Until then the chain claim is OPEN; Challenge-3 minima authorize no adapter.

### CL-PD-TRANSPOSE
- **Statement**: on the two-element carrier, the unique non-identity
  permutation (`Bool.not` / the swap of the two points) carries `D2`
  onto `D2rev` and `D2rev` onto `D2`, and two applications restore
  either orientation; both orientations have the same symmetrization
  `S2`; that permutation is an automorphism of `S2` and of neither
  orientation; unpointed, every inhabited decidable irreflexive
  relation equals `D2` or `D2rev` or `S2`.  The pointed census
  `bool_irrefl_witness_classification` remains, and excludes `D2rev`
  by fixing the designated pair.  Collision already identified the
  two orientations; this names the transposition that identification
  forgets.
- **Class**: theorem.
- **Deps**: none. **Assumptions**: the one-relation signature of
  `paper/primitive_difference.md` S1; the census quantifies over
  pointwise-decidable relations (`[∀ x y, Decidable (r x y)]`).
- **Python**: `primdiff.json:transposition`;
  `test_carrier_swap_carries_each_orientation_onto_the_other`,
  `test_carrier_swap_twice_is_identity_and_restores_both`,
  `test_both_orientations_have_the_same_symmetrization`,
  `test_carrier_swap_is_auto_of_S2_not_of_either_orientation`,
  `test_unpointed_irrefl_nonempty_census_on_two`,
  `test_transposition_report_agrees_with_the_live_maps`.
- **Lean**: `PrimDiff.swap_carries_D2_to_D2rev`,
  `PrimDiff.swap_twice_restores_D2`,
  `PrimDiff.swap_twice_restores_D2rev`, `PrimDiff.sym_D2_eq_S2`,
  `PrimDiff.sym_D2rev_eq_S2`, `PrimDiff.swap_auto_of_S2_not_of_D2`,
  `ObserverInventory.swap_not_auto_of_D2rev`,
  `PrimDiff.bool_irrefl_nonempty_classification`.
- **Axioms**: within `{propext, Quot.sound}`.
- **Falsifier / boundary**: a non-identity permutation of the
  two-element carrier that preserves `D2` or preserves `D2rev`, or an
  inhabited decidable irreflexive relation on that carrier outside
  `{D2, D2rev, S2}`.  Carrier 3 is outside this census.

### CL-PD-INVENTORY
- **Statement**: the nine slots (`carrier`, `local_state`, `support`,
  `defect`, `reversal`, `closure`, `residual`, `maps`, `terminal`)
  are a declared classification of existing objects on the
  two-element carrier.  Every decidable irreflexive relation equals
  empty or `D2` or `D2rev` or `S2`.  Witness assignments are present
  as data: the zero assignment and the one-oriented assignment both
  exist, the latter has presence `D2`, and neither is derived as the
  unique inhabitant.  A structure can assert its pair while failing
  irreflexivity (the one-point self-difference), and on the sealed
  side a collision exists without any protected law and rises to
  obstruction only relative to `Irrefl` — the two defect readings
  stay distinct.  Relation `Transpose` is an involution, carries
  `D2` onto `D2rev`, and agrees with pushforward along `Bool.not` on
  `D2` while remaining a different operation.  `edgeCount` and
  `isSymBit` are distinct residuals.  Empty and `D2` are both legal
  irreflexive local states, so irreflexivity does not determine the
  local state; no next state is singled out by the `Irrefl` law
  alone.  (An earlier draft said no next state is "a function of"
  the carrier and local state — a non-sequitur, since the identity
  is such a function; narrowed to the underdetermination statement,
  which is what the cited theorems prove.)
- **Class**: theorem (census and residuals) + declared metatheory
  (slot classification).
- **Deps**: `CL-PD-TRANSPOSE`. **Assumptions**: the one-relation
  signature of `paper/primitive_difference.md` S1; the census
  quantifies over pointwise-decidable relations
  (`[∀ x y, Decidable (r x y)]`); slot names are a declared
  classification, not a derived carving.
- **Python**: `observer_inventory.json`;
  `test_nine_slots_and_no_duplicates`,
  `test_irrefl_census_is_exactly_the_four`,
  `test_witnesses_are_data_not_a_unique_inhabitant`,
  `test_reversal_transpose_and_swap_agree_on_D2_and_differ`,
  `test_defect_collision_is_not_source_irreflexivity`,
  `test_residuals_are_not_unique`,
  `test_inventory_report_flags`,
  `test_runner_byte_stable`,
  `test_every_named_elsewhere_citation_is_declared_in_the_source`.
- **Lean**: `ObserverInventory.slot_count`,
  `ObserverInventory.slots_nodup`,
  `ObserverInventory.empty_irrefl`,
  `ObserverInventory.empty_ne_D2`,
  `ObserverInventory.bool_irrefl_full_classification`,
  `ObserverInventory.witnesses_are_data`,
  `ObserverInventory.collision_is_not_obstruction`,
  `PrimDiff.collapse_unobstructed_without_fidelity`,
  `PrimDiff.obstruction_under_irrefl`,
  `ObserverInventory.transpose_involutive`,
  `ObserverInventory.transpose_D2_eq_D2rev`,
  `ObserverInventory.transpose_D2rev_eq_D2`,
  `ObserverInventory.pushNot_D2_eq_D2rev`,
  `ObserverInventory.transpose_eq_pushNot_on_D2`,
  `ObserverInventory.transpose_ne_pushNot`,
  `ObserverInventory.closure_empty_family_is_identity`,
  `ObserverInventory.residuals_not_unique`,
  `ObserverInventory.swap_not_auto_of_D2`.
- **Axioms**: within `{propext, Quot.sound}`.
- **Falsifier / boundary**: a fifth decidable irreflexive relation on
  `Bool`; equality of `zeroW` and `oneW`; `Transpose D2 ≠ D2rev`;
  extensional equality of `Transpose` and `pushNot`; a unique
  residual that is both `edgeCount` and `isSymBit`; a proof that
  `Irrefl` determines the local state on `Bool` (any two irreflexive
  local states equal).  Carrier 3 is outside this census.
  History-bearing fillings of the terminal slot are named citations,
  not theorems of this claim.

### CL-G1-TERMINAL-20260826

- **Statement**: the current terminals are
  `LOCAL_STRATEGY_CLASS_DEFINED`, `FIVE_STRATEGIES_CLASSIFIED`,
  `T5_PROFILE_CORRESPONDENCE_PROVED`,
  `CAPACITY_APPLIES_TO_EVERY_CLASS_MEMBER`,
  `G1_CLASS_EXCLUSION_PROVED`, `G3_REMAINS_CONJECTURE`,
  `G4_REMAINS_CONJECTURE`,
  `OB1_UNCHANGED`, and `OBJECT_LANGUAGE_GENERATOR_NOT_IN_SCOPE`, plus
  explicit H1-H6 done/skipped dispositions. The earlier three-line terminal
  is withdrawn as the current complete block; its generation theorem remains
  supported and its two bounded repair findings remain historical evidence.
- **Class**: declared metatheory.
- **Deps**: `CL-G1-LOCAL-CLASS`, `CL-G1-T5-GENERAL`,
  `CL-G1-CAPACITY-APPLICATION`, `CL-G1-CLASS-EXCLUSION`,
  `CL-G1-FIVE-STRATEGIES`, `CL-G1-G3-COUNTEREXAMPLE`, and
  `CL-G1-G4-FINITE`.
- **Assumptions**: each component retains the exact assumptions and evidence
  class in its own entry; this terminal aggregates them without flattening.
- **Python**: `code/derivation/g1_class_receipt.py` recomputes the concrete
  strategy payload, validates the pinned inputs, records the G4 withdrawal,
  and exports the exact terminal list.
- **Axioms**: theorem components lie within `{propext, Quot.sound}`; the
  G4 conjecture has no Lean claim.
- **Evidence**: `artifacts/g1_class_receipt.json`, which binds 34 new theorem
  reports, exact source declarations, supporting payloads, bounds, OPEN and
  WITHDRAWN sentences, base commit, task hash, prompt hashes, and Python lock;
  `artifacts/completion_dependency_graph.json` independently resolves the
  source statement and explicit kind/role of every new theorem report.
- **Falsifier / boundary**: a missing terminal boundary, stale supporting
  payload, unresolved theorem name, changed pinned input that regenerates
  without failure, or reintroduction of a chain G4 terminal without a live
  adapter. OB-1 remains open outside the declared class.


## Publication reconciliation claims (2026-09-08)

Entries added while reconciling the paper with its evidence.  Each names
the paper passage it governs.

### CL-IDENTITY-NOT-PROFILE
- **Statement**: Internal identity is the datum index, never the profile:
  a valid response separates the challenged pair by profiles while other
  distinct data may stay observationally equivalent.  Witness: in reading
  F, the first-round `mu2` minimum that admits one unary form and its
  instance on datum 1 (cost (2, 1)) separates the required pair (1, 2)
  and leaves indices 0 and 2 distinct with identical empty profiles
  (profile sizes [0, 1, 0]; collapsed pairs {(0, 2)}).  Governs the
  section 10.11 sentence withdrawn 2026-09-08.
- **Class**: counterexample.
- **Deps**: CL-3-UNIQUE-MU2-F, CL-3-COST1-IMPOSSIBLE. **Assumptions**:
  shared + bounds.
- **Python**: `test_identity_is_index_not_profile` (the delta is in the
  engine's first `mu2` minimum family; the profiles and the collapsed
  pair are recomputed).
- **Lean**: `deltaU0F_valid` (the response is valid), `U0F` (its result),
  `cost1_insufficient_F` (no one-item response); the collapse of 0 and
  2 in `U0F` is decided by the Python recount, not stated in Lean.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a proof that every valid first-round response
  separates every pair of distinct data — refuted by the witness.

### CL-TRANSITION-STEPS-VS-RESPONSE-ROUNDS
- **Statement**: The engine's depth counts transition steps, and a step is
  either a separation response or an external supply with an empty
  response; the requested depth of 15 was reached in transition steps.
  Over the completed `mu2` leaves, the separation-response rounds per
  leaf are 10 (527 leaves) and 11 (41) in L, and 10 (268), 11 (605) and
  12 (12) in F; every exported edge satisfies child depth = parent depth
  - 1. The seed prompt's "fifteen accepted augmentation rounds" were
  therefore not reached as response rounds, and no run under a
  response-only counter has been made.
- **Class**: finite computation.
- **Deps**: CL-TREE-MU2-COMPLETE. **Assumptions**: shared + bounds.
- **Python**: `test_completed_mu2_leaves_carry_ten_to_twelve_response_rounds`
  (recount over `full/tree_L_mu2.json.gz` and `full/tree_F_mu2.json.gz`).
- **Lean**: --. **Axioms**: --.
- **Falsifier / boundary**: a completed leaf whose response-round count
  is outside the stated distribution; a run under a response-only
  counter would be a different result.

### CL-REGISTER-SCOPE
- **Statement**: The residual register of section 11 is closed for the
  statements its rows asked for under a renaming of the datum indices
  with the forms fixed (R6, R7); the form-action components — collapse
  transport under the full two-bijection isomorphism — are proved
  separately (`collapsed_transport`, `collapsed_renameForms`,
  `collapsed_renameDataForm`), and the executable components — the
  correctness of the reported count, the identification of the mapped
  candidate list with the engine's pair enumeration, minimum-family
  transport under a form bijection, and the conversion of relation-level
  congruence to equal canonical-key class sets — are finite computation
  with CL-ISO-SOUND.  "All residuals closed" means exactly this.
- **Class**: theorem.
- **Deps**: CL-COUNT-INVARIANCE, CL-TRANSITION-EQUIVARIANCE, CL-ISO-SOUND.
  **Assumptions**: shared.
- **Python**: `test_canonical_invariant_under_rename`,
  `tests/test_equivariance.py`.
- **Lean**: `collapsed_rename`, `collapsedCount_rename`,
  `transStep_rename_fwd`, `collapsed_transport`, `collapsed_renameForms`,
  `collapsed_renameDataForm`.
- **Axioms**: `propext, Quot.sound`.
- **Falsifier / boundary**: a form bijection under which collapse or a
  transition fails to transport; the executable components remain
  computational until proved.
