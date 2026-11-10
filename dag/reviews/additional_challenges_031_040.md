# C031–C040 mathematical audit (complete)

Pinned source: `8050c66900899771766f33e8f5fdd200b7dd9120`. 199/199 source files fully read; 1012/1012 data files have per-file dispositions. 0 paths remain pending.

Source reads, artifact replays, and historical provenance claims are separate. No source changes or provider calls.

The 199 full reads cover 35,136 lines. All 1,211 current files match frozen SHA-256 pins; no duplicate JSON keys, timeouts or execution errors were found. All 420 judge cases and 92 examples pass their owner replays; all 479 retained mutants are rejected. The retained answer stream and 20 metadata files have separate dispositions. These results do not certify the broader mathematical claims: counterexamples and unverified premises below remain material.

Independent arithmetic detects six retained C035 character inputs whose identity value does not match the stated coefficient. All 956 manifest references match raw bytes, while C038 and C039 retain stale declared_file_count values (100 vs 101 and 102 vs 103); their files_count fields are correct.

## C031

Finite exact integer equations sum(q)=sum(q^3)=0; nonzero bound, gcd1 and task-defined non-vector-like chirality; canonical representative under permutation and global sign. Algebraic final-pair quadratic derivation and independent enumeration MITM are coherent under stated integer premises.

46 judge cases and12 examples pass both;45 mutations reject;12 retained answer lines replayed.96 manifest refs raw-match.Independent brute-force complete where <=1m combinations, explicit arithmetic-only ceilings elsewhere.

- AC31-F01: Both checkers accept SOLVED with excluded fixed0 or fixed charge outsideQ; neither revalidates all fixed-input domain.
- AC31-F02: Result IDs are not bound, and OOS kind only is checked; false index/charge witness accepted. case_id-only wellformed inputs can receive accepted MALFORMED_CASE_STRUCTURE.
- AC31-F03: Both negative completion claims share one reference search; trusted false ground_truth admits false empty enumeration; dual agreement is not independent completeness in these modes.

Limits: Negative completion both routes call same complete_chiral_u1. Optional supplied ground_truth replaces enumeration completeness in both; only as strong as that trusted input. Chiral is defined here as not wholly vector-like, permitting spectator opposite pairs; paper uses stricter no mass-term reading. Runner directly imports/executes candidate; docstring sandbox claim not realized. DDC hashes certify encoded labels, not derivations. README/test-ready name absent governance/commitment files and stale36mutant count; current45 retained mutants replayed, no live execution certified. solve_pair O(1) docstring excludes zero-sum branch: it enumerates O(Q) opposite pairs.

## C032

Rational H,V, anomaly trace identities and symmetric Gram inertia for a fixed catalogue. Table coefficients and full Cartan-weight polynomial coefficients agree on70 supported group/rep pairs.125 exact2x2 inertia controls pass independent determinant/trace sign check.

42judge and10example cases pass both;46 retained mutants reject;93manifest refs raw-match. Independent dimension/gravity arithmetic across solved outputs; trace/inertia replay has stated owner premises.

- AC32-F01: Both early ANOMALOUS branches accept false first_failure lhs/rhs/factor and arbitrary unrelated allowed arithmetic payloads.
- AC32-F02: Passing certificates accept absent quartic records and false B_adj/group/ok fields; only reported B_hypers is compared when a valid index is present.
- AC32-F03: SOLVED branch misses domain restrictions: accepted nonpseudoreal half SU3fund with H truncated3/2 to1, and T31 above bound30.
- AC32-F04: One-factor-only half-hyper rule emits accepted nonpseudoreal witness for genuinely pseudoreal SU2fund x SO7vect product. Mathematical counterproof epsilon2 tensor I7 supplies exact boundary.

Limits: Only named fundamental/adjoint/symmetric/antisymmetric/spinor catalogue, not arbitrary highest weights from challenge prose. Condition3/4 are constructed formulas, not separate tests of supplied lattice vectors. No full Gram cross-term payload; real inertia is not an integral unimodular lattice or positive gauge kinetic/construction proof. The two inertia functions implement nearly identical elimination despite distinct method labels. Reference and both OOS checks restrict half-hypers to exactly one nontrivial factor; this is narrower than pseudoreal tensor products. SU2fund x SO7vect has invariant antisymmetric epsilon2 tensor I7. Runner does not unwrap example case envelopes and runs candidates in-process; no process isolation. Accounting is budget config only, not enforcement or billed evidence.

## C033

Finite crystallographic root data; Weyl dimension, Freudenthal and Kostant characters; tensor route uses common Brauer-Klimyk reference. Independent A1 closed character/Clebsch-Gordan checks applied to eligible files.

All108 data replay complete:46judge+12examples PASS,48mutants FAIL,manifest and budget config checked.

- AC33-F01: Hard n>25 Freudenthal cutoff loses zero weight for highest A1[54], dimension55: reference fails both checkers; exact character passes Kostant and fails Freudenthal.
- AC33-F02: Both checkers accept SOLVED on excluded boolean highest-weight input True.
- AC33-F03: Kostant alone accepts a non-dominant representative -2 in place of2 in A1[4] dominant table; dual catches it.

Limits: Both tensor checkers share the same decomposition function; distinct names do not supply independence. Root/Cartan/Weyl data shared across character routes. Exact finite checks do not prove all dimensions up to1m.

## C034

4D rational facet/polar vertex determination, exhaustive bounding-box integer points, face incidences and admitted Batyrev Hodge formula. Quintic independently counted by shifted simplex:6 and binomial(9,4)=126;five facets each4 interior points gives1,101.

All108 data replay complete:46judge+8examples PASS,52mutants FAIL; manifest and config checked. Flat examples handled as input with embedded expected_output; earlier audit adapter errors corrected and replayed.

- AC34-F01: Both checkers unconditionally accept multiple_interior_points OOS on reflexive quintic with false point99.
- AC34-F02: Both accept false codim2 factors and arbitrary optional side/facet arrays; only combined product sum is checked.
- AC34-F03: Both accept45input points, invalid reading interpreted primal, and missing answer ID; domain/binding incomplete.

Limits: Second checker contains no HNF basis/Pick theorem implementation despite header; both enumerate global bounding boxes. Mirror check algebraically swaps identical computed expressions, not separate mirror computation. Bounding boxes can be expensive; no native/Rust/PALP engine run. Only aggregate correction sum verified; full face certificate not certified.

## C035

Finite coefficients throughq30 via Laurent theta-product/Appell-Lerch and rational half-period series; all31 full residual polynomials checked zero. All676 embedded character inner products orthonormal and dimension-square sum244823040. Distinct character projection and rational-system solvers are conditional on embedded M24 table.

All96 data replay complete:38judge PASS,48mutants FAIL,8example inputs replayed,manifest/config checked. Six retained solved decompositions fail advertised n-to-An identity binding.

- AC35-F01: Both checkers accept trivial character for n1 with identity1 != A1=90 and ignore noninteger n; decomposition is generic character arithmetic, not verified nth moonshine component.
- AC35-F02: Both accept fabricated OOS kind/irrep/value on a noncharacter, including nonnumeric value.
- AC35-F03: Malformed string character value returns reference UNKNOWN but both checkers reject that warranted refusal; float24 is accepted in specialization despite exact integer contract.

Limits: Character table copies have internal consistency, not authenticated GAP source custody. No twining-genus generator establishing each supplied class function as An(g); six solved retained cases have identity value unequal to current series An. TASK equation omits A0=-2 and q-shift in massless prefactor while later prose and runtime incorporate them; EOT equations1.3,1.7-1.11 support retaining these. C1 and reference residual assertion inspect only y^(-1),y^0,y^1; audit full-monomial residual checks pass at all31 orders. C2 ignores radicand in imaginary linear rows; C1 projection assumes same radicand per class, neither validates input triple p catalogue. No abstract moonshine module or physical explanation certified.

## C036

Exact factorial/harmonic periods for four admitted weighted hypersurface families; coefficient and Newton mirror-map reversion routes compute the admitted normalized Yukawa series. Independent Lagrange reversion, multicover divisor sums, kappa and first GV formula agree in all 40 family/order controls. This is conditional series arithmetic, not a derivation of the geometric mirror theorem.

All 84 pinned data files replayed: 28 judge cases, 48 mutants, six examples and two metadata records. Full owner/checker/tests source read separately.

- AC36-F01: Both rational-string guards accept a repeated minus prefix before converting it with int; malformed gw value --1/2 raises ValueError instead of returning a rejection.
- AC36-F02: The participant specification omits the central normalized z-Yukawa formula actually used by the reference and both checkers; agreement depends on that external mathematical admission.

Limits: Both owner routes admit the same Yukawa normalization and family geometry. The so-called PF route uses a factorial-ratio differential recurrence, not an independently derived fourth-order geometric operator. The participant task does not supply the central z-Yukawa expression used by all implementations. All executions are local Python with bounded per-file time; no live model or billing evidence.

## C037

C1 derives every candidate coefficient by cyclotomic reduction of finite Verlinde sums; C2 constructs truncated Clebsch-Gordan products with Kac identification and explicitly checks finite associativity and identity. An independently implemented path-graph adjacency/Chebyshev recurrence matches the reference for all 65 allowed SU2/minimal parameter choices. These are conditional finite fusion-ring calculations, not a CFT construction or unitarity certificate.

All 92 pinned artifacts replayed: 34 judge cases and eight input-only examples PASS; 48 mutants FAIL; one manifest and budget declaration checked. All solved outputs also pass independent full-table matrix recurrence checks.

- AC37-F01: Both checkers ignore answer ID equality and accept a wrong ID on an otherwise correct solution. Boolean input exits even before required ID/refusal/schema checks: {status: UNKNOWN, arbitrary: anything} passes.
- AC37-F02: Both rational parsers raise ValueError on central_charge --1/2; unknown-model refusal accepts fabricated codes, and invalid_p_prime witness accepts a fabricated parameter value.
- AC37-F03: Reference trace asserts ring_axioms_satisfied and factored_su2_verlinde_descent for minimal models without running those computations; the actual independent checks occur only in separate judge checkers.

Limits: C1 and C2 share model formulas by specification; reference minimal computation uses combinatorial products, despite trace labels claiming factored Verlinde descent and ring audit. Commutativity audit fills symmetric tensor entries by construction; only canonical triangular output is supported. Reference/owner refusal classification for p<=p_prime and unlisted models differs from TASK wording. Runtime runner is in-process and JSON sort serialization is not a general RFC8785 implementation. No provider runs or arm-comparison evidence.

## C038

Closed connected triangulated surfaces are checked by edge incidence and single-cycle links before curvature; orientation propagation is cross-checked against rational top homology. Graph certificates enforce positive transport masses, exact source/target marginals, graph-Lipschitz potentials and zero primal-dual gap. Weak duality directly proves the optimum when those checks hold. Independent incidence/GF3 top-homology checks and all 129 connected labeled graphs on two through four vertices at three laziness values support this bounded slice.

All 106 pinned data files replayed: 46 judge cases and ten examples PASS; 48 mutants FAIL; manifest and budget configuration checked. Every solved graph has independent exact certificate verification; surfaces have independent counts/links/curvature and GF3 top rank.

- AC38-F01: Both checkers accept fabricated edge/vertex/count values in OUT_OF_SCOPE witnesses when kind matches the internally found defect.
- AC38-F02: Malformed rational mass --1/2 raises ValueError in the dual evaluation rather than a rejection.
- AC38-F03: Both accept nested phantom fields and extra potential vertices; shifted half-integer potentials pass despite the participant integer-potential contract. C2 alone accepts repeated edge certificates (dual C1 rejects).
- AC38-F04: Historical manifest has declared_file_count=100 but files_count=101 and 101 entries; all listed raw hashes match. The local manifest test checks only files_count.

Limits: Actual implementation is pure Python rational Gaussian rank, not the proposed Rust/Smith-normal-form route. No claim about continuum curvature, physical gravity, or native backend execution. C2 alone does not compare V/E/F counts or ensure unique complete edge coverage; dual C1 catches those gaps. Reference accepts unreduced rational alpha while both checkers reject that reference result. Nested schema and integer-potential requirements are not fully enforced; fractional potential remains mathematically valid. Witness kind is validated but its coordinates/counts are not; historical labels and budget declarations do not establish provider-arm results.

## C039

CSS star and plaquette ranks over F2 determine k=E-rankA-rankB when boundaries commute; full logical centralizer and perfect Z/X pairing certify independent quotient generators. CW multiplicities are reduced mod2. The small-complex checker counts flat computational states modulo star flips, not a dense rational Hamiltonian diagonalization. Independent set elimination and exact X-eigenbasis enumeration agree on all 646 connected simple graphs through four vertices with every charge assignment.

All 108 data artifacts have bounded dispositions: 48 judge cases, 48 mutants, ten examples and two metadata files. Every canonical solved output receives independent rank/logical or sector checks. All 22 family source files plus root C039 test fully read.

- AC39-F01: Both sector checkers accept missing, Boolean or zero charges as nonempty sectors; multiplying all mapping entries also lets an extra unrelated charge flip a valid nonempty sector into an accepted empty one.
- AC39-F02: Odd-charge early return accepts SOLVED without any graph at all and on a 301-edge graph, bypassing mandatory schema, connectivity and size checks.
- AC39-F03: Both topology paths reinterpret any unrecognized direction as -1 and accept Boolean +1 directions. OUT_OF_SCOPE accepts any witness mapping including empty, without binding even its kind.
- AC39-F04: Refusal guards check only query/edge-list shape/edge count; legitimate reference MALFORMED_CASE_STRUCTURE refusals (for example empty faces) are rejected by both.
- AC39-F05: Historical manifest has declared_file_count=102 but files_count=103 and 103 entries; all listed raw hashes match. The local manifest test checks only files_count.

Limits: Two checkers repeat topology and elimination logic despite no shared imports; actual C2 uses F2 homology, not proposed integral Smith form/universal-coefficient route. Physical topological phases, material realization, continuum gauge theory and paid synthesis arms are not established. Reference supports broader labels/edge encodings than checkers; malformed cases can crash or produce valid reference refusals rejected by both. The root test checks only retained reference/case agreement. Independent replay enumerates <=16-qubit states; larger instances use exact ranks and pairing, with owner topology as stated premise.

## C040

Internal-index subset counts for the eleven-dimensional metric and 3-form, together with the admitted p-potential -> (D-p-2)-potential duality rule, yield scalar totals 1,3,7,14,25,42,70,128 and vector totals 1,3,6,10,16,27,28,0 in the stated frames. Full independent Weyl-reflection closure on all 12 nonabelian Cartan inputs agrees with the owner root-string sets, and dimG-dimK matches every scalar total. These computations certify dimensions conditional on the declared field inventory and group identifications; they do not establish representation branching or M-theory equivalence.

All 104 data files replayed: 46 judge cases, eight retained example answers, 48 mutants, one manifest and one budget declaration. All 20 source/spec/test files fully read. All 32 k/query positive controls pass; each solved retained certificate receives independent subset-count/Hodge arithmetic and Weyl-closure dimension checks. Eleven synthetic countercontrols record accepted bad certificates, rejected legitimate reference refusals and mutable-return contamination.

- AC40-F01: Both checkers accept G=made_up_group, K=1 for the k=7 coset and accept branching [[adjoint(fiction),63],[banana,70]]. Missing group names also pass. Dimensions alone do not certify the advertised group/representation identity.
- AC40-F02: Both accept vector dual_forms=-999 with total=27, or omit all vector components except total. Irrelevant scalar components +99 and -99 also cancel to an accepted total. The advertised complete nonnegative field breakdown is not enforced.
- AC40-F03: Both accept a solved answer with mandatory id and D removed; provenance/instance binding is incomplete despite the strict-schema claim.
- AC40-F04: Legitimate reference UNKNOWN_QUERY_TYPE and MALFORMED_CASE_STRUCTURE refusals fail both checkers. theory=IIB,k=1 yields a reference/checker disagreement because one checker adds a different ten-dimensional field inventory without excluding that comparison domain.
- AC40-F05: The reference get_branching returns a shared mutable table. Editing one returned answer mutates future solve results, and a substituted non-adjoint representation label still passes both checkers. Reproduced only in memory, then restored.

Limits: Reference coset/branching answers are table lookups; root recomputation occurs only in checker 2. Compact-subgroup identification, real forms and global group forms are admitted, not reconstructed. Both branching verifiers check dimensions plus an adjoint substring; neither implements a restriction matrix or character identity. The advertised IIA/IIB comparison is partial and theory is ignored by the reference solver. Hodge dual-potential counting assumes the stated field content, duality frame and local free-field degree accounting. No quantum compactification, interacting dynamics, physical vacuum or string/M-theory duality is proved. All retained artifacts are historical local inputs/outputs; no paid provider execution or model quality is inferred.

Full path/hash/read ranges, artifact checks, exact controls, primary sources, and pending paths are in the JSON and same-prefix ledgers.
