# Change log

Material changes only, newest last.

## 1. 2026-08-11 — Repository scaffold and plan

`CLAUDE.md` (execution plan, boundary, discipline, gates, stop conditions)
committed before substantive work.  Prompt inputs carried byte-identically
(SHA-256 recorded in `paper.md` section 1).

## 2. 2026-08-11 — Canonicalization defect found and fixed pre-publication

The first canonical-form implementation permuted color-class members *in
place* instead of assigning them to color-ordered positions, so the
canonical key was not isomorphism-invariant: the two unary marks (and the
paired binary variants) failed to merge, reporting 6 Challenge 3 classes
in reading L instead of 3.  Caught by the first smoke run against the hand
analysis; fixed in `code/derivation/iso.py` (`_class_perms`); regression
locked by `test_mark_variants_are_isomorphic` and the brute-force
agreement test.  No published artifact ever contained the wrong counts.

## 3. 2026-08-11 — First full artifact generation

Challenges 0-3 computed for both admission readings; four external-policy
trees and two closed-system baselines exported; byte-determinism verified
by dual runs.

## 4. 2026-08-11 — Caller correction (10 points) applied

1. Blind protocol tightened: the post-hoc comparison with known
   mathematics, originally required as a final section, is withheld
   entirely; a blindness sweep confirms no external-theory terminology
   anywhere outside the read-only seed prompt.
2. Every minimality claim now states candidate bounds, cost measure, and
   whether uniqueness is absolute or bounds-relative (paper section 7;
   ledger entries CL-3-*).
3. `CL-UNBOUNDED-WITH-SUPPLY` renamed to
   `CL-REACHES-REQUESTED-DEPTH-WITH-SUPPLY`: reaching a finite requested
   depth does not prove unboundedness; the unboundedness statement is
   downgraded to a conjecture supported by the progress theorem.
4. Termination evidence corrected: `any terminal node` replaced by
   per-branch reports (terminal / open / budget-cutoff / round-cutoff
   branches, plus an every-maximal-branch-terminates flag) in
   `CL-BRANCH-REPORTS` and `CL-ENDOGENOUS-TERMINATION`.  A related
   engine defect was found and fixed: a closed-system node reaching the
   fixpoint exactly at the round limit had been labeled as round-cut
   (`completed`) rather than terminal; terminal-ness is now checked
   before the round cutoff (`test_closed_system_terminal_at_round_
   boundary`).
5. Fresh-data supply reclassified as an explicitly declared external
   continuation policy (engine docstring, paper sections 3.10, 8.1).
6. `supply=False` runs retained and labeled as the closed-system
   baseline.
7. -9. New research obligation answered (paper section 9): the endogenous
   generator exists (least collapsed pair; token-blind; no fresh data; no
   new goal kind), is implemented deterministically
   (`next_endogenous_challenge`), preserves requirement satisfaction, and
   provably terminates at the all-pairs-separated fixpoint within
   n(n-1)/2 rounds (new Lean lemma `allPairs_length`; closed-system
   baselines terminate in 1 / 3 rounds with every maximal branch
   terminal).  Beyond the fixpoint no endogenous continuation exists: the
   native tower stops; further continuation requires the external policy.
10. Statement classification switched to the eight-way vocabulary
   (declared metatheory / definition / finite computation / theorem /
   bounded theorem / conjecture / counterexample / unresolved) throughout
   the paper and ledger.

Also in this pass: `cost1_insufficient` generalized in Lean to any
form-less, instance-less regime (now absolute over the item grammar and
instantiated for both readings); reading-F existence witness
`deltaU0F_valid` added; exported theorem count 42.

## 5. 2026-08-11 — Second caller correction (10 points) applied

1. `wfCtx` strengthened: well-formed contexts now require the slot count
   to equal the form's arity (`c.slots.length = r.forms.getD c.form 0`).
   Affected Lean proofs repaired (separation witnesses, `mark_progress`
   including a new `getD_append_lt` lemma, `separable_of_subrules`); the
   Python context enumeration already produced only arity-length slot
   tuples by construction.
2. Lean is now labeled a token-erased abstraction, never a mirror, and
   the abstraction is proved: `Derivation/Erasure.lean` adds a
   token-aware state with deduplicating admission and the simulation
   theorems `erase_step` / `erase_replay` (a duplicate admission erases
   to a bare supply, a proved no-op).  A first draft of the history-level
   statement was vacuous (`lhs = lhs`); it was caught and replaced by
   the genuine state-threaded statement before any claim cited it.
3. Claim scopes separated explicitly in paper and ledger: reading-L
   minimality Lean-proved; reading-F grammar-wide mu2 uniqueness is
   finite computation; Python class counts carry max_items=2 /
   max_arity=2; the arity-indexed `markK` family is its own theorem.
4. Every unboundedness claim removed (including the former conjecture):
   `mark_progress` is response existence for a supplied demand only;
   behavior beyond the exported depths is unresolved.
5. Claim ID renamed to
   `CL-REACHES-REQUESTED-DEPTH-WITH-EXTERNAL-SUPPLY`.
6. Fresh supply remains the declared external continuation policy;
   no-supply runs remain the closed-system baseline.
7. Termination is reported over all maximal branches (branch reports);
   no claim rests on the existence of one terminal node.
8. The counting laws (`strict_bounded_length`, `no_supply_round_bound`)
   are labeled conditional; the connection of their hypotheses to the
   transition system is recorded as computational and a Lean connection
   theorem as unresolved.
9. `separable_of_subrules` docstring and ledger weakened to exactly what
   is proved (witness transfer under a shrunken final rule set); the
   delta-level pruning corollary is recorded as computationally
   certified.
10. Axiom status stated exactly: no sorry, admit, or custom
   conclusion-producing axioms; standard `propext` and `Quot.sound`
   dependencies remain (44 per-theorem reports).

## 6. 2026-08-11 — Third caller correction (7 points) applied

1. Quotient-transition soundness repaired.  Raw least-pair challenge
   selection was not isomorphism-equivariant: on the regression regime
   (four data, one unary form, instances on data 2 and 3, collapsed
   pairs (0,1) and (2,3), renaming (2,3,0,1)) the canonical keys agree
   while the same-index least-pair selections produce non-isomorphic
   children (`test_least_pair_selection_is_not_equivariant`).  Replaced
   by one challenge branch per automorphism orbit of collapsed pairs,
   all non-isomorphic orbits retained (`automorphisms`, `pair_orbits`,
   `closure_challenge_orbits`); transition congruence under isomorphism
   is tested exhaustively over all renamings of the sample regimes.
   Every tree, count, role report, artifact, and dependent claim was
   regenerated: the numbers are unchanged and
   `expansions_with_multiple_orbits = 0` in every exported run — the
   defect was latent within the explored bounds.
2. Continuation rule reclassified: "endogenous generator" renamed to
   *declared pair-separation closure policy*; `CL-ENDOGENOUS-*` replaced
   by `CL-CLOSURE-*`; the paper now states that no object-language
   endogenous demand generator was derived and that under the declared
   policy the fixed finite datum set reaches an all-pairs-separated
   fixpoint; "native tower stops" replaced by "pair-separation closure
   terminates".
3. Lean/Python bridge repaired: instance, rule, and requirement
   admission in Lean now use deduplicating insertion (`insertNew`),
   matching the Python set semantics; the erasure simulation was
   re-proved over the new semantics, so repeated admission of every
   event kind agrees.  The bridge is stated as an abstraction with a
   proved simulation, not as an exact mirror.
4. `wfCtx` gained the hole requirement (`none ∈ c.slots`), making the
   Lean context space coincide with the Python enumeration; witnesses
   and transfers repaired.
5. Claim language corrected: "Least" removed from the paper title (and
   the new PR title); the result is stated as beginning from an opaque
   seed under declared external challenges; "admission never increases
   expressive power" weakened to "admission need not increase expressive
   power"; the remaining unboundedness sentence removed from the
   `Progress.lean` module comment; the counting laws remain labeled
   conditional.
6. Independent verification added: pinned dependencies
   (`requirements.txt`), GitHub Actions (`.github/workflows/verify.yml`)
   running pytest with independent 95% line and branch gates
   (`ci/check_coverage.py`), mypy strict, `lake build`, forbidden-token
   and axiom audits (`ci/check_lean_audit.py`,
   `ci/check_axiom_report.py`), prompt-hash verification
   (`ci/check_prompt_hashes.py`, pinning both the supplied and the
   repository-canonical bytes), and artifact regeneration with content
   comparison (`ci/compare_artifacts.py`).
7. Generated-artifact duplication reduced: trees now export as
   normalized DAG records (root history, per-node regime hashes, edge
   event-deltas, parent references — no per-node histories); committed
   summaries carry statistics and the SHA-256 of each full export; full
   exports live under `artifacts/full/*.json.gz`, reproducibly
   compressed, and `verify_full_export` replays every node from the DAG
   (the exported artifact footprint dropped from ~17 MB to ~320 KB).

## 7. 2026-08-12 — Fourth caller correction (4 points, PR #2 review) applied

1. Every DAG edge is now certified, not only one creation edge per node.
   Merge edges carry explicit datum/form bijections, computed at attach
   time (`find_iso`, built on `canonical_witness`) and re-verified before
   storage; `verify_full_export` replays every edge — creation edges must
   reproduce the exact stored child, merge edges must map the replayed
   result exactly onto the stored representative through their stored
   bijections (bijectivity checked, tampered events rejected rather than
   crashing).  Required regression added: one invalid merge edge is
   rejected even when every node retains a valid creation path
   (`test_verify_rejects_invalid_merge_edge_despite_valid_creation_
   paths`), plus corruption of merge events and deletion of the
   certificate.
2. `node_budget` renamed to `pre_expansion_node_guard` everywhere
   (engine parameter, tree metadata, bounds keys, CLI flags, statuses
   `frontier_budget` → `frontier_guard`, branch-report key
   `budget_cutoff_branches` → `guard_cutoff_branches`, paper and
   ledger), because the guard is checked before expansion and an export
   may slightly exceed the guard value: it is not a strict node cap and
   is no longer named like one.
3. Transition equivariance rescoped honestly: no general transport of
   candidates, costs, validity, minima, or children under regime
   isomorphism is claimed; those transports are recorded as unresolved.
   The surviving classification is finite adversarial evidence —
   exhaustive congruence over all renamings of the sample regimes
   including the adversarial regression, plus a verified isomorphism
   certificate on every exported merge edge.
4. The list-vs-set gap between Lean and Python closed by proof:
   `Derivation/Ext.lean` adds the membership-extensional relation
   (`SetEq`, `RegimeExt`) with transport theorems for derivability,
   context well-formedness, collapse, separability, item and delta
   application, and response validity.  The bridge claim now rests on
   erasure simulation plus membership extensionality — never on
   duplicate-admission idempotence alone.  Exported theorem count 51.

Artifacts, ledger, paper, and CI receipts regenerated; tree statistics
unchanged except the status rename.

## 8. 2026-08-12 — Paper suite frozen

`paper.md`, `paper_claim_ledger.md`, and this log written against the
frozen artifacts; final gate run recorded in `paper.md` section 12.

## 9. 2026-08-12 — Frontier Run 006 correction pass (PR #7 verdict)

One narrow correction pass on `paper/refusal_as_difference.md` and its
evidence, per verdict; the protocol class is unchanged and no research
search was reopened.

1. Terminal split by target: FREE_REFUSAL_BRIDGE_FAILS /
   UNIQUE_MINIMUM_WITNESSED_BRIDGE_IN_CLASS /
   MULTIPLE_MINIMUM_WEAKER_BRIDGES.  The artifact shows one minimum
   protocol (datum + relation rule) for the witnessed milestones under
   both cost orders; the ties and the order disagreement live at
   two-carrier and separable/oriented pair.  The earlier single-line
   MULTIPLE_MINIMUM_BRIDGES conflated these targets.
2. New Lean theorem `min_witnessed_route_closes` verifies the actual
   computed minimum witnessed route on a state type with no tag store
   and no result store (receipt as a literal coproduct).  `stepP` is
   relabeled a sufficient, non-minimum construction; its comment no
   longer claims a binary result algebra (it has no result store).
   Axiom reports: 135, within {propext, Quot.sound}.
3. Import channels scoped by target (constructors — result outcomes;
   tags/relations — carrier profiles; relations — witnessed relations);
   the target-independent three-channel reading is withdrawn.
4. `normal_form_check` strengthened to test exactly the claims made:
   added separable/oriented pair → tag-or-relation and result
   distinction → binary algebra checks (all empty in class); claims and
   checks now match one-for-one.
5. The implication matrix renamed to the nine-state-level-notion
   matrix; the twelve declared notions remain, with histories, states,
   event classes, and orientation reported separately at their own
   levels.
6. Proto-numeral headline scoped: the declared reflective protocol
   *realizes* a successor chain (horizon-free); refusal itself derives
   no numerals.  Initiality remains open (F4).

Tests 129 → 131; coverage 99.10% line / 97.29% branch; artifact
`refusal_frontier.json` regenerated deterministically.

## 10. 2026-08-12 — F5 run: the composite generator

New research leg answering F5 of `paper/refusal_as_difference.md`:
`paper/endogenous_generator.md`, `lean4/Derivation/Generator.lean`
(16 theorems), `code/derivation/generator.py`, `code/run_generator.py`,
`tests/test_generator.py`, `artifacts/generator.json`, CL-G-* ledger
entries, CI regeneration line.

Terminal, split by claim: ENDOGENOUS_GENERATION_PROVED /
OBJECT_LANGUAGE_GENERATOR_NOT_IN_SCOPE /
ENDOGENOUS_REPAIR_FAILS_IN_DECLARED_CLASS /
GENERATION_REPAIR_EXCLUSION_IN_CLASS.  The composite of reflective
growth and pair-separation closure fires at every round from the third
on, horizon-free, with no per-round external act -- the first such
generator exhibited in the development, without a minimality or
uniqueness claim, and not genesis from `<>`.  Its obstruction set is
identified exactly (interior pairs, an iff).  Over the declared
five-strategy repair class within the 15-round computation, no branch
fires, repairs, and never
imports: presence marking is vacuous, per-pair marking is outgrown by
every finite marking (a fresh import per repair, forever), valued
marking kills generation at the price of identity-grade observation,
and depth-2 observation is outrun in the deep interior (Lean instances
at lengths 4 and 5; general depth-d open as G2).  The direct
transposition of interior points 1 and 2 is proved not to preserve the
successor relation; full rigidity and the quantified automorphism
claim are not established here.

Axiom-hygiene note recorded for the metatheory: `omega` on conjunction
or disjunction *goals* introduces `Classical.choice` in this
toolchain; all such uses were restructured (goal-splitting, explicit
trichotomy) and the build's 151 axiom reports remain within
{propext, Quot.sound}.

## 11. 2026-08-12 — Native primitive-difference interface

Externally imposed challenge (caller request): a self-contained,
adapter-independent theorem package —
`lean4/Derivation/DiffInterface.lean` (core-only imports, 35 exported
theorems), mirrored in `code/derivation/diff_interface.py` with
artifact `diff_interface.json`, documented in
`paper/difference_interface.md` with CL-DI-* ledger entries.

Pipeline delivered and proved: typed difference operation with
equivalence-before-quotient (the quotient consumes the Setoid built
from the equivalence proof, so the ordering is dependency-enforced);
retained / observer-zero / protected as independent predicates with
active obstruction their conjunction; factored bare reflection
(embedding + retraction, a point outside the old live image, declared
parent, live-scoped preservation, and an explicitly retained,
protected, observer-zero parent/new pair) certifying an active
obstruction; map-saturated closure over abstract demand predicates
under declared preserving maps (no inverse or composition assumed),
preserving old distinctions and strictly decreasing the concrete
declared measure.  Extension requests are represented as proposal data,
never applied.  Fuel termination follows from the generic measure-based
driver; the concrete two-element demand bound is a separate fact.  A
uniform pointwise successor-step family is proved; no trace object or
finite-prefix induction theorem is claimed.  Every Boolean view over
three protected points remains obstructed (pigeonhole; exhaustive over
all eight views); proposal data is available, but no decision theorem
forces its selection.  Countermodels for freshness, tagging, an edge, a
new hash, and repetition now each include an unprotected stage and an
explicit inactivity proof.

Further axiom-hygiene findings recorded: `List.eq_nil_iff_forall_not_mem`
depends on `Classical.choice` in this toolchain (replaced by a
cases-based proof); the build's 186 axiom reports remain within
{propext, Quot.sound}.

## 12. 2026-08-12 — Represented progress without an outside

Externally imposed challenge (caller assignment): can all load-bearing
causes of represented progress themselves be represented, with no
hidden evaluator, selector, or source outside the replay semantics?

New leg: `lean4/Derivation/Represented.lean` (native, core-only, 48
exported theorems), `code/derivation/represented.py`,
`code/run_represented.py`, `tests/test_represented.py`, artifact
`represented.json`, `paper/represented_progress.md`, CL-RP-* ledger
entries, CI regeneration line.

Terminal, split by claim: REPRESENTED_KERNEL_EXISTS /
HIDDEN_INPUT_CLASSES_REFUTED /
CERTIFICATION_BOUNDED_BY_PANEL_QUOTIENT.  One kernel carries every
load-bearing input in its state or history (evaluator, requirement,
scheduler, tie-break, fresh names, fuel, authorization, stopping
condition) and satisfies the eight target theorems: replay
determinism/composition; the support theorem (result-affecting data
occur in the represented support); complete tied successor families
with replay-equivalence invariance; repair soundness (discharge +
preservation); augmentation soundness (exact conservativity equation +
verified expressive increase); represented progress (repair family
non-empty or certified obstruction with accepted canonical
augmentation; budget and license isolated as the represented
load-bearing hypotheses; refusal only with a verified certificate);
closure (new violations only from represented require events);
productivity (one prefix-compatible unbounded run with carrier
`range (k+1)` derived through the acceptance-guarded kernel) separated
by proof from per-length witnessing (a represented Koenig failure).
Internal certification is priced exactly: equivalent to the panel's
joint separation, refuted as correspondence, non-monotone under panel
extension.  The eight required countermodels each consume exactly one
unrepresented input and are machine-checked; obstruction requires
exhaustive failure of the declared response menu by definition, and
the incomplete-search countermodel shows why.

The `admit` event constructor is spelled `admitTok` (forbidden-token
audit).  Test count 155 -> 175; the build's 234 axiom reports remain
within {propext, Quot.sound} with no new hygiene exceptions.

## 13. 2026-08-12 — Represented-progress correction pass (PR #10 verdict)

One focused correction pass; the research programme is unchanged.

1. Terminal scoped to a fixed kernel constitution: the event grammar,
   sep/sat laws, response menu, acceptance predicates, and history
   producer are fixed metatheory; the theorems cover *runtime* inputs
   relative to that fixed `step` semantics, and the constitution does
   not derive itself.
2. Python/Lean carrier mismatch closed: every negative token, index,
   view member, requirement endpoint, mark point, budget, and note is
   rejected in the mirror, matching Lean's `Nat`; negative-domain and
   malformed-event tests added.
3. The claim that bounded runs terminalize in refusal is withdrawn:
   refusal records verified same-level exhaustion and is
   non-absorbing; run termination belongs to the metatheoretic history
   producer.
4. "Augmentation conservativity" renamed: `aug_preserves_satisfied`
   preserves satisfied positive requirements; old non-separation
   judgments are not preserved — changing them is the licensed content
   of augmentation.
5. RP8 scoped to an explicitly supplied prefix-compatible event
   stream (never called endogenous); per-event acceptance and
   per-stage quiescence verified exhaustively to the 15-round bound.
6. No-hidden-choice scoped to `repairFamily`; the structural branch's
   canonical augmentation `[i]` takes its orientation from the
   ordered, recorded requirement — a represented datum and a stated
   scoping, with no retained augmentation family claimed.
7. The evaluator panel classified as an explicit certification
   argument, not replay-integrated.
8. Countermodels split: hidden runtime inputs (scheduler, fresh-name
   source, hidden evaluator, order-sensitive tie-break) versus
   neighboring semantic/inference failures (incomplete search,
   destructive rewrite, repetition-as-progress, König witnesses).
9. Support wording changed to operational-support factorization, not
   full result causation.

Tests 175 -> 177; artifact, ledger, paper, and CI receipts
regenerated; 234 axiom reports remain within {propext, Quot.sound}.

## 14. 2026-08-12 — Ultra closure run

One autonomous run composing the sealed estate (PRs #1-#10) into the
final native spine: `paper/native_derivation_completion.md` (verdict,
both rules, event source, constitution, autonomy, initiality,
adversarial audit), `paper/native_derivation_map.md` (one row per
bridge), four Lean modules (Completion, NoOutside, Constitution,
Initiality; 57 new exported theorems, 291 total, all within {propext,
Quot.sound}), the completion Python mirror with source-derived
inventory, and five deterministic artifacts including the receipt.

Terminals: RELATIVE_REPLAY_CLOSURE_ONLY;
EVENT_SOURCE_INTERNALIZED_RELATIVE_TO_FIXED_INTERPRETER;
KERNEL_CONSTITUTION_INTERNALIZED_RELATIVE_TO_FIXED_INTERPRETER;
KERNEL_CONSTITUTION_REMAINS_META (the single OPEN bridge);
INITIAL_KERNEL_PROVED (declared class);
ABSOLUTE_NO_OUTSIDE_UNFORMULABLE.  FULL_NATIVE_COMPOSITION not
claimed.  Highlights: the driver reproduces the previously supplied
tower stream from represented state (the supplied-vs-endogenous
laundering closed in the strong direction); the extension family
retains both orientations (strengthening the PR #10 scoping); refusal
proved object-inert; Rule 1 reduced to preservation + declared
fidelity; Rule 2's dichotomy proved operationally and its absolute
form recorded as unformulable; the kernel's own description executes
to the sealed step under the fixed family interpreter; the kernel is
the unique compliant and initial member of its declared 64-member
class.  No sealed theorem or claim was altered.

## 15. 2026-08-12 — Ultra-closure correction pass (PR #11 verdict)

One focused correction pass; no new research phase.

1. Artifacts regenerated against the final paper and ledger state,
   with the correction-pass edits applied first.
2. Generation scoped honestly: `towerGen` now invokes the next-family
   interpreter on the replayed state; the result is described
   everywhere as state-derived, prefix-compatible generation under
   metatheoretic iteration and a fixed interpreter; the
   internal-trigger claim (ladder level 4) is withdrawn as NOT
   attained.
3. Freshness proved on the tower invariant
   (`freshName_fresh_on_tower`) and refuted in general
   (`freshName_not_fresh_generally`).
4. Terminal renamed: INITIAL_KERNEL_PROVED ->
   UNIQUE_PROBE_COMPLIANT_DESCRIPTOR_IN_DECLARED_TOGGLE_CLASS; a
   six-probe singleton and one split retract do not prove categorical
   initiality, and none is claimed.
5. The common obstruction now has independent retention, protection,
   and zero conditions (`obstC_conditions_independent`); the kernel
   transport's identification of retention and protection is stated.
6. S2 symmetry scoped: relation store swap-invariant; whole state not
   (`s2_state_not_swap_invariant`).
7. `rule1_trichotomy` renamed `rule1_repair_or_extension`: the action
   alternative is binary; refusal is a parallel non-absorbing record;
   budget/license execution remains a separate gate.
8. Nat agreement enforced for every constitution descriptor: the
   mirror's `interp_step` rejects negative tokens, endpoints, points,
   and view members unconditionally, so disabled guards can never
   license states unavailable in Lean.
9. Graph scope stated: one OPEN edge in the declared graph; no claim
   that the graph exhausts every possible bridge.

Axiom reports 291 -> 295, all within {propext, Quot.sound}.

## PR #12 — Primitive Difference contact and passage, Phase I corrections

Pre-contact correction pass over PR #11's strongest labels
(full audit: `paper/pr11_correction_ledger.md`).  Ten claims audited;
two defects found and repaired:

1. **C10 (cross-language exactness), refuted and repaired.**  Old
   claim (42a33d9 item 8): "disabled guards can never license states
   unavailable in Lean."  Countermodel: descriptor `(T,T,F,F,T,T)`,
   world `{data=(10,20), views=((0,),), reqs=((0,1),), budget=0}`,
   event `mark (1,) 0` — a Lean no-op but a Python state change to
   budget `-1` (unsaturated subtraction under a disabled budget
   gate).  Replacement: the mirror's two decrement sites now saturate
   (`max(0, budget - 1)`); Lean pins the exact shared semantics
   (`Horizon.interp_budget_bound`, `Horizon.budget_saturation_noop`,
   `Horizon.mark_saturation_all_descs`); the Python suite asserts the
   identical facts over all 64 descriptors on the declared basis.
   Affected claims: 42a33d9 item 8 (recorded here as refuted; left in
   place as history), `interp_step` docstring.

2. **C6 (horizon lawfulness), closed upward.**  Old state: the only
   Lean lawfulness fact for the generated run was the stage-3
   quiescence instance, while CL-NC-AUTONOMY spoke of "lawfulness
   across extension" citing a theorem with no lawfulness conjunct.
   Replacement: `Derivation/Horizon.lean` proves the complete record
   characterization of the generated world at every stage
   (`worldAt_spec`, by induction) and derives quiescence,
   well-formedness, and per-event acceptance at every horizon
   (`worldAt_quiescent`, `worldAt_wf`, `block_all_accepted`,
   `genesis_accepted`), lifted to the driver (`gen_quiescent`,
   `gen_wf`).  Affected claims: CL-NC-AUTONOMY (rewritten, old defect
   recorded inside the entry).

Verdicts C1, C2: hold as labeled.  C3, C4, C5, C7, C8, C9: already
corrected by 42a33d9; re-verified against current Lean statements.


## PR #12 — Phases II–IX: characterization, contact, passage, growth

1. Native characterization (blind, committed before any contact
   reading): nine candidate readings, 72-cell implication matrix (17
   proved implications, 51 compiled minimum countermodels, 4 OPEN
   located cells with exact scope), genuine categories with proved
   laws, `d2_initial` as a true universal property, the orientation
   fork retained, and the observer branching theorem
   (`no_terminal_pres`).
2. Contact: the declared package is absent; terminal
   CONTACT_INPUT_ABSENT recorded with a runtime check; the native
   kernel interface committed as the fixed target of any future
   collision.  No contents invented.
3. Apartness refinement (caller directive, mid-run): positive
   apartness with indistinguishability proved an equivalence;
   minimal insufficiency countermodels at carriers 1, 2, 3; the
   orientation/apartness separation; the exact operation-preservation
   characterization (identity only; identity and swap; constants
   neither; closure iff generators).
4. Passage: the full arrow chain with per-arrow statuses; the
   four-condition active obstruction (observation declared vs
   pre-observational, a refinement over the sealed three-condition
   reading, with agreement and divergence proved); P1–P8 including
   the two-rule theorem — at an active obstruction the response
   universe never runs dry: same-level repair or certified
   exhaustion plus a provably nonempty extension family.
5. Growth: the first graph grows by iterated
   obstruction-and-response, characterized at every horizon; the
   0-, 1-, 2-, 3-simplices grow under horn-guarded declared cell
   admission with replayable creation records; named invariants
   (ladder invariant, connectivity residue, occurrence alternation
   number, cut census, orientation residue, budget trichotomy);
   d²=0 under the declared calculus with the convention proved
   non-forced.  Higher structure: admitted, never forced.
6. New claims CL-PD2-* in the ledger; papers
   `primitive_difference_contact.md`,
   `primitive_difference_passage.md`, `primitive_difference_map.md`.


## PR #12 — Phases VII–VIII and completion

1. Controller category (Phase VII): the six-toggle proxy replaced by
   a genuine 1024-member variable-event-grammar class with a
   simulation category (laws proved).  Initiality REFUTED by the
   constant-simulation countermodel, surviving restriction to the
   live subcategory; NONUNIQUE_CONTROLLER_FAMILY proved (live census
   128; refusal is response-invisible); strict refinement excludes
   constants but global uniqueness still fails (invariant-twist
   countermodel); uniqueness holds exactly on the genesis-reachable
   orbit.  Agreement is a replay theorem, not a categorical one.
2. Interpreter boundary (Phase VIII): tower persistence proved by
   finite diagonalization (every finite closure has a new top);
   universal code/evaluator exact for the declared family; the
   typed-refusal top was initially described as closing by partiality
   what totality cannot (this necessity claim is withdrawn below);
   verified self-description alongside finite non-exhaustion; and the
   boundary formalized as a Primitive Difference (candidates A and F
   satisfied, collapse obstructed, difference behaviorally grounded).
   Absolute no-outside not claimed.
3. Completion: receipt with ten terminals, five open obligations,
   the twenty-attack adversarial record, and the two
   withdrawn-or-repaired claims; papers
   `primitive_controller_universality.md`,
   `primitive_interpreter_boundary.md`; ledger claims
   CL-PD2-CONTROLLER, CL-PD2-INTERPRETER, CL-PD2-RECEIPT.

## PR #12 review pass (request-changes verdict applied)

Fourteen-point correction pass; no candidate search reopened, no
speculative idea deleted.  Old statements, countermodels/reasons, and
replacements:

1. Hosted CI red on artifact comparison: the receipt hashed
   CRLF-checkout bytes of `requirements.txt`; replaced by a
   line-ending-normalized hash (raw hashes retained for the
   `-text`-pinned `prompt/**` and `artifacts/**` files).
2. `prompt_pr12.md` claimed "verbatim" while summarizing the ultra
   prompt; the exact bytes are now committed as
   `prompt/ultra_prompt_pr12.md` and the receipt binds both; the
   0,1,3,3 → 0,1,2,3 reading is labeled ASSUMED_TYPO_CORRECTION.
3. Composition gap (blocking): the passage had no pre-retention
   witness store — `admitWit` created witness and retention
   together, so PRIMITIVE_DIFFERENCE_PASSAGE_COMPOSED overreached.
   Repaired by construction: separate `asserted` store and
   `assertWit` event; retention now requires assertion
   (`retention_requires_assertion`); `assertion_not_retained` is the
   pre-retention witness state; transport from candidate A proved
   (`assert_transport` via the `asserted_offdiag` invariant;
   `kernel_enters_preretained`; `retained_sub_asserted`).
4. `d2_initial` scoped: `PtdRel` has no irreflexivity, so the
   initiality characterizes the bare-witness reading W (free pointed
   object on one witnessed arrow); A-initiality is the restriction
   corollary; A's justification is `imp_a_d` vs `nimp_w_d` — the
   two arguments are no longer merged anywhere.
5. Native terminal rescoped: "within the declared nine-candidate
   signature, A is the weakest studied positive-witness candidate
   forcing endpoint inequality".
6. Interpreter terminals replaced: INTERPRETER_TOWER_PERSISTS →
   FINITE_CODE_FAMILY_NOT_EXTENSIONALLY_COMPLETE (the diagonal
   changes only the inert notes field; nothing about
   self-interpretation follows); INTERPRETER_BOUNDARY_IS_PRIMITIVE_
   DIFFERENCE → DECLARED_BOUNDARY_MODEL_SATISFIES_A_AND_F (the
   boundary model's relations are inserted by definition; no theorem
   links the uncoded occurrence to the missed function).  The
   stronger identification is retained as a frontier conjecture with
   its missing denotational/operational-grounding theorem stated.
7. `openTerminalPres2` was not open: closed constructively by
   `no_terminal_pres2` (free-point presentation gives every target
   two distinct commuting maps); positive fragment stays scoped to
   surjective presentations.  The earlier selection-principle
   frontier conjecture is superseded.
8. Graph provenance stated exactly: the driver SUPPLIES occurrences,
   assertions, retention, protection; the obstruction creates the
   observation column.  Graph genesis by obstruction is recorded as
   a frontier conjecture for a later experiment.
9. `horn2`/`horn3` renamed `shell2`/`shell3` (complete unfilled
   boundaries, not simplicial horns); `horn_guard_load_bearing` →
   `shell_guard_load_bearing`.
10. Higher-structure scoping: ladder proved only at dimensions 2–3
    (general recurrence a conjecture); `altNum` relabeled a
    statistic; path/no-cycle attributed to `graphAt_spec`, not
    V−E=1; D2-to-walking-arrow labeled a free completion.
11. Two-rule scoped grammar-relatively (the declared
    singleton-column universe supplies the separator; `setBudget 1`
    is declared self-funding); extension "loses nothing" replaced by
    the exact preservation statement; arrow count fixed at thirteen.
12. "51 minimum countermodels" → "51 finite countermodels; minimum
    carrier proved where cited".
13. Contact scope: this PR is the native characterization and
    passage; the external collision is deferred to a future PR with
    exact manifest and source hashes.
14. All artifacts, papers, ledger entries, and the receipt
    regenerated under the corrected statements.

## PR #12 next-goals pass (caller directive)

1. `d2_map_injective`: the unique map out of the two-element kernel
   is injective into every irreflexive pointed witnessed
   presentation; the hypothesis is not removable
   (`d2_map_not_injective_without_irrefl`).
2. One-edge attachment defined (fresh walking edge glued along a
   represented parent); every attachment policy is lawful at every
   stage, produces a tree, and preserves V−E=1 (policy-uniform
   theorems).
3. Path and star policies exhibited as non-isomorphic countermodels
   to forced global shape (decided over all carrier bijections at
   four occurrences).
4. Up defined as the complete family of legal extensions (one block
   per represented parent, never a selection); proved
   presentation-invariant; orbit-valued choices demonstrated where
   symmetry remains (star leaves one orbit; the oriented path rigid
   — undirected flip refused by the oriented stores).
5. The simplex ladder generalized to arbitrary finite dimension.
   *(Superseded by the audit repair below: `ladder_general` was
   renamed and NARROWED to `uniform_guarded_filler`, and it upgrades
   the review-pass conjecture only in that narrowed sense - guarded
   admission plus strict extension, not a dimension-general two-rule
   or homology claim.)*  Dimension-4 demonstration replayed in Lean,
   dimension 5 in Python; at this stage the general composite boundary
   vanishing remained open (superseded by Goal 4 below).

## PR #12 final repair pass (caller directive, 2026-08-13)

1. Receipt hashing made deterministic under explicit CRLF-to-LF
   canonicalization; for the current tracked inputs each result equals
   the Git blob hash.  The originally supplied CRLF
   rendering of the seed prompt is recorded as provenance; the
   blob/checkout distinction and content-mutation detection are
   tested.
2. Attachment policies are never clamped: `LawfulPolicy` carries
   the representedness proof; illegal parents meet the typed
   refusal `AttachOutcome.refusedParent`; the retired clamp is the
   recorded countermodel (`clamp_rewrote_input`).
3. Occurrence identity resolved: tokens (admission order) versus
   positions (relational identities); canonical fresh token proved
   fresh on every carrier; `length_not_fresh_countermodel` on the
   non-initial carrier `[1, 2]`; on canonical tree states tokens
   and positions provably coincide (`attachBlock_is_upBlock`).
4. Completeness made registry-relative and an iff
   (`up_iff_legal`); every Up block executes to a strict legal
   extension (`up_exec_eq`, `up_executes`).
5. Length equality replaced by a genuine positional renaming
   action with transport and replay commutation (`act_up_comm`);
   the old statement survives only as identical-carrier grammar
   uniformity; countermodels: equal size with equal family but no
   relating renaming; two legal equal-cost non-isomorphic
   extensions.
6. Generalized cells made well-formed: strict ascent in the shell
   guard; the legacy guard's `[0, 0]` pseudo-cell recorded as the
   required countermodel; well-formedness proved a replayed
   invariant (`wf_nreplay`).
7. `ladder_general` renamed and NARROWED to
   `uniform_guarded_filler`: a theorem about guarded admission and
   strict extension, not homology.
8. CL-PD2-LADDER and CL-PD2-LADDER-GENERAL reconciled in the
   ledger; at this stage the general composite vanishing remained OPEN
   (superseded by Goal 4 below).
9. Part II delivered: target-relative presentation compression
   (`Compression`, 22 theorems, axiom-clean) — factorization iff
   fiber-constancy with image-scoped uniqueness; coarsest-adequate
   quotient with exact universal property; witnessed descent
   failures; enlargement refinement with exact split
   characterization; absolute adequacy = injectivity; replay and
   digests non-evidential without a new separator; refinement
   non-unique with retained ties; strict chains bounded by the
   domain.
10. One axiom regression caught by the report and repaired:
    `omega` on a conjunction goal proves it classically; the
    conjunction is now split first, restoring
    propext/Quot.sound-only across all 707 reports.

11. Caller finals (stable content).  *(Overclaimed; corrected by
    the audit repair section below.)*  What was actually proved is
    the SUFFICIENCY direction and the quiescence iff.

## Audit repair gate (caller directive, 2026-08-13)

Four repairs required before the next derivation goal.

**A. "Stable content is exactly protected separation" was an
overclaim; withdrawn and replaced.**  The actual trace-stability
predicate is now DEFINED (`TraceStableSep`: separated after every
replay; `RestrictedStableSep`: after every replay in a syntactically
restricted fragment omitting occurrence admission, budget setting,
and license setting).  This makes no ownership claim; generated blocks
may contain `setBudget`.  Only SUFFICIENCY is proved
(`protSep_trace_stable`).  The CONVERSE IS FALSE, with the two
countermodels the audit demanded: an ABSORBED (halted) state, where
`replay_halted` makes every trace inert so an unprotected separation
is trace stable; and a LIVE but RESOURCE-BLOCKED state, where
`restricted_replay_inert_unfunded` shows no event in the stated
restricted fragment can change an unfunded observation, so an
unprotected separation is restricted-stable.  Instability is proved
to be witness-borne
(`separation_breakable`), and the residual gap - whether trace
stability implies protection on the live funded class - is recorded
as an unproved Prop (`openExactStabilityCharacterization`), never as
a theorem.  Ledger, receipt, module docstring, Python mirror, and
tests were all weakened together; `stableSep` was renamed `protSep`
because it names protected separation, not stability.

**B. Stale open obligation removed.**  `openTerminalPres2` was
closed constructively by `no_terminal_pres2` in the PR #11
correction pass but was still listed among the receipt's open
obligations.  It is removed and the artifact regenerated; the
receipt now carries four open obligations, and the test pins both
the count and the absence of the retired entry.

**C. Synthesis paper reconciled with the narrowed result.**  The
synthesis paper still described GENERAL_DIMENSIONAL_LADDER as an
open frontier conjecture about dimension-general recurrence.  It now
states the reconciliation explicitly: what is proved at every
dimension is the UNIFORM GUARDED FILLER
(`LadderGeneral.uniform_guarded_filler`) - guarded admission plus
strict extension in the standalone generalized calculus - which is
neither a homology claim nor a dimension-general transport of the
`ladder_dim2/dim3` two-rule reading.

**D. `i5_difference_grounded` renamed and narrowed.**  Its statement
was literally `family_missed`: it mentions neither the boundary pair
nor the uncoded occurrence, and connects neither to the missed
function.  It is renamed `i5_family_not_extensionally_complete` and
its docstring now says exactly what it does and does not carry.
`arbitrary_uncoded_assignment` further proves that a freely chosen
meaning for the uncoded occurrence is vacuous.  The denotational bridge
is therefore retained only as the OPEN obligation label
`openDenotationalBridge`, not as a trivially inhabited proposition.

## PR #13 carrier correction (adversarial repair, 2026-08-13)

1. Withdrawn: `tower_persists` does not force partiality, rule out a
   total evaluator, or prove self-application impossible.  I3 now
   records only one optional typed-refusal construction and its two
   definitional equations.
2. Repaired the denotational frontier: the former existential carrier
   was freely inhabitable.  `arbitrary_uncoded_assignment` proves that
   defect directly; `openDenotationalBridge` is now an obligation label
   requiring independent lawful semantics and an accessible behavioral
   consequence.
3. Removed the false event-ownership label from stability.  The second
   countermodel is explicitly restricted to a syntactic trace fragment;
   it is not a reachable-state necessity result and not a countermodel
   to full trace stability.
4. Narrowed reproducibility wording to deterministic generation under
   the declared line-ending canonicalization and fixed inputs.  Equality
   with Git blobs is verified for the current tracked inputs, not made
   true by definition for arbitrary files.

## Goal 1 - the renaming structure around Up (2026-08-13)

`Attachment` transported a single renaming; a transported arrow is
neither an action nor functoriality.  This pass supplies the missing
structure and proves its laws BEFORE using the vocabulary.

1. Identity, inverse and composition defined on `Renaming n`, with
   the group laws proved via a componentwise extensionality
   principle.
2. `act` proved to be an action: identity unconditionally,
   composition on the scope `n <= occ.length` (weakened from
   equality precisely so the extended state is covered), inversion
   as a consequence.
3. Block and family transport proved to respect identity and
   composition.
4. Coherence proved: replay of an `Up` block commutes with a
   composed renaming, and the composite and two-step routes agree.
5. Orbit closure proved with no selected representative; the family
   has exactly one block per represented parent.
6. Three countermodels recorded: an arbitrary non-bijective map (no
   left inverse; pushforward is not even a legal store), equal
   carrier size, and equal cost.  They do not instantiate the proved
   renaming/equivariance structure; no universal claim is made against
   other monoid actions by non-bijective maps.
7. Only then, in `equivariance_summary`, is `Up` described as
   equivariant, with the exact scope stated in the same theorem.

## Goal 5 - the true graph-genesis boundary (2026-08-13)

First the negative theorems about the current calculus, then one
explicit sufficient proposal schema that would change it, then the
verdict.

1. `refineCol` and `addCol` change observation structure only: seven
   other state fields are proved unchanged.
2. The internal response family ranges over columns on existing
   occurrences, in exactly two block shapes, with no third.
3. Along every internal trace the four graph stores are fixed, so the
   family cannot create occurrences, asserted, retained or protected
   pairs.
4. Corollary: current graph growth is supplied by the external driver
   or the `Up` grammar, never generated by `nextFamilyP`.
5. One explicit sufficient represented proposal schema is delivered as
   `ProposalRecord`: a NAMED complete-family member with its membership
   proof, embedding and retraction, fresh-token evidence,
   preservation obligations, the new pair with provenance, and a
   declared cost - with no license, execution or activation field.
   The named branch is not certified canonical or unique, and no
   minimality theorem is claimed for the schema.
   It transports under renaming and retains equal-cost
   non-isomorphic branches.
6. Verdict: `nextFamilyP` does not request the lift at an obstruction.  Every
   obstruction meeting the kernel's hypotheses is resolved inside the
   existing carrier, and no state admits an internal family member
   that grows the carrier.  The growth demand is not entailed by this
   represented response semantics and is separately declared.  The
   receipt's
   GRAPH_GENESIS_BY_OBSTRUCTION conjecture is settled negatively for
   this calculus; whether some OTHER declared family could request
   the lift stays OPEN.

## Goal 4 - general boundary cancellation (2026-08-13)

The dimension-2-to-5 computation is replaced by a general theorem,
and the standing conjecture GENERAL_BOUNDARY_COMPOSITE_VANISHING is
closed.

1. `d2_zero_unrestricted`: the coefficientwise composite boundary
   vanishes at every face of every finite cell.  The proof pairs the
   two orders for each unordered pair of deleted positions and cancels
   their signs; it is not a computation.
2. `d2_zero_general` records the declared ascending hypotheses and
   discharges them from the stronger theorem.
3. A premise of the task was false and is recorded as false: strict
   ascent is NOT load-bearing for the vanishing.  It IS load-bearing
   for distinctness of the codimension-two faces, which is what the
   ill-formed countermodel now exhibits.
4. Connected to replayed cells via `LadderGeneral.wf_nreplay`;
   renaming independence proved for strictly monotone renamings, with
   the non-monotone case stated exactly.
5. The signless countermodel keeps the orientation convention
   declared: without the signs the composite is nonzero, and nothing
   claims the filler rule forced the coefficients.
6. `LadderGeneral`'s docstring, the attachment/ladder mirror's
   `general_d2_zero` field, and the receipt conjecture list are all
   downgraded to corollaries or marked settled.

## Contact response correction: finite weights, no Hilbert climb
(2026-08-13)

The PR 17 contact surface was repaired after adversarial review.

1. Restricted profile equivalence and scaling to positive totals; zero scale
   now has an explicit boundary theorem instead of being called a positive-ray
   action.
2. Added the duplicate-free carrier policy. Raw list sums retain their honest
   multiplicity semantics.
3. Renamed lift-facing theorems as presentation theorems and fenced them as
   finite factorization identities.
4. Replaced the invalid `eB` non-presentation with two valid integer-square
   presentations differing by sign, scoped to one declared mixing read-out.
5. Reclassified the three alleged climb imports: one is trivially inhabited,
   one is proved by list algebra, and the proposed uniqueness schema is false
   by the zero read-out.
6. Rewrote the paper, ledger, receipt, artifact, and tests to state the actual
   ceiling: finite `Nat`/`Int` profile algebra and a sign-shadow fixture, with
   no Hilbert space, dynamics, probability law, or representation climb.

## Goals 2 and 3 - the one-step codebook and the trace algebra
(2026-08-13)

1. Repaired after adversarial review: 13 is the image size of a
   declared one-step signature (12 after guard erasure), not a native
   or presentation-invariant alphabet.  The coverage theorem proves
   every accepted well-formed step receives exactly one code; it does
   not derive the projection itself.
2. Two profile components were excluded from the class signature
   because they are provably not transition invariants; what they do
   carry invariantly was recovered as separate theorems.
3. A merge is reported as a result: refinement and extension have
   literally identical effect profiles on every well-formed state and
   differ only in acceptance domain.
4. Two common-suffix countermodels now prove the code is not a right
   congruence: equal occurrence-admission codes and equal budget-write
   codes can both be separated by a following event.  Raw events and
   states remain mandatory for replay.  No quotient, renaming
   invariance, DDA correspondence, or presentation-independent count
   is claimed.
5. A SECOND PREMISE OF MINE WAS FALSE.  I required a proof that
   occurrence supply, budget setting and license setting are never
   generated by the internal response family.  That holds for supply,
   license and the terminal, and FAILS for budget: `nextFamilyP`
   prefixes every extension block with `setBudget 1`.  The refutation
   is recorded, the repaired statement proved, and the scope note in
   `StableContent` corrected to say that its environment partition is
   a declared fragment, not a claim about the response family.
6. `Origin` is now explicitly documented as a constructor policy
   label, not issuer or causal provenance.  The internal family emits
   an event classified as environment, so the label cannot authorize
   an ownership conclusion.
7. The trace algebra derives its laws rather than assuming them, and
   one is stronger than expected: idempotence is universal, holding
   for every event at every state. Three sufficient frame families are
   proved; necessity and exhaustiveness are not. "Disjoint support
   implies commutes" is false because guards read fields their step
   never writes, with five non-commutation countermodels.
8. The two-rule rewrite system is sound, terminating and confluent, but
   not complete for universal replay equivalence: two universally
   replay-equivalent lists receive different `nf` values. This refutes
   completeness of this normalizer, not the possible existence of every
   richer universal or start-scoped canonicalizer.

## Contact collision executed - the arriving development processed
(2026-08-13)

The declared contact input, absent through every prior phase, arrived
and was executed against the interface those phases had already
committed.  Recorded facts of the run: base `a5caee2`; sealed
blind-native-base `ccd3a53`; one external Lean file bound by
`contact/core_primdiff/CONTACT_MANIFEST.json` (manifest sha256
`3b65253d8338b5f0283a29a194fe673d0200ca091284ab92ef315246e328065f`,
file sha256
`d9cdb350a53c513e3e211e72f17262be6ba85d7da6159f910388c7137e814a89`);
no prose stage (PROSE_INPUT_ABSENT); the file was read under the
committed statements-only discipline, never copied into the
repository, and its vocabulary is quoted nowhere outside
`contact/analysis/`.  Status moves CONTACT_INPUT_ABSENT ->
**CONTACT_PROCESSED_LEAN_ONLY**, with the former preserved as
history, not deleted (`PrimitiveContact.contactStatusHistory`,
`contact_status_count`).

1. **Three new Lean modules** (2015 lines in the working tree — 539
   `ObsDescent.lean` + 710 `ContactBridge.lean` + 766
   `ContactKernel.lean`; 1942 at the spine commit `ebb1e0b`, the
   difference being the uncommitted `toDiffObs` and
   `collapse_collision` additions; every `#print axioms` report
   within {propext, Quot.sound}; `artifacts/lean_axioms.txt` grows
   from 1037 to 1149 reports).
   `lean4/Derivation/ObsDescent.lean` reconstructs the arriving
   quotient-descent layer in native vocabulary over the sealed
   `DiffInterface.DiffObs` / `ObsQuotient`: exactness
   (`obsQuotient_exact`, `obsQuotient_mk_eq_iff`,
   `obsQuotient_mk_surjective`), unary and binary descent with
   existence-iff-compatibility, global uniqueness and witness
   blocking (`descend_*`, `deltaDescend_*`), pairing and the flagship
   obstruction shape (`classConstant_pair_iff`,
   `pair_descend_exists_iff`, `view_descends_pair_blocked`), the
   mod-setoid layer collapsed to the equality layer
   (`classConstant_comp_mk_iff`, `descendMod_exists_iff`,
   `deltaDescendMod_exists_iff`, `coarsenMap`, `pairSetoid`), the
   all-zero countermodel family (`collapseAllObs_*`), and the
   integer tail as one instance plus five one-line lemmas
   (`intDiffObs`, `int_sub_ne_zero_iff`, `int_sub_ne_zero_of_gt`,
   `int_shift_cancel`, `int_two_mul_eq_zero_iff`,
   `int_add_sub_cancel`).
   `lean4/Derivation/ContactBridge.lean` builds the complement bridge
   (`obsApart` and its laws, `obsSetting` and the candidate cells
   `obsSetting_w/a/bs/d/e` with `obsSetting_bc/bl` conditional on
   pointwise decidability), the apartness meet and its round trips
   (`apartObs`, `apartObs_roundtrip`, `isApart_repr`,
   `obsApart_isApart`, `indist_obsApart_iff`), the representability
   characterization (`obsApart_repr_iff`) with four countermodels
   (`unit_total_not_repr`, `d2_not_obs_complement`,
   `triSym_not_obs_complement`, `d_not_witnessed_repr`) and the
   minimality positive (`bool_bs_repr`), the exact prices for the
   dropped hypotheses (`cotrans_schema_iff_wlem`,
   `stability_schema_iff_dne`, `located_schema_implies_wlem`, plus
   two OPEN records), the placement theorems
   (`declared_zero_as_view`, `observation_stage_realizes_observer`,
   `kernelStage`, `kernel_stage_no_obstruction`), and the bridge to
   the native collapse obstruction
   (`pair_blocked_is_collapse_collision`).
   `lean4/Derivation/ContactKernel.lean` constructs the common
   replacement kernel `WitnessedDiff` with both realizations
   (`ofSetting`, `ofSetting_exact`, `ofDiffObs`), the sealed-interface
   meeting (`toNativeKernel`), the inherited gateway
   (`kernel_gateway_unique`, `kernel_gateway_injective`), the
   non-collector (`kernel_no_terminal`,
   `kernel_no_terminal_collector`), value-grade rigidity
   (`value_presentation_fork`, `vhom_not_unique`,
   `vhom_unique_of_onto`), passage entry
   (`kernel_licenses_entry`, `entry_pre_observation`,
   `passage_gateway_unique`), and the 37-cell matrix (`contactCells`,
   `contactCells_length`).
2. **`lean4/Derivation/PrimitiveContact.lean` was extended, not
   edited.**  The sealed pre-contact declarations (`contactStatus`,
   `NativeKernel`, `nativeKernelWitness`, `native_kernel_initial`) are
   unchanged; a dated section adds the status history, the current
   status and primary verdict as declared strings, the length check,
   and one re-export
   (`native_interface_not_representable = ContactBridge.d2_not_obs_complement`).
   `lean4/Derivation.lean` gained three imports and the per-theorem
   `#print axioms` lines of the new modules.
3. **Artifacts regenerated by their generators only.**
   `artifacts/primitive_contact.json` gains `history`,
   `manifest_sha256`, `external_file_sha256_per_manifest` (read from
   the manifest field, never from the external file), `prose_status`,
   the `verdict` block with full terminal scopes, the 37-row
   `collision_cells` mirror of the Lean literal, and five finite
   enumerations E1-E5 with their bounds; the generator raises on any
   enumeration mismatch, so a red probe blocks regeneration.
   `artifacts/primitive_completion_receipt.json` gains the three
   collision terminals (10 -> 13, with CONTACT_INPUT_ABSENT retained
   and given an explicit sealed-history scope), one new adversarial
   attack with its disposition (20 -> 21), contact bounds, and the
   updated axiom block.  `completion_receipt.json`,
   `completion_dependency_graph.json` and `coverage.json` follow the
   new theorem count (1037 -> 1149).  Generators emit identical bytes
   whether or not the external file is present.
4. **Analysis quarantine.**  The `contact/analysis/` DIRECTORY is the
   only repository location that quotes the arriving vocabulary
   (SUPPLIED_INPUT), and it holds FOUR files, all of which do so:
   `contact_dictionary.md` and `contact_countermodels.json` (103
   declaration rows with native counterparts and evidence classes, the
   countermodel table, the G1-G20 gap dispositions — including the
   refused comment-borne physics and authority claims — and five
   METATHEORY scope notes), plus `lean_definition_map.md` and
   `lean_theorem_transport.md`, which quote arriving declaration names
   and full arriving Lean statements verbatim throughout.  `lean4/`,
   `code/` and `paper/` carry none of it.
5. **Verdict, tested rather than asserted.**  Primary
   CONTACT_INCOMPARABLE_WITH_COUNTERMODELS, with the asymmetry
   proved: the native -> arriving gap is signature-level and permanent
   (countermodels at carriers 1, 2 and 3, and `d2_not_obs_complement`
   quantifies over all value types), while the arriving -> native gap
   was content-level and is closed this run by the reconstruction
   under the identical axiom budget.  Also issued:
   COMMON_PRIMITIVE_KERNEL_REPLACES_BOTH, scoped to the overlap only,
   and CONTACT_EQUIVALENT_UNDER_DECIDABLE_ZERO_PLUS_APARTNESS_ADMISSIONS,
   on the relational core only.  NOT issued, with recorded reasons:
   CONTACT_STRICTLY_STRONGER (refuted by the countermodels) and
   NATIVE_STRICTLY_STRONGER (as a sealed-corpus claim it would launder
   this run's reconstruction into the sealed record; the honest
   sentence is recorded in the artifact's verdict block, and the
   containment statement is carried as a frontier CONJECTURE about
   the ENLARGED corpus).
6. **What gained scope notes** (dated 2026-08-13, marking the text
   true at its run and superseded only as to the absence of contact
   input): `paper/primitive_difference_map.md` (new section 10 plus
   the receipt-count note in section 9),
   `paper/primitive_difference_passage.md`,
   `paper/primitive_controller_universality.md`,
   `paper/primitive_interpreter_boundary.md`,
   `paper/native_derivation_completion.md`,
   `paper/native_derivation_map.md`, and the ledger entry
   CL-PD2-CONTACT.  `paper/primitive_difference_contact.md` was
   rewritten in place - it is this run's own paper, and its
   pre-contact content is preserved as the sealed history section it
   describes.
7. **Ledger extended, not amended.**  Seven new entries carry the new
   substantive claims with their evidence classes and exact evidence
   pointers: CL-PD2-CONTACT-RECONSTRUCTION (the descent layer),
   -BRIDGE (the complement bridge and the priced hypotheses),
   -COUNTERMODELS (the representability characterization and its
   refutations), -DICTIONARY (descent versus factorization),
   -KERNEL (the common replacement kernel), -ENTRY (passage entry),
   and -VERDICT (status, terminals, and the not-issued codes).  The
   sealed CL-PD2-CONTACT keeps its statement and gains only a dated
   scope note pointing at them.
8. **No sealed claim was rewritten.**  No prior theorem statement,
   terminal code, ledger claim, or countermodel was altered, weakened,
   or deleted; nothing in the arriving file bears on passage
   dynamics, growth, the cell calculus, controllers, or the
   interpreter boundary, so those records stand as written.  The only
   pre-existing claim whose WORDING became time-relative is the
   absence of contact input, which is preserved verbatim as sealed
   history in Lean (`contactStatus`,
   `contactStatusHistory`), in the receipt (CONTACT_INPUT_ABSENT with
   a sealed-history scope field), and in the ledger, each carrying a
   dated scope note instead of an edit.

## Collision audit repair - scopes narrowed to the proved statements
(2026-08-13)

An adversarial audit of the executed collision found the Lean spine
sound and the summary prose ahead of it in five places.  Every repair
below either narrows a claim to exactly what its cited theorems prove
or adds the missing theorem; no theorem statement was weakened and no
terminal code was renamed.

1. **The equivalence terminal spends TWO decidability admissions, one
   per direction.**  `isApart_repr` and `apartObs_roundtrip` carry
   `[forall x y, Decidable (r x y)]` on the ASSERTED APARTNESS;
   `obsApart_isApart` and `indist_obsApart_iff` carry
   `[forall x y, Decidable (ZeroRel O x y)]` on the ZERO relation.
   They are not interchangeable - the zero relation of `apartObs r h`
   is the negation of `r`, and `Decidable` of a negation does not
   return `Decidable` of the statement, which is exactly the residue
   `stability_schema_iff_dne` prices at DNE.  Every summary site had
   collapsed them into one banner; each now states the split, and the
   generator strings that produce the artifact and the receipt were
   the source of the error, so they were fixed there
   (`code/run_primitive_contact.py:SCOPE_EQUIVALENT`).  The word
   "exactly" was dropped where only sufficiency plus one countermodel
   is proved (`obsSetting_bc` / `obsSetting_bl`, `vhom_unique_of_onto`).
2. **The observer half of COMMON_PRIMITIVE_KERNEL_REPLACES_BOTH now
   has a theorem.**  `ContactKernel.toDiffObs` builds the observer
   record from a kernel plus the two law declarations,
   `toDiffObs_fields` proves the fields are carried unchanged and the
   kernel is recovered (`ofDiffObs (toDiffObs K hs ht) K.a K.b
   K.apart_ab = K`), and `toDiffObs_apart` proves the relations match
   - all three by `rfl`, classed DEFINITION (a record identity, not a
   derivation).  Before this the clause rested on prose while the
   only theorems in that direction were the negatives
   `kernel_not_observer` and `kernel_zero_not_trans`.
3. **The four OPEN cells the collision declared are registered as
   open obligations.**  `open_bridge_cotrans` (price WLEM),
   `open_bridge_located` (a WLEM-implication, converse OPEN),
   `open_kernel_grade` (DNE) and `open_kernel_bl` (metatheoretic
   underivability of Located) now appear in
   `primitive_completion_receipt.json:open_obligations`, taking it
   from four entries to eight; the two collision conjectures
   (enlarged-corpus containment; the converse of
   `located_schema_implies_wlem`) appear in `frontier_conjectures`,
   taking it from three to five.  The sentence in
   `paper/primitive_difference_map.md` asserting that both counts were
   unchanged was replaced by the actual accounting.
4. **Scope qualifiers carried from the analysis into the summaries.**
   The representability crown and the carrier-1 countermodel are
   Prop-valued statements (`DiffObs X Prop`), and every contact
   theorem quantifies over `Type` (universe 0); the factorization
   dictionary is stated for kernel observers on `Nat` with
   `Nat`-valued views; `kernel_no_terminal_collector` is terminality
   at the induced-apartness morphism grade, not at `VHom` grade;
   `kernel_licenses_entry` contributes endpoint distinctness only, its
   other two conjuncts being sealed constants; `quot_barrier` is more
   general than the arriving SETOID-BASED machinery (METATHEORY,
   citation only); the 37 matrix rows are machine-checked for COUNT
   and mirror-consistency, their statuses being declared labels naming
   their evidence; the field-for-field premise `H_struct` is a scratch
   compile outside the repository and is NOT reproducible from it;
   and of the nine candidate readings only Bs has a Lean-proved
   carrier minimality (the others are least-carrier-by-signature
   METATHEORY, unclaimed for D and E, inherited for Bc/Bl/F).  The
   `WITH_COUNTERMODELS` half of the primary terminal covers the
   native -> arriving direction only; the other half is an absence
   claim about the sealed corpus and now says so first.
5. **One converse added rather than a claim withdrawn.**
   `ContactBridge.collapse_collision_is_pair_blocked` and
   `pair_blocked_iff_collapse_collision` supply the direction the
   "same event in two vocabularies" reading needed;
   `PrimitiveContact.contactStatus` keeps its sealed value and loses
   its misleading doc-comment.  `artifacts/lean_axioms.txt` grows
   from 1145 to 1149 reports, all within {propext, Quot.sound}.

## Review repair - firewall scan, pair-choice grade, committed anchor
(2026-08-13)

Three leftover-prose findings from the collision review, none of
which change a theorem, a terminal, or an artifact:

1. **Vocabulary firewall is now scanned.**  `tests/test_primitive_contact.py`
   walks `git ls-files` against the working denylist of 102
   (full census minus the nine native-or-core names).  A hit outside
   `contact/analysis/` fails, except the documented native subject
   name `PrimitiveDifference` (verified at `a5caee2`).  The 111/102
   census pins in `tests/test_primitive_receipt.py` are unchanged.
2. **The pair-choice grade is corrected.**  The original wording
   misclassified `pair_choice_load_bearing` as non-uniqueness; that
   lemma says only that an arbitrary pair may fail its side
   condition.  The observer-alone row in
   `contact/analysis/lean_theorem_transport.md` now uses
   `kernel_not_unique_of_pair` for presentation-grade non-uniqueness,
   while `kernel_from_obs_iff_pair` carries the inhabitation boundary
   and `kernel_no_witness_from_collapse` carries the collapsed-observer
   failure.  Row 14 and §2.11 were verified at `de080af`; they were not
   rewritten in this repair.
3. **Anchor no longer says UNCOMMITTED.**  The five declarations
   added after `ebb1e0b` are described as committed in this
   collision.  Companion wording in `lean_definition_map.md` matches.

## Packet 5 audit and packet 2 pair-choice lemma (2026-08-14)

Base `bd2e8c8` (PR #19 merged).  Mission
`prompt/flw_mission_pr14.md`.  AuthorityEffect None.

1. **Packet 5 — audit only, no new Lean.**
   **WITHDRAWN 2026-08-14 — see the review-repair entry below.**  The
   withdrawn text claimed that
   `PrimitivePassage.obst_conditions_independent` "already exhibits
   the four maximal proper subsets of the `obstP` conjunction
   (retained / protected / declared / zero)" and that the companion
   theorems "confirm the declared-observation conjunct is not a
   convention."  Both were false.  `obstP` as written has three
   factors, not four conjuncts; the cited theorem was five verdict
   atoms asserting nothing about any subset; and
   `obst_requires_observation` unfolds a chosen definitional branch,
   so it cannot establish that the branch is not a convention.  The
   surviving true remainder: the predicate reads only `wit`, `prot`
   and `obs` (now a theorem, `obstP_reads_three_stores`), and
   `two_rule` may keep citing the activation theorem.

2. **Packet 2 — pair-choice necessity as a reusable lemma.**
   `ContactKernel.kernel_from_obs_iff_pair`: a kernel carrying an
   observer's `delta` and `Zero` exists iff a non-zero pair exists.
   `ContactKernel.eq_ofDiffObs_of_fields`: any such kernel equals
   `ofDiffObs` at its own endpoints.  Neither statement claims
   uniqueness of the pair; `kernel_no_witness_from_collapse` remains
   the no-pair witness.  Axiom reports 1149 → 1151, both new
   theorems axiom-free.
   **Correction 2026-08-14**: the parenthesis calling
   `pair_choice_load_bearing` "the non-uniqueness witness" is
   WITHDRAWN — that theorem is not one.  See the review-repair entry
   below.

## Review repair of PR #20 (2026-08-14)

Head under review `cbcee09`.  A review requested changes on six
findings; all six are confirmed and repaired here.  Where the repair
could be made by strengthening the mathematics rather than weakening
the prose, it was.  Two prose claims are WITHDRAWN outright rather
than softened, and both withdrawals are quoted at their original
sites above.

1. **The four-way independence claim was false; it is now proved.**
   `obstP` as written has three factors
   (`obstP_strict_factors`).  There are four gates in the proved
   factorization: the TOTAL gates `retainedP`, `protectedP`,
   `declaredP`, `zeroDeclP` are now defined, and `obstP_factors`
   proves their conjunction equals `obstP` at
   every state and pair, `obst_of_gates` / `gates_of_obst` name both
   directions, and four `gate_*_independent` theorems prove — over
   ALL states and pairs, as pairs of `¬ ∀` statements — that no gate
   follows from the other three and no maximal proper subset entails
   obstruction.  The five witness states are unchanged and are now
   named definitions stating their own gate values.  Recorded
   honestly: `obstP_factors` alone is near-definitional and must be
   cited together with the independence theorems;
   `obs_gates_not_both_false` proves the gates are NOT jointly free
   (gates 3 and 4 both read `obs`, so four of sixteen valuations are
   unreachable); and `strict_gate_entails_declared` prices the
   `none => true` convention on gate 4.

2. **Pair choice: correspondence, presentation non-uniqueness, and a
   fixed-action obstruction.**  `pair_choice_load_bearing` proved only
   that an arbitrary pair may fail; its docstring now says so.  The
   inhabitation equivalence is upgraded to a bijection —
   `toPair` / `ofPair` between `NonZeroPair O` and
   `SameDataKernel O` with both round trips and injectivity, so the
   pair choice IS the kernel choice.  `kernel_not_unique_of_pair`
   proves non-uniqueness generally (any observer with an admissible
   pair has at least two distinct same-data kernels), with
   `(false, true)` / `(true, false)` over `boolEqObs` as the
   concrete instance.  `no_equivariant_pair_valued_map` rules out
   total maps `DiffObs Bool Bool → Bool × Bool` satisfying the
   Bool-negation equivariance law at `boolEqObs`; it says nothing
   about other carriers, actions, or non-equivariant maps.  Scope
   declared in the ledger: PRESENTATION GRADE,
   resting on the ADMITTED `zero_symm` field, and claiming no
   priority over the native relation-stratum obstruction
   (`Bridge.no_swap_fixed_offdiag_pair`).  Its statement and
   construction contain no quotient object, while its axiom report
   includes `Quot.sound` because Lean core realizes the `funext` step
   through that principle.

3. **Declaration is selected semantics, and the divergence is now
   checked.**  The `none => false` branch is reclassified
   DECLARED_POLICY; `obst_requires_observation` is documented as an
   unfolding of that branch and not evidence about the choice.  The
   review's suggested wording would have left the divergence witness
   unproved, so instead the rival reading is NAMED (`obstEmptyObs`)
   and compared.  The policies agree on every declared state
   (`obst_policies_agree_when_declared`) and differ at one named
   undeclared state (`obst_policies_differ`, both predicates applied
   to that same state).  A complete divergence characterization
   remains OPEN.  Also recorded: the older
   `obst_diverges_when_undeclared` does NOT carry this content — its
   first conjunct writes the lists out instead of projecting them
   from the state, so it is a closed truth mentioning no state at
   all.  It is retained as the historical witness only.

4. **The transport document's evidence boundary is regenerated and
   now machine-checked.**  The seven named post-`ebb1e0b`
   declarations were the historical collision/packet-2 audit set,
   not a census of `de080af`: packet 2R, packet 5R, and
   `SeparationCapacity` landed later.  The current boundary is the
   `de080af` tree plus this repair.  Stale line citations are corrected, and
   `ci/check_transport_citations.py` with
   `tests/test_transport_citations.py` now fails the build on any
   future drift or unclassified citation token.  It checks names and
   current line anchors, not commit provenance or declaration counts.

5. **The owned-path firewall violation is recorded, not
   retroactively legalized.**  PR #20 wrote
   `paper/native_derivation_map.md` and
   `paper/primitive_difference_map.md`, neither in
   `prompt/flw_mission_pr14.md`'s `owned_paths`.  The edits were
   necessary (they carry the axiom-report count, which would
   otherwise contradict the artifact), so the paths are added by a
   DATED AMENDMENT that names the violation as a violation.

6. **The axiom artifact is restored to LF and its bytes are now
   bound.**  PR #20 flipped all 1151 lines LF → CRLF; because
   `.gitattributes` marks `artifacts/** -text`, those bytes were
   committed verbatim and `git diff --check` failed on every line.
   The two receipts bound different domains — raw bytes in
   `completion_receipt.axiom_report_sha256`, LF-canonicalized bytes
   in `primitive_completion_receipt`, and nothing compared them
   (`ci/compare_artifacts.py` covers only `*.json` and
   `full/*.json.gz`).  The artifact is regenerated LF-only by
   `ci/regen_axiom_artifact.py`, which writes bytes explicitly so a
   shell redirect can never reintroduce CRLF, and
   `tests/test_axiom_artifact_bytes.py` binds the newline discipline
   AND the raw/canonical parity — the two hashes now coincide at
   `83adee7b…`, which holds exactly when the file is LF-only.

Axiom reports 1151 → 1178 (27 new theorems), all within
{propext, Quot.sound}; `lake build` clean at 44 jobs.

## Depth-`d` outrun on the reflective chain (2026-08-14)

`lean4/Derivation/SeparationCapacity.lean` generalizes the sealed
generator's structural outrun to every fixed radius.  Bound to the
sealed generator, not a mirror: `profileD` is `Generator.profile1` on
`Generator.reflState`, and `profileD_deep` spends
`Generator.middle_profile`.

1. **`depth_d_outrun`** — all deep-interior points share one depth-`d`
   profile.  Horizon-free: the statement carries no threshold, only
   deepness of the two points.  **`depth_d_obstruction`** derives the
   threshold `n ≥ 2d + 3` rather than assuming it — it is exactly the
   least `n` at which the deep interior holds two distinct points.

2. **The radius convention is reconciled, as two theorems.**  Sealed
   `Generator.profile2` reads the ball `{i-1, i, i+1}` — radius ONE,
   not two.  So sealed "depth `k`" indexes radius `k-1`, and `2d + 3`
   at `d = 1` is `n = 5`, exactly `Generator.depth2_obstruction_n5`
   (`sealed_depth2_is_radius_one`).  At `n = 4` the deep interior is
   the singleton `{2}` (`deep_interior_singleton_at_four`), which is
   why `depth2_separates_near_ends_n4` separating `(1, 3)` is
   consistent — that pair is not deep.

3. **Scope, stated in the module.**  This is the STRUCTURAL profile
   only.  No coloured view, no finite view alphabet, no repair
   strategy, and no capacity bound is proved; those need a finite
   pigeonhole that stays within {propext, Quot.sound}, which is OPEN.
   `contact/analysis/separation_capacity_open.md` records the exact
   residual: core's `List.length_erase`,
   `List.Nodup.mem_erase_iff`, `List.filter_eq_nil_iff` and
   `List.nodup_range` are each `Classical.choice`-dependent, and so is
   Mathlib's `Fintype.card_le_of_injective`, so the counting argument
   must be rebuilt from `filter`.  Five of six supporting lemmas were
   brought within the gate; `nodup_length_le` still leaks and the
   source is not isolated.  Recorded as OPEN rather than admitted.

Axiom reports 1178 → 1184 (6 new theorems), all within
{propext, Quot.sound}; `lake build` clean at 45 jobs, lean audit 43
sources.

## PR #21 clearance repair: citation domain and radius correspondence (2026-08-14)

Reviewer amendment "FINAL CLEARANCE REPAIR", items 1 and 2. Both withdraw a
receipt that did not cover its prose.

1. **The transport-citation gate was checking a domain two citations short,
   and could not notice.**  `citations()` counted its raw population with the
   SAME `CITE` regex it classified with, so `_assert_totality` compared the
   parser against itself and was vacuous by construction.  `CITE`'s file group
   `[A-Za-z_][A-Za-z0-9_]*` cannot span a path separator, so the two
   path-prefixed citations in `contact/analysis/lean_theorem_transport.md`
   matched nothing, went missing from both sides of the comparison, and were
   never line-checked — while the gate reported success.  The population is now
   stated independently (`RAW_CITE`: every backticked token, on one line,
   ending in a colon and digits), the totality assertion is made against THAT
   number, and `CITE` gained a path group, so all 190 tokens are parsed,
   classified and verified; `--fix` preserves path prefixes.
   `tests/test_transport_citations.py` pins the population at 190 and adds a
   regression that reinstates the old blind regex and proves the path-prefixed
   token stays in the raw count and surfaces as a totality failure instead of
   cancelling out on both sides.  This narrows the claim made in item 4 of the
   "PR #20 review findings" entry above, which said the checker failed the
   build on any unclassified citation token: it did not, for a citation the
   regex could not match at all.

2. **The radius-convention "correspondence" did not transport, and is now
   proved or scoped.**  `SeparationCapacity.sealed_depth2_is_radius_one` never
   mentioned `Generator.profile2` and never consumed
   `Generator.depth2_obstruction_n5`; it re-instantiated this module's own
   `depth_d_obstruction` at `d = 1, n = 5`.
   `deep_interior_singleton_at_four` mentioned no profile at all and was pure
   arithmetic under a geometric name.  Both are replaced by
   `radius_one_agrees_with_sealed_depth2_n5` and
   `radius_one_agrees_with_sealed_depth2_n4`, whose STATEMENTS mention both
   `profileD` and `Generator.profile2` and whose PROOFS consume the sealed
   theorems.  Each proves that over its chain's interior indices the two
   profile equalities are the same relation, then carries the sealed instance
   across that equivalence.  Withdrawn with them: the module docstring's
   "recovered" and "reconciled" wording, and
   `contact/analysis/separation_capacity_open.md`'s "Radius convention
   (residual closed)".  The equivalence is decided on those two chains only;
   the general-`n` correspondence is not proved and is recorded as OPEN.
   Item 2 of the entry above is narrowed accordingly.

Axiom reports 1184 → 1184 (two theorems renamed and restated, no net change),
all within {propext, Quot.sound}; `lake build` clean at 45 jobs, lean audit 43
sources.

## 2026-08-14 — Naturality obstruction across presentations

`ContactKernel.no_equivariant_pair_valued_map` rules out one relabelling-
equivariant map, on one carrier, for one action, and its own docstring says it
is not a general refutation of a preferred choice.  This entry records a
PARALLEL obstruction and the transport machinery it needs, in a new module
`lean4/Derivation/PresentationNaturality.lean`.  It does NOT subsume the
sealed theorem: the derivation that would make that theorem an instance is
OPEN, and until it is proved the sealed result stands on its own scope.  An
earlier draft of this entry, of the module header, and of the pull request
described the module as supplying "the general statement it was standing in
for".  That was aspirational — it asserted a subsumption the OPEN status
denies — and it is WITHDRAWN.

1. **A presentation isomorphism is now a typed object.**  `PresIso` carries a
   bijection of carriers and a bijection of residual values, with transport
   laws for `delta` and `Zero`.  `zeroRel_transport` proves the induced zero
   relation transports — the law-level content — and `PresIso.mapPair`
   transports the admissible-pair bundle.  Bijections are `Bij`, with BOTH
   round trips given as data, so nothing inverts a function by a choice
   principle.

2. **Identity, inverse and composition come with their component laws,
   proved before any categorical vocabulary is used** — and no categorical
   vocabulary is then used.  `refl_car`, `trans_car`, `symm_car_left`,
   `symm_car_right`, `symm_symm_car` are pointwise statements about
   components.  No `PresIso` equality is proved and no groupoid, category or
   functor is asserted.  Stated as a non-claim rather than left implicit.

3. **The general obstruction.**  Over the declared one-object family
   generated by a presentation automorphism (`autoFamily`), a section of the
   admissible-pair bundle is natural when it commutes with that automorphism.
   `no_natural_section_of_fixed_point_free`: if the automorphism fixes the
   observer but fixes no admissible pair, no natural section exists.

4. **Both boundaries are proved, so the theorem is neither vacuous nor a
   universal refusal.**  `selection_is_possible_naturality_is_not` exhibits a
   raw section over the very family that admits no natural one — selection is
   possible, natural selection is not.  `card4_has_natural_section` exhibits a
   four-element presentation whose declared automorphism transposes two
   elements and fixes two; its fixed pair is admissible, so a natural section
   DOES exist.  `naturality_separates_presentations` states the two together,
   which also shows multiplicity of admissible pairs is not what decides it:
   both presentations have several.

5. **What is NOT claimed, recorded at the claim site.**  The sealed Bool
   selector theorem is NOT licensed as an instance of the general obstruction.
   `bool_obstruction_and_sealed_selector` states the two together and derives
   neither from the other; they quantify over different objects — maps out of
   the observer type, versus sections of the pair bundle.  Deriving the sealed
   statement from the general one is recorded as OPEN.  See
   CL-PN-NATURAL-SELECTION for the full non-claim list.

Axiom reports 1184 → 1202 (eighteen added, none removed), all within
{propext, Quot.sound}; every new theorem is axiom-free except
`bool_obstruction_and_sealed_selector`, which inherits `Quot.sound` from the
sealed theorem it co-states.  `lake build` clean at 46 jobs, lean audit 44
sources.

## 2026-08-14 — Heterogeneous many-object transport, and bundle coherence

Review of the entry above recorded a scope defect: `Family` fixed ONE carrier
`X` and ONE residual type `R` for every object, so heterogeneous families with
object-indexed carrier and residual types were not representable, and every
result was over one-object families.  This entry narrows that bound.

1. **The cause was the arrow encoding, not an accident.**  `Family` declared
   arrows as a flat `Arr` with `src`/`tgt` functions.  That makes an
   endomorphism a propositional side condition (`src f = tgt f`) rather than a
   typed one, and it forces a common carrier, since `obs : Obj → DiffObs X R`
   cannot depend on the object.  `HFamily` indexes arrows as `Hom a b`, so an
   endomorphism is definitionally an inhabitant of `Hom a a`, and `car`, `res`
   and `obs` become object-indexed.  No dependent transport appears anywhere in
   the new development.

2. **The obstruction over many objects.**  `no_natural_section_of_endo`: a
   declared endomorphism at ANY object, fixing no admissible pair there,
   already rules out a natural section of the whole family, with carrier and
   residual type varying by object.

3. **Coherence of the transported bundle**, which the earlier entry left as
   future work: `mapPair_refl`, `mapPair_trans`, `mapPair_symm_left`,
   `mapPair_symm_right`.  These are the bundle-level companions of the earlier
   component laws.  They remain statements about `mapPair` and `PresIso`, not
   about `HFamily`, and no categorical structure is claimed by either.

4. **Both boundaries, on a genuinely heterogeneous two-object family** —
   `Bool` with `boolEqObs` and `Card4` with `card4Obs`, different carriers and
   different residual types.  `twoFamilyNeg_no_section`: negation at the `Bool`
   object sinks the whole family, though its `Card4` component alone carries a
   natural section.  `twoFamilyPos_has_section`: replacing only that one
   automorphism by the identity restores it.
   `heterogeneous_naturality_separates` states both — same objects, same
   carriers, same admissible pairs, and only the declared automorphism differs.
   So the obstruction is carried by the declared arrows, not by heterogeneity.

5. **What remains OPEN, narrowed rather than removed.**  A general embedding of
   `Family` into `HFamily` is not proved; `hAuto_iff_auto` bridges the two at
   ONE object only, and `Family` is retained.  Arrows that genuinely CROSS
   objects with different carriers are still not exercised — the two-object
   fixtures declare no arrow between their objects.  `HFamily` still assumes no
   composition, no inverses and no identities.  Deriving
   `ContactKernel.no_equivariant_pair_valued_map` remains OPEN and untouched.
   See CL-PN-HETEROGENEOUS-TRANSPORT.

Axiom reports 1202 → 1213 (eleven added, none removed), all within
{propext, Quot.sound}; all eleven new theorems are axiom-free.  `lake build`
clean at 46 jobs, lean audit 44 sources.

## 2026-08-14 — The coloured separation-capacity bound, closed

`contact/analysis/separation_capacity_open.md` recorded, since it was written,
that the capacity bound was "not in this repository" and that "the pigeonhole
is the blocker".  Both are now WITHDRAWN at their original site; this entry
records what replaced them.

1. **The pigeonhole leak was not where the residual document said it was.**
   That document proposed bisecting `nodup_length_le`, on the reasoning that
   "the leak is inside it, not in any lemma it cites".  The bisection would not
   have found it.  Every lemma it listed as checked-and-clean was checked at
   the wrong place: `#print axioms F` reports the axioms of `F`'s own proof
   term, NOT of the instances a use site supplies.  The carrier was the
   `ReflBEq Nat` INSTANCE, required by `beq_self_eq_true` at `Nat`:
   `LawfulBEq Nat` is clean, `ReflBEq Nat` is not.  Controls: the equation
   compiler alone reports no axioms and the `induction`-tactic variant leaked
   identically, so neither the recursion machinery nor any cited lemma was
   responsible.  Using `decide (x = B)` in place of `x == B` removes it.
   `lean4/Derivation/Pigeonhole.lean` reports `propext, Quot.sound` throughout.

2. **The same trap recurred once more, and is recorded here so it is not
   rediscovered a third time.**  A bare `simp` closing a length-mismatch case
   in `CapacityBound.encode_inj` pulled `Classical.choice` from the default
   simp set; `Nat.noConfusion` cleared it.  Neither leak was in a cited lemma.
   Both were in something the proof text did not name — an instance, and a
   simp set.

3. **The capacity bound** (`CapacityBound.capacity_bound`): for a colouring
   below `k` and a view factoring through the radius-`d` colour ball, once
   `n ≥ k ^ (2d + 1) + 2d + 2` the deep interior of `reflState n` holds two
   distinct points the view does not separate.  This is exactly the target form
   `n ≥ B + 2d + 2` the residual document stated, with `B = k ^ (2d + 1)`.

4. **The locality hypothesis is what makes it a capacity statement.**  `B` is
   DERIVED by counting colourings of a radius-`d` ball, so it depends on the
   radius and the alphabet and not on `n`.  §4 of the residual document warned
   that an unconstrained view makes the radius inert and the result ordinary
   global pigeonhole; that warning is retained, because it is precisely the
   condition the proof had to meet, and `ViewLocal` is what meets it.

5. **Non-vacuity is exhibited, not assumed.**  `capacity_at_one_colour` is the
   degenerate end; `local_view_can_separate` fixes `k = 2`, `d = 0`, and
   `n = 3`, proves indices `1` and `2` deep and `3` strictly below the
   threshold `4`, and exhibits a local parity view that separates every
   distinct deep pair (including `1` and `2`). This refutes the existential
   forced-collision conclusion below threshold, not merely collision of one
   selected pair.

Not claimed: tightness of `k ^ (2d + 1)`; anything about views that do not
factor through the ball; anything about the sealed `Generator.profile2`
colouring in particular. The general-`n` radius correspondence and a
repair-strategy-class consequence are the two OPEN residuals. Identity-grade
observation, absolute interior, and "no outside" are outside this
investigation's statement language. See CL-CAP-BOUND.

Axiom reports 1213 → 1229 (sixteen added, none removed), all within
{propext, Quot.sound}.  `lake build` clean at 48 jobs, lean audit 46 sources.

## 2026-08-14 — Separation-capacity clearance repair

The capacity theorem was already proved, but its residual document and the
`SeparationCapacity` module header still called the capacity/pigeonhole layer
OPEN. Both headers now state the closed capacity result and name exactly two
remaining obligations: the general-`n` `Generator.profile2` correspondence
and a repair-strategy-class consequence. Identity-grade observation,
absolute interior, and "no outside" remain outside this investigation's
statement language rather than additional OPEN cells.

`CapacityBound.local_view_can_separate` now carries its entire non-vacuity
claim in the theorem type: `k = 2`, `d = 0`, `n = 3`, deep indices `1` and
`2`, strict position below threshold `4`, locality, bounded colour values,
explicit separation of `1` and `2`, and separation of every distinct deep
pair. Wording that called enumerated reports "axiom-free" now says
exactly that they are choice-free within `{propext, Quot.sound}`.

The completion inventory now stops equation-style theorem statements before
their first proof clause; resolves qualified references and known theorem
member suffixes; permits backticked bare ledger shorthand only when the final
component is globally unique; and has explicit semantic metadata for the
`Pigeonhole` and `CapacityBound` namespaces. Ambiguous ledger citations are
now qualified at their source. Regression tests pin each repair.

## 2026-08-14 — Presentation-relative identity and comparison-forced refinement

`PresentationRelativity.lean` removes spatial polarity from the formal
statement. On a supplied finite carrier, mutual factorization is proved
equivalent both to equality of induced fiber relations and to two-sided
directional-residual emptiness. A declared question-family split is proved
exactly equivalent to an old-family agreement separated by the new family.

A failed supplied comparison now has a necessity theorem and a bounded
construction. The necessity theorem extracts the exact collapsed/separated
pair and proves that every presentation carrying both maps must split it and
strictly increase represented class count. The construction
`jointPresentation` supplies one ordered first-match joint refinement. The
comparison is not generated and the construction is not claimed natural,
canonical, unique, or preferred.

The operational witnesses are presentation-indexed: support versus
support-plus-notes, source versus extended certification panel, and depth-one
versus identity-grade generator comparison. The ambient all-view declarations
are fenced in `PresentationRelativity.Metatheory` as diagnostics only.
`ABSOLUTE_NO_OUTSIDE_UNFORMULABLE` is retained; no physical-time,
cosmological-origin, capital-T truth, observer-completeness, heterogeneous
forced-split, or self-certification claim is added.

`native_derivation_completion.md` records NC3 as partially closed at the
one-step refinement law. `endogenous_generator.md` is corrected to record the
already-proved structural G2 depth-`d` outrun while retaining the general-`n`
profile correspondence and repair-strategy consequence as OPEN. The
identity-grade supplied comparison does not close G1.

Axiom reports 1229 → 1261 (32 added, none removed), all within
{propext, Quot.sound}. `lake build` is clean at 49 jobs; the Lean audit
covers 47 sources. Final Python coverage and artifact-replay counts are
recorded from the publication gate rather than inferred here.

## 2026-08-14 — Closure failure as loss of internal symmetry invariance

`ClosureSymmetry.lean` removes an evaluator-shaped reading of the
relative obstruction. The two maps `p` and `q` are internal faces of
one attempted closure. A directional residual constructs the
transposition of its represented pair; that involution preserves the
represented domain and leaves `p` invariant, while `q` ceases to be
invariant. Conversely, any represented involutive symmetry with that
invariance break reconstructs the residual.

The load-bearing theorem
`closure_failure_iff_internal_symmetry_break` identifies failed
factorization, represented residual, and symmetry loss. It supplies no
evaluator, observer from nowhere, repair authority, preferred face,
next comparison, or ontological inside/outside predicate.

Seven theorem reports are added: 1,261 → 1,268. `lake build` is clean
at 50 jobs; the Lean audit covers 48 sources and admits only
`{propext, Quot.sound}`. The exact new inventory regression passes;
the broad completion test file hit the six-minute host command timeout
without reporting an assertion failure and is left to repository CI.

## 2026-08-14 — Heterogeneous fidelity closure and endogenous quotient generator

Six source modules are integrated as one reviewed chain. `ResidualClosure`
closes the current finite residual without claiming future quiescence.
`PresentationDescent` removes the common-carrier assumption: coherent round
trips for one declared total translation pair are proved equivalent to a
faithful common descent whose injective images coincide. Translation gaps
refuse only exact constraint-preserving totalizations.

`QuotientRetention` proves the carrier-independent quotient statement:
failed identification retains two fine classes and makes the attempted
collapse non-injective. `FidelityClosure` generates coherent paths from
admitted steps and separates missing paths, holonomy, and label descent.
`EndogenousFidelityGenerator` proves that this path relation is the least
equivalence containing the admitted steps; multiplicity is precisely what the
attempted indiscrete erasure fails to remove.

`NoOutsideFidelity` supplies the bounded operational witness. The exact
`World → Supp` projection has no coherent inverse for any proposed backward
map because distinct notes occupy one support fiber, while the notes field has
no kernel authority. This is not an ontological no-outside theorem.

The integrated surface adds 46 theorem reports: 1,268 → 1,314. The aggregate
build completes 56 jobs; the Lean audit covers 54 sources and admits only
`{propext, Quot.sound}`. The focused exact-surface regressions pass, and the
artifact replay reproduces 37 JSON files byte-for-byte plus six hash-pinned
exports. No observer, finite common carrier, metric, canonical selector,
first presentation, continuation authority, or automatic admission is added.
`AuthorityEffect: None`.

## 2026-08-16 — The paper's own receipts were stale; measured and withdrawn

No object-language content changes here. This entry records a correction to
the paper's metatheoretic receipts, and nothing else.

Section 12 reported gate status "at freeze" as 82 tests passing, line
coverage 99.77%, branch coverage 98.75%, and 51 exported axiom reports.
Every one of those figures had been overtaken by the development and none
had been re-measured. The true values, measured on this date: **435 tests
passing; line coverage 99.10%; branch coverage 96.73%; 1,314 exported
reports, of which 413 are axiom-free; `lake build` clean across 56
sources**, with the audit admitting only `{propext, Quot.sound}` and the
committed `artifacts/lean_axioms.txt` matching the fresh log exactly.

The old figures are quoted at the site and WITHDRAWN rather than silently
overwritten, so the fact that the paper carried false receipts stays in the
record. The failure mode is worth naming: a receipt that is not re-measured
is a claim about the past wearing the tense of the present. The coverage
figures in particular had drifted DOWNWARD (99.77 → 99.10, 98.75 → 96.73),
so the stale text was not merely old, it was flattering.

The substantive derivation results were checked in the same pass and are
NOT affected. Every number in Section 11 verifies against
`artifacts/claims.json`: minimum response cost two in both readings
(`CL-3-MIN-TWO`); three tied classes in reading L and five in reading F
under the item-count measure (`CL-3-NONUNIQUE-MU1`); uniqueness up to
isomorphism under the refined measure (`CL-3-UNIQUE-MU2`); and the
refined-measure trees fully enumerated at 963 and 1,847 nodes, both at
depth 15 (`CL-TREE-SUMMARY`). The terminal statement stands as written.

One open obstruction is added to Section 12, carried over from the
verification apparatus rather than from the object language: **elaboration
is not auditing**. Every module under `lean4/Derivation/` is now elaborated
against a pinned census, but a module the root does not import emits no
`#print axioms` report, so the whitelist never inspects it. "Axiom-clean"
is a claim about the 1,314 enumerated reports, not about every declaration
in the tree. Closing it needs a compiler-emitted declaration census; the
regex approach is known to fail here and is refused rather than adopted
badly.

No theorem is added, strengthened, or withdrawn. No claim ledger entry
changes. `AuthorityEffect: None`.

## R6 discharged: count-invariance is now a theorem (2026-08-17)

Section 12's residual register listed eight residuals in five kinds. R6
— "count-invariance transport under regime isomorphism", kind (a),
needing "a Lean transport proof" — is now proved and struck from the
register.

`lean4/Derivation/CountTransport.lean` adds `DRen`, an action on
regimes, and the chain `plug_mapCtx` → `derivable_rename` →
`wfCtx_rename` → `collapsed_rename` → `collapsedCount_rename`. Six new
`#print axioms` reports, all within `{propext, Quot.sound}`; the axiom
inventory goes 1314 → 1320 and the module census 55 → 56.

`CL-COUNT-INVARIANCE` is reclassified **[finite computation]** →
**[theorem]**. The exhaustive Python certification is retained as
independent evidence rather than replaced.

What made the proof clean is worth recording, because it is a fact about
the definitions and not a convenience: `collapsed` reads only `forms`,
`data`, `insts` and `rules`. It never reads `reqs`. A renaming need not
preserve the `q.1 < q.2` ordering that `Regime.wf` imposes on
requirements, and that would have been a genuine obstruction had collapse
depended on them. It does not, so the action leaves `reqs` alone.

Scope stated rather than implied: `collapsed_rename` needs only
bijectivity, not the bound fields, which are used solely by
`wfCtx_rename`. `collapsedCount_rename` takes the decision procedure as
a parameter with a proof that it tracks `collapsed` — nothing here
decides `collapsed`, whose quantifier ranges over the infinite type
`Ctx`. The requirement conjunct of `Regime.wf` is not claimed to
transport.

The four remaining kind-(a) residuals (R1, R2, R3, R7) are open by the
same route. That the route worked once is not a claim that they are
done.

## R1, R2, R3 discharged: the mention lemma (2026-08-17)

`lean4/Derivation/Mention.lean` proves the three pruning residuals. They
were one argument, not three.

`wfCtx` requires `none ∈ c.slots`, so a well-formed context always has a
hole, and `plug c d` therefore always mentions `d` at that hole. An
instance that does not mention `d` can never be `plug c d`. That is R3
(`collapsed_append_unmentioning`).

R1 and R2 are not instances of R3, because a fresh datum or form
genuinely enlarges the space of well-formed contexts — new contexts do
appear. What is proved is that every new context mentions something no
instance mentions, so BOTH plugs fail membership and the iff in
`collapsed` holds by failing on both sides. A context that reaches
outside the regime does not separate; it only fails twice. Their
hypotheses are conjuncts of `Regime.wf`, not new assumptions.

Seven new `#print axioms` reports, all within `{propext, Quot.sound}`;
the inventory goes 1322 → 1329 and the census 56 → 57.

`CL-PRUNE-STRUCTURAL` gains Lean evidence for its three irrelevance
inputs and **stays a [bounded theorem]**. The enclosing claim — that the
pruned enumeration contains every minimum — quantifies over the declared
cost-2 grammar slice and is still computational. Three inputs became
theorems; the enumeration did not, and the class is not upgraded on the
strength of its parts.

`by_contra` is a Mathlib tactic and this development imports only core,
so `exists_out_of_range_slot` extracts its witness by induction instead.
Recorded because the constructive-only constraint is easy to breach
silently.

The register is down to four: R4, R5, R7, R8.

## The register closes: R4, R5, R7, R8 discharged (2026-08-18)

Section 12's residual register is empty. Each of the four remaining
rows closed by a Lean proof of the statement its row asked for, and the
computational evidence is retained everywhere as independent.

**R7** (`lean4/Derivation/TransitionTransport.lean`, the largest): the
transition — impose, then respond — reads the requirement store, which
the collapse action deliberately ignores, so the action is EXTENDED to
`renameRegimeR` with requirement pairs renormalized to ordered form,
and padded (`padF`) across the fresh data a response admits. The
congruence is stated at the relation level as mapping
(`transStep_rename_fwd`) plus image totality (`transStep_image_total`)
— deliberately NOT an equality-form iff over an arbitrary child, which
would be FALSE: `mapReq` renormalizes, so the action is not injective
on disordered-requirement regimes. `validCount_rename` carries minima
and counts of both declared measures.
`least_pair_selection_not_congruent` witnesses in Lean, on the
regression regime, that the SELECTION is not congruent even though the
relation is — keeping the module consistent with
`test_least_pair_selection_is_not_equivariant` rather than appearing
to contradict it. CL-TRANSITION-EQUIVARIANCE is reclassified; the
conversion to equal canonical-key class sets stays with CL-ISO-SOUND.

**R5** (`lean4/Derivation/MinimalityF.lean`): `mu2_unique_F`,
grammar-wide, by transfer of the L case tree — R2F shares with R2L the
only two structural facts the tree uses (form-less and instance-less;
a singleton requirement list). The one genuinely new case, the mark on
the genesis datum outside the requirement pair, dies by the R3 mention
lemma: its instance mentions neither required datum, so the pair stays
collapsed and validity fails. A residual closed on 2026-08-17 closed a
case of a residual closed on 2026-08-18. Section 11(d) is strengthened:
mu2 uniqueness is now grammar-wide in BOTH readings.

**R4** (`lean4/Derivation/RuleBridge.lean`): the bridge is
definitional, which is why it was provable at all — no `applyItem`
guard reads the rule field and only `newRuleAll` writes it, so rule
items commute out of a delta over ANY replacement rule field
(`applyDelta_dropRules`, parametrized so the subset condition enters
only at the final `separable_of_subrules` call).
`rule_item_never_minimal`: valid, strictly shorter, arity sum
unchanged — never a minimum under either declared measure.
CL-PRUNE-RULE (ii) is reclassified from bounded theorem to theorem.

**R8** (`lean4/Derivation/Rounds.lean`): `ClosedRun` is the first
Lean object representing a run — a round is an imposed FRESH target
plus a response admitting NO fresh datum, mirroring the engine's
asserted invariants. Under that declared shape: exactly-one growth
(`round_reqs_succ`), datum fixity (`round_data_eq`), and
`closedRun_round_bound_from_empty` — 2 *rounds bounded by
n* (n - 1), the division-free n(n-1)/2 — via a new choice-free
subset-counting lemma (`nodup_subset_length`) built with the
decide-filter technique recorded in `Pigeonhole.lean`, since
`List.nodup_range` and the erase route carry `Classical.choice` on
this toolchain. What stays computational NARROWS to: each exported
round has the declared shape. CL-CLOSURE-TERMINATION's conditionality
note is rewritten accordingly.

## Two gate defects found and repaired in passing (2026-08-18)

**Primed theorem names were invisible to the axiom artifact.** The
report parser in `ci/regen_axiom_artifact.py` and
`ci/check_axiom_report.py` used `'[^']+'` to capture names, which
cannot parse a report for a primed name — the closing quote of
`'Derivation.nodup_head'' ...` is ambiguous under that pattern — so
four reports were silently absent from `artifacts/lean_axioms.txt`
while the match gate stayed green, BOTH SIDES sharing the blind
pattern. This is the exact defect class the transport-citation gate
documents: a totality invariant computed with the classifier's own
pattern proves nothing. Both parsers now use a non-greedy capture; the
audit's independent line count (1417) now agrees with the artifact.

**A doc comment wrapped onto the word theorem.** The module header of
`MinimalityF.lean` wrapped a sentence onto a line beginning with that
word, and a name-extraction pass grepping declaration heads captured
the following word as a theorem name. CLAUDE.md records this exact
failure twice before; it happened again, to the person who had just
re-read the warning. The line is rewrapped. The lesson is unchanged:
never derive an inventory from a text grep of declaration heads.

## A ledger evidence gate (2026-08-18)

`ci/check_ledger_evidence.py` verifies that every evidence citation in
`paper/paper_claim_ledger.md` resolves: Lean names against
`artifacts/lean_axioms.txt`, test names against `tests/`, artifact keys
against the committed exports — with the citation population enumerated
independently of the classifier, per the `check_transport_citations.py`
discipline. Wired into CI as a ninth gate family.

On its FIRST real run it found three dead references: CL-TREE-MU1-
FRONTIER cited `tree_L_mu1.json` and `tree_F_mu1.json`, which do not
exist (the exports are the `_summary` files and the gzipped full
trees), and CL-PD2-INTERPRETER cited a theorem name that survives only
in a rename note. All three repaired; the historical name is now
mentioned without backticks, because a deliberately dead citation must
not look live. The gate then caught two of the very edits recording
tonight's work (a backticked formula, a backticked field name) before
they landed. Injected and reversed: a broken test reference failed by
claim ID, token, and reason.

## The walk: every ledger claim audited wording-against-evidence (2026-08-18)

All 127 ledger claims, plus the section 11 terminal statement, the
closed register, and a restricted-word sweep, were audited for the one
question no gate can check: does the wording say more than the named
evidence proves?  Every finding was then adversarially verified by an
independent pass instructed to refute it.  94 findings were raised; 13
survived verification and are applied below; 5 were refuted with
reasons; the remainder were low-severity and are held in the walk
report rather than silently dropped.

No finding was high-severity: nothing in the ledger asserted a result
that does not exist.  Every confirmed defect was a scope or bookkeeping
divergence — the exact class of drift this audit exists to catch:

- **Three stale axiom fields** (CL-1-SUPPLY-NOT-ADMISSION,
  CL-2-COLLAPSED, CL-QUOT-BARRIER): recorded axiom sets contradicted
  `artifacts/lean_axioms.txt`, the field's own declared source.  All
  three now match the artifact per-theorem.
- **Reading-silent statements** (CL-3-NONUNIQUE-MU1, CL-3-TIE-CLASSES):
  Lean evidence stated over reading L only, while the entries read as
  covering both readings.  Scope now explicit: reading F rests on the
  bounded enumeration.
- **"Every bijection" narrowed to datum bijections**
  (CL-TRANSITION-EQUIVARIANCE): an isomorphism here is a PAIR of
  bijections, and neither the Lean transport nor the exhaustive test
  exercises the form component.
- **A missing dependency** (CL-TREE-MU2-COMPLETE): tree completeness is
  conditional on the orbit policy losing no child classes — the
  class-set form of CL-TRANSITION-EQUIVARIANCE — which the Deps now
  name.
- **A conjunction reading as fully Lean-proved** (CL-COUNT-INVARIANCE):
  the Lean transport covers datum-index bijections; token renaming is
  inexpressible in the Lean model and form bijections are not
  transported.  Split made explicit.
- **A universal proved as an instance** (CL-FR6-T7-CEILING): "never
  being fixed points" was backed by non-fixedness of one exemplar.
  Narrowed to the exhibited bypass.
- **An in-class clause resting on a theorem that does not cover it**
  (CL-FR6-T6-LAW): the covering exhaustive test is now named.
- **A horizon-relative universal with no horizon stated**
  (CL-FR6-T10-NORMAL-FORM): the 6-event horizon and carrier cap are now
  in the entry.
- **The restricted word "minimal" with no minimality relation**
  (CL-RP-COUNTERMODELS): now "small (not proved minimal)".
- **"Implements exactly that semantics" without its basis**
  (CL-PD2-HORIZON): the module header's own declared-finite-basis
  wording is restored in the ledger.

Two of the thirteen were against entries written during the register
closure the previous day (CL-COUNT-INVARIANCE's class line,
CL-TRANSITION-EQUIVARIANCE's statement): the walk catches its own
operator, which is the point of running it.

## The walk, wave two: the overflow verified, the ledger narrowed (2026-08-18)

The 76 findings the first verification pass could not reach were each
adversarially verified: 42 confirmed, 34 refuted.  With wave one that
makes 94 raised, 55 confirmed, 39 refuted, all confirmed findings
applied.  Still zero high-severity: every confirmed defect is a scope
or bookkeeping divergence, none a claim of a result that does not
exist.

**The walk caught a false receipt in this change log.**  The
register-closure session ran one script applying several paper edits
with a single write at the end; a failed assertion midway killed it
after the first three edits had been logged as applied but before the
write.  This log then claimed "Section 11(d) is strengthened" about an
edit that never touched the file, and sections 7, 8, 10 and 11
contradicted section 12 for a day.  All six passages are now actually
applied, each with a dated note.  The mechanism is recorded so it is
not rebuilt: batch edits must write incrementally or verify the final
file state, never trust in-memory success.

**The body prose is aligned with the closed register.**  Sections 7.4,
8.2, 8.3, 8.5 and 10 no longer call the discharged results unresolved;
the gate-figures bullet gains a third dated supersession (62 sources,
1417 reports, 435 tests, line 99.10% / branch 96.73%); the kind-(e)
bullet's enumerated-report figure tracks the inventory.

**Twenty-one ledger entries narrowed** in the established idiom —
weaken to what the evidence proves, name the missing scope, date the
correction: reading-L scope on the infinite tie family; the progress
theorem's conjunct quantifies over imposed requirements, not all
separations (docstring and paper wording aligned); receipt counts
gain a dated scope note with the current artifact's counts (13
terminals, 8 open obligations, 21 adversarial entries, 12 extensions);
universals proved as instances are reworded witness-shaped
(CL-PD2-RECEIPT-BYTES, CL-FR6-T2-TRACE, CL-PD2-CONTROLLER); a
direction-of-implication error in CL-PD2-TRACE-STABILITY is repaired
(sufficiency proved, necessity routed to its own OPEN item); the
CL-FR6-T3 countermodel is re-attributed from the tag route to the
relation route, confirmed against the artifact's recorded protocol
(`autorel: true, tagging: false`); platform scope, panel non-emptiness,
nonempty-domain hypotheses, and cited-count corrections land where the
verifiers confirmed them.

**Thirty-nine findings refuted** are recorded as evidence the entries
were right: each refutation names where the scope was already stated.
One follow-up was noted and not silently fixed: the prose of
`StableContent.lean` was not re-checked against the narrowed (iii) of
CL-PD2-TRACE-STABILITY.

## Passage stations renamed to native labels; the supply disclosed
(2026-08-21)

**The station names of the Phase VI passage were SUPPLIED, and this is
the first entry to say so.**  `prompt/ultra_prompt_pr12.md` lines
453-471 give the fourteen stations and thirteen arrows verbatim, under
the instruction "construct the exact passage".  They are an
EXTERNALLY IMPOSED CHALLENGE.  `paper/primitive_difference_passage.md`
previously presented the chain as its object of study without naming
its origin; a reader could reasonably have concluded the carving was
found rather than given.  That omission is repaired, not restated.

Two further supply facts are recorded with it.  Four of the six files
in `prompt/` — including the one carrying this chain — are declared as
inputs nowhere in the paper and pinned by no hash gate; only
`prompt/prompt.md` and `prompt/seed_prompt.md` are.  And the
vocabulary firewall in `tests/test_primitive_contact.py` derives its
denylist from the supplied *Lean* file, so the prompt's vocabulary is
a second supply channel that no denylist enumerates.  Neither is
repaired here; both are recorded so that the next reader does not have
to rediscover them.

**What the rename moved: nothing.**  The Arrow column and the module
docstrings now name the objects the development constructs.  Of the
sixteen supplied names, exactly two were ever Lean identifiers —
`ZeroRel`, already classified native-or-core, and `ActiveObstruction`,
definitionally the conjunction of three native `Stage` fields.  The
other fourteen existed only as prose.  One supplied word had already
been refused on contact: the chain says "protected" and the stage
field is `guarded`.

The claim that nothing moved is checked, not asserted: `lake build`
followed by `ci/check_axiom_report.py` reports 1417 axiom reports
matching `artifacts/lean_axioms.txt`, with the name-blind count
agreeing at 1417, and the ledger's 1055 evidence tokens all still
resolve.  No theorem, definition, countermodel, or artifact changed,
because none of them depended on a label.

That is a result about this development and not a general one.  It
says the supplied vocabulary steered the exposition and did not reach
the mathematics.  It does not say a supplied vocabulary never could,
and it does not discharge the two supply facts recorded above.



## The equivariance obstruction generalized, audited, narrowed (2026-08-21)

`Derivation.Breaking` previously held one obstruction: for a declared
fixed-point-free involution, no endomap is both orbit-constant and
equivariant.  Three things changed, and only the first is an addition.

**Generalized.**  `Symmetry` replaces the single involution with a
family of transformations having no common fixed point — no involution
law, no group law, no identity, no inverses, no composition.
`no_orbit_constant_equivariant_selector` proves the same conclusion
there, and `ofBreak` exhibits `Break` as the one-symbol case, so the
general result SUBSUMES the involution one rather than sitting beside
it.  `triSymmetry` and `no_fixed_point_free_involution_on_Tri` witness
that the generalization is not cosmetic: `Symmetry` is inhabited at a
three-point carrier where `Break` is not.

**Audited.**  `lean4/Derivation.lean` now imports the module and prints
an axiom report for each of its seven exported theorems.  All seven
report *does not depend on any axioms* — not `propext`, not
`Quot.sound`.  The parked-module residual recorded in `CLAUDE.md` is
closed FOR THIS MODULE and remains open for every other module the root
does not import.  Closing it here is not evidence about those.

**Narrowed, on review.**  Three claims made in the first version of
this work did not survive, and are recorded here rather than quietly
fixed.

1. *The premise was overstated.*  `Symmetry.no_common_fixed` says every
   point is moved by some symbol.  The argument never needs that: the
   two selector laws compose to make the selected value a common fixed
   point, so the weaker `¬ ∃ p, ∀ g, act g p = p` suffices, and does so
   constructively.  `no_selector_of_no_common_fixed_point` now proves
   the obstruction from that premise over a bare action;
   `no_common_fixed_point` derives it from the field in the one
   direction available.  The claim that the field is "exactly what the
   obstruction costs" is **WITHDRAWN**, and replaced by a theorem:
   `selector_iff_common_fixed_point` characterizes, in both directions,
   when an orbit-constant equivariant selector exists.  The repair
   strengthened the result; that is why it is recorded as a repair and
   not as a correction.

2. *A parity claim was asserted without proof.*  The module and
   `paper/representative_selection.md` both stated that a
   fixed-point-free involution pairs any finite carrier into two-cycles,
   so every finite `Break` carrier has even cardinality, and applied it
   to tie sets of size three and five.  Only the three-point case is
   proved.  The general statement needs counting, which the module does
   not use, and it is **WITHDRAWN** and left OPEN rather than kept on
   the strength of the case that is proved.  The application was doubly
   wrong: even granting the general fact, the cited theorem never
   reached the five-element set.  Nothing depended on the remark — the
   tie it was said to reinforce is refuted by `mu2_unique` and
   `mu2_unique_F`, which are proved — so it is removed, not repaired.

3. *The paper contradicted itself about its own verification state.*
   `representative_selection.md` withdrew "parked" in one section while
   four others still called the obstruction parked and axiom-unaudited,
   and §8 still promised the module would not be un-parked without a
   separate review.  All five passages are reconciled: the import
   happened on exactly the terms §8 demanded, and the sentences are
   moved to the past rather than deleted, because the ordering they
   record — audited substrate, unaudited obstruction, absent link — is
   still the finding.

**What did NOT change.**  Layer 3 still does not exist: no proof
connects `Break` or `Symmetry` to the tied delta pair.  Auditing the
obstruction makes it citable, not applicable.  An audited theorem about
a structure nobody has connected to the pair is exactly as unusable here
as an unaudited one, and the page still argues from the code and from
the audited substrate.

## The blindness attestation narrowed to what is true (2026-08-21)

Section 13 of the paper carried two sentences.  The first withheld the
post-hoc comparison.  The second said: *"No external theory,
architecture, or terminology is named anywhere in this repository
outside the read-only seed prompt."*

The second sentence was false, and had been for some time.  Six
documents under `paper/` carry end-placed sections that name external
mathematics -- `bridge_provenance.md`, `endogenous_generator.md`,
`primitive_difference.md`, `refusal_as_difference.md`,
`refusal_difference.md`, and the fenced realization table in
`primitive_difference_map.md`.  Each was read before being listed, not
inferred from its heading.

**The sentence is WITHDRAWN and the section narrowed.**  This is the
established move here -- weaken the statement, never keep the wording
and lean on the receipt -- and it is the same move
`pr11_correction_ledger.md` documents.

Three points, because the narrowing is easy to over- or under-state.

1. *The six were not alike at this date.*  Five carried no fence. The
   sixth was fenced ("comparison only -- nothing above depends on this
   section") and cited a run directive as its authorization. Listing them as
   six equal violations would have replaced one wrong sentence with another.
   **Superseded 2026-08-27:** all six comparison sections now carry an
   explicit local fence.

2. *Historical conflict, superseded 2026-08-27*: the
   withdrawn sentence, the run directive the sixth section cites, and
   `CLAUDE.md`'s record that the 2026-08-11 clause is restored and holds
   "again without exception".  Section 13 no longer asserts the
   strongest of the three.  Choosing among them was not performed in this
   entry. **Superseded 2026-08-27:** the paper takes the fence path and
   leaves `CLAUDE.md` as the stricter operating boundary for future
   derivational work.

3. *What survives is still substantial, and is what the evidence
   supports*: the derivation was carried out blind, and no external name
   appears in `prompt/`, `code/`, `lean4/Derivation/`, `artifacts/`, or
   in the body of any `paper/` document above its final comparison
   section.

No gate detects the defect or the repair.  `ci/check_paper_citations.py`
checks that a cited path resolves; the vocabulary firewall bars a
denylist of identifiers, not prose naming of a theory.  The attestation
was an operator claim before this change and the narrowed version still
is.  A gate over comparison headings is possible -- all six sections use
one of two heading forms, so a literal scan would catch them -- but no such
gate was added in this entry. **Superseded 2026-08-27:** the comparison
sections are locally fenced; no automation is added here.


## The parked-module audit residual closed, and narrowed (2026-08-22)

Section 12 carried, as an open obstruction: *"Elaboration is not
auditing ... a module the root does not import contributes no `#print
axioms` report, so the axiom whitelist never inspects it ... it is left
OPEN rather than closed badly."*  It is closed, and the bullet is
rewritten rather than deleted.

**What closed it.**  `lean4/ParkedAudit.lean` enumerates the twelve
modules outside `lean4/Derivation.lean`'s import closure and emits one
axiom report per theorem, in the shape `#print axioms` produces, so the
existing whitelist reads them unchanged.  The inventory moves from 1417
reports (1424 after the intervening equivariance work) to 1472; every
one lies within `{propext, Quot.sound}`.

Two design points, both forced rather than chosen.  The census is a
second `defaultTargets` entry and not an import of the root, because
five of the twelve begin with `import Derivation` and the root importing
them is a cycle Lake rejects -- being unimportable by the root is what
"parked" meant for those five.  And the population is read from the
compiled environment (`Environment.getModuleIdx?`,
`ModuleData.constNames`, `ConstantInfo.isTheorem`) rather than from
source text, because the obvious pattern approach is the one already
known to fail here: a doc-string line beginning with the word `theorem`
has twice defeated a text count.

**The residual was demonstrated before it was closed.**  With a
`Classical.em` theorem placed in the parked
`Derivation/IsoCollapseCompat.lean`, the previous single-target build
reported `lean audit clean: 74 sources, 1424 axiom reports, axioms
within ['Quot.sound', 'propext']`; the same working tree with the census
enabled reported `FAIL: disallowed axioms ['Classical.choice']`, naming
the declaration.  Both states were observed minutes apart and the
injection reversed.

**What is NOT closed, stated here because the first draft of this work
overstated it.**  The census reports *theorems*.  A definition carrying
an axiom that no theorem reaches is unreported, and that is not the dead
letter it was first called: `Derivation.Minimality.Iso` is Type-valued,
so the parked isomorphism material is `def`-valued, `IsoBridge.lean`
contributes zero reports, and its content is unaudited.  Separately,
every census in the repository is rooted at `lean4/Derivation/`, so a
top-level `lean4/*.lean` is named by none of them -- including the
census module itself.

**Repairs made in the same change, each of which was a false or
misleading statement rather than a missing feature.**

1. `code/derivation/completion.py` resolved a theorem's module with a
   name terminator and its statement without one, so `theorem foo`
   matched the source line `theorem fooBar`.  Six committed records
   carried another theorem's statement, among them
   `Derivation.cost1_insufficient`, which the claim ledger cites.  Both
   patterns now share one terminator.
2. Adding the parked files to `DERIVATION_FILES` routed 31 of the 48 new
   theorems into `Derivation`'s declared role, stamping a commutativity
   and a strict bound as `preservation` -- the exact false label deleted
   on 2026-08-18.  They now resolve to the explicit absence, pinned by
   `test_unclassified_modules_are_pinned`.
3. `ci/check_ledger_evidence.py` anchored its report pattern to
   `Derivation.lean:`, so it read 1424 of the artifact's 1472 names and
   every parked theorem was invisible to its strongest matching tier.
4. Nothing read `defaultTargets`, so deleting one word disabled all 48
   reports with every gate green.  `ci/check_parked_audit.py` now checks
   the target and pins the report count; the disable was injected and
   the gate named it.
5. `ci/check_parked_audit.py` claimed an `import` "cannot be commented
   into existence"; it read raw text.  Comments are now stripped, which
   makes the claim true rather than narrower.

The paper, `README.md`, `paper/representative_selection.md`,
`paper/pr_review_template.md` and `.claude/skills/inject/SKILL.md` all
asserted the residual was open and are corrected here.  No gate reads
any of those sentences.

## G1 local finite-alphabet class theorem (2026-08-26)

The generator paper's old three-line terminal is preserved verbatim and
marked WITHDRAWN as the current complete block. Its generation theorem
remains supported. Its two five-strategy, 15-round repair findings remain
historical finite evidence, while the new result is recorded separately as a
horizon-free theorem over an exact declared class.

1. `Derivation.LocalStrategy` defines fixed-radius local strategies, a
   chain-independent finite declaration, firing, clearing, recurring import,
   and identity grade without conflating them. The locality proof is a field,
   not prose.
2. `strategy_capacity_collision` consumes
   `CapacityBound.capacity_bound` at the derived threshold
   `k ^ (2*d+1) + 2*d + 2`. `finite_local_not_clears` and
   `G1Class.g1_class_exclusion` prove the class-relative cycle exclusion with
   no finite horizon.
3. The five existing strategies are classified without forced membership.
   Bare, presence, and depth-two are finite local failures; per-pair marking
   is recurring and not finite; valued marking is one-time identity-grade,
   clearing, and not finite. A separate theorem supplies non-vacuity.
4. T5 is closed at general length by
   `radius_one_agrees_with_sealed_depth2`. The first proof shape was withdrawn
   after its use-site axiom report exposed a choice dependency; the repaired
   `decide`-based filter proof and all new use sites lie within
   `{propext, Quot.sound}`.
5. G3 remains conjectural. `clears_does_not_imply_not_fires` exhibits why the
   current pre-repair/post-repair predicates do not support the proposed
   corollary without a state-transition hypothesis.
6. **WITHDRAWN by the correction below.** This item said G4 was a finite split
   obtained by running the engine over 455 obstruction pairs. The loop did not
   pass those pairs to the engine; it repeated the four fixed Challenge-3
   catalogs.
7. `g1_class_receipt.json` deterministically binds the base and task hashes,
   toolchains, Python lock, prompt hashes, exact declarations, 34 new theorem
   reports, every finite bound, the five strategy verdicts, all terminals,
   and every OPEN/WITHDRAWN sentence introduced here.
8. Three new decision points were demonstrated by reversible injections: an
   inconsistent local fiber, a hidden outside-target G4 argument, and a
   missing named axiom report each failed the intended test by name and
   recovered after reversal. No artifact was regenerated under injection.
9. The first full completion-inventory test exposed a real integration
   defect: all LocalFiniteAlphabet/G1Class reports lacked source-module
   resolution. Both namespaces and all 34 new reports now carry explicit
   module/kind/role records, pinned by an exact-surface test. Ordered
   regeneration updated the completion graph and both axiom-dependent
   receipts; no `UNRESOLVED` record remains.
10. The next full run exposed the independent claim-schema boundary. All
    eight new claim IDs now carry explicit dependencies, assumptions,
    closed-vocabulary classes, Python/Lean/axiom fields, and falsifiers. The
    frozen heading census and generated body pin were deliberately extended
    to 135 entries; no new omission was added to a legacy-gap ratchet.

Terminals: LOCAL_STRATEGY_CLASS_DEFINED /
FIVE_STRATEGIES_CLASSIFIED / T5_PROFILE_CORRESPONDENCE_PROVED /
CAPACITY_APPLIES_TO_EVERY_CLASS_MEMBER / G1_CLASS_EXCLUSION_PROVED /
G3_REMAINS_CONJECTURE / G4_HOLDS_UNDER_MU2 /
G4_FAILS_AT_<3,mu1,reading_F_outside_target_argument> / OB1_UNCHANGED /
OBJECT_LANGUAGE_GENERATOR_NOT_IN_SCOPE. H1-H3 and H6 were skipped; H4-H5
were done. The two G4 strings in this historical block are WITHDRAWN by the
correction below. None of those hygiene dispositions advances OB-1.

## G4 correspondence and lock-receipt correction (2026-08-26)

1. The statements that all 455 chain obstructions reached the Challenge-3
   engine, that G4 held under `mu2`, and that its first `mu1` failure occurred
   at a derived chain coordinate are **WITHDRAWN**. The enumerated `pair` was
   used only as a label; `min_responses` always received the fixed target of
   reading L or F.
2. The false G4 runner, artifact, and dedicated test are removed. The
   surviving computation is the pre-existing Challenge-3 classification in
   `artifacts/challenges.json`: three `mu1` classes in L, five in F, and one
   `mu2` isomorphism class in each reading, all under their original declared
   bounds. No chain pair is quantified.
3. No collapse-preserving carrier encoding or L/F choice is silently made to
   replace the deleted loop. Such an adapter would be new declared structure;
   the existing minima do not authorize it. G4 therefore returns to
   `G4_REMAINS_CONJECTURE`.
4. The Python-lock receipt now pins the canonical LF Git blob of
   `requirements.txt`, SHA-256
   `932FDECBE9D0ACC035CE1C701B6E790B5CED06E16954FB9E5B1BD02F1839EDD5`.
   `.gitattributes` fixes that path as byte-preserving, and tests reject CRLF
   conversion rather than accepting a platform-specific checkout hash.
5. `g1_class_receipt.json` advances to schema v2, removes all G4 finite bounds
   and payloads, records the withdrawal, and retains the G1 class theorem,
   G3 conjecture, OB-1, and object-language boundaries unchanged.

Current terminals: LOCAL_STRATEGY_CLASS_DEFINED /
FIVE_STRATEGIES_CLASSIFIED / T5_PROFILE_CORRESPONDENCE_PROVED /
CAPACITY_APPLIES_TO_EVERY_CLASS_MEMBER / G1_CLASS_EXCLUSION_PROVED /
G3_REMAINS_CONJECTURE / G4_REMAINS_CONJECTURE / OB1_UNCHANGED /
OBJECT_LANGUAGE_GENERATOR_NOT_IN_SCOPE. No new event, generator, carrier
adapter, reading selection, or authorization rule is introduced.

## The D7 paper fence made explicit; policy still open (2026-08-27)

The D7 paper fence is made uniform, but D7 is not constitutionally closed.
The six comparison sections listed in `paper/paper.md` section 13 now all
say the same thing locally: they are post-hoc comparison only, not
derivational input, theorem evidence, or authorization, and nothing above
depends on them.

`CLAUDE.md` is left as the stricter operating boundary for future
derivational work. This change does not amend that authority record; it stops
the public paper and README from treating unfenced historical comparison
sections as part of the derivational claim.

Two placement defects remain recorded rather than hidden:
`paper/endogenous_generator.md` and `paper/primitive_difference_map.md` still
have substantive sections after their comparison surfaces. Terminal:

```text
OB3_PAPER_FENCE_UNIFORM
OB3_END_ONLY_PLACEMENT_DEFECTS=2
OB3_COMPARISON_POLICY_STILL_OPEN
AuthorityEffect: None
```

## Two-element transposition (2026-08-31)

`PrimDiff` now proves the map that collision already forgot.  The unique
non-identity permutation of the two-element carrier carries `D2` onto
`D2rev` and squares to the identity; both orientations share
symmetrization `S2`; that permutation is an automorphism of `S2` and not
of `D2`.  Unpointed, the inhabited irreflexive relations on that carrier
are exactly those three.  Python enumerates the same facts into
`primdiff.json:transposition`.  Claim `CL-PD-TRANSPOSE`.  No imported
names; the F1 tower remains a conjecture above this rung.

## Nine-slot inventory (2026-08-31)

A declared classification of existing objects, instantiated on the
two-element fragment: nine slots, each named for what it hosts
(carrier, local state, support, defect, reversal, closure, residual,
maps, terminal) in `lean4/Derivation/ObserverInventory.lean`,
`code/derivation/observer_inventory.py`, and
`paper/observer_inventory.md`.  Witness assignments are present as
data and are not derived as a unique inhabitant.  Relation
`Transpose` is an involution that carries `D2` onto `D2rev` and
agrees with carrier-swap pushforward on `D2` while remaining a
different operation.  Claim `CL-PD-INVENTORY`.  The slot names are
this repository's own; the classification itself is supplied, not
derived.

## Inventory review repairs and vocabulary refusal (2026-08-31)

Same-branch repairs before merge, from the completed review of the
transposition-and-inventory change:

- A single-letter slot grid and an outside phrase for the pair of
  maps in the reversal slot had been offered through the operator
  channel and briefly adopted; by author ruling they are refused as
  vocabulary.  The slots are renamed to this repository's own words
  (carrier, local state, support, defect, reversal, closure,
  residual, maps, terminal), the claim formerly named after the
  offered phrase is now `CL-PD-TRANSPOSE`, and the refusal is
  recorded in `paper/observer_inventory.md` §1 without reproducing
  the offered names.
- The terminal-slot sentence "no next state is a function of the
  carrier and local state" was a non-sequitur (the identity is such
  a function) and is narrowed to what the theorems prove:
  irreflexivity does not determine the local state.  Recorded in
  place in the paper and `CL-PD-INVENTORY`.
- Both censuses now state their decidability scope ("every decidable
  irreflexive relation"), matching the pointed census's precedent
  wording.
- The defect-slot ledger sentence is weakened to what
  `collision_is_not_obstruction` states, and the sealed
  `PrimDiff.collapse_unobstructed_without_fidelity` and
  `PrimDiff.obstruction_under_irrefl` now carry the collapse-map
  separation in the citation list.
- `swap_not_auto_of_D2rev` closes the "neither orientation" receipt
  gap; a duplicated pushforward helper is deleted in favour of the
  pre-existing one; the residual readers document their off-diagonal
  domain; named-elsewhere citations are now resolved against the
  Lean sources by test.

## Vocabulary purge, step 1: sealed comments, artifact strings, and outside names in live paper documents

Author direction (2026-09-01): purge the repository of outside vocabulary,
sealed portion first, the rest in steps so nothing breaks.  This entry
records step 1.  The instrument is the prose watchlist census (gate 12,
`ci/check_prose_watchlist.py`): every removal below surfaced as a stale
pin before the pin was regenerated, and no replacement word is itself
watched.  51 line edits across 24 source files; two committed artifacts
regenerated.

- Stage-sense wording.  The run stages of PR #12 had borrowed a word that
  also names an outside physical quantity.  It is replaced by "stage" in
  19 Lean doc-comment lines under `lean4/Derivation/`, 9 Python docstring
  and string-literal lines under `code/`, and one test docstring.
  `artifacts/primitive_contact.json` and
  `artifacts/primitive_completion_receipt.json` are regenerated from the
  changed literals: three string values each, no key changes.  No
  backticked ledger citation carried the word, so no evidence resolution
  moved (checked before editing).
- Loop transport.  Four comments (two in `FidelityClosure.lean`, one in
  the root inventory `lean4/Derivation.lean`, one in `completion.py`)
  named the closed-walk carrier action by an outside geometric word; they
  now say loop transport or loop action.  No theorem name changes.
- Candidate space.  Two docstrings (`primitive_core.py`,
  `run_primitive_core.py`) called the enumerated candidate universe by an
  outside order-theoretic word; they now say candidate space.
- Total weight.  `WeightProfile.lean` and `CL-PD2-WEIGHT-PROFILE` named
  the forgotten total by an outside word for it; they now say total
  weight, which is what `profile_forgets_total` states.
- Outside names in live paper documents, replaced by descriptions per the
  refused-grid clause of `CLAUDE.md`: in `weight_profile_contact.md` and
  `CL-PD2-WEIGHT-PROFILE`, a lift to an inner-product space and a
  squared-weight probability rule, signed scaled weights, and a
  circle-group action; in the fenced comparison table of
  `primitive_difference_map.md`, the vertex-minus-edge count of a tree
  and the alternating face count; in the `PrimitiveContact` refusal list
  of this ledger, a non-commutative-observable conclusion; and one
  English verb in `pr_review_template.md` that collided with a watched
  word.
- NOT changed in this step, recorded so it is not mistaken for oversight:
  this log's own historical entries, two of which carry an outside proper
  name in a 2026-08 entry title and body; stage-sense wording in the
  paper documents (about thirty lines across nine files, including this
  ledger); and the house words for closed-walk transport, the axiom
  order, and total weight in `paper/primitive_difference.md`,
  `paper/refusal_as_difference.md`, `paper/refusal_difference.md`,
  `paper/native_derivation_completion.md`, and this ledger.  Those are
  step 2, to be done together with the research trees that share the
  same words, so that a rename lands everywhere at once and the pins
  between trees are repinned once.

No theorem, computation, artifact key, claim ID, or claim status changed.
The seal is not amended: every edit is to a comment, a docstring, a
string value, or paper prose, and the derivation's recorded results are
untouched.  Verification: the affected tests, strict typing, the ledger
evidence gate, and the paper citation gate were run after the edits; the
Lean edits are doc comments only and the package was rebuilt.

## 2026-09-08 -- stale counts re-measured at `60c2cb05`

The measurements listed below were checked against the machine at
`60c2cb05d91cdfa099017c9cd205b52564db884b`.  Each stale figure below is
dated and superseded rather than overwritten, quoting the withdrawn
wording.  Measured: 77 Lean sources and 1530 axiom reports
(`ci/check_lean_audit.py`, `ci/check_axiom_report.py` on a fresh build
log); 75 modules, 63 in the root's closure and 12 parked
(`ci/check_parked_audit.py`); 516 tests collected, 515 passed and 1
skipped; line 99.10% and branch 96.71% (`ci/check_coverage.py`); and
539 + 710 + 1025 lines for the three collision modules.

- `paper.md`, the "elaboration is not auditing" bullet: withdrawn "The
  inventory is 1472 reports (the figure tracks the inventory and earlier
  read 1417, and 1314 before that)"; now 1530, dated and commit-pinned,
  with the chain of earlier readings kept.
- `paper.md`, the gate-status chain: the 2026-08-18 entry ("62 sources and
  1417 axiom reports ... 435 tests collected (434 passed, 1 skipped), line
  99.10%, branch 96.73%") stands as taken; a dated supersession is
  appended below it, which is the convention that chain already uses.
- `native_derivation_map.md`: withdrawn "`artifacts/lean_axioms.txt` now
  carries 1184 reports" and "checked name by name against all 1184
  reports"; now dated to the time of writing with the 1530 figure beside
  it, and the name-by-name check scoped to the reports it was run
  against.
- `primitive_difference_map.md`: withdrawn "Three modules, 2015 lines in
  the working tree (539 + 710 + 766; 1942 at the spine commit `ebb1e0b`)"
  and "(`artifacts/lean_axioms.txt`, 1184 reports)"; now 2274 lines
  (539 + 710 + 1025) and 1530 reports, dated, with the earlier figures
  kept.
- `skill_inbox.md`, the 2026-08-16 entry: withdrawn "covers only the 1314
  enumerated reports"; now dated to the entry with the 1530 figure beside
  it.
- NOT changed, recorded so it is not mistaken for oversight:
  `paper_claim_ledger.md`, `CL-PD2-CONTACT-RECONSTRUCTION`
  ("`artifacts/lean_axioms.txt`, 1184 reports").  Its body is
  digest-pinned by `tests/claim_ledger_body_pin.txt`, outside `paper/`,
  so that correction waits for a deliberate repin by the author.

No theorem, computation, artifact key, claim ID, or claim status changed.
Every edit is to dated prose, and the derivation's recorded results are
untouched.

Scope correction on review: the opening sentence originally read "A fresh
audit compared every number in `paper/` with the machine".  The recorded
commands cover the measurement families listed above; this entry records
no census or verification of every numerical statement in the paper.  The
name-by-name theorem check and the digest-pinned ledger value remain
outside this measurement update.

## 2026-09-08 -- reconciliation with the publication review, batch one

Source revision `f12a498e` (main); the external publication review of the
same date listed twelve findings, and this entry records the passages
changed for the first eleven.  Every change narrows a sentence to its
evidence or names a scope; no theorem, computation or artifact changed.
The recounts are pinned by `tests/test_paper_reconciliation.py`.

- `paper.md` section 10.11: withdrawn "from Challenge 3 round 1 onward,
  each datum's internal identity is exactly its profile" — false in the
  model (reading F, the first-round `mu2` minimum marking datum 1 leaves
  indices 0 and 2 collapsed).  Now: identity is the index; a valid
  response separates the challenged pair, other distinct data may stay
  observationally equivalent.  New entry `CL-IDENTITY-NOT-PROFILE`.
- `paper.md` section 2 bounds, section 8 tree bullets, terminal clause
  (g); ledger `CL-TREE-MU2-COMPLETE`,
  `CL-REACHES-REQUESTED-DEPTH-WITH-EXTERNAL-SUPPLY`: withdrawn "15
  requested augmentation rounds" and "the full tree to the requested 15
  rounds is fully enumerated".  The engine's depth counts transition
  steps, supply included; completed `mu2` leaves carry 10 to 12
  separation responses (L 527 / 41 at 10 / 11; F 268 / 605 / 12 at 10 /
  11 / 12).  New entry `CL-TRANSITION-STEPS-VS-RESPONSE-ROUNDS`.
- `paper.md` section 8 mu1 bullet; ledger `CL-TREE-MU1-FRONTIER`:
  withdrawn "at depths 7 / 6" for the guard cut.  First cuts are at 6 / 5,
  maximum depths 7 / 6, frontier across two levels (L 47 + 880, F 303 +
  583).
- `paper.md` section 3 definition 6: withdrawn "a finite multiset of
  items"; a delta is an ordered list, the enumerator's canonical order is
  the convention, the cost measures read the items.
- `paper.md` section 3 opening and ledger `CL-TOKEN-ERASURE`: "the bridge
  is proved" now names its endpoints — the two Lean models; the Python
  implementation is connected by executable checks, not by a proof over
  the source.
- `paper.md` section 11 register bullet, the R6 paragraph and the R6 / R7
  rows; ledger `CL-COUNT-INVARIANCE`: the discharged transports act on
  datum indices with forms fixed; full two-bijection collapse transport is
  credited to `collapsed_transport`, `collapsed_renameForms`,
  `collapsed_renameDataForm`; withdrawn "the count is a component of the
  canonical key" (false: the key carries no such count).  New entry
  `CL-REGISTER-SCOPE`.
- `paper.md` section 8 mu2 bullet and terminal clause (g): the
  completeness of the `mu2` quotient trees now carries the ledger's
  condition — the orbit challenge policy losing no child classes.
- `paper.md` section 10 item 10: withdrawn "what is proved: determinism
  of the engine (byte-identical artifacts)"; determinism is finite
  computation (`CL-DETERMINISM`), completeness is a bounded theorem under
  its conditions.  Section 5 inertia item: the forcing clause is a
  structural property of the declared grammar, tagged **[definition]**,
  the bare-supply case **[theorem]**; ledger `CL-0-INERTIA` scoped the
  same way.  Ledger
  `CL-PD2-RECEIPT-BYTES`: withdrawn "the universal is a property of the
  hash construction".
- `paper.md` opening: the ledger's measured classification debt (137
  entries; 85 composite classes, 6 without a class) is disclosed beside
  the paper's own promise; the normalization is open work.
- `paper.md` new section 14: the publication unit (sections 1 to 11), the
  sixteen ledger entries the paper cites, and where the supplementary
  sections live.
- `paper.md` section 13: the mechanically checked present-file
  properties are separated from the operator's attestation of blindness
  (dated 2026-08-16); withdrawn "what survives, and is checked: the
  derivation itself was carried out blind".

The body pin `tests/claim_ledger_body_pin.txt` was regenerated
deliberately for all 140 entries: the seven edited entries, the three new
ones, and `CL-G1-TERMINAL-20260826`, whose parsed body runs to the next
heading and now ends where the appended section begins.  The frozen
heading census in `tests/test_claim_ledger_conformance.py` gained the
three new IDs at its end.

Not changed here, and recorded so it is not mistaken for oversight: the
ledger's `KNOWN_*` conformance debt (finding nine of the review) beyond
its disclosure; the `CL-PRUNE-RULE` and `CL-CAP-BOUND` propagation items
and the collision reconstruction count binding (finding twelve), which
follow in the next batch.

## 2026-09-08 -- reconciliation with the publication review, batch two

Source revision `fe84ce09` (the batch-one commit).  Three propagation
items of finding twelve, closed at their sites:

- `CL-PRUNE-RULE`: the statement's clause (ii) said "computational" while
  the class said "theorem (bridge proved 2026-08-18)"; the statement now
  says proved, naming `applyDelta_dropRules`.
- `CL-CAP-BOUND`: the two OPEN residuals now carry a forward pointer to
  the G1 entries that discharge their restricted forms
  (`CL-G1-CAPACITY-APPLICATION`, `CL-G1-CLASS-EXCLUSION`); the
  unrestricted forms stay open.
- `CL-PD2-CONTACT-RECONSTRUCTION`: "1184 reports" is bound to the
  2026-08-13 run, with the 1530 figure at `f12a498e` beside it.  This
  closes the item the 2026-09-08 stale-count entry recorded as "NOT
  changed", and the body pin `tests/claim_ledger_body_pin.txt` is
  regenerated deliberately for the three edited entries.

Outside `paper/`, the same batch adds `research/README.md` (which research
trees the workflow enumerates, which are local receipts, and which
verifier files are hand copies), names the eight registered research
verifiers the gates skill omitted, with
`tests/test_gates_skill_matches_workflow.py` to hold the skill to the
workflow, and repins the primitive-difference manifest to the batch-one
commit.  No theorem, computation or artifact changed.

## 2026-09-23 -- terminal descriptor scope and author vocabulary ruling

The final paragraph of `native_derivation_completion.md` withdraws the
unqualified initial-member wording. It states unique probe compliance in
the declared 64-member descriptor class, does not claim categorical
initiality, and binds the single OPEN edge to the declared bridge graph.
This incorporates the preserved correction `9e4d724a` at the author's
explicit request. No Lean theorem or sealed computation is changed.

The author separately approved the exact vocabulary rule now in
`CLAUDE.md`. Section 13 records it: explicitly classified supplied vocabulary
is permitted in research outside the seal, and the six already fenced
comparison sections are preserved as historical records in their existing
positions. They are not derivational inputs, theorem evidence, or permission
to extend sealed comparison. External citations remain prohibited and the
scanner populations are unchanged. The policy and placement questions are
resolved by this author act; historical blindness remains an attestation.
