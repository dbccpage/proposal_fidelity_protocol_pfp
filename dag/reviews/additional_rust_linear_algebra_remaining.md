# Rust linear-algebra audit

{"files": 83, "full_source_reads": 83, "full_source_lines": 35011, "pending": 0}

All source assessments, exact SHA256 pins, and complete body ranges are in the sibling JSON report. The initial 37-file checkpoint is preserved in takeover snapshots; this continuation adds 46 direct body reviews when complete.

No original Rust, Cargo, native binary, provider, or private benchmark execution. Repository-wide completion is not claimed.

## Claims and reusable mechanisms

**RLA-C01** The reviewed integer determinant and rational alternating-matrix Pfaffian routines implement substantive finite elimination algorithms, with square/alternation admission and explicit empty/singular conventions. Independent finite models agree with different reference expansions; arbitrary dimensions and scalar implementations still require their mathematical and representation premises.

- `code/rust/core_linear_algebra/src/determinant.rs` lines 25–62; SHA256 `8b30282c01deb21fda285d5507af9691ededa346915fcb5d52789e092c15c00d`.
- `code/rust/core_linear_algebra/src/exact_pfaffian.rs` lines 24–81; SHA256 `0f6b8f03c6b5dae5065a1d1e8055a98ccef0c5819e0a5950654769fb42a5cada`.

Controls: RLA-P02, RLA-P03.

Limits: No original Rust execution; generic traits and dependency correctness are not certified by this finite panel.

**RLA-C02** Basis and choice wrappers explicitly record declared coordinate conventions, not existence, independence or spanning of an actual basis. Their nonclaims and private descriptor invariants are useful and should be preserved.

- `code/rust/core_linear_algebra/src/basis.rs` lines 34–90; SHA256 `01ac33717a4bb5b870f4886acc5435351f78f2f7abab024ddd2542b541584a04`.
- `code/rust/core_linear_algebra/src/choice.rs` lines 39–86; SHA256 `902a16f1b10022fc06c4e3e8c2658224b7bb129f8a293b31a2d7bda4e7c636b8`.

**RLA-C03** The sealed fallible exact-field protocol excludes integer truncation and floating equality, while the public scalar marker traits require lawful operations and representability as external premises. A marker or capacity record alone cannot establish exact mathematical arithmetic.

- `code/rust/core_linear_algebra/src/scalars.rs` lines 8–87; SHA256 `0f931d158060c86fba23d0077ab6265e3feafff609601b9ffc40c9bddb8bba2b`.
- `code/rust/core_linear_algebra/src/scalars.rs` lines 93–177; SHA256 `0f931d158060c86fba23d0077ab6265e3feafff609601b9ffc40c9bddb8bba2b`.
- `code/rust/core_linear_algebra/src/scalars.rs` lines 229–267; SHA256 `0f931d158060c86fba23d0077ab6265e3feafff609601b9ffc40c9bddb8bba2b`.

**RLA-C04** The2x2 adjugate witness checks its actual four product entries with wide checked arithmetic and refuses an unrepresentable output. The tensor shape owner separately checks positive finite extent products; neither retained value binds an arbitrary semantic object or supplies a general tensor view.

- `code/rust/core_linear_algebra/src/lib.rs` lines 82–118; SHA256 `b6a7f3c4cb28c0477d4340fd934af3cffafc1285dbc1de4509b07bc807373fdc`.
- `code/rust/core_linear_algebra/src/tensor/tensor_view.rs` lines 1–59; SHA256 `255f901a159fc192f28e7c69b83475172607cf95f73adcaccb9c686d97bd7296`.

Controls: RLA-P01.

**RLA-C05** The matrix owner enforces rectangular storage and provides separately fallible arithmetic with preflight element and operation-count limits. Exact interpretation still requires lawful scalar operations, representable intermediates and available resources; its limits are not elapsed-time or arbitrary scalar-memory bounds.

- `code/rust/core_linear_algebra/src/backend/basic_matrix.rs` lines 143–167; SHA256 `6adf8811c58b01cc1dcf3599c694f543e352ac309f4f43cfa5cb1457e393d7ac`.
- `code/rust/core_linear_algebra/src/backend/basic_matrix.rs` lines 238–337; SHA256 `6adf8811c58b01cc1dcf3599c694f543e352ac309f4f43cfa5cb1457e393d7ac`.
- `code/rust/core_linear_algebra/src/backend/basic_matrix.rs` lines 350–394; SHA256 `6adf8811c58b01cc1dcf3599c694f543e352ac309f4f43cfa5cb1457e393d7ac`.
- `code/rust/core_linear_algebra/src/backend/basic_matrix.rs` lines 846–875; SHA256 `6adf8811c58b01cc1dcf3599c694f543e352ac309f4f43cfa5cb1457e393d7ac`.
- `code/rust/core_linear_algebra/src/basic_matrix_serde.rs` lines 7–29; SHA256 `3e82317861433e8ea361363323c73e46aa56b5b7a65a40e28d7bac1abfd14622`.

Limits: Source review only; no original execution or proof of external scalar implementations.

**RLA-C06** The canonical exact image/kernel owner implements finite Gauss-Jordan reduction, basis extraction and a replayed particular image witness. Independent rational controls agree with determinant-minor rank and augmented-rank membership over the bounded panel.

- `code/rust/core_linear_algebra/src/linear_algebra/image_kernel.rs` lines 207–279; SHA256 `8ca0c5c63db3766ea70970f2947cfc00d3723687c81fc98f5c8aa9bef49946c9`.
- `code/rust/core_linear_algebra/src/linear_algebra/image_kernel.rs` lines 308–357; SHA256 `8ca0c5c63db3766ea70970f2947cfc00d3723687c81fc98f5c8aa9bef49946c9`.
- `code/rust/core_linear_algebra/src/linear_algebra/image_kernel.rs` lines 411–477; SHA256 `8ca0c5c63db3766ea70970f2947cfc00d3723687c81fc98f5c8aa9bef49946c9`.

Controls: RLA-P04.

Limits: Finite independent model, not original Rust execution, a universal resource bound or a semantic natural-language certificate.

**RLA-C07** The rational symmetric LDLT path supplies a substantive finite PSD decision under explicit shape, symmetry and exact-arithmetic premises. The private ExactRepair owner separately replays a supplied potential against its finite linear residual; neither mechanism infers its application semantics.

- `code/rust/core_linear_algebra/src/exact_ldlt.rs` lines 30–168; SHA256 `a145f112d28efb0cbd98cbbe1fc5883dbf47ad3b7538e0129043af325bd764d2`.
- `code/rust/core_linear_algebra/src/exact_repair.rs` lines 66–138; SHA256 `d6a4f9c4683085fee65053a20de6e628c77334efeed451b1bb12c086475f6481`.

Controls: RLA-P05.

Limits: Failed PSD paths can contain partial factors; independent finite controls are not original execution. ExactRepair does not assert a full cochain complex or optimization result.

**RLA-C08** The checked basis-change constructor replays both inverse products and retains its matrices; typed linear-map composition checks both intermediate basis label and dimension. These enforce concrete coordinate relations under lawful exact scalar arithmetic, while provenance remains caller-supplied metadata.

- `code/rust/core_linear_algebra/src/change_basis.rs` lines 294–338; SHA256 `b3cf23eafc9da6df0b6e0a43f90a1af5dba423e462cb55f918e0f9cf6e0965d6`.
- `code/rust/core_linear_algebra/src/change_basis.rs` lines 392–444; SHA256 `b3cf23eafc9da6df0b6e0a43f90a1af5dba423e462cb55f918e0f9cf6e0965d6`.
- `code/rust/core_linear_algebra/src/linear_map.rs` lines 174–260; SHA256 `0d01e0c99049021335171d5bcfcb72b900aa5ddeeca176b35b048b3af6cf8c88`.
- `code/rust/core_linear_algebra/src/proof.rs` lines 146–169; SHA256 `b7e5a1c6f12255f95201c848b59e389f68950fed9ccb7a6cd49e9a2414f949f6`.

Controls: RLA-P08.

Limits: No actual basis family, authenticated theorem or public kernel/image implementation is supplied by these wrappers; no original execution.

**RLA-C09** The cochain window, map and homotopy owners check complete finite matrix equations: d1*d0=0, commuting squares and F-G=dH+Hd with shared endpoints. For lawful ring coefficients this makes the usual induced cohomology and homotopy reasoning available under the supplied presentation.

- `code/rust/core_linear_algebra/src/finite_cochain_map.rs` lines 18–75; SHA256 `20901b3a403b1c99313cfb54150ed656c3297c2fb316cc30b8337df76f437d7b`.
- `code/rust/core_linear_algebra/src/finite_cochain_map.rs` lines 101–133; SHA256 `20901b3a403b1c99313cfb54150ed656c3297c2fb316cc30b8337df76f437d7b`.
- `code/rust/core_linear_algebra/src/finite_cochain_map.rs` lines 136–218; SHA256 `20901b3a403b1c99313cfb54150ed656c3297c2fb316cc30b8337df76f437d7b`.

Controls: RLA-P12.

Limits: Semiring quotients require an explicit congruence; no semantic extraction, norm preservation or reflection of equality is implied. Independent finite F2 control only.

**RLA-C10** Rational sensing is strengthened to a report on repair cosets exactly by checking R*d0=0. Its supplied blindspot witness is recomputed, and the homogeneous-equation implication wrapper separately replays row-combination or separating-vector evidence.

- `code/rust/core_linear_algebra/src/linear_observer_presentation.rs` lines 26–83; SHA256 `dae161c9201d44023d689455e6f023a56cb6189d5cb305c7aa4a235b44e95741`.
- `code/rust/core_linear_algebra/src/linear_observer_presentation.rs` lines 107–155; SHA256 `dae161c9201d44023d689455e6f023a56cb6189d5cb305c7aa4a235b44e95741`.
- `code/rust/core_linear_algebra/src/row_constraint_implication.rs` lines 52–148; SHA256 `996e18fdcd0ef25eb453992904048d2155a11bb982f894d671ac5d1bb76e9a91`.

Controls: RLA-P10.

Limits: Well-formed exact rationals and available resources are premises; the implication solver body is now fully read with separate finite controls. No memory, policy, physical or general answer-correctness interpretation is derived; no native execution.

**RLA-C11** The lumpability owner validates an exhaustive partition and the exact intertwining equation MH=HB. Its induction genuinely preserves endpoint-block path aggregates for every length under lawful semiring operations. The separate Boolean square-root routine exhaustively enumerates its admitted n<=3 carrier.

- `code/rust/core_linear_algebra/src/semiring_lumpability.rs` lines 1–9; SHA256 `8fcafc3a8d758182ffc345d94b23ccdc649aefe1948fe7fcf7a91662fe464a32`.
- `code/rust/core_linear_algebra/src/semiring_lumpability.rs` lines 62–135; SHA256 `8fcafc3a8d758182ffc345d94b23ccdc649aefe1948fe7fcf7a91662fe464a32`.
- `code/rust/core_linear_algebra/src/semiring_matrix.rs` lines 95–143; SHA256 `0b42adc9683669747f463f7a9691f52808012bffee0099adca5d521ac9c5de3a`.

Controls: RLA-P09.

Limits: Endpoint-block aggregates are not individual paths or arbitrary-distribution preservation. Finite models corroborate the source reasoning; no native execution or universal runtime bound.

**RLA-C12** The generic exact-field solver constructs either an affine solution family or a dual inconsistency witness, and separately replays its answer against the supplied matrix and right-hand side. Under lawful field operations these are concrete finite linear-algebra certificates, with explicit preflight limits for both branches.

- `code/rust/core_linear_algebra/src/exact_field/mod.rs` lines 32–54; SHA256 `13498e00565db34e3e621a418bc94b37e0eee2daea1d7857b104ab52819dedfd`.
- `code/rust/core_linear_algebra/src/exact_field/elimination.rs` lines 237–282; SHA256 `dcd4c6d10cf4210edb74d047e17e625ac288eb58fa580f99b648dda3186e33fe`.
- `code/rust/core_linear_algebra/src/exact_field/elimination.rs` lines 316–476; SHA256 `dcd4c6d10cf4210edb74d047e17e625ac288eb58fa580f99b648dda3186e33fe`.

Controls: RLA-P13.

Limits: The independent exhaustive control covers2x2 systems over F2/F3, not native execution or arbitrary-field validation. Algebraic laws, well-formed scalar values and scalar resource behavior remain premises.

**RLA-C13** The characteristic-polynomial owner implements a division-free Berkowitz recurrence over lawful commutative coefficients; its separate Krylov solver finds the first monic dependence over a lawful field. Finite independent checks compare the characteristic result with permutation determinants and minimality with exhaustive monic search.

- `code/rust/core_linear_algebra/src/exact_field/characteristic_polynomial.rs` lines 39–142; SHA256 `d2b41a2a270a7c308dbc05292e96545daa451e453b6895345edcdc38eda67d73`.
- `code/rust/core_linear_algebra/src/exact_field/characteristic_polynomial.rs` lines 202–295; SHA256 `d2b41a2a270a7c308dbc05292e96545daa451e453b6895345edcdc38eda67d73`.

Controls: RLA-P16.

Limits: 1919 finite characteristic cases and616 finite-field minimal-polynomial cases, not original execution or a universal proof. Noncommutative rings are outside the valid extension; finite random tests do not establish mutation completeness.

**RLA-C14** The centralizer owner builds the exact linear equations XG-GX=0 in row-major coordinates, obtains their kernel basis and replays every resulting matrix against all supplied generators. Under lawful field elimination this is a complete finite-dimensional common centralizer construction.

- `code/rust/core_linear_algebra/src/exact_field/commutant.rs` lines 10–21; SHA256 `0db3dd785dc6e17e27860d2b5c9160b29b4b059a0b537c2b9fc273f9d6be4ee6`.
- `code/rust/core_linear_algebra/src/exact_field/commutant.rs` lines 35–111; SHA256 `0db3dd785dc6e17e27860d2b5c9160b29b4b059a0b537c2b9fc273f9d6be4ee6`.
- `code/rust/core_linear_algebra/src/exact_field/commutant.rs` lines 126–140; SHA256 `0db3dd785dc6e17e27860d2b5c9160b29b4b059a0b537c2b9fc273f9d6be4ee6`.

Controls: RLA-P17.

Limits: 355 independent finite families; no native execution. Separate phase budgets do not provide the advertised whole-call scalar bound.

**RLA-C15** The pseudoinverse owner replays its full-rank factorization and all four Penrose identities against the intact matrix. The adjoint owner implements the required involutive conjugation and matrix transpose; with a positive Hermitian norm, the Gram-factor construction gives a substantive exact Moore-Penrose inverse.

- `code/rust/core_linear_algebra/src/exact_field/pseudoinverse.rs` lines 1–6; SHA256 `defb30695bf8fc699a83af4167e9a4d9a20509eea5eee6bc6c9a7e631fb279fd`.
- `code/rust/core_linear_algebra/src/exact_field/pseudoinverse.rs` lines 25–121; SHA256 `defb30695bf8fc699a83af4167e9a4d9a20509eea5eee6bc6c9a7e631fb279fd`.
- `code/rust/core_linear_algebra/src/exact_field/involution.rs` lines 24–71; SHA256 `654ad5aff9dc27a84d6aef9cd81fdc955ab2d7547d77ac7b79b704bd82eed151`.

Controls: RLA-P19.

Limits: Independent1560 rational inputs and1560 tampered-output refusals; not native execution or validation of every HermitianOrdered implementation. Involution alone supplies a Hermitian form, not positivity; the ordered owner explicitly states the additional universal laws without universally checking them.

**RLA-C16** Congruence diagonalization tracks invertible elementary basis changes and offers a separate verifier of S*AS=diag(D). Under the explicit ordered-field or positive Hermitian-norm premises, the sign counts give inertia, while LDL returns either a reconstructing positive-semidefinite factorization or a concrete negative quadratic-form witness.

- `code/rust/core_linear_algebra/src/exact_field/congruence.rs` lines 37–115; SHA256 `ba50317cb238b16d2e539eef6b449a54fe8ad12b2b971733be68a24ec3768924`.
- `code/rust/core_linear_algebra/src/exact_field/congruence.rs` lines 192–306; SHA256 `ba50317cb238b16d2e539eef6b449a54fe8ad12b2b971733be68a24ec3768924`.
- `code/rust/core_linear_algebra/src/exact_field/ordered.rs` lines 36–131; SHA256 `5b86785889c0cb6a3e3e8fa8adf901ad0bc55e5c0a9cbd473bc920ce2b0df00b`.
- `code/rust/core_linear_algebra/src/exact_field/ordered.rs` lines 453–590; SHA256 `5b86785889c0cb6a3e3e8fa8adf901ad0bc55e5c0a9cbd473bc920ce2b0df00b`.

Controls: RLA-P21.

Limits: 760 independent rational symmetric cases, including33 PSD,445 negative-pivot and282 zero-pivot/nonzero-column outcomes. No native execution or universal validation of open scalar traits. Congruence production and optional replay are distinct, and sign guards alone do not prove ordering laws.

**RLA-C17** The scalar-law owners implement explicit finite field, involution and order checks and correctly distinguish sampled passes from universal trait proofs. Their arithmetic test carriers include exact rational quadratic extensions and deliberate negative controls; consumers still need the relevant complete set of premises.

- `code/rust/core_linear_algebra/src/exact_field/laws.rs` lines 1–29; SHA256 `693c3ae72fce742cb1e6b8f670eb1b8acf4d222be10172fbaa390943ca569965`.
- `code/rust/core_linear_algebra/src/exact_field/laws.rs` lines 42–133; SHA256 `693c3ae72fce742cb1e6b8f670eb1b8acf4d222be10172fbaa390943ca569965`.
- `code/rust/core_linear_algebra/src/exact_field/laws.rs` lines 136–260; SHA256 `693c3ae72fce742cb1e6b8f670eb1b8acf4d222be10172fbaa390943ca569965`.
- `code/rust/core_linear_algebra/src/exact_field/test_support.rs` lines 239–299; SHA256 `7872900b48ba8e1a2eb70c4fb387b0bb2d6c61a588e56071ca84cff6a06a1a16`.
- `code/rust/core_linear_algebra/src/exact_field/test_support.rs` lines 341–425; SHA256 `7872900b48ba8e1a2eb70c4fb387b0bb2d6c61a588e56071ca84cff6a06a1a16`.

Controls: RLA-P22.

Limits: No retained tests executed; incomplete samples, missing combined checks, fixed-width fixture bounds and the derived-norm sign gap prevent blanket certification of arbitrary scalar implementations.

**RLA-C18** A shared caller-owned rational budget composes canonical-value checks and fraction-free solving through final equation replay. On distinct rational nodes, Neville evaluation computes finite interpolants; Lagrange interval images are tight for the admitted independent sample box, while recursive interval propagation can be wider.

- `code/rust/core_linear_algebra/src/exact_field/rational_bareiss.rs` lines 47–158; SHA256 `a04f5e16e9792823507afb0353910acb03e55dc4d0977c9fdc040ea1221eb21a`.
- `code/rust/core_linear_algebra/src/exact_field/rational_bareiss.rs` lines 416–439; SHA256 `a04f5e16e9792823507afb0353910acb03e55dc4d0977c9fdc040ea1221eb21a`.
- `code/rust/core_linear_algebra/src/exact_field/neville_aitken.rs` lines 1–13; SHA256 `3f2885c855add1fe695a553b35fc2a2aed6017f4e509e5e24214772116ca32af`.
- `code/rust/core_linear_algebra/src/exact_field/neville_aitken.rs` lines 167–306; SHA256 `3f2885c855add1fe695a553b35fc2a2aed6017f4e509e5e24214772116ca32af`.

Controls: RLA-P23, RLA-P24.

Limits: Independent921 systems and900 interval cases only. Scalar-call fuel and exposed-value bit limits are not elapsed-time or total-heap bounds. No inconsistency certificate, function remainder, convergence theorem or original execution.

**RLA-C19** The matrix jet owner implements the ordered second-derivative product rule with the factor2 on the cross term and a whole-product arithmetic preflight. Rational polynomial-curve controls agree with independent coefficient convolution.

- `code/rust/core_linear_algebra/src/exact_field/second_order_jet.rs` lines 1–22; SHA256 `6f53d865e6e2960e39491c2a470a8d2ee5b8b240a0af308d6e2f34f7f4bb0845`.
- `code/rust/core_linear_algebra/src/exact_field/second_order_jet.rs` lines 33–79; SHA256 `6f53d865e6e2960e39491c2a470a8d2ee5b8b240a0af308d6e2f34f7f4bb0845`.

Controls: RLA-P25.

Limits: 64 independent rational2x2 jet pairs, no native execution or analytic existence theorem. Shape admission alone does not establish that arbitrary derivative triples arise from curves over every coefficient field.

**RLA-C20** Coordinate row/column owners bind declared basis descriptors and dimensions before arithmetic or pairing. Separate integer orthogonality, shared-window dot and prefix owners replay concrete finite equations with checked integer arithmetic; their compact outputs retain limited summary data, not source ownership.

- `code/rust/core_linear_algebra/src/vector/vector.rs` lines 27–118; SHA256 `6133e517dba1a989e251f6e139a8e25a40431fee2fc3162d0befdd5df0cfbeb4`.
- `code/rust/core_linear_algebra/src/vector/row_vector.rs` lines 246–278; SHA256 `99ca625f1944cee2d4c6acb2cb41b63d53cf59e7d5983fd96998db153430b15a`.
- `code/rust/core_linear_algebra/src/vector/mod.rs` lines 33–65; SHA256 `bbcc901646808d2b0cc512aa97511804456c22d0fbde344c5976c60e925864e1`.
- `code/rust/core_linear_algebra/src/vector/view_mut.rs` lines 70–145; SHA256 `dc7fe359da1b41d856d792097c90399a2d0766d1548acac01be57ed1af1b64cc`.

Controls: RLA-P27.

Limits: Scalar laws, ordinary arithmetic representability and actual basis meaning remain premises. Prefix reverse-tail representability can safely refuse additional cases; no native execution.

**RLA-C21** The symbolic Vec owners explicitly distinguish dimensions/names/endpoints from vector-space structure. Their fallible tensor bookkeeping checks dimension products and refuses overflow without claiming coherence, naturality or actual linear maps.

- `code/rust/core_linear_algebra/src/linear_algebra/vec_types.rs` lines 13–125; SHA256 `326402bc7e20fd692ea77252bf29850af1b4316769fce50e3ba2a41d26179e45`.
- `code/rust/core_linear_algebra/src/linear_algebra/vec_monoidal.rs` lines 23–109; SHA256 `3e6a69cf0aaed6c755e244fbcdaccbb4ac54d6249483562643a581908da0c9ac`.
- `code/rust/core_linear_algebra/src/linear_algebra/vec_monoidal.rs` lines 111–183; SHA256 `3e6a69cf0aaed6c755e244fbcdaccbb4ac54d6249483562643a581908da0c9ac`.
- `code/rust/core_linear_algebra/src/linear_algebra/vector_space.rs` lines 109–145; SHA256 `c0d1039bb49f28f4038ea9f8c4914728d32872250d2e2c1eb4cab51a1db09d07`.

Limits: The Category implementation is category-shaped only: identity equations fail actual equality (F11). FiniteVectorSpace and rank-nullity counts are declarations/arithmetic, not operator-specific certificates.

**RLA-C22** Complex tensor balancing is an exact finite coefficient construction: realification, T(rr,ri,ir,ii)=(rr-ii,ri+ir), projector T^tT/2 and intertwiner-checked compression. It explicitly distinguishes operator normalization, product-state scaling and balanced lift, while refusing characteristic2 or invalid inverses of2.

- `code/rust/core_linear_algebra/src/exact_field/complex_tensor.rs` lines 37–158; SHA256 `ae14c1637f2534ac3f1630d5563c202e74f3690cb85d79d653394cabfc08913e`.
- `code/rust/core_linear_algebra/src/exact_field/complex_tensor.rs` lines 174–209; SHA256 `ae14c1637f2534ac3f1630d5563c202e74f3690cb85d79d653394cabfc08913e`.
- `code/rust/core_linear_algebra/src/exact_field/complex_tensor.rs` lines 256–335; SHA256 `ae14c1637f2534ac3f1630d5563c202e74f3690cb85d79d653394cabfc08913e`.
- `code/rust/core_linear_algebra/src/exact_field/complex_tensor/tests.rs` lines 8–200; SHA256 `239b3e6ee55f826c336ac7071758a08e81dcf5a15fdceb5cff7ab2bc3010c9f4`.

Controls: RLA-P30.

Limits: Lawful exact fields and a supplied complex structure are hypotheses. No derivation of positivity, density-state admission, complex scalars or physics from these coordinate identities; no native execution.

**RLA-C23** Trace-one reference factors give a genuine direct-sum decomposition into reference and traceless sectors. The implemented product differential projects onto support0/1, its complement onto support>=2, and the separate highest-order projector onto all-traceless support; complete inclusion-exclusion has the correct sign and includes the full subset.

- `code/rust/core_linear_algebra/src/exact_field/tensor_projector.rs` lines 1–18; SHA256 `25ac8e619fa6b1cfd0c31af29aab0d562ae6a5270e2d6886c0245c37a0bd275f`.
- `code/rust/core_linear_algebra/src/exact_field/tensor_projector.rs` lines 415–609; SHA256 `25ac8e619fa6b1cfd0c31af29aab0d562ae6a5270e2d6886c0245c37a0bd275f`.
- `code/rust/core_linear_algebra/src/exact_field/tensor_projector.rs` lines 613–687; SHA256 `25ac8e619fa6b1cfd0c31af29aab0d562ae6a5270e2d6886c0245c37a0bd275f`.

Controls: RLA-P31.

Limits: Reference-dependent algebraic projections over lawful fields, not necessarily orthogonal or positive maps. Full64 matrix-unit control uses a non-Hermitian trace-one reference; no universal implementation proof or original execution.

**RLA-C24** Tensor coordinate products, rectangular partial traces and right partial transpose implement concrete finite index maps with checked shapes. Partial transpose preserves trace and is involutive while failing positivity, exactly as documented; numeric rank-product witnesses are separate declarations.

- `code/rust/core_linear_algebra/src/tensor/tensor.rs` lines 294–395; SHA256 `f57fc5b5b6c0614c5a5d189eb94e3522d01fa3db66c971bc9c3ab784ef6f3b1f`.
- `code/rust/core_linear_algebra/src/tensor/tensor.rs` lines 397–488; SHA256 `f57fc5b5b6c0614c5a5d189eb94e3522d01fa3db66c971bc9c3ab784ef6f3b1f`.
- `code/rust/core_linear_algebra/src/tensor/partial_transpose.rs` lines 1–40; SHA256 `f63e11aea0a577d1edb18ec50cb75e5af26ef33d1a36e75f35b864796bb567eb`.
- `code/rust/core_linear_algebra/src/tensor/mod.rs` lines 35–56; SHA256 `36a1e486a79d54a7a6253ee076426c7e819177f236dbceba9d02c346bc41cd9c`.

Controls: RLA-P32.

Limits: Generic Numeric operations may overflow or be inexact; source/basis metadata is declared. No physical entanglement interpretation or global authority is established by the coordinate formulas.

**RLA-C25** Dense BigInt Smith construction tracks unimodular row and column operations, admits positive divisibility-chain invariants and independently replays U*A*V=D before returning its private full result. Sparse column gcd is explicitly a heuristic, not a Smith invariant.

- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 67–179; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.
- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 258–538; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.
- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 742–792; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.

Controls: RLA-P33.

Limits: Unimodularity is construction-trusted; product replay alone would not prove it. Per-pivot iteration ceiling does not bound BigInt growth/allocation. Standalone diagonal admission does not bind any source matrix.

**RLA-C26** At a supplied rational chain step, homology_basis checks d*d_next=0, extends the computed boundary basis by independent cycles, verifies rank-nullity for the quotient and replays each representative as a cycle. Incidence/Laplacian code separately implements the finite edge-coordinate identities.

- `code/rust/core_linear_algebra/src/linear_algebra/homology_basis.rs` lines 139–265; SHA256 `af4b176515985798f4924c270dcf3c5ef183c527492a173207ec0c45dc479b5e`.
- `code/rust/core_linear_algebra/src/linear_algebra/incidence_matrix.rs` lines 23–83; SHA256 `8cf595b9c12698fecb069d66bb59bcc2c20ecdbc61bb2e764b5a934a292730a5`.
- `code/rust/core_linear_algebra/src/linear_algebra/graph_laplacian.rs` lines 69–127; SHA256 `0c884f46ce7b6ff15daab8372fd54d3e85e986a65bd9730db313af1d459dc8a5`.

Controls: RLA-P34.

Limits: Rational quotient dimensions and finite graph coordinates, not integral homology/torsion, inferred topology, or an authenticated provenance/degree. Arithmetic representation and reviewed RREF correctness are premises.

**RLA-C27** The rank/norm/support interfaces distinguish exact rational reduction and weighted L1 calculation from absolute-threshold numerical rank/support. Shape bounds, threshold margins and tolerances are explicit limited diagnostics; they do not alone certify exact rank or approximation error.

- `code/rust/core_linear_algebra/src/linear_algebra/rank.rs` lines 32–170; SHA256 `8a8e05188bc011e2f4548630a9053ca070bc131132d22bfb6f1eed770b5c5e15`.
- `code/rust/core_linear_algebra/src/linear_algebra/norm.rs` lines 51–146; SHA256 `8cafe725b4590268e6644e25a80711aa65c58f48a2af5e9a2afecd3d749adb10`.
- `code/rust/core_linear_algebra/src/linear_algebra/support_operations.rs` lines 58–175; SHA256 `430fc664e449c0ba9ded76d761cac62b2014d84fa81e08119872b6703d5ad46c`.
- `code/rust/core_linear_algebra/src/linear_algebra/l1_additivity.rs` lines 47–112; SHA256 `704ec17d7d394a2f6eb1e53f0ba64628a9d4cc7b2343a92a04b938ef9071f29b`.

Controls: RLA-P35.

Limits: Finite representable arithmetic and lawful canonical rationals; external SVD behavior not executed. Approximate support is nonlinear, and floating L1 arithmetic can return NaN despite finite input.

**RLA-C28** Exact gauge-table normalization retains diagonal/cycle data and, when repeated after every shared relabeling, yields a finite orbit representative. Total pair-table pushforward descends modulo all integer gradients precisely in the stated complete fiber-count cases, with replayable triangle obstructions otherwise.

- `code/rust/core_linear_algebra/src/gauge_pair_table.rs` lines 25–124; SHA256 `47d99dabf296591b4ca58f95d07514eca95caeb2aa0bf0e4c94967d050d163ae`.
- `code/rust/core_linear_algebra/src/gauge_pair_transport.rs` lines 72–216; SHA256 `4ef34a6ca1331d2d12f3635891d7f77175b2ef4e5bcaa6082e575b61aa6ff22e`.
- `code/rust/core_linear_algebra/src/pair_table_canonical.rs` lines 34–93; SHA256 `1a1e122faa25dab7c21326a1592f5a3f83798ce57f662930bc7ef9d4dce3cc78`.

Controls: RLA-P36.

Limits: Complete enumeration and lawful scalar/order premises; decoration equivariance/determinism is caller-owned. Finite full directed tables, not arbitrary sparse graph cohomology. Source/target cap256 does not bound coefficient bits. Independent499map panel is not universal implementation proof.

**RLA-C29** The Regge helpers implement exact rational polynomial/linear-algebra identities: oriented determinant4volume, Cayley-Menger determinant scaling, four-dimensional Plucker simplicity and exterior-square action. Checked SO4 constructor proves its equations at that call.

- `code/rust/core_linear_algebra/src/regge_exact/cayley_menger.rs` lines 25–134; SHA256 `208c8c000ef947cc0b1085c1153da6f15b1b6f6053e2ecb58cd084e591b21b93`.
- `code/rust/core_linear_algebra/src/regge_exact/bivector.rs` lines 23–70; SHA256 `b2491bec631a42c71a4593d123204c5524eada27e6c2d2c6f35e144b1d301c40`.
- `code/rust/core_linear_algebra/src/regge_exact/so4.rs` lines 32–123; SHA256 `5e0176c7f1524a22703f5666330018eb6a0ddcfc084c95cfad47f36c26dbbee8`.
- `code/rust/core_linear_algebra/src/regge_exact/gaussian.rs` lines 15–112; SHA256 `6608cd861fa6d423d81d1911907ede8db0c5f703f0ad2e14cdc4951bd85dec66`.

Controls: RLA-P37.

Limits: Euclidean realizability is not admitted by length-table validation; So4 public storage permits bypass. No classical deficit-angle, curvature/dynamics, physical field or allocation-free conclusion.

**RLA-C30** Contract symbol witnesses and repeated capacity/Result suffixes provide compilation or elementary count-admission evidence only. They do not verify rank-nullity of a concrete map, gauge descent, geometric formulas or the stated six mutation kills.

- `code/rust/core_linear_algebra/src/contract_property_witnesses.rs` lines 1–97; SHA256 `05bb6abb483f2ca87867d5af433a603528629a63c9c778da093609c19a0000b5`.
- `code/rust/core_linear_algebra/src/contract_property_witnesses.rs` lines 126–184; SHA256 `05bb6abb483f2ca87867d5af433a603528629a63c9c778da093609c19a0000b5`.
- `code/rust/core_linear_algebra/src/pair_table_canonical.rs` lines 96–111; SHA256 `1a1e122faa25dab7c21326a1592f5a3f83798ce57f662930bc7ef9d4dce3cc78`.
- `code/rust/core_linear_algebra/src/gauge_pair_table.rs` lines 142–253; SHA256 `47d99dabf296591b4ca58f95d07514eca95caeb2aa0bf0e4c94967d050d163ae`.

Limits: Source test adequacy assessment, not a claim that all external tests are absent or historical mutation runs never happened. Adjacent substantive owner tests assessed separately.

**RLA-C31** BigRational standard-dot Gram-Schmidt separately verifies nonzero orthogonal output and the unit-diagonal triangular reconstruction, supporting exact span preservation without an orthonormality claim. Rational complement projectors use the corresponding rank-one formula and replay P²=P, P^t=P and PA=0.

- `code/rust/core_linear_algebra/src/linear_algebra/gram_schmidt.rs` lines 261–398; SHA256 `90f1492187e61aa8bb9bb5593e319555bb773ce5e1de345cd91c324c9ffc8e9c`.
- `code/rust/core_linear_algebra/src/linear_algebra/projector.rs` lines 119–160; SHA256 `f9d271c99dfa41a88330575b1d77ab8ecc1306b0890c050be04c8cd48e282629`.
- `code/rust/core_linear_algebra/src/linear_algebra/projector.rs` lines 174–311; SHA256 `f9d271c99dfa41a88330575b1d77ab8ecc1306b0890c050be04c8cd48e282629`.

Controls: RLA-P38.

Limits: No general Gram form/complex case. Caller family hash is not recomputed; Rational64 projector arithmetic has F17 ceiling gap and no independent rank/completeness certificate beyond construction.

**RLA-C32** Successful COO compression establishes sorted unique coordinate entries and preserves the operator under lawful arithmetic; similarity stores an actually computed conjugate from an admitted basis isomorphism, not a canonical similarity class. These mechanisms retain local metadata rather than authenticated external source certificates.

- `code/rust/core_linear_algebra/src/linear_algebra/sparse_operator.rs` lines 107–203; SHA256 `c1024d8ffa0300a1cf3323667ff89f716d6cc10ff2e734fc1d01772df646fae3`.
- `code/rust/core_linear_algebra/src/similarity.rs` lines 83–146; SHA256 `036478e3019ade25547025fe2e41f00e67bb8de1679735d0d8dbd4c9543c5d2f`.

Limits: Compression failure is destructive (F18); finite arithmetic can change refusal behavior under reassociation. Generic Numeric/CheckedNumeric algebraic laws remain premises.

**RLA-C33** Packed Hermitian owners retain genuine symmetry invariants through private storage and diagonal checks. The exact owner supplies single-pass contractions, a Hermitian rank-two update and positive-definite LDL solve with an independent packed Ax=b replay.

- `code/rust/core_linear_algebra/src/packed_hermitian.rs` lines 55–115; SHA256 `020356aeeaf7f18c424934be80203b3ad8061ca905643744b4045cf2fe2e8bdf`.
- `code/rust/core_linear_algebra/src/packed_hermitian.rs` lines 367–541; SHA256 `020356aeeaf7f18c424934be80203b3ad8061ca905643744b4045cf2fe2e8bdf`.
- `code/rust/core_linear_algebra/src/packed_hermitian.rs` lines 564–647; SHA256 `020356aeeaf7f18c424934be80203b3ad8061ca905643744b4045cf2fe2e8bdf`.

Controls: RLA-P40.

Limits: Hermiticity is not positivity; exact ordered/involutive scalar laws and prior LDL owner are premises. Element caps do not bound coefficient bits or total solve work; numerical-vector/result finiteness is weaker than storage admission.

**RLA-C34** The bounded Hermitian-spectrum owner checks both supplied triangles and diagonal, limits solver policy, scales with nonzero-erasure refusal, replays all residual and orthonormality entries, and retains original matrix plus paired sorted eigenvectors. It explicitly issues numerical diagnostics only.

- `code/rust/core_linear_algebra/src/hermitian_eigen.rs` lines 45–187; SHA256 `b5a6ee9d3c125eeac4780294020d6e5808eae0f64355f238f0064cc329b05b6b`.
- `code/rust/core_linear_algebra/src/hermitian_eigen.rs` lines 210–318; SHA256 `b5a6ee9d3c125eeac4780294020d6e5808eae0f64355f238f0064cc329b05b6b`.
- `code/rust/core_linear_algebra/src/hermitian_eigen.rs` lines 321–445; SHA256 `b5a6ee9d3c125eeac4780294020d6e5808eae0f64355f238f0064cc329b05b6b`.

Controls: RLA-P41.

Limits: Floating residual checks are not rigorous interval error bounds, exact spectra, density positivity or physics. No original nalgebra solver or compile-fail tests executed. Legacy eigen/density helpers do not automatically inherit these gates.

**RLA-C35** Numerical density validation records tolerance-dependent trace, Hermitian defect and approximate minimal eigenvalue; graph conversion returns a candidate, and float Kraus application always refuses channel admission regardless of completeness defect. These boundaries prevent treating a small float residual as an exact channel.

- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 108–135; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 282–328; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 698–727; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 755–779; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.

Limits: F20 identifies missing nonfinite gates on internal construction routes. Numerical tolerances permit approximate/nonexact density properties, and no convergence/residual proof is supplied by the legacy eigensolver call. ExactKrausChannel is a cited external owner, not reread here.

**RLA-C36** Given an admitted real positive Gram structure and compatible operator basis, SelfAdjoint::new_checked replays the concrete equation A^tG=GA, allowing nonsymmetric coordinate matrices for nontrivial G. Positive-definite admission is delegated to a backend, while from_witness is an explicitly trusted shape/label-only route.

- `code/rust/core_linear_algebra/src/self_adjoint.rs` lines 47–141; SHA256 `8a7a70c5b1999a686a376d1ae5e76da875a60477c29212898951df862af95672`.
- `code/rust/core_linear_algebra/src/self_adjoint.rs` lines 264–364; SHA256 `8a7a70c5b1999a686a376d1ae5e76da875a60477c29212898951df862af95672`.
- `code/rust/core_linear_algebra/src/self_adjoint.rs` lines 425–445; SHA256 `8a7a70c5b1999a686a376d1ae5e76da875a60477c29212898951df862af95672`.
- `code/rust/core_linear_algebra/src/self_adjoint.rs` lines 660–699; SHA256 `8a7a70c5b1999a686a376d1ae5e76da875a60477c29212898951df862af95672`.

Limits: Test backend mocks PD verification, so its passing tests do not verify arbitrary Gram positivity. Detached witness has no matrix hash; crate-private construction and no owned extraction in this file limit exposure. No spectral theorem/physical observable derivation.

## Findings

**RLA-F01** RankNullity admission accepts a reduced matrix and kernel from different matrices, and a declared column count different from the reduced width. Its count certificate cannot certify that the supplied vectors form the kernel of the supplied matrix.

- `code/rust/core_linear_algebra/src/image_kernel.rs` lines 1–124; SHA256 `49e7665a68897228015ed1374233c4dc9a57e98ec5c1e6213cd5f7368a9d0c97`.
- `code/rust/core_linear_algebra/src/linear_algebra/image_kernel.rs` lines 129–177; SHA256 `8ca0c5c63db3766ea70970f2947cfc00d3723687c81fc98f5c8aa9bef49946c9`.
- `code/rust/core_linear_algebra/src/linear_algebra/image_kernel.rs` lines 207–279; SHA256 `8ca0c5c63db3766ea70970f2947cfc00d3723687c81fc98f5c8aa9bef49946c9`.

Controls: RLA-P06.

Limits: Independent exact model of constructible outputs; no native execution. The rank-nullity theorem is unaffected.

Recommendation: Derive both values from one admitted matrix, or bind and validate source dimensions/content plus kernel annihilation and independence before asserting a common-source certificate.

**RLA-F02** ExactRepairSpace counts an arbitrary supplied vector list as rank without checking independence or rectangular shape. Two copies of (1,0) are stored with rank2 although their span has dimension1.

- `code/rust/core_linear_algebra/src/exact_repair.rs` lines 18–44; SHA256 `d6a4f9c4683085fee65053a20de6e628c77334efeed451b1bb12c086475f6481`.

Controls: RLA-P07.

Limits: Public metadata path only. This does not bypass the separate private ExactRepair residual replay.

Recommendation: Name these fields as declarations, or compute and check a basis for a bound source matrix before using them as mathematical rank or repair-space evidence.

**RLA-F03** The semiring multiplication budget named MAX_SCALAR_OPERATIONS counts one unit per dot-product term although the body calls both mul and add. An admitted256-square multiplication therefore performs2^25 such scalar calls against the named2^24 limit.

- `code/rust/core_linear_algebra/src/semiring_matrix.rs` lines 7–28; SHA256 `0b42adc9683669747f463f7a9691f52808012bffee0099adca5d521ac9c5de3a`.
- `code/rust/core_linear_algebra/src/semiring_matrix.rs` lines 52–69; SHA256 `0b42adc9683669747f463f7a9691f52808012bffee0099adca5d521ac9c5de3a`.

Controls: RLA-P11.

Limits: Exact loop-count model, not a large runtime experiment. The term count is bounded and no elapsed-time guarantee is established or refuted.

Recommendation: Rename the limit as a dot-product-term bound, or count both scalar calls consistently with the checked BasicMatrix owner and document per-call versus whole-power accounting.

**RLA-F04** Empty-axis matrix helpers weaken their stated shape/index contract: row(2x0,99) and column(0x2,99) return an empty vector because no indexed element is visited; to_rows followed by from_rows turns0x3 into0x0 despite inverse wording.

- `code/rust/core_linear_algebra/src/exact_field/matrix.rs` lines 85–112; SHA256 `79c9c4419985b585bb27c0b2429a1689b51d3a7ba180afef840111a9dc713871`.
- `code/rust/core_linear_algebra/src/exact_field/matrix.rs` lines 144–163; SHA256 `79c9c4419985b585bb27c0b2429a1689b51d3a7ba180afef840111a9dc713871`.

Controls: RLA-P14.

Limits: Independent tiny control-flow and shape model; no native memory safety failure is asserted. Ordinary nonempty-axis accesses are checked.

Recommendation: Validate the requested row/column before iteration and either carry shape metadata in row-list conversion or document its loss for zero-row matrices.

**RLA-F05** Exact rational conversion relies on an unstated canonical-value admission at its boundary. Narrowing checks raw numerator and denominator before normalization, so raw2^63/2 is refused although its reduced value2^62 fits Rational64; raw zero denominators also reach constructors without a local validity gate.

- `code/rust/core_linear_algebra/src/exact_field/matrix.rs` lines 165–199; SHA256 `79c9c4419985b585bb27c0b2429a1689b51d3a7ba180afef840111a9dc713871`.

Controls: RLA-P15.

Limits: Dependency num-rational0.4.2 raw/normal constructor and reduction excerpts are pinned in the control receipt. Canonical valid ratios avoid the mismatch; no native conversion or panic was executed. Generic field law premises do not by themselves validate raw values at this public conversion boundary.

Recommendation: Explicitly reject zero denominators and normalize before representability checks, or make the valid canonical input precondition explicit and enforce it at ingress.

**RLA-F06** The characteristic-polynomial documentation extends the division-free construction to rings of any kind, omitting the commutativity premise. Over M2(F2), take diagonal coefficient blocks a=E12,d=E21: the returned polynomial has coefficients(ad,-a-d,1), whose evaluation at the first diagonal block is ad-da=I, not zero.

- `code/rust/core_linear_algebra/src/exact_field/characteristic_polynomial.rs` lines 1–17; SHA256 `d2b41a2a270a7c308dbc05292e96545daa451e453b6895345edcdc38eda67d73`.
- `code/rust/core_linear_algebra/src/exact_field/characteristic_polynomial.rs` lines 77–141; SHA256 `d2b41a2a270a7c308dbc05292e96545daa451e453b6895345edcdc38eda67d73`.
- `code/rust/core_linear_algebra/src/exact_field/characteristic_polynomial.rs` lines 615–635; SHA256 `d2b41a2a270a7c308dbc05292e96545daa451e453b6895345edcdc38eda67d73`.

Controls: RLA-P18.

Limits: Documentation-scope counterexample, not a failure under a lawful commutative field or the tested commutative ring Z/6. No native execution.

Recommendation: State commutative rings explicitly for the division-free extension and distinguish that algebraic premise from the stronger Field trait signature.

**RLA-F07** The centralizer-basis function and standalone Penrose verifier reset the scalar-operation allowance across phases. A1x1 generator[1] admits6 counted calls with cap4; verifying the1x1 identity inverse admits8 with cap2. These exceed the facade promise of a whole-operation worst-case bound before scalar work.

- `code/rust/core_linear_algebra/src/exact_field/mod.rs` lines 47–54; SHA256 `13498e00565db34e3e621a418bc94b37e0eee2daea1d7857b104ab52819dedfd`.
- `code/rust/core_linear_algebra/src/exact_field/commutant.rs` lines 24–32; SHA256 `0db3dd785dc6e17e27860d2b5c9160b29b4b059a0b537c2b9fc273f9d6be4ee6`.
- `code/rust/core_linear_algebra/src/exact_field/commutant.rs` lines 85–140; SHA256 `0db3dd785dc6e17e27860d2b5c9160b29b4b059a0b537c2b9fc273f9d6be4ee6`.
- `code/rust/core_linear_algebra/src/exact_field/elimination.rs` lines 182–191; SHA256 `dcd4c6d10cf4210edb74d047e17e625ac288eb58fa580f99b648dda3186e33fe`.
- `code/rust/core_linear_algebra/src/exact_field/matrix.rs` lines 312–321; SHA256 `79c9c4419985b585bb27c0b2429a1689b51d3a7ba180afef840111a9dc713871`.
- `code/rust/core_linear_algebra/src/exact_field/pseudoinverse.rs` lines 87–121; SHA256 `defb30695bf8fc699a83af4167e9a4d9a20509eea5eee6bc6c9a7e631fb279fd`.

Controls: RLA-P20.

Limits: Exact tiny source-correspondent models, not retained Rust execution. The top-level pseudoinverse constructor has its own conservative aggregate bound and is not refuted by this witness; no time or scalar-bit complexity claim is made.

Recommendation: Preflight the sum of construction, elimination and replay costs, or pass a remaining budget across phases; document and name per-operation versus per-subcall limits explicitly.

**RLA-F08** The LDL documentation suggests a matrix can be positive definite up to a permutation yet have a zero leading principal minor, and presents this routine as incomplete for PSD. Under its lawful ordered/Hermitian premises this cannot occur: positive definiteness is invariant under permutation and every principal restriction remains positive definite. The implemented zero-pivot/zero-column rule is the complete PSD rule, consistent with later source tests.

- `code/rust/core_linear_algebra/src/exact_field/ordered.rs` lines 398–405; SHA256 `5b86785889c0cb6a3e3e8fa8adf901ad0bc55e5c0a9cbd473bc920ce2b0df00b`.
- `code/rust/core_linear_algebra/src/exact_field/ordered.rs` lines 538–571; SHA256 `5b86785889c0cb6a3e3e8fa8adf901ad0bc55e5c0a9cbd473bc920ce2b0df00b`.
- `code/rust/core_linear_algebra/src/exact_field/ordered.rs` lines 1238–1283; SHA256 `5b86785889c0cb6a3e3e8fa8adf901ad0bc55e5c0a9cbd473bc920ce2b0df00b`.

Controls: RLA-P21.

Limits: A mathematical documentation inconsistency, not a demonstrated algorithmic false rejection. The finite control corroborates cases; completeness reasoning comes from the stated factorization and negative-witness construction.

Recommendation: Remove the impossible positive-definite example and state that LDL completes exactly for PSD under lawful coefficient and representability premises.

**RLA-F09** The Hermitian-order sample checker validates sign range on supplied samples but accepts any nonnegative sign on a computed norm. A valid Gaussian arithmetic/involution with fixed_field_sign(17)=Some(2) passes samples0,1,-1,4+i even though the checker itself queries the invalid sign on norm(4+i)=17.

- `code/rust/core_linear_algebra/src/exact_field/laws.rs` lines 202–260; SHA256 `693c3ae72fce742cb1e6b8f670eb1b8acf4d222be10172fbaa390943ca569965`.

Controls: RLA-P22.

Limits: Independent exact model of the full checker path. This concerns its treatment of a value it actually evaluates, not a demand that finite samples prove universal laws. Adding17 to the sample exposes the defect.

Recommendation: Apply the same fixed-sign domain/range validation to every generated norm before checking positivity and zero equivalence.

**RLA-F10** The rational-budget description overstates its bit bound as covering every intermediate integer. Its checks admit operands and returned normalized values, while num-rational arithmetic constructs temporary numerators first:3/2+3/2 creates6 before reducing to3, and the operation succeeds with max_bits=2.

- `code/rust/core_linear_algebra/src/exact_field/rational_bareiss.rs` lines 1–9; SHA256 `a04f5e16e9792823507afb0353910acb03e55dc4d0977c9fdc040ea1221eb21a`.
- `code/rust/core_linear_algebra/src/exact_field/rational_bareiss.rs` lines 82–123; SHA256 `a04f5e16e9792823507afb0353910acb03e55dc4d0977c9fdc040ea1221eb21a`.
- `code/rust/core_linear_algebra/src/exact_field/rational_bareiss.rs` lines 134–156; SHA256 `a04f5e16e9792823507afb0353910acb03e55dc4d0977c9fdc040ea1221eb21a`.

Controls: RLA-P26.

Limits: Pinned num-rational0.4.2 addition excerpts and exact arithmetic, not native allocation measurement. Accepted exposed values are bounded; the source already disclaims CPU/bit-operation accounting.

Recommendation: Document the bound as applying to admitted and returned values, or use a scalar implementation that checks temporary-size growth before arithmetic if that stronger resource contract is needed.

**RLA-F11** VecCategory composition concatenates names without identity normalization. For valid f:X->Y, composing id_X then f produces name id_X ; f and composing f then id_Y produces f ; id_Y, both unequal to f under derived VecMor equality. Tests named identity-composition-preserves-morphism only compare endpoints, so they miss this law failure.

- `code/rust/core_linear_algebra/src/linear_algebra/vec_types.rs` lines 69–111; SHA256 `326402bc7e20fd692ea77252bf29850af1b4316769fce50e3ba2a41d26179e45`.
- `code/rust/core_linear_algebra/src/linear_algebra/vec_category.rs` lines 36–57; SHA256 `4e3e35442655aa4a31df8926fe40f90dd99a8b1b0f2ca0757a6970cc66a0f72c`.
- `code/rust/core_linear_algebra/src/linear_algebra/vec_category.rs` lines 93–112; SHA256 `4e3e35442655aa4a31df8926fe40f90dd99a8b1b0f2ca0757a6970cc66a0f72c`.
- `code/rust/core_linear_algebra/src/linear_algebra/vec_category.rs` lines 166–204; SHA256 `4e3e35442655aa4a31df8926fe40f90dd99a8b1b0f2ca0757a6970cc66a0f72c`.

Controls: RLA-P28.

Limits: The source already calls this a category-shaped symbolic structure and disclaims stronger semantic equality. The defect is relying on its Category trait or test name as evidence of categorical unit laws, not failure of endpoint bookkeeping.

Recommendation: Keep the explicit symbolic scope, or introduce normalized composition/equality and actual unit-law assertions before treating this as a lawful category.

**RLA-F12** CoordinateTuple<f64>::checked_dot refuses nonfinite inputs but does not check computed products or their sum. Finite coordinates1e308 produce an infinite square; two opposite products produce NaN, both returned as Ok. The numerical-profile comment about monitored convergence/error bounds is not implemented by this input-only gate. The disjoint-support L1 checker likewise returns Ok(error=NaN,passed=false) for finite x=(1e308,0), y=(0,1e308), because both norm totals overflow. ComplexMatrix add/sub/mul likewise directly wrap arithmetic without the finite check used by its constructors; adding two[1e308] matrices yields a nonfinite stored result.

- `code/rust/core_linear_algebra/src/linear_algebra/vector_space.rs` lines 147–187; SHA256 `c0d1039bb49f28f4038ea9f8c4914728d32872250d2e2c1eb4cab51a1db09d07`.
- `code/rust/core_linear_algebra/src/linear_algebra/vector_space.rs` lines 230–235; SHA256 `c0d1039bb49f28f4038ea9f8c4914728d32872250d2e2c1eb4cab51a1db09d07`.
- `code/rust/core_linear_algebra/src/linear_algebra/l1_additivity.rs` lines 63–80; SHA256 `704ec17d7d394a2f6eb1e53f0ba64628a9d4cc7b2343a92a04b938ef9071f29b`.
- `code/rust/core_linear_algebra/src/linear_algebra/complex_matrix.rs` lines 165–203; SHA256 `1afed6e017380bd2b0a6a5418924aa82bb58be2b61cda3bdf696f66e66b3620e`.

Controls: RLA-P29, RLA-P35, RLA-P42.

Limits: A floating-output admission boundary, not an exact-arithmetic theorem failure. No robust finite output or error bound is established by this method; no Rust execution.

Recommendation: Document the input-only check or refuse nonfinite intermediate/final outputs when callers require a finite numerical result.

**RLA-F13** The partial-trace refusal path computes expected=ceil(rows/traced_dim)*traced_dim with unchecked multiplication. A valid BasicMatrix of shape(usizeMAX,0) needs no scalar allocation; tracing factor2 takes the nondividing-row branch and computes usizeMAX+1, causing overflow rather than the intended typed shape refusal.

- `code/rust/core_linear_algebra/src/tensor/tensor.rs` lines 458–487; SHA256 `f57fc5b5b6c0614c5a5d189eb94e3522d01fa3db66c971bc9c3ab784ef6f3b1f`.
- `code/rust/core_linear_algebra/src/backend/basic_matrix.rs` lines 143–167; SHA256 `6adf8811c58b01cc1dcf3599c694f543e352ac309f4f43cfa5cb1457e393d7ac`.

Controls: RLA-P32.

Limits: Symbolic64-bit arithmetic and constructible zero-area shape, no native panic or huge allocation. Correct admitted divisible shapes and ordinary tensor formulas are unaffected.

Recommendation: Avoid rounding an invalid dimension upward in diagnostics, or check/saturate the diagnostic multiplication separately.

**RLA-F14** Smith and sparse conversion expose panic/resource boundaries despite checked-construction terminology: admitted BasicMatrix(usizeMAX,0) takes the empty Smith path and bigint_identity(usizeMAX) converts typed dimension failure into unreachable panic; SparseColMatrix(usizeMAX,2,[[],[]]) is admitted but to_dense multiplies rows*cols unchecked.

- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 132–179; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.
- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 516–531; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.
- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 620–659; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.
- `code/rust/core_linear_algebra/src/smith_normal_form.rs` lines 690–698; SHA256 `fb1187bd88603019eb4dff390e906222fe1ab98d7512e809e3cd4c8db02e53dd`.
- `code/rust/core_linear_algebra/src/backend/basic_matrix.rs` lines 143–167; SHA256 `6adf8811c58b01cc1dcf3599c694f543e352ac309f4f43cfa5cb1457e393d7ac`.

Controls: RLA-P35.

Limits: Symbolic64-bit arithmetic and admitted empty buffers only; no native execution, huge allocation or false mathematical Smith result. General BigInt bit/time bounds are also absent.

Recommendation: Propagate identity construction errors and use fallible checked sparse-to-dense shape/allocation conversion.

**RLA-F15** So4 exposes pub m, so any caller can construct or mutate a So4 containing diag(2,1,1,1) without try_new. Methods then treat that value as their unchecked input and return So4; the type name does not preserve the documented M^tM=I,det=1 invariant.

- `code/rust/core_linear_algebra/src/regge_exact/so4.rs` lines 1–53; SHA256 `5e0176c7f1524a22703f5666330018eb6a0ddcfc084c95cfad47f36c26dbbee8`.
- `code/rust/core_linear_algebra/src/regge_exact/so4.rs` lines 56–108; SHA256 `5e0176c7f1524a22703f5666330018eb6a0ddcfc084c95cfad47f36c26dbbee8`.

Controls: RLA-P37.

Limits: try_new itself correctly refuses the example; raw multiplication and exterior action formulas remain valid for arbitrary matrices. Public construction bypass is static evidence, not executed Rust.

Recommendation: Make matrix storage private and expose read-only access/checked replacement, or name/document the type as a raw candidate.

**RLA-F16** Cayley-Menger admits symmetric zero-diagonal tables without Euclidean realizability. Positive squared edge lengths1,1,9 pass that admission but yield volume_squared=-45/16, so the returned value cannot serve as a certified Euclidean volume square.

- `code/rust/core_linear_algebra/src/regge_exact/mod.rs` lines 79–98; SHA256 `09d8454cf54ff833ff021a8331fa4a34f0b8a23eee97044cb414df8040585387`.
- `code/rust/core_linear_algebra/src/regge_exact/cayley_menger.rs` lines 25–76; SHA256 `208c8c000ef947cc0b1085c1153da6f15b1b6f6053e2ecb58cd084e591b21b93`.
- `code/rust/core_linear_algebra/src/regge_exact/cayley_menger.rs` lines 110–134; SHA256 `208c8c000ef947cc0b1085c1153da6f15b1b6f6053e2ecb58cd084e591b21b93`.

Controls: RLA-P37.

Limits: Formula evaluation is correct and docs explicitly list only symmetry/diagonal checks; this is an interpretation/admission boundary, not a determinant arithmetic defect. Zero/degenerate simplices also return zero.

Recommendation: Explicitly label polynomial evaluation versus Euclidean admission, or check the anchored Gram matrix positive semidefinite before issuing geometric certification.

**RLA-F17** The Rational64 projector path uses ordinary arithmetic for Gram-Schmidt norms, coefficients and rank-one subtraction, and ordinary matrix multiplication for admission. Even a1x1 input column3037000500 requires norm-square9223372037000250000 beyond i64, so Result does not provide the typed arithmetic refusal available in the checked exact owners.

- `code/rust/core_linear_algebra/src/linear_algebra/projector.rs` lines 119–130; SHA256 `f9d271c99dfa41a88330575b1d77ab8ecc1306b0890c050be04c8cd48e282629`.
- `code/rust/core_linear_algebra/src/linear_algebra/projector.rs` lines 186–201; SHA256 `f9d271c99dfa41a88330575b1d77ab8ecc1306b0890c050be04c8cd48e282629`.
- `code/rust/core_linear_algebra/src/linear_algebra/projector.rs` lines 271–290; SHA256 `f9d271c99dfa41a88330575b1d77ab8ecc1306b0890c050be04c8cd48e282629`.

Controls: RLA-P39.

Limits: Mathematical complement is well-defined and formulas are correct; static operation/representation evidence and independent integer arithmetic, not native panic or release-wrap reproduction.

Recommendation: Use checked exact scalar operations throughout or BigRational, and replay using the same explicit arithmetic admission policy.

**RLA-F18** compress_checked drains self.entries before a fallible duplicate addition. On overflow, dropping the drain removes remaining entries and local compressed data is discarded, leaving the original operator empty after Err. Example entries(0,0,MAX),(0,0,1),(1,1,7) act on(0,1) as(0,7) before compression and(0,0) after failed compression.

- `code/rust/core_linear_algebra/src/linear_algebra/sparse_operator.rs` lines 158–193; SHA256 `c1024d8ffa0300a1cf3323667ff89f716d6cc10ff2e734fc1d01772df646fae3`.
- `code/rust/core_linear_algebra/src/linear_algebra/sparse_operator.rs` lines 344–351; SHA256 `c1024d8ffa0300a1cf3323667ff89f716d6cc10ff2e734fc1d01772df646fae3`.
- `code/rust/core_linear_algebra/src/linear_algebra/sparse_operator.rs` lines 396–410; SHA256 `c1024d8ffa0300a1cf3323667ff89f716d6cc10ff2e734fc1d01772df646fae3`.

Controls: RLA-P39.

Limits: Rust ownership/drain behavior assessed statically with a bounded state model; no retained program execution. Successful compression math is unaffected.

Recommendation: Compute into separate storage without draining the original until all checked additions succeed, and test unchanged state after refusal.

**RLA-F19** Shared Hermitian input validation checks only j<i and omits imaginary diagonal entries. Thus n1 A=[1+i] passes even tolerance0; square_checked returns[2i] and identity congruence returns[1+i], neither Hermitian. Both blocked and unblocked public checked APIs inherit this gap.

- `code/rust/core_linear_algebra/src/linear_algebra/hermitian_mul.rs` lines 92–110; SHA256 `015a4d8371a139bb99e38f5017d6be03734bd35ea3d7a4cbb9ee9f3f6357c217`.
- `code/rust/core_linear_algebra/src/linear_algebra/hermitian_mul.rs` lines 113–175; SHA256 `015a4d8371a139bb99e38f5017d6be03734bd35ea3d7a4cbb9ee9f3f6357c217`.
- `code/rust/core_linear_algebra/src/linear_algebra/hermitian_mul_blocked.rs` lines 99–120; SHA256 `3cc4e6e9b0b2b0e5b586348fd79dd1083a6b061d1246c673aabbe47e5a07799d`.

Controls: RLA-P39.

Limits: Exact small complex arithmetic, no floating subtlety or native execution; genuine Hermitian inputs still satisfy the mathematical square/congruence formulas subject to numerical errors.

Recommendation: Check diagonal imaginary parts against the stated tolerance and validate finite/real-diagonal output under an explicit numerical policy.

**RLA-F20** Density finiteness admission is inconsistent across constructors. from_amplitudes/from_cvector compute norm without rejecting NaN, then use from_rho, which checks shape only. validate compares trace/Hermitian defect/minimum eigenvalue with ordinary inequalities, all of which fail to reject NaN, and does not check finite eigenvalues. Malformed amplitudes can therefore reach the external eigensolver without the promised finite-input boundary.

- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 268–328; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 399–443; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 331–334; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.

Controls: RLA-P42.

Limits: The missing pre/postguards and NaN comparisons are established; final acceptance, panic or nontermination of nalgebra for NaN is not claimed or executed. Raw from_raw and diagonal-probability inputs do reject nonfinite values.

Recommendation: Centralize finite-entry validation before eigensolver calls, check every computed diagnostic/eigenvalue for finiteness and use the bounded spectrum owner or equivalent replay policy.

**RLA-F21** Several numerical Result APIs perform unchecked dimension/index arithmetic before refusal: density from_raw computes dim*dim (dim2^32 overflows64-bit), partial traces multiply supplied factors, get formats max(i,j)+1, ComplexMatrix::to_real_block doubles admitted zero-area dimensions, and set computes an invalid nonfinite entry index before checking bounds.

- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 234–245; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 540–574; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/density.rs` lines 642–647; SHA256 `2974c5ab99c4767cde13e2eb88e17f7b22834f5ece83090d0df82d3248fe0452`.
- `code/rust/core_linear_algebra/src/linear_algebra/complex_matrix.rs` lines 114–122; SHA256 `1afed6e017380bd2b0a6a5418924aa82bb58be2b61cda3bdf696f66e66b3620e`.
- `code/rust/core_linear_algebra/src/linear_algebra/complex_matrix.rs` lines 211–226; SHA256 `1afed6e017380bd2b0a6a5418924aa82bb58be2b61cda3bdf696f66e66b3620e`.

Controls: RLA-P42.

Limits: Static64-bit arithmetic bounds; no large allocation/native panic test. This is error-path totality/resource handling, distinct from valid finite-dimensional matrix mathematics.

Recommendation: Use checked products and nonoverflowing diagnostics before allocation/indexing; propagate typed dimension failures.

## Control receipts and limits

- **RLA-P01** (bounded_recorded): 2x2 adjugate identity. Exact integer identity model; source checked i128 intermediates and i64 output have separate representability premises.

- **RLA-P02** (bounded_recorded): Bareiss algorithm versus independent permutation expansion. 

- **RLA-P03** (bounded_recorded): Paired Pfaffian elimination versus independent matching expansion and determinant square. 

- **RLA-P04** (bounded_recorded): Exact reduction/image/kernel models versus independent minor rank. Finite rational source models; rank reference uses determinant minors, not the reduction algorithm.

- **RLA-P05** (bounded_recorded): PSD LDLT model versus all principal minors. Rational symmetric input, sizes1..3; negative paths return partial factors, not a complete inertia decomposition.

- **RLA-P06** (bounded_recorded): RankNullity count admission accepts mixed source witnesses. Independent exact model of public constructor outputs and count predicate, not a native run. Rank-nullity theorem itself is not refuted; missing common-source binding is exposed.

- **RLA-P07** (bounded_recorded): ExactRepairSpace declared basis count is not matrix rank. Public metadata constructor only; this does not bypass private ExactRepair residual checking.

- **RLA-P08** (bounded_recorded): Two-sided rational basis changes and conjugacy transport. Independent exact model on small matrices, not arbitrary scalar traits or original execution.

- **RLA-P09** (bounded_recorded): Lumpability commutation and bounded Boolean roots. Finite checks corroborate the source induction; relational composition is the separate Boolean-square reference.

- **RLA-P10** (bounded_recorded): R*d=0 exactly controls rational report invariance under supplied repair shifts. Small exact model; no semantic or physical interpretation of the supplied maps.

- **RLA-P11** (bounded_recorded): Semiring multiply budget counts dot-product terms, not individual scalar method calls. Exact loop-count calculation only; no large allocation or original execution. Per-call dot-product budget remains finite.

- **RLA-P12** (bounded_recorded): Cochain-map composition and homotopy-induced equality on degree-one cohomology. One-dimensional F2 windows only; general theorem remains conditional on lawful ring operations and the checked equations.

- **RLA-P13** (bounded_recorded): Exact-field solve and inconsistency certificates against exhaustive finite-field solution sets. Every2x2 matrix and right-hand side over F2/F3; particular-plus-kernel sets compared with exhaustive vector search. Independent model, not native execution or arbitrary-field proof.

- **RLA-P14** (bounded_recorded): Empty-axis extraction and row-list shape loss. Tiny independent control-flow/shape model; no out-of-bounds native memory access is asserted.

- **RLA-P15** (bounded_recorded): Narrowing unreduced rational checks raw pair instead of mathematical representability. Exact arithmetic plus source/dependency inspection. Canonical nonzero-denominator inputs avoid this mismatch. No native panic or conversion was executed.

- **RLA-P16** (bounded_recorded): Berkowitz versus permutation determinant polynomials and Cayley-Hamilton; Krylov minimality versus exhaustive monic search. All matrices through n=3 over F2 and through n=2 over F3 and Z/6; minimality only on F2/F3. Independent exact models, not retained Rust execution.

- **RLA-P17** (bounded_recorded): Row-major commutator kernel spans exactly the direct finite centralizer. Empty and singleton2x2 families over F2/F3, and all ordered pairs over F2; direct multiplication independently compared with full kernel span. No native execution or arbitrary-dimension proof.

- **RLA-P18** (bounded_recorded): Noncommutative coefficient ring invalidates unrestricted ring wording. Exact finite counterexample to literal rings-of-any-kind extension, not to the lawful commutative-field contract or the commutative Z/6 example.

- **RLA-P19** (bounded_recorded): Exact rational full-rank factorization and all four Penrose identities, with tampered-result rejection. All entries -1,0,1 in shapes1x1,1x2,2x1,2x2,2x3,3x2. Independent Fraction models; not native execution, arbitrary-field proof or HermitianOrdered admission validation.

- **RLA-P20** (bounded_recorded): Separately reset scalar-call limits do not bound the composite call. Tiny source-correspondent branch model. The top-level pseudoinverse constructor has its own conservative whole-call preflight; this witness concerns the standalone verifier and commutant-basis function.

- **RLA-P21** (bounded_recorded): Congruence certificate replay, unit determinant, LDL outcomes and negative witnesses against all-principal-minor PSD oracle. Every symmetric rational matrix of dimension0..3 with entries -1,0,1. Congruence model uses complete elementary matrix products; all certificates replay against the intact input. Independent models, not native execution or generic Hermitian proof.

- **RLA-P22** (bounded_recorded): Hermitian sample checker accepts invalid sign2 on a computed norm. All sampled values include0,1,-1 and a mixed complex value. Independent exact predicate model; universal trait satisfaction is not claimed.

- **RLA-P23** (bounded_recorded): Neville scalar recurrence matches Lagrange; tight box image matches corners and lies inside propagated interval. Permutations of up to3 distinct rational nodes, three interval choices and four evaluation points. No function remainder, asymptotic limit or native execution.

- **RLA-P24** (bounded_recorded): Fraction-free row-cleared systems versus independent rational Gauss-Jordan, with original-equation replay. All0..2 shapes over a three-element rational entry set and three right-hand-side values, plus60 larger deterministic cases. No original solver or budget implementation executed.

- **RLA-P25** (bounded_recorded): Matrix derivative jets versus independent polynomial convolution. Rational2x2 polynomial matrix curves. Proves neither analytic realizability of arbitrary abstract jets nor native execution.

- **RLA-P26** (bounded_recorded): Input/result bit admission does not bound dependency arithmetic temporaries. Exact arithmetic plus pinned num-rational addition source; no native allocation measurement. Accepted exposed values remain within the declared bound.

- **RLA-P27** (completed_bounded): Finite integer orthogonality and forward/backward prefix consistency. Own integers in {-1,0,1}^3 and lists length1..4 over {-2,0,3}; no original execution or arbitrary fixed-width overflow guarantee.

- **RLA-P28** (counterexample_observed): Symbolic category unit composition differs under actual string equality. Same valid endpoint labels/dimensions. Shape-only documentation is acknowledged; no upstream category implementation executed.

- **RLA-P29** (counterexample_observed): Finite binary64 coordinates can produce nonfinite checked-dot output. Own IEEE754 Python scalar operations mirror the two multiply/add expressions only; not Rust execution or evidence about robust numerical owners.

- **RLA-P30** (completed_bounded): Complex balance projector and rectangular operator compression against direct component algebra. Own rational models with dimensions1..3 and12 rectangular pairs; supplied complex structure and invertible2 are assumptions, not physical scalar selection.

- **RLA-P31** (completed_bounded): Reference support projectors on every matrix unit of a three-site carrier. Own exact8x8 rational carrier. Projections are reference-dependent algebraic maps; no positivity or orthogonality claimed.

- **RLA-P32** (completed_bounded_with_counterexample): Partial transpose involution and explicit positivity failure; empty-axis diagnostic overflow. Own finite index/arithmetic models and symbolic64-bit bound; no native huge allocation or panic executed.

- **RLA-P33** (observed): Integer two-by-two determinantal-divisor invariance under elementary shears. Independent integer characterization; not execution of Smith algorithm, termination proof or all-size certification.

- **RLA-P34** (observed): Rational chain-step quotient representatives and graph Laplacian quadratic identity. Q chain shapes1x2 and2x1, entries-2..2; simple graphs n<=4 and ternary coordinate vectors; no torsion or native execution.

- **RLA-P35** (counterexample_observed): Admitted empty/sparse dimension arithmetic and finite-input L1 overflow. 64-bit symbolic size model and Python binary64; no large allocations or Rust execution.

- **RLA-P36** (observed): Root normalization, relabeling orbit and complete finite gradient-descent criterion. Root/gauge panel n2; maps source/target<=4. Complete unit-potential basis suffices for each tested integer-linear map; no retained enumeration dependency executed.

- **RLA-P37** (observed): Cayley-Menger formula versus Euclidean admission, and bivector Plucker identity. Independent exact rational formulas; constructor bypass is source-visible, not native execution. Polynomial correctness does not admit metric geometry.

- **RLA-P38** (observed): Exact rational Gram-Schmidt triangular replay and complement identities. Two ternary vectors in Q3, exact Fraction; not source execution, general Gram form or normalizing square roots.

- **RLA-P39** (counterexample_observed): Projector scalar overflow, failed sparse compression state and imaginary Hermitian diagonal. Source-aligned arithmetic/state models only. Drain error semantics statically visible; no retained Rust or external library execution.

- **RLA-P40** (observed): Packed coordinate bijection, complex contraction/quadratic form and rational positive-definite solve replay. Index n<=64, exact-small Gaussian integer operations n<=8,2x2 rational systems. No original packed/LDL code executed.

- **RLA-P41** (observed): Independent exact eigenpair and orthonormality replay for rotated two-dimensional spectra. Residual identities and degeneracy control, not eigenvalue solver execution or floating error certification.

- **RLA-P42** (counterexample_observed): Nonfinite comparison holes, complex finite-input overflow and dimension arithmetic. Python binary64 comparisons and64-bit symbolic integers. Confirms missing pre/postguards, not whether external nalgebra terminates or accepts NaN on any path.

Source review and independent finite controls only; no original Rust/Cargo/native/provider execution.
Display receipts require separate manual substantive notes; metadata scans earn no full-source credit.
All 83 original source hashes and full line-range unions are reconciled; no source edits or new external-dependency body coverage.
Control helpers are independent audit-authored models in available Python 3.14.2, not Rust/native builds or integration-test reproduction.
Exact mechanisms remain conditional on the stated field/ring/order/involution laws, source metadata, coefficient representation and resource bounds.
Historical mutation counts, authority fences and type-name witnesses are not fresh mathematical or execution evidence.
This declared slice is complete only when pending is zero; the broader repository audit remains incomplete.
