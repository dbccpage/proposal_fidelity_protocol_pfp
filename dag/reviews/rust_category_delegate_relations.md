# Delegated Rust relations and separation audit

Complete:5/5 full bodies;3322 lines,116622 bytes;0 partial/bounded/pending.4 claims,7 findings,8 independent controls. No Rust/native/provider execution or source edits.

The concrete reusable contributions are exact finite report-respecting bisimulation, bounded-morphism factorization, SCC/preorder distinctions, and admitted rational quotient separation with strict decoder threshold. The other owners range from explicitly discrete relational declarations to registry descriptors and a dormant Grothendieck draft.

## Per-file assessments

### code/rust/core_category_theory/src/family_category.rs

SHA `45d1c9f3226b803f7888f00315d88f6d8e7b9974f7c8d6fce421540593ebb0f7`; full lines1–567.

Full567-line body, including documentation, every constructor/map/query and all inline tests. Useful active-member/lifecycle registry, deduplicated propagation among active targets and arbitrary per-key capability mappings. No category objects/arrows/composition/identity definitions or functor/naturality laws are implemented: Constraint/PropagationRule are descriptors, String is standard string and AgentFunctor import is commented out. Unknown severity becomesLow and unknown lifecyclePlanned; mappings allow unknown keys/duplicate strings. Public mutable fields admit arbitrary registry data. Generic item-count boundary is unrelated to registry populations. Tests check parsing/filtering/target lookup/construction and scalar capacity only; mutation-count claim is historical, no mutation campaign reproduced.

No external implementation dependency needed for these standard-library registry operations. AgentFunctor is a commented reference, not a linked implementation.

### code/rust/core_category_theory/src/finite_profunctor.rs

SHA `3f21e216c85d52fa8428e9da016a2702503e94825b89fa7a6dcaf786e5edba61`; full lines1–493.

Full493-line body, all relations/actions/maps, weighted methods, composition, companion/conjoint, boundary validator and inline tests. Sparse finite witness multisets with source/target names; action tables are declared but never admitted, applied or checked for totality/identity/composition/commutation. Validator checks category names and relation-key objects only; its boundary_checks label is accurate but not full profunctor law admission. Discrete-middle coproduct is explicitly scoped and does not pretend to general coend quotienting; supplied middle enumeration must be complete and unique, but neither condition is checked. Companion/conjoint collect the mathematically correct Hom fibers under admitted F,C,D but construct no action maps and do not validate input category/functor/name. Finite nonnegative insertion guard can be bypassed by public maps; even valid finite weights may sum to infinity. Pair labels are unescaped strings, not injective tuple encoding. Three mathematical/data tests plus unrelated capacity test read, not run.

cat_functor::DeclaredFiniteFunctor, finite_category::DeclaredFiniteCategory and validation report owners are parent-reviewed dependencies; not reread or credited here. No assumption that these callers automatically validated inputs.

### code/rust/core_category_theory/src/finite_relational.rs

SHA `ce1db361b5b5aebe2ecf2f8fe3f47f10662a3fa7dcd81b951afeaf84017772ab`; full lines1–612.

Full612-line body including admission, exact partition refinement/replay, behavior-set union, bounded factorization, SCC/preorder algorithms and all tests. Nonempty relational carrier, exact shape/range checks, duplicate successors rejected and successor sets sorted; zero labels allowed. Refinement starts from report equality and includes old block, so it only splits and stabilizes within n-1 strict rounds. Full receipt recomputation rejects unnecessarily fine stable partitions and history tampering. same_behavior_set is unpointed and requires identical report/label interpretation; it does not infer correspondence from arbitrary report IDs. Bounded morphisms enforce surjection, reports and equality of successor images (forth and back), giving target-to-minimal-source factor. Raw reachability/SCC quotient distinction is explicit. Private fields protect invariants; unreachable unwraps rely on those proofs, not unchecked external receipts. Finite resource cost remains unbounded by explicit n ceiling; no clock/trace/HoTT/physical semantics claimed. Independent4096-case Python reconstruction matches greatest-relation elimination; this is separate from the read4096-case Rust test, which was not executed.

Standard library only. No unreviewed domain dependency; no native compiler/runtime execution.

### code/rust/core_category_theory/src/finite_section_separation.rs

SHA `16b2bb3081fc4cb496c1165770ab0ac30037d935b6f18099188ff55b346c0bb3`; full lines1–1120.

Full1120-line exact source/prose/test body. Private SectionRecord admits explicit common domain and exact total BigRational values; weights total/nonnegative, zero weights intentionally allow pseudometric collisions. FinitePseudometric admits complete pair table and all nonnegative/zero-diagonal/symmetry/triangle laws with512-point bound; empty metric allowed, separation rejects fewer than2points/classes as typed nonverdict. FiniteEquivalence explicitly checks laws rather than silently closing, canonical classes ordered by least point; redundant empty classes normalize away. Main separation correctly distinguishes E not subset zero kernel, zero collision, and strictly positive attained interclass gap. Separated replay redecides/checks full table/classes/gap; ZeroCollision replay omits carrier equality and E subset zero-kernel admission and can accept when decision refuses. Weighted wrapper allocates/computes n² rows before512 guard; equivalence construction has no analogous ceiling and pair iteration may be quartic; coordinate and rational bit lengths unbounded. Epsilon decoder validates through DP-1 total-table owner, exact error bounds, output-restricted gap and strict2epsilon<gap, then obtains a class-valued factor. One-class output is intentionally refused because this API requires a positive interclass gap. Inline mutation test checks only standard Result Ok/Err, not actual owner predicates; external tests not inventoried in this slice.

finite_report_query.rs is parent-reviewed prior evidence (RCT-C22), not a fresh read here. num_rational::BigRational and num_traits are third-party dependencies not reviewed/built.

### code/rust/core_category_theory/src/grothendieck_construction.rs

SHA `17a6624c93ff39dd1e6d974bfbacb998e5ed832c47507d4f52161621e7804448`; full lines1–530.

Full530-line body read including every nested commented draft/test and active capacity code. Outer Rust block comment spans1–411, so CategoryOfElements, SetValuedFunctor, unsafe transmutes, ColorFunctor and proposed fibration/opfibration tests are inactive. Active module implements only generic count/capacity record/errors/test. Draft mathematical defect: covariant Set-valued functor gives discrete opfibration; arbitrary preimage does not give cartesian lift when a fiber has two preimages. Draft ColorFunctor returnsNone on identities, violating functor identity; ElementMorph equality ignores base morphism and would collapse parallel arrows; unsafe generic transmutes are not sound representations. These are dormant design gaps, not current executed unsafe code. L4 boundary labels and mutation counts cannot establish a working Grothendieck construction.

core::Category/arrow::Morph/Obj/fibration references occur only inside inactive draft; not read as implementation dependencies. Standard library capacity owner only is active.

## Claims

### RDR-C01 — Finite relational refinement supplies a concrete report-respecting greatest-bisimulation mechanism.

Admitted successor sets, report equality and repeated splitting compute stable quotient; receipt verification recomputes full result/history. Surjective bounded maps require the back condition, and SCC condensation changes carrier rather than manufacturing strict order on cyclic raw states.4096 independent small systems match a separate greatest-relation fixed-point algorithm.

Strong set-level bisimulation; report/label meanings are supplied and identical across compared systems. No trace/clock/physical equivalence or compiled execution claim.

Evidence: `code/rust/core_category_theory/src/finite_relational.rs:191–218`; `code/rust/core_category_theory/src/finite_relational.rs:239–327`; `code/rust/core_category_theory/src/finite_relational.rs:330–403`; `code/rust/core_category_theory/src/finite_relational.rs:405–452`.

### RDR-C02 — Exact finite pseudometric and equivalence admission makes the main separation criterion useful.

Complete exact tables are checked for all pseudometric/equivalence laws. The main decision checks E⊆Z, finds zero collisions, and otherwise produces complete pair distances and an attained positive gap when at least2classes exist. Independent finite representative-independence checks support E⊆Z iff quotient distance is well defined.

Private admitted data and exact rational arithmetic are assumptions. Zero-collision replay has the separate RDR-F01 gap. Third-party rational arithmetic was not audited.

Evidence: `code/rust/core_category_theory/src/finite_section_separation.rs:139–175`; `code/rust/core_category_theory/src/finite_section_separation.rs:208–341`; `code/rust/core_category_theory/src/finite_section_separation.rs:510–600`; `code/rust/core_category_theory/src/finite_section_separation.rs:674–768`.

### RDR-C03 — The epsilon-decoder construction preserves strict threshold and declared-domain assumptions.

Total report/query/decoder tables are delegated to DP-1; errors are measured in the admitted ambient pseudometric. Output restriction supplies the gap, requires2epsilon<gap, and class-query factorization is then checked. Independent finite line-metric controls confirm fiber diameter≤2epsilon and constancy under strict gap.

finite_report_query source receipt RCT-C22 is prior parent evidence, not fresh dependency reading. At most1output class is refused by this gap-specific API. No global physical/report interpretation is derived.

Evidence: `code/rust/core_category_theory/src/finite_section_separation.rs:922–972`; `code/rust/core_category_theory/src/finite_section_separation.rs:974–1102`.

### RDR-C04 — Discrete-middle profunctor composition has a useful narrowly declared coproduct meaning.

The implementation explicitly restricts composition to a discrete middle and forms all declared witness pairs. Companion/conjoint Hom-fiber formulas have the correct variance, conditional on valid input functor/categories. These are finite data mechanisms, distinct from the parent-reviewed older general coend owner.

Requires complete unique middle-object enumeration and admitted outer action laws; current code does not establish these. No general coend quotient, category/functor certificate or new task-specific workflow is inferred.

Evidence: `code/rust/core_category_theory/src/finite_profunctor.rs:139–197`; `code/rust/core_category_theory/src/finite_profunctor.rs:209–259`.

## Findings

### RDR-F01 — ZeroCollision replay can accept an outcome when the decision refuses the quotient.

The collision branch checks only known metric pair, zero distance and inequivalence. It omits carrier equality and E⊆Z. In the admitted three-point pseudometric d01=0,d02=d12=1 with E={{0,2},{1}}, decide_separation refuses IdentificationNotZero, while replay accepts collision(0,1). The enum explicitly says the outcome assumes E⊆Z, so the replay promise is false for this branch.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Reapply input carrier/quotient admission in the collision branch, then validate the chosen zero witness without requiring a canonical pair.

Evidence: `code/rust/core_category_theory/src/finite_section_separation.rs:659–670`; `code/rust/core_category_theory/src/finite_section_separation.rs:739–755`; `code/rust/core_category_theory/src/finite_section_separation.rs:787–805`; `code/rust/core_category_theory/src/finite_section_separation.rs:871–896`.

### RDR-F02 — The weighted metric wrapper performs expensive work before its advertised point ceiling.

weighted_coordinate_pseudometric creates records.len² rows and exact coordinate sums before calling the512-point-admitting constructor.513 records therefore compute263169rows before ResourceLimit; multiplication can overflow at extreme usize counts and allocations/BigRational sizes are not bounded. Equivalence law admission independently has no input ceiling and nested relation-pair scan can be quartic.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Check point/coordinate/pair/bit-size budgets before allocation and use checked capacities; retain typed refusal before expensive work.

Evidence: `code/rust/core_category_theory/src/finite_section_separation.rs:60–64`; `code/rust/core_category_theory/src/finite_section_separation.rs:208–225`; `code/rust/core_category_theory/src/finite_section_separation.rs:472–492`; `code/rust/core_category_theory/src/finite_section_separation.rs:510–600`.

### RDR-F03 — Declared profunctor boundary validation does not establish action laws or complete discrete-middle scope.

Public left/right action tables can contain arbitrary indices and missing/nonfunctional maps; validate_relational_profunctor ignores them and only checks category names/relation objects. Companion/conjoint leave both action tables empty. Repeating a middle object duplicates product witnesses and omission silently drops support. Declared names and boundary_checks avoid claiming full admission, but consumers must not promote this report to a true profunctor/coend certificate.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Add explicit admitted category/action inputs and complete unique middle carrier, or expose these strictly as sparse declared relation/multiset operations.

Evidence: `code/rust/core_category_theory/src/finite_profunctor.rs:16–36`; `code/rust/core_category_theory/src/finite_profunctor.rs:148–197`; `code/rust/core_category_theory/src/finite_profunctor.rs:214–259`; `code/rust/core_category_theory/src/finite_profunctor.rs:265–320`.

### RDR-F04 — Finite nonnegative weighted witness insertion does not guarantee finite aggregate mass.

Individual insertion rejects negative/nonfinite weights, but total_weight sums f64 values unchecked. Two maximum finite weights produce infinity. Public weighted_relations permits bypassing insertion admission entirely; no end-to-end mass invariant or numerical error bound is provided despite the computational-profile label.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Use exact rational/checked accumulation or refuse nonfinite total and constrain direct mutation; state numerical scope explicitly.

Evidence: `code/rust/core_category_theory/src/finite_profunctor.rs:81–132`; `code/rust/core_category_theory/src/finite_profunctor.rs:417–448`.

### RDR-F05 — Family functor terminology names a registry without category/functor/naturality checks.

FamilyFunctor owns two HashMaps of string vectors; map_constraint/map_propagation accept arbitrary names and do not establish source/target morphisms, identities or composition preservation. Meta-String natural transformation is documentation only. The useful mechanism is active-member filtering and scoped propagation, and should not be counted as implemented categorical learning.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Retain registry utility with accurate status; introduce admitted algebra only where a concrete workflow needs and checks its laws.

Evidence: `code/rust/core_category_theory/src/family_category.rs:15–27`; `code/rust/core_category_theory/src/family_category.rs:249–286`; `code/rust/core_category_theory/src/family_category.rs:293–361`.

### RDR-F06 — The Grothendieck module has no active category-of-elements implementation and its dormant cartesian-lift claim is false.

Lines1–411 are one outer block comment including nested comments/tests. The active owner is only scalar count/capacity admission. The draft covariant functor gives an opfibration; selecting Red from F(A)={Red,Blue} mapping toGreen cannot provide a cartesian lift of Green because Blue has no vertical arrow toRed over id_A. Draft identity action returnsNone and arrow equality ignores base morphism. Unsafe casts occur only in inactive text.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Keep status dormant/proposed; implement and verify typed category-of-elements/opfibration laws before claiming this mechanism, and use actual cartesian universality if fibration is intended.

Evidence: `code/rust/core_category_theory/src/grothendieck_construction.rs:1–160`; `code/rust/core_category_theory/src/grothendieck_construction.rs:180–220`; `code/rust/core_category_theory/src/grothendieck_construction.rs:319–345`; `code/rust/core_category_theory/src/grothendieck_construction.rs:411–530`.

### RDR-F07 — L4 capacity and mutation declarations do not cover the named categorical mechanisms.

Family/profunctor/Grothendieck BoundaryRecord tests exercise only1≤count≤capacity. They have no connection to functor actions or Grothendieck data. Section-separation mutation test merely asserts standard Result Ok/Err. Inline killed=6 comments contain no executable mutant population or source-bound receipt here. Finite-relational tests are materially stronger but still only read, not run in this audit.

Source review and explicitly independent finite controls only; no Rust build/test execution.

Next: Keep historical assertion separate from demonstrated mutation evidence; test actual owner invariants and retain each mutant/source/result binding.

Evidence: `code/rust/core_category_theory/src/family_category.rs:372–456`; `code/rust/core_category_theory/src/family_category.rs:542–567`; `code/rust/core_category_theory/src/finite_profunctor.rs:331–415`; `code/rust/core_category_theory/src/finite_profunctor.rs:468–493`; `code/rust/core_category_theory/src/grothendieck_construction.rs:419–530`; `code/rust/core_category_theory/src/finite_section_separation.rs:1105–1120`; `code/rust/core_category_theory/src/finite_relational.rs:461–612`.

## Controls and dependency limit

- RDR-T01: Partition refinement matches independent greatest-relation elimination. `{"systems": 4096, "states": 3, "labels": 1, "report_colors": 2, "all_relations": 512, "max_recorded_partitions": 3}`

- RDR-T02: Back condition refuses a forward-only deadlock collapse. `{"forward_preserving": true, "bounded_morphism": false, "missing_successor_state": 0}`

- RDR-T03: Collision replay accepts a witness when the decision must refuse ill-defined quotient. `{"metric": [["0", "0", "1"], ["0", "0", "1"], ["1", "1", "0"]], "equivalence_classes": [[0, 2], [1]], "decision": "IdentificationNotZero(0,2,1)", "supplied_collision": [0, 1], "collision_branch_accepts": true}`

- RDR-T04: Finite quotient-distance criterion agrees with representative independence. `{"admitted_three_point_integer_pseudometrics": 15, "partition_checks": 75, "distance_range": [0, 1, 2]}`

- RDR-T05: Exact decoder threshold enforces report-fiber constancy under its assumptions. `{"enumerated_cases": 648, "strict_gap_qualified_cases": 16, "boundary_example": "q=(0,2), one report, decoder=1, epsilon=1 has 2epsilon=gap and must be refused"}`

- RDR-T06: Finite weighted summands can overflow and repeated middle objects overcount. `{"finite_summand": "1.7976931348623157e+308", "sum": "inf", "single_middle_true_pair_count": 1, "repeated_middle_implementation_count": 2}`

- RDR-T07: Grothendieck draft is inactive and arbitrary preimage is not a cartesian lift. `{"outer_comment_ends_line": 411, "active_category_of_elements_implementation": false, "countermodel": "walking arrow A->B with F(A)={Red,Blue}, F(B)={Green}; chosen Red lift cannot factor Blue over id_A"}`

- RDR-T08: Weighted wrapper performs quadratic work before the point ceiling. `{"n": 513, "rows_built_before_refusal": 263169, "guard_points": 512, "no_large_allocation_performed": true}`

DP-1 dependency receipt: `dag/reviews/additional_rust_category_remaining.json`, claim RCT-C22, source `code/rust/core_category_theory/src/finite_report_query.rs`, SHA `be0e0595acf4314cfb41f91548cd36c9f1ce807d021eff73c0b68958a8aed633`. This is parent evidence, not a fresh delegated source read. Other category/functor/validation and rational-library dependencies are explicitly bounded in file notes.
