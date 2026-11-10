# Rust finite algebra audit — complete declared slice

All **83 files / 42,277 lines / 1,524,595 bytes** in the frozen scope received direct full-body review. There are **0 pending paths, 0 partial reads, 0 parsed-data substitutions and 0 template transfers**. All original hashes match. The larger repository audit remains incomplete.

The report contains **41 findings, 33 qualified claims and 16 independent bounded control groups**. Rust tests were read, not run; no native/Cargo/retained program, provider or private-answer execution occurred. Only audit-authored stdlib Python ran under 3.14.2.

Scope SHA256: `739fa75e199d7fbd0b8a9bd84623929d9b290559ead7d749d6a37894ab8afefa`. Original commit: `8050c66900899771766f33e8f5fdd200b7dd9120`. JSON and final validation carry the per-file hashes, complete nonoverlapping ranges, substantive assessments and control/source bindings. Prior checkpoint snapshots are preserved with `.json.snapshot` suffixes.

## Main conclusions

- The strongest reusable components reconstruct or bind their full carrier and replay a precise predicate: private polynomial/root representations, finite group-table admission, complete cochain reconstruction, signed transport certificates, rational gauge quotients, fusion-ring laws, pentagon/hexagon residuals and finite braid closure. Their classical theorem and backend premises remain explicit.
- Public or unchecked representations need separate admission. Findings cover reducible binary-field moduli, malformed field/ordered-root carriers, missing scalar-law restrictions, shape/overflow boundaries, ambiguous hash framing and unguarded modular invariants. Cases that deliberately violate a documented caller premise are identified as such.
- The legacy connection Laplacian has a concrete orientation error under a valid rational orthogonal gauge (F032). The newer edge-indexed incidence construction computes the correctly oriented D*WD and is not implicated.
- Exact finite checks do not derive physical geometry, quantum state spaces, topology or Genesis primitives. Closure exceeding a bound is not infinity or density; one spectral residual is not an all-parameter theorem; dimension consistency does not construct an independent pivotal coherence witness.
- Inline test quality varies. Several modules have meaningful mathematical mutants and resource controls; other mutation-labeled tests exercise only capacity wrappers or literal Ok/Err values. No claim is made that external integration tests are absent or that a native suite passed.

## Qualified mathematical mechanisms

### RFA-CL001

The four library-entry admissions enforce narrow arithmetic predicates: normalized Farey determinant magnitude one, an i128-bounded rational skew-block square, one positive fusion-channel product, and nonempty cyclic displacement zero. They do not by themselves certify the full domain modules or promote authority.

Limit: All scoped module owners are now fully reviewed separately. Sibling integration tests remain outside this slice; no Rust execution. Mutation-count comments do not supply reproducible mutation evidence.

Evidence: [code/rust/core_number_theory/src/lib.rs:118–158](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/lib.rs:118) (SHA256 `e55138db466ba55f722ba25854a29a52eeeef3cf27f9739bb95a08335766eb96`); [code/rust/core_lie_theory/src/lib.rs:86–169](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lib.rs:86) (SHA256 `14b8fc146b655cbd20a71aabfde2e7f1b0d5e4fb9f0fa46891c6351d0277f615`); [code/rust/core_fusion_categories/src/lib.rs:61–83](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/lib.rs:61) (SHA256 `ca842af5a529d8d0f4be92afb26b4278c540dc3ef0a322bd4367920e147b5436`); [code/rust/core_holonomy/src/lib.rs:52–97](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/lib.rs:52) (SHA256 `6152e9e98e16bf21d06a8f107ba3275b0581594a925270e445d52c6fd45da606`); [code/rust/core_holonomy/src/lib.rs:104–227](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/lib.rs:104) (SHA256 `6152e9e98e16bf21d06a8f107ba3275b0581594a925270e445d52c6fd45da606`)

### RFA-CL002

For normalized rational/integer inputs, checked roots and bounded squarefree extraction compute exact identities or explicit refusal; the residual threshold is justified because all remaining prime factors exceed the trial limit.

Limit: 13,013 independent small controls,8,485 admitted and4,528 refused; exact bit complexity and unrestricted raw Ratio validity not certified. rq is explicitly partial.

Evidence: [code/rust/core_number_theory/src/rational.rs:109–173](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:109) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`); [code/rust/core_number_theory/src/rational.rs:215–327](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:215) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`)

### RFA-CL003

The searched FiniteField constructor checks primality and complete bounded-degree monic-divisor irreducibility. Canonical arithmetic is polynomial quotient arithmetic; BinaryField must additionally exclude the demonstrated even-modulus and degree-zero admission gap.

Limit: No resource cap beyond machine cardinality; machine coefficient overflow for large primes and malformed public representations are not covered by small canonical-field controls.

Evidence: [code/rust/core_number_theory/src/finite_field.rs:74–87](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:74) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`); [code/rust/core_number_theory/src/finite_field.rs:206–340](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:206) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`); [code/rust/core_number_theory/src/binary_field.rs:43–140](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:43) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`)

### RFA-CL004

Integer factorization uses a shared explicit work counter and exact split/primality decisions, while residue roots combine exact prime-power formulas through CRT instead of scanning all residues. Exhaustion yields a typed error without a purported complete factorization.

Limit: Full u64 Miller-Rabin base theorem trusted as stated; finite control compares20,000 small integers, and999 residue moduli. No Rust/backend implementation run or universal complexity bound.

Evidence: [code/rust/core_number_theory/src/integer_factorization.rs:50–241](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/integer_factorization.rs:50) (SHA256 `b20c3c6e53044a5f215eeac01fd8e9c3eabb0eabe2f50347f63caf838162b81f`); [code/rust/core_number_theory/src/residue.rs:18–77](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/residue.rs:18) (SHA256 `ac0e61c5c4c4376901925c11b1d08d88249c687e806b8806b206518de09a7429`)

### RFA-CL005

Gaussian norm verification replays submitted coordinates exactly and obstruction verification binds the input, rechecks a prime3mod4 and recomputes odd signed valuation; bounded construction separates exhaustion from non-norm. Two/four-square constructors replay positive witnesses, with a reduced-input caveat for rational norm realization.

Limit: Prime-factorization and sum-of-two-squares theorem dependencies; independent small controls do not certify unrestricted factorization or total bounded search. F009 records raw representation false-negative.

Evidence: [code/rust/core_number_theory/src/gaussian_norm.rs:108–206](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gaussian_norm.rs:108) (SHA256 `280c87abd6d873ffcd3f2c44f0c52de7cbf334073c5e2c505571080435c7c075`); [code/rust/core_number_theory/src/sums_of_squares.rs:105–134](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/sums_of_squares.rs:105) (SHA256 `4ad80a76a41b852c210b7920ceb1fb65567ff11ac300357e37289ef2b79d279a`); [code/rust/core_number_theory/src/four_squares.rs:29–129](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/four_squares.rs:29) (SHA256 `886f8903ab2a97cc8a3f630168473e69512827ed86304f2f571c3906ea10b3a1`)

### RFA-CL006

Rational circle and finite dyadic modules preserve explicit carrier, conductor, finite-prefix and budget boundaries. Circle Haar routines execute finite character sums and return conditional finite Lipschitz enclosures; they do not infer an infinite sampling family or topology.

Limit: Exact conditional circle/Haar formulas and bounded controls; cyclotomic owners now fully reviewed, while the external Interval owner remains a dependency. No measure-theoretic universality or physical admission follows.

Evidence: [code/rust/core_number_theory/src/rational_circle.rs:13–51](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational_circle.rs:13) (SHA256 `c9ad54faef3007a103422060e30153c06955013c4802e7fcf68a05bb5c4e9787`); [code/rust/core_number_theory/src/rational_turns.rs:22–92](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational_turns.rs:22) (SHA256 `25b7c1379ab56c2e2570ec5d2dd795e7665ca190b8a3683dd5ea5f370fc92129`); [code/rust/core_number_theory/src/dyadic_presentation.rs:67–218](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/dyadic_presentation.rs:67) (SHA256 `510c44b8c2ce8525d5c4bd5394836b3e0249dc755833279fea6a830029e9d654`); [code/rust/core_number_theory/src/circle_haar.rs:45–168](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/circle_haar.rs:45) (SHA256 `141b0a3eebc2cf2f809a154c5746f08cd5d53d61861fdb97a95c46b22e647ce1`)

### RFA-CL007

Certified-angle routines construct rational endpoint enclosures with explicit input and series limits; square roots replay endpoint squares, while atan/pi use alternating-series and rational argument identities with allocated width budgets.

Limit: Bounded independent square and alternating-bound nesting checks; no external transcendental oracle or Interval backend execution. Machin/branch and alternating-series mathematical premises remain explicit.

Evidence: [code/rust/core_number_theory/src/certified_angles.rs:36–143](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/certified_angles.rs:36) (SHA256 `a0fcb9fc43501ff03437f5300887c345b5a562ffc6b37efcb5a6cf1bbd6d2b5f`)

### RFA-CL008

Private truncated-series and sparse rational-map carriers enforce their declared shape/constant/exponent conditions; exact recurrences support formal inverse/log/exp and Jacobian difference as a one-way non-affinity witness, with explicit truncation and sample ceilings.

Limit: Generic scalar laws and BasicMatrix backend trusted;81 finite rational tails and6561 Leibniz pairs checked independently. No unrestricted series convergence or complete affinity inference.

Evidence: [code/rust/core_number_theory/src/power_series.rs:39–201](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/power_series.rs:39) (SHA256 `7c8c4f185815295e119a89e842dade357eafc625cb84630f1e489b5fcfe35ac5`); [code/rust/core_number_theory/src/polynomial_map.rs:28–148](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial_map.rs:28) (SHA256 `b80cb1754515402a0a0f8657c1bfaa1bc5b62f3c360def3ff63a11643b78bf41`)

### RFA-CL009

Quadratic arithmetic has an actual radicand admission mechanism: a private compile-time proof token for fixed D and bounded squarefree validation for runtime D. Private Surd/runtime coordinates preserve canonical radical structure, exact root criteria and sign comparisons; complex and Galois conjugation are explicitly distinct over real fields.

Limit: Compile-time admission and native tests not executed; normalized valid upstream rational limbs and external polynomial/Interval behavior are premises.490 generated-square,24,010 norm-pair and294 sign-bracket finite controls do not certify universal native behavior.

Evidence: [code/rust/core_number_theory/src/quadratic.rs:65–158](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/quadratic.rs:65) (SHA256 `78aebe31aeffd2a86c4dc4b555187b3ff55e400600bd03850492f6e52d1448d4`); [code/rust/core_number_theory/src/quadratic.rs:195–349](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/quadratic.rs:195) (SHA256 `78aebe31aeffd2a86c4dc4b555187b3ff55e400600bd03850492f6e52d1448d4`); [code/rust/core_number_theory/src/quadratic.rs:492–700](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/quadratic.rs:492) (SHA256 `78aebe31aeffd2a86c4dc4b555187b3ff55e400600bd03850492f6e52d1448d4`); [code/rust/core_number_theory/src/quadratic.rs:749–1035](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/quadratic.rs:749) (SHA256 `78aebe31aeffd2a86c4dc4b555187b3ff55e400600bd03850492f6e52d1448d4`); [code/rust/core_number_theory/src/radical_sum.rs:7–40](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/radical_sum.rs:7) (SHA256 `36b934ebfc6fc5594c120ce361e103056761abd8bafb78c589635ffcfea5e068`)

### RFA-CL010

The private polynomial/Sturm owners implement exact quotient identities, distinct half-open real-root counts, rational-root lattice recognition and multiplicities. Rational factorization adds bounded prime search, Berlekamp/Hensel/recombination with explicit exhaustion and final product replay; its public verifier expressly checks only product binding.

Limit: External scalar/linear algebra/enumeration/Interval correctness and classical Sturm/Berlekamp/Hensel coefficient-bound arguments remain dependencies. Independent small exact controls do not run native algorithm or establish all irreducibility claims. Public root refinement boundary is F011.

Evidence: [code/rust/core_number_theory/src/polynomial.rs:350–531](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial.rs:350) (SHA256 `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0`); [code/rust/core_number_theory/src/polynomial.rs:785–922](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial.rs:785) (SHA256 `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0`); [code/rust/core_number_theory/src/polynomial.rs:1048–1215](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial.rs:1048) (SHA256 `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0`); [code/rust/core_number_theory/src/polynomial_factorization.rs:73–110](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial_factorization.rs:73) (SHA256 `1fa6bd69cdbb0e6f8c198a654e2a5c978647a3c23e865403d3bf5b1f73162d30`); [code/rust/core_number_theory/src/polynomial_factorization.rs:224–560](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial_factorization.rs:224) (SHA256 `1fa6bd69cdbb0e6f8c198a654e2a5c978647a3c23e865403d3bf5b1f73162d30`)

### RFA-CL011

The fixed cyclotomic owners implement rational quotient rings with explicit Phi5/8/12/24/28/44/52/120 and coordinate-exact multiplication, conjugation and nonzero inverse solving. Quadratic Gauss sums and explicit phase sums give reusable exact square identities for finite Weyl/MUB controls.

Limit: Cyclotomic irreducibility and chosen complex embedding are mathematical premises; positivity is not inferred from square identities alone. Public rational limbs need valid upstream values; zero inherent inverse is partial. Many files have local elimination despite shared-solver prose. Capacity records confer no arithmetic or authority certification; exponent boundary F012 remains.

Evidence: [code/rust/core_number_theory/src/cyclotomic.rs:31–948](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic.rs:31) (SHA256 `1d120eac163f026e4b24d0da609823e6254193cb6e4d197f059725834a4b8699`); [code/rust/core_number_theory/src/cyclotomic28.rs:36–206](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic28.rs:36) (SHA256 `6b81a9c8bf01ceda0d43324029424d10ff3722ea7679e493679fddcfa428749e`); [code/rust/core_number_theory/src/cyclotomic44.rs:36–208](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic44.rs:36) (SHA256 `f82eb3be0d3f82adef58b88bc8ac93ac422365ea96b680a08728810fb1d800e3`); [code/rust/core_number_theory/src/cyclotomic52.rs:36–202](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic52.rs:36) (SHA256 `4ce4933e0bb9d24fab1a3d8b8b37af541d3694e5fbb1bc2fe84bc5ca984abb6e`); [code/rust/core_number_theory/src/cyclotomic120.rs:36–211](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic120.rs:36) (SHA256 `d09b420e11f4473ad1cb43728b0eeb1579713d93f72ea0b54fd24eab513cc1a6`)

### RFA-CL012

General cyclotomic numbers and cyclotomic integers enforce private conductor and canonical coordinate shape, supporting exact reusable arithmetic, Galois maps, trace/norm, normalized field inclusion, and finite quantum/Gauss constructions. Input-bound square-root replay is separate from canonical embedding positivity.

Limit: Classical cyclotomic irreducibility, conductor inclusion and Gauss sign theorems plus rational/polynomial backend are dependencies. Limits bound conductors or selected entries/indices, not all bit complexity. No Rust tests executed.

Evidence: [code/rust/core_number_theory/src/cyclotomic_field.rs:109–380](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_field.rs:109) (SHA256 `ab6d4eb5163ac7bb10b8d0b35ae5b6b295d3f7eaa01394f95a351cb62ce43183`); [code/rust/core_number_theory/src/cyclotomic_field.rs:447–774](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_field.rs:447) (SHA256 `ab6d4eb5163ac7bb10b8d0b35ae5b6b295d3f7eaa01394f95a351cb62ce43183`); [code/rust/core_number_theory/src/cyclotomic_field.rs:781–943](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_field.rs:781) (SHA256 `ab6d4eb5163ac7bb10b8d0b35ae5b6b295d3f7eaa01394f95a351cb62ce43183`); [code/rust/core_number_theory/src/cyclotomic_integer.rs:99–353](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_integer.rs:99) (SHA256 `38cf0656fff0f4357773f2f8265907ff52e79a121ff36169d4105753f4b9df6d`)

### RFA-CL013

The private algebraic-root and RealEmbeddings owners bind roots to actual squarefree/Sturm isolation; rational/quadratic recognition replays membership, and sign algorithms use reduced-polynomial zero plus exact interval separation. The separate first-dependence routine computes an element minimal polynomial conditional on exact linear algebra.

Limit: Classical Sturm/irreducibility/embedding monotonicity premises, rational interval and external kernel dependencies remain explicit. Finite precision refusal differs from universal success. Legacy public ordered carriers have F014-F016 gaps; those do not transfer to private owners.

Evidence: [code/rust/core_number_theory/src/algebraic_real.rs:47–315](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/algebraic_real.rs:47) (SHA256 `8b16f01f83d53cf85a6bd3743ea65d03045ddafd98ef0a42efdcfc9752c872f1`); [code/rust/core_number_theory/src/real_embedding.rs:86–110](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/real_embedding.rs:86) (SHA256 `b2dbc497543e1414717f434db3201179e891aca5dac7ef27421eabedf912ceb3`); [code/rust/core_number_theory/src/real_embedding.rs:191–344](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/real_embedding.rs:191) (SHA256 `b2dbc497543e1414717f434db3201179e891aca5dac7ef27421eabedf912ceb3`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:85–110](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:85) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:887–918](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:887) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`)

### RFA-CL014

The GF2 owner provides exact reusable row reduction, kernel/image bases, affine solution torsors and canonical span reduction on private bounded vector/matrix representations. The semantic carrier is finite GF2 linear algebra, not a geometric/homological interpretation.

Limit: Small exhaustive mathematical models do not compile or execute the Rust implementation. Zero-axis size admission is F017; kernel storage and enumeration bounds are not a universal time/memory budget. Public Rref labels are not standalone proof objects.

Evidence: [code/rust/core_number_theory/src/gf2.rs:78–83](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:78) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`); [code/rust/core_number_theory/src/gf2.rs:289–351](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:289) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`); [code/rust/core_number_theory/src/gf2.rs:673–914](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:673) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`)

### RFA-CL015

Vanishing-sum owners construct and replay prime-polygon length witnesses, bounded numerical-semigroup membership, and primitive-root conductor witnesses with exact element-order tests and prior-conductor exclusion. These mechanisms explicitly separate repeated roots/length existence from irreducible-sum classification.

Limit: Lam-Leung necessity, irreducibility of prime polygons, and full root-of-unity groups of cyclotomic fields are classical premises; verifier recomputation checks arithmetic bindings but does not prove those theorems. Finite controls and explicit budget refusal do not imply broad physical/genesis claims.

Evidence: [code/rust/core_number_theory/src/vanishing_sums.rs:1–4](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/vanishing_sums.rs:1) (SHA256 `765d3f70c2fa266a9d12aa95d70363e25776d9aa3ed55a19873fbf223697bdab`); [code/rust/core_number_theory/src/vanishing_sums.rs:49–220](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/vanishing_sums.rs:49) (SHA256 `765d3f70c2fa266a9d12aa95d70363e25776d9aa3ed55a19873fbf223697bdab`); [code/rust/core_number_theory/src/vanishing_sums.rs:301–399](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/vanishing_sums.rs:301) (SHA256 `765d3f70c2fa266a9d12aa95d70363e25776d9aa3ed55a19873fbf223697bdab`)

### RFA-CL016

Exact Cayley and phase-shifted unitary charts enforce finite shape and skew/Hermitian/unit phase premises, expose cut-locus refusals, and provide rational circle composition including infinity. They are reusable algebraic parameterizations conditional on lawful field/matrix owners.

Limit: No geometric universality follows from finite charts; singular locus and supplied parameter conventions matter. Matrix backend and scalar laws remain dependencies; no native tests run.

Evidence: [code/rust/core_lie_theory/src/cayley.rs:65–171](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/cayley.rs:65) (SHA256 `1d4e7dd29becef243b69b4c535b29c6c0136df9225d5c82ae3ecb37c7fd0785a`); [code/rust/core_lie_theory/src/cayley.rs:201–289](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/cayley.rs:201) (SHA256 `1d4e7dd29becef243b69b4c535b29c6c0136df9225d5c82ae3ecb37c7fd0785a`); [code/rust/core_lie_theory/src/cayley.rs:326–339](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/cayley.rs:326) (SHA256 `1d4e7dd29becef243b69b4c535b29c6c0136df9225d5c82ae3ecb37c7fd0785a`); [code/rust/core_lie_theory/src/cayley_unitary.rs:32–115](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/cayley_unitary.rs:32) (SHA256 `8202a444e6d1e8e208880c0ec04622ce189feb40534f4460f7bb7cbaf587f074`)

### RFA-CL017

The structure-constant owner can check basis-level Jacobi and adjoint equations, recover constants from independent commutator-closed matrices, and construct bounded exterior differentials. Rational spin matrices explicitly satisfy sl2relations/Casimir on independent finite controls; Rodrigues reconstruction distinguishes projective rational rotations from rational unit lifts through a squareclass obstruction.

Limit: Trait labels/table shape are not Lie admission; F018-F021 constrain validation/irreducibility claims. Group and Pauli owners now fully reviewed with checked versus inherited premises explicit. Rational squareclass factorization may refuse boundedly; no physical spin or Genesis origin is established.

Evidence: [code/rust/core_lie_theory/src/lie_algebra.rs:168–351](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:168) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`); [code/rust/core_lie_theory/src/lie_algebra.rs:358–519](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:358) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`); [code/rust/core_lie_theory/src/su2.rs:184–313](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2.rs:184) (SHA256 `149302c8432180bb3f11e7ddf9fe1381d76db63701a8e2d10fd4009ef3d85c7a`); [code/rust/core_lie_theory/src/su2.rs:319–414](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2.rs:319) (SHA256 `149302c8432180bb3f11e7ddf9fe1381d76db63701a8e2d10fd4009ef3d85c7a`); [code/rust/core_lie_theory/src/su2_matrix.rs:36–119](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2_matrix.rs:36) (SHA256 `0cbf52dd64cd75cc85b0d3c686aa56295e275dea1afdaaf76528055d85bd4ddd`)

### RFA-CL018

Finite group table admission exhausts the group equations, whereas operation/generation constructors rely on documented ambient associativity and canonical keys. Exact subgroup/quotient/regular-function constructions are reusable finite mathematics conditional on those admissions; character table reconstruction combines finite computations with classical representation-theory premises.

Limit: No native build or character-table replay; finite size bounds do not establish resource bounds for arbitrary scalar/parameter inputs. F023-F024 concern public output/input handling.

Evidence: [code/rust/core_lie_theory/src/finite_group.rs:169–345](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_group.rs:169) (SHA256 `d7ebe04efe35a4f3976016e84d3783642816cffdf9d3eb798c1db76690530a42`); [code/rust/core_lie_theory/src/finite_group.rs:501–712](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_group.rs:501) (SHA256 `d7ebe04efe35a4f3976016e84d3783642816cffdf9d3eb798c1db76690530a42`); [code/rust/core_lie_theory/src/finite_group.rs:1216–1467](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_group.rs:1216) (SHA256 `d7ebe04efe35a4f3976016e84d3783642816cffdf9d3eb798c1db76690530a42`)

### RFA-CL019

Rational finite-order detection uses complete bounded-degree cyclotomic enumeration plus actual matrix-power equality, separating root-of-unity eigenvalues from Jordan obstructions. Twisted abelian algebra admission checks all cocycle triples; path/groupoid algebra constructions provide concrete finite regular representations and central/origin projections under their imported category contracts.

Limit: Category owners and matrix backend are external dependencies; complex completion and representation theorems are mathematical premises, not a derivation of physical state/dynamics.

Evidence: [code/rust/core_lie_theory/src/finite_order.rs:24–137](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_order.rs:24) (SHA256 `061995d0253dceb91116996147b1e9d85b42582b2a7c2e747fda6ed5cd62f6ea`); [code/rust/core_lie_theory/src/twisted_abelian_algebra.rs:30–190](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/twisted_abelian_algebra.rs:30) (SHA256 `e6fc9c62da02de42eb5e3a888c69952ebd92c5d25abb294b6bda9b3ac09b49c7`); [code/rust/core_lie_theory/src/finite_path_algebra.rs:38–228](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_path_algebra.rs:38) (SHA256 `64dc3c651ffeb41b7fa355f4dd21f14182ac6275aed840e640e0d11b234bad9c`); [code/rust/core_lie_theory/src/finite_groupoid_algebra.rs:36–237](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_groupoid_algebra.rs:36) (SHA256 `1c03090f37adefde8c39605aa167cd8eecdd5ba59aabaf03a61c389240a4d5c5`)

### RFA-CL020

Finite Weyl systems, Clifford families and symplectic images enforce concrete exact admissions. Supplied clock-seed intertwiners are reconstructed then checked against both unitarity and defining operator equations; this reusable certificate mechanism is stronger than a dimension census or label alone.

Limit: Lawful characteristic-zero complex fields and matrix backend remain dependencies; no physical origin, arbitrary-dimensional classification or native test run. Scalar phase/kernel information is deliberately lost by the symplectic quotient.

Evidence: [code/rust/core_lie_theory/src/heisenberg.rs:76–110](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/heisenberg.rs:76) (SHA256 `58fc3142ab285e69f9dc3747af5ec1b806eb867085843aa2df8b726c7fe005c7`); [code/rust/core_lie_theory/src/heisenberg.rs:291–430](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/heisenberg.rs:291) (SHA256 `58fc3142ab285e69f9dc3747af5ec1b806eb867085843aa2df8b726c7fe005c7`); [code/rust/core_lie_theory/src/clifford.rs:50–94](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/clifford.rs:50) (SHA256 `654f9823822fae39cf63deefe8ce5f664859c411abf4c1940809c110eff485fa`); [code/rust/core_lie_theory/src/clifford.rs:212–245](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/clifford.rs:212) (SHA256 `654f9823822fae39cf63deefe8ce5f664859c411abf4c1940809c110eff485fa`); [code/rust/core_lie_theory/src/pauli_symplectic.rs:305–328](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/pauli_symplectic.rs:305) (SHA256 `9b89d9878a665979c17cdf3c51e8c34522811fc1f48cf89d5b74367b97994e08`)

### RFA-CL021

Rational Lorentz admission and polar decomposition explicitly replay form, determinant, time direction and spatial block constraints. Gell-Mann coordinates keep irrational normalization separate through rational squared scales; weighted identities are finite exact contractions over an independently declared label space.

Limit: F026-F027 qualify real/complex and component interpretations; raw formula helpers inherit input premises. Finite exact models do not derive spacetime or label carriers from primitives.

Evidence: [code/rust/core_lie_theory/src/lorentz.rs:137–199](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lorentz.rs:137) (SHA256 `51a055a3bd057b32a6af62829894c735d0285ccfd2b17ead9d17e24629fd7015`); [code/rust/core_lie_theory/src/lorentz.rs:284–319](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lorentz.rs:284) (SHA256 `51a055a3bd057b32a6af62829894c735d0285ccfd2b17ead9d17e24629fd7015`); [code/rust/core_lie_theory/src/su_n.rs:169–260](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su_n.rs:169) (SHA256 `9a38043aa2cb8b44be93a1f35cb8ccd7916ae6920c901b9de71799ecd339bafa`); [code/rust/core_lie_theory/src/su_n.rs:301–424](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su_n.rs:301) (SHA256 `9a38043aa2cb8b44be93a1f35cb8ccd7916ae6920c901b9de71799ecd339bafa`)

### RFA-CL022

Finite partial-function orbits are checked on the whole supplied carrier and classified by first visits; huge iteration indices reduce before lookup. CellComplex.cochain_matrices reconstructs every public index/map/boundary, bounds dense and nilpotence work, then explicitly checks d1d0=0.

Limit: These are reusable exact finite admission/reconstruction mechanisms, not arbitrary topology or dynamical claims. Other public-carrier consumers do not automatically inherit the reconstruction checks.

Evidence: [code/rust/core_holonomy/src/functional_graph.rs:26–94](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/functional_graph.rs:26) (SHA256 `2d3d26191b1b72acb17fb2d8b68724192c6334883f6a1d132162ab6251ebd2c4`); [code/rust/core_holonomy/src/graph.rs:268–413](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/graph.rs:268) (SHA256 `ec8ae5aba841586cd21971277fda279a3d973ce20c4d8a123c0f3ef3e48eab3e`)

### RFA-CL023

Pure-gauge transport construction and ordered path products implement endpoint gauge covariance, and Bianchi explicitly limits its result to the supplied ordered loop-product identity. Matrix arithmetic is exact conditional on valid shapes and lawful field scalars.

Limit: F028-F036 identify state-binding, selfloop, Laplacian, scalar and budget boundaries. No generic topological homology pairing, pure-gauge converse or physical field theory follows.

Evidence: [code/rust/core_holonomy/src/connection.rs:129–215](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:129) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/holonomy.rs:66–125](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/holonomy.rs:66) (SHA256 `90f5b1438a5ca6dab1819c20a79c8ea0376dd75bcb601a641e7c5539fa9c10c2`); [code/rust/core_holonomy/src/curvature.rs:74–99](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/curvature.rs:74) (SHA256 `073913b9789a90bbe8e40ebfb4529f050c49abaee23eea6282b27b4b4818fa22`); [code/rust/core_holonomy/src/matrix.rs:461–614](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:461) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`)

### RFA-CL024

Signed transport certificates bind the complete canonical coefficient matrix and separately verify either a realizing sign gauge on every original edge or a genuine simple negative cycle. The finite dichotomy and componentwise gauge freedom are reusable exact mechanisms, limited to diagonal plus/minus1 gauges.

Limit: No general Hamiltonian/unitary sign-problem or sampling interpretation; no global resource bound. Literal inline tests are not runtime mathematical coverage.

Evidence: [code/rust/core_holonomy/src/signed_transport.rs:38–115](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/signed_transport.rs:38) (SHA256 `e4f053f601d75fd0074697ca1e0e60fc7a76f5d4859b827627ae3bdebfc02bbb`); [code/rust/core_holonomy/src/signed_transport.rs:153–269](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/signed_transport.rs:153) (SHA256 `e4f053f601d75fd0074697ca1e0e60fc7a76f5d4859b827627ae3bdebfc02bbb`); [code/rust/core_holonomy/src/signed_transport.rs:310–359](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/signed_transport.rs:310) (SHA256 `e4f053f601d75fd0074697ca1e0e60fc7a76f5d4859b827627ae3bdebfc02bbb`)

### RFA-CL025

Edge-indexed holonomy retains orientation and computes actual covariant incidence and D*WD. Spanning-forest residuals decide pure gauge, provide replayable obstructing cycles, distinguish flat/nontrivial/curved, and conservatively return Undetermined for unresolved simultaneous conjugacy. Cyclic flat-class counts use integer face relations and Smith invariants.

Limit: Valid public complex indices and lawful field/matrix owners remain premises; F028/F036 identify reconstruction/budget gaps. General nonabelian gauge equivalence is intentionally incomplete; Smithbackend notexecuted.

Evidence: [code/rust/core_holonomy/src/gauge_fixing.rs:351–449](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:351) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:517–627](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:517) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:873–891](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:873) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:1036–1139](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:1036) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:1149–1301](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:1149) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`)

### RFA-CL026

RationalGaugeQuotient correctly separates the full cochain quotient from its H1kernel, binds complete matrices and declared source using lengthframing, and replays shifts, exact repairs and commuting-map transport. Private context-bound classes/receipts prevent unchecked payload construction; zero curvature is never automatically promoted to exact repair.

Limit: Source digest is declared custody, not a filecontent or semantic theorem check. Finite rational homology dependency previously read under exactpin; eliminationbackend remains external. AuthorityNone tags do not by themselves enforce governance in callers.

Evidence: [code/rust/core_holonomy/src/gauge_quotient.rs:108–222](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_quotient.rs:108) (SHA256 `fc79543b48941c3d4f4cc897df0b524f5fb4f6444707b38011b329401dd73308`); [code/rust/core_holonomy/src/gauge_quotient.rs:287–420](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_quotient.rs:287) (SHA256 `fc79543b48941c3d4f4cc897df0b524f5fb4f6444707b38011b329401dd73308`); [code/rust/core_holonomy/src/gauge_quotient.rs:425–541](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_quotient.rs:425) (SHA256 `fc79543b48941c3d4f4cc897df0b524f5fb4f6444707b38011b329401dd73308`); [code/rust/core_holonomy/src/gauge_quotient.rs:543–724](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_quotient.rs:543) (SHA256 `fc79543b48941c3d4f4cc897df0b524f5fb4f6444707b38011b329401dd73308`)

### RFA-CL027

FusionTable is explicitly shape-only, while FusionRing exhaustively checks unit, associativity, coefficient-one duality/involution and reciprocity; commutativity is a separate gate. Bounded exact path counts, Perron dimensions and Verlinde residuals are useful ring-level computations, with no automatic categorifiability claim.

Limit: Classical Perron theory and reviewed algebraic-root owners remain dependencies; no native test run. Complete category, braided and modular owners are now separately assessed in CL028–CL032.

Evidence: [code/rust/core_fusion_categories/src/fusion_ring.rs:217–260](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_ring.rs:217) (SHA256 `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892`); [code/rust/core_fusion_categories/src/fusion_ring.rs:304–451](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_ring.rs:304) (SHA256 `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892`); [code/rust/core_fusion_categories/src/fusion_ring.rs:581–691](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_ring.rs:581) (SHA256 `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892`); [code/rust/core_fusion_categories/src/fusion_ring.rs:741–856](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_ring.rs:741) (SHA256 `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892`); [code/rust/core_fusion_categories/src/fusion_ring.rs:1006–1118](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_ring.rs:1006) (SHA256 `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892`)

### RFA-CL028

For admitted multiplicity-free fusion rings and lawful exact field backends, validated category construction checks every admissible F block for invertibility, normalized units and every pentagon residual. Nonzero vertex coboundaries give a reusable gauge transformation; normalization and unitarity are separate replayable predicates.

Limit: Structure-only new is intentionally weaker. Resource limits exclude arbitrary callback work. Dimension consistency and FS signs rely on explicit pivotal assumptions and do not construct an independent pivotal coherence witness.

Evidence: [code/rust/core_fusion_categories/src/fusion_category.rs:54–214](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:54) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_category.rs:471–590](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:471) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_category.rs:699–940](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:699) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_category.rs:941–1047](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:941) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`)

### RFA-CL029

The fusion catalog specifies exact Ising, Fibonacci and finite pointed associator/braiding data with explicit coefficient-field requirements. Fibonacci uses an algebraic gauge rather than claiming its displayed F matrix is unitary; pointed phase orders are reduced before field admission.

Limit: Physical realization and universal classification are absent. The braided/ribbon/modular owner checks are assessed separately; capacity-only appended test does not establish the catalog mathematics.

Evidence: [code/rust/core_fusion_categories/src/catalog.rs:1–138](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/catalog.rs:1) (SHA256 `3cf82452b5eb56d1331874c8ef82075bcf4953822b6463f6d59317036953071a`); [code/rust/core_fusion_categories/src/catalog.rs:141–347](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/catalog.rs:141) (SHA256 `3cf82452b5eb56d1331874c8ef82075bcf4953822b6463f6d59317036953071a`)

### RFA-CL030

The braid layer replays defining matrix relations, reconstructs fusion-space paths against the current ring, and tracks exchanged words. Finite BFS closure on invertible generators and exact projective keys certifies the enumerated finite order upon completion; exceeding a bound establishes neither infinity nor density.

Limit: Generic lawful fields and equality/hash semantics remain premises. Structure-only braided objects need explicit validation or relation replay before representation claims; no native run.

Evidence: [code/rust/core_fusion_categories/src/braid_group.rs:64–181](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braid_group.rs:64) (SHA256 `3d112297ddb2f2991a9e6619c170e4e2973dc5e3502f81f6009f847b03e2f8d6`); [code/rust/core_fusion_categories/src/braid_group.rs:222–360](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braid_group.rs:222) (SHA256 `3d112297ddb2f2991a9e6619c170e4e2973dc5e3502f81f6009f847b03e2f8d6`); [code/rust/core_fusion_categories/src/braid_group.rs:410–456](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braid_group.rs:410) (SHA256 `3d112297ddb2f2991a9e6619c170e4e2973dc5e3502f81f6009f847b03e2f8d6`); [code/rust/core_fusion_categories/src/braided.rs:925–1009](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braided.rs:925) (SHA256 `b1d5ed963a67f39e3e3761291c6dda6c2d04c04ea897249afcd43777df676b31`); [code/rust/core_fusion_categories/src/braided.rs:1012–1239](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braided.rs:1012) (SHA256 `b1d5ed963a67f39e3e3761291c6dda6c2d04c04ea897249afcd43777df676b31`)

### RFA-CL031

Ribbon construction replays the supplied F/R/dimension/twist consistency equations; modular verified construction separately checks all declared S/T/Verlinde identities. Exact finite labels and residuals are reusable mechanisms, while positive D, coefficient fields, chosen pivotal data and verified modularity are distinct prerequisites.

Limit: F041 identifies unguarded invariant methods on unverified data. No physical host, entropy measurement or universal pivotal-coherence construction follows; positive dimensions are not generally enforced.

Evidence: [code/rust/core_fusion_categories/src/braided.rs:1242–1348](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braided.rs:1242) (SHA256 `b1d5ed963a67f39e3e3761291c6dda6c2d04c04ea897249afcd43777df676b31`); [code/rust/core_fusion_categories/src/braided.rs:1407–1471](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braided.rs:1407) (SHA256 `b1d5ed963a67f39e3e3761291c6dda6c2d04c04ea897249afcd43777df676b31`); [code/rust/core_fusion_categories/src/modular.rs:249–341](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/modular.rs:249) (SHA256 `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e`); [code/rust/core_fusion_categories/src/modular.rs:344–391](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/modular.rs:344) (SHA256 `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e`)

### RFA-CL032

The SU2 constructor is bounded to six positive levels, materializes actual algebraic-gauge q-Racah coefficients, verifies weighted association metrics, and delegates full coherence/ribbon replay. Its tests address each admitted level and a genuine F-entry mutation; displayed coordinate F matrices need not be unitary in the ordinary Euclidean metric.

Limit: No Rust test execution or arbitrary-level theorem. Canonical field embedding and classical q-number positivity remain mathematical premises; independent control checks all2957 admissible index sextuples through level6, not all coefficient values.

Evidence: [code/rust/core_fusion_categories/src/su2_level.rs:1–57](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/su2_level.rs:1) (SHA256 `a120ee244427f238f160328c38fb67dfe0296a00e23e4f8239a70b0024377236`); [code/rust/core_fusion_categories/src/su2_level.rs:60–171](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/su2_level.rs:60) (SHA256 `a120ee244427f238f160328c38fb67dfe0296a00e23e4f8239a70b0024377236`); [code/rust/core_fusion_categories/src/su2_level.rs:234–324](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/su2_level.rs:234) (SHA256 `a120ee244427f238f160328c38fb67dfe0296a00e23e4f8239a70b0024377236`); [code/rust/core_fusion_categories/src/su2_level.rs:425–515](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/su2_level.rs:425) (SHA256 `a120ee244427f238f160328c38fb67dfe0296a00e23e4f8239a70b0024377236`)

### RFA-CL033

Yang-Baxter helpers compute exact finite matrix defects on one checked tensor carrier and distinguish constant, spectral and braid forms. They include genuine parameter/entry mutations and warn correctly that commuting diagonal or uniformly rescaled-flip families are not negative controls.

Limit: One evaluated spectral triple is not a quantified family theorem; zero residual does not assert invertibility. Resource bounds exclude arbitrary supplied callback work and scalar bit complexity.

Evidence: [code/rust/core_fusion_categories/src/yang_baxter.rs:1–19](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/yang_baxter.rs:1) (SHA256 `62eecc306dcaa11247bcc9cca781b8bf1bc610e296a33ed7bcdbc64e386fe2d0`); [code/rust/core_fusion_categories/src/yang_baxter.rs:42–95](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/yang_baxter.rs:42) (SHA256 `62eecc306dcaa11247bcc9cca781b8bf1bc610e296a33ed7bcdbc64e386fe2d0`); [code/rust/core_fusion_categories/src/yang_baxter.rs:141–309](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/yang_baxter.rs:141) (SHA256 `62eecc306dcaa11247bcc9cca781b8bf1bc610e296a33ed7bcdbc64e386fe2d0`); [code/rust/core_fusion_categories/src/yang_baxter.rs:312–396](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/yang_baxter.rs:312) (SHA256 `62eecc306dcaa11247bcc9cca781b8bf1bc610e296a33ed7bcdbc64e386fe2d0`); [code/rust/core_fusion_categories/src/yang_baxter.rs:600–780](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/yang_baxter.rs:600) (SHA256 `62eecc306dcaa11247bcc9cca781b8bf1bc610e296a33ed7bcdbc64e386fe2d0`)

## Findings

### RFA-F001 — Opening totality claim contradicts rational constructor (low)

rational.rs says every routine is total and none panics on caller data, but rq(n,0) explicitly panics and a should_panic test confirms that design. checked_ratio is the data-safe alternative.

Limit: Documentation inconsistency; panic is locally documented and not a failure of checked_ratio. No Rust execution.

Evidence: [code/rust/core_number_theory/src/rational.rs:8–11](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:8) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`); [code/rust/core_number_theory/src/rational.rs:60–78](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:60) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`); [code/rust/core_number_theory/src/rational.rs:374–383](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:374) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`)

### RFA-F002 — Binary field admission accepts reducible even moduli and degree zero (medium)

is_irreducible_binary tries only divisors with constant term1 and never requires positive degree. BinaryField::new(2,4) therefore admits modulus x²: encoded2 is nonzero but its square is0. new(0,1) admits an order-one carrier. The constructor claim that every admitted modulus is irreducible is false.

Limit: Independent mask model,127 polynomials degree<=6:23 false admissions including the constant1 case. Standard first-irreducible search starts odd and valid degrees1..4 retained sound bounded arithmetic checks. No source execution.

Evidence: [code/rust/core_number_theory/src/binary_field.rs:44–61](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:44) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`); [code/rust/core_number_theory/src/binary_field.rs:85–98](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:85) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`); [code/rust/core_number_theory/src/binary_field.rs:129–140](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:129) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`); [code/rust/core_number_theory/src/binary_field.rs:349–374](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:349) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`)

### RFA-F003 — Public field elements are not admitted to their carrier (medium)

FieldElement.coeffs is public; even a searched valid GF4 accepts [] beside [1,0], with add returning [] by zip and trace_value subsequently indexing an empty sum. Longer vectors can index past product. No length, coefficient range or field identity is checked.

Limit: Malformed/publicly assembled element boundary; generated canonical elements under valid small field assumptions avoid it. Raw FiniteField::new already documents a separate irreducibility trust premise.

Evidence: [code/rust/core_number_theory/src/finite_field.rs:38–47](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:38) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`); [code/rust/core_number_theory/src/finite_field.rs:127–170](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:127) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`); [code/rust/core_number_theory/src/finite_field.rs:187–203](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:187) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`)

### RFA-F004 — Binary operations disagree on out-of-carrier masks and raw phases (medium)

For valid GF4 modulus7, mul(4,1)=0 but mul(1,4)=3; arbitrary usize arguments are neither refused nor consistently reduced. Public BinaryPauli.phase allows values>3; adjoint uses 4-phase and mul adds raw u8 values, yielding debug overflow/panic or wrapped release arithmetic instead of typed refusal.

Limit: Canonical masks0..3 and phases0..3 avoid this counterexample. This is missing admission, not a failed law on valid field elements; no Rust panic executed.

Evidence: [code/rust/core_number_theory/src/binary_field.rs:81–98](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:81) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`); [code/rust/core_number_theory/src/binary_field.rs:166–209](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:166) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`)

### RFA-F005 — Subset builder silently assumes generator count equals field degree (medium)

build_line_group documents every subset but iterates 0..field.order. For degree1 and two generators it returns only masks0,1, omitting subsets2,3; fewer generators produce repeated rows. No commutation/independence check establishes a line group.

Limit: Expected Weyl-line callers may supply exactly degree independent commuting generators; this function does not enforce that contract. Large generator counts also risk unchecked shift width.

Evidence: [code/rust/core_number_theory/src/binary_field.rs:217–230](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:217) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`); [code/rust/core_number_theory/src/binary_field.rs:388–399](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/binary_field.rs:388) (SHA256 `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9`)

### RFA-F006 — Character-sum verifier can certify a vacuous nonfield (medium)

Unchecked FiniteField::new(0,1,[]) enumerates zero elements. Both nonzero-coefficient loops are empty, so verify_character_sum_identities returns field_order0 and zero checked counts without ever testing a field or sum equation. Public counts carry no modulus/scalar binding.

Limit: Caller violated the raw constructor field premise; searched constructor excludes it. This is a missing verifier admission gate, not false acceptance for an admitted genuine finite field.

Evidence: [code/rust/core_number_theory/src/finite_field.rs:60–72](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:60) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`); [code/rust/core_number_theory/src/finite_field.rs:299–310](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/finite_field.rs:299) (SHA256 `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650`); [code/rust/core_number_theory/src/character_sums.rs:106–154](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/character_sums.rs:106) (SHA256 `3ec26b7e0b3f2ded88c7aa75e635386d989a959f2fc034f588fadae10f50963f`)

### RFA-F007 — Quadratic Gauss-norm prose omits odd characteristic (low)

The advertised norm-squared=q for every nonzero quadratic coefficient is false in characteristic2: in GF2, a1,b0 gives sum 1+(-1)=0, squared norm0, not2. The actual equality checker correctly refuses it.

Limit: Claim-scope issue only; source origin explicitly discusses odd-prime controls and does not bypass the equality check.

Evidence: [code/rust/core_number_theory/src/character_sums.rs:3–19](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/character_sums.rs:3) (SHA256 `3ec26b7e0b3f2ded88c7aa75e635386d989a959f2fc034f588fadae10f50963f`); [code/rust/core_number_theory/src/character_sums.rs:91–103](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/character_sums.rs:91) (SHA256 `3ec26b7e0b3f2ded88c7aa75e635386d989a959f2fc034f588fadae10f50963f`); [code/rust/core_number_theory/src/character_sums.rs:136–145](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/character_sums.rs:136) (SHA256 `3ec26b7e0b3f2ded88c7aa75e635386d989a959f2fc034f588fadae10f50963f`)

### RFA-F008 — Mutation-labeled tests do not call arithmetic owners (low)

integer_factorization and residue inline mutation tests only construct literal Ok(1)/Err strings and assert variant labels. Their six-killed comments therefore do not furnish evidence for primality, factorization budgets, CRT correctness or negative mathematical controls.

Limit: Explicit sibling integration test targets may supply additional evidence outside this slice; not claiming all repository tests are vacuous.

Evidence: [code/rust/core_number_theory/src/integer_factorization.rs:274–289](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/integer_factorization.rs:274) (SHA256 `b20c3c6e53044a5f215eeac01fd8e9c3eabb0eabe2f50347f63caf838162b81f`); [code/rust/core_number_theory/src/residue.rs:80–95](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/residue.rs:80) (SHA256 `ac0e61c5c4c4376901925c11b1d08d88249c687e806b8806b206518de09a7429`)

### RFA-F009 — Gaussian norm realization needs reduced rational limbs (medium)

realize_norm tests numerator and denominator separately with two_squares without reducing the rational. BigRational::new_raw(3,3) represents1, whose Gaussian norm witness is1+0i, but the numerator3 immediately returns None. In the same module norm_class cancels the two odd3 valuations and propose_obstruction returns none. The negative realization verdict is therefore representation-dependent.

Limit: Requires an unreduced but nonzero-denominator positive Ratio spelling obtainable through public upstream new_raw; normalized Rational::new avoids it. No native dependency execution. Rational root owner already explicitly handles unreduced spellings; realization has no documented reduced-only input gate.

Evidence: [code/rust/core_number_theory/src/gaussian_norm.rs:53–106](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gaussian_norm.rs:53) (SHA256 `280c87abd6d873ffcd3f2c44f0c52de7cbf334073c5e2c505571080435c7c075`); [code/rust/core_number_theory/src/gaussian_norm.rs:168–206](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gaussian_norm.rs:168) (SHA256 `280c87abd6d873ffcd3f2c44f0c52de7cbf334073c5e2c505571080435c7c075`); [code/rust/core_number_theory/src/sums_of_squares.rs:105–124](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/sums_of_squares.rs:105) (SHA256 `4ad80a76a41b852c210b7920ceb1fb65567ff11ac300357e37289ef2b79d279a`); [code/rust/core_number_theory/src/rational.rs:138–150](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:138) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`); [code/rust/core_number_theory/src/rational.rs:433–449](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/rational.rs:433) (SHA256 `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0`)

### RFA-F010 — Power-basis helper allocates before checked shape admission (medium)

invert_by_multiplication_matrix computes vec![zero;dim*dim] using unchecked usize multiplication before invoking BasicMatrix::from_row_major. At64bit dim=2^32, mathematical square is2^64: debug arithmetic panics, release multiplication wraps0 and subsequent nonempty column writes can index out of bounds. Return Option does not cover this input failure.

Limit: Direct public helper boundary. Fixed cyclotomic callers may pass tiny compile-time dimensions; no huge allocation, callback, backend or Rust execution performed.

Evidence: [code/rust/core_number_theory/src/power_basis.rs:18–44](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/power_basis.rs:18) (SHA256 `6ee507c0195830579f5d7c819e03ea1b8364c743d07e35799e1d48b9bc13276f`)

### RFA-F011 — Public refinement does not establish root record properties (medium)

RootLocation::Isolated is documented as a unique irrational root, yet refine_simple_root(2x-1,[0,1],tolerance1) returns Isolated without bisection although its unique root1/2 is rational. With an untrusted interval, x^3-x over[-2,2] and tolerance4 passes the sole sign-change gate despite three roots. refine_root also copies a public Exact(123), multiplicity0 record unchanged for x²-2.

Limit: The rational-tag example satisfies the simple/isolating interval premise. The multi-root and foreign Exact examples deliberately violate documented caller trust assumptions; isolate_real_roots performs actual Sturm isolation and lattice recognition and is not shown unsound. Root records are not standalone verified certificates.

Evidence: [code/rust/core_number_theory/src/polynomial.rs:924–962](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial.rs:924) (SHA256 `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0`); [code/rust/core_number_theory/src/polynomial.rs:972–1045](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial.rs:972) (SHA256 `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0`); [code/rust/core_number_theory/src/polynomial.rs:2180–2208](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/polynomial.rs:2180) (SHA256 `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0`)

### RFA-F012 — Cyc24 cube-root exponent overflows before reduction (medium)

Cyc24::zeta3_pow(k:i32) promises any integer exponent but evaluates 8*k before zeta24 reduces modulo24. k=536870912 gives exact residue16 and wrapped i32 residue0, yielding a different field element with overflow checks disabled; checked builds panic.

Limit: Exact fixed-width independent model, not a Rust run. Ordinary small exponents and other fixed zeta constructors that reduce first are unaffected.

Evidence: [code/rust/core_number_theory/src/cyclotomic.rs:723–726](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic.rs:723) (SHA256 `1d120eac163f026e4b24d0da609823e6254193cb6e4d197f059725834a4b8699`)

### RFA-F013 — Real embedding refinement limit is a working limit (low)

The comment says MAX_REFINEMENTS guards only corrupt state, but valid irrational root enclosures at conductor8 with requested width W/2^400000 from current widthW require the final refinement before success. The last condition check is at399992bits, then the loop returns PrecisionLimit without rechecking. Arbitrary positive rational tolerance is otherwise admitted.

Limit: Typed refusal is safe; this contradicts the claimed corruption-only scope, not soundness of returned enclosures. Exact iteration-bound control avoids expensive native execution.

Evidence: [code/rust/core_number_theory/src/real_embedding.rs:34–37](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/real_embedding.rs:34) (SHA256 `b2dbc497543e1414717f434db3201179e891aca5dac7ef27421eabedf912ceb3`); [code/rust/core_number_theory/src/real_embedding.rs:166–179](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/real_embedding.rs:166) (SHA256 `b2dbc497543e1414717f434db3201179e891aca5dac7ef27421eabedf912ceb3`); [code/rust/core_number_theory/src/real_embedding.rs:227–258](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/real_embedding.rs:227) (SHA256 `b2dbc497543e1414717f434db3201179e891aca5dac7ef27421eabedf912ceb3`)

### RFA-F014 — Public real-root record can certify a foreign point sign (medium)

At conductor8, mutate the public CyclotomicRealRoot endpoints to a=b=-1, retaining polynomial x²-2. sign_of_poly(t) takes the equal-point branch and returns-1, whereas the intended canonical root sqrt2 is positive; it never replays root membership. Polynomial, Sturm chain and conductor are independently mutable.

Limit: Normal constructor correctly isolates the intended root. This is an untrusted-record/caller mutation boundary, distinct from the private RealEmbeddings and generic standard_real_sign paths.

Evidence: [code/rust/core_number_theory/src/cyclotomic_ordered.rs:152–160](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:152) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:223–270](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:223) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:402–405](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:402) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`)

### RFA-F015 — Unchecked ordered-field vectors lose terms in addition (medium)

FieldElementFPlus publicly exposes and directly deserializes conductor/coeffs. A conductor8 raw vector[0,0,1] represents theta²=2 through as_cyclotomic, but addition of zero reads only the two canonical positions and returns zero; short vectors panic at indexing. FieldElementF likewise has public nested conductors and derived unchecked deserialization.

Limit: Normal constructors reduce to the proper dimension. Countercontrol targets admitted public/Serde representation bypasses, not arithmetic on canonical constructor output.

Evidence: [code/rust/core_number_theory/src/cyclotomic_ordered.rs:331–351](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:331) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:390–447](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:390) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:557–574](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:557) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:626–635](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:626) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`)

### RFA-F016 — Polynomial enclosure lacks nonpositive tolerance refusal (medium)

CyclotomicRealRoot::bound_poly(theta,epsilon0) at the valid conductor8 initial interval computes Lipschitz bound1 and target0, then bisects forever: sqrt2 is never a rational midpoint, so width remains positive at every finite step. Negative epsilon also cannot terminate. Unlike refine_to_width, this public method has no positive-width gate.

Limit: Analytic loop-invariant counterexample plus128bounded exact bisections; no intentionally nonterminating program executed. Constant polynomials and conductor4 return early; positive tolerance with valid root state terminates mathematically.

Evidence: [code/rust/core_number_theory/src/cyclotomic_ordered.rs:212–220](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:212) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:272–314](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:272) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`); [code/rust/core_number_theory/src/cyclotomic_ordered.rs:407–414](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/cyclotomic_ordered.rs:407) (SHA256 `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980`)

### RFA-F017 — Zero-row GF2 matrix bypasses axis bound before augmentation overflow (medium)

F2Matrix::zeros(0,usize::MAX) passes checked rows*cols<=MAX_F2_ENTRIES and allocates no words. solve(empty_vector) then evaluates self.cols+1 unchecked in build_solve_augmented, panicking in checked-overflow builds before the promised typed TooLarge refusal. Nullspace also allocates directly from the unbounded column axis.

Limit: Own fixed-word arithmetic/control-flow model; no huge allocation or native execution. With overflow checks disabled the augmented width wraps to0 and later F2Vector::zeros rejects the huge column length. Ordinary bounded axes and exact small matrix mathematics pass independent controls.

Evidence: [code/rust/core_number_theory/src/gf2.rs:5–9](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:5) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`); [code/rust/core_number_theory/src/gf2.rs:67–76](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:67) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`); [code/rust/core_number_theory/src/gf2.rs:384–393](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:384) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`); [code/rust/core_number_theory/src/gf2.rs:763–785](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:763) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`); [code/rust/core_number_theory/src/gf2.rs:811–844](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_number_theory/src/gf2.rs:811) (SHA256 `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9`)

### RFA-F018 — Generic Lie antisymmetry fails to enforce alternation in characteristic two (medium)

verify_antisymmetry checks c_ab+c_ba=0 and claims this includes[x_a,x_a]=0, but Field+ExactRing permits characteristic2. A two-dimensional GF2table with[e0,e0]=e1and all other brackets0 passes both antisymmetry and Jacobi while failing the alternating Lie axiom; the CE differential discards its diagonal bracket.

Limit: Characteristic2custom lawfulscalar model, not a claim that the existing rational sl2 examples fail. Constructors do not claim to prevalidate axioms; the named antisymmetry check itself has the mathematical gap.

Evidence: [code/rust/core_lie_theory/src/lie_algebra.rs:81–109](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:81) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`); [code/rust/core_lie_theory/src/lie_algebra.rs:153–166](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:153) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`); [code/rust/core_lie_theory/src/lie_algebra.rs:210–222](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:210) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`); [code/rust/core_lie_theory/src/lie_algebra.rs:448–469](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:448) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`)

### RFA-F019 — Structure table cube size uses unchecked multiplication (medium)

On64bitusize, dimension2^22 gives dimension³=2^66. StructureConstants::new(dimension,empty_table) panics with overflow checks or wraps expected length to0 and accepts with checks disabled; subsequent claimed valid indices have no table entries.

Limit: Symbolic fixed-word model without allocations/native execution. Finite ordinary dimensions are unaffected; from_fn has the same capacity product but is not executed at giant size.

Evidence: [code/rust/core_lie_theory/src/lie_algebra.rs:98–139](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:98) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`)

### RFA-F020 — Betti routine trusts complex premise before unsigned subtraction (medium)

For rational antisymmetric brackets[e0,e1]=e0,[e0,e2]=e2,[e1,e2]=e1, Jacobi fails and CE differential ranks are[0,3,1,0]. cohomology_betti_numbers computes degree2value3-1-3=-1 inusize, causing checked-build panic or wrapped output. It never calls the available square-to-zero predicate.

Limit: This countercontrol deliberately violates the explicitly documented Requires complex property caller premise. It shows the function is not a standalone cohomology admission/validator; valid Lie algebras are not shown to yield wrong Betti numbers.

Evidence: [code/rust/core_lie_theory/src/lie_algebra.rs:505–538](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lie_algebra.rs:505) (SHA256 `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca`)

### RFA-F021 — General rational commutant dimension does not characterize irreducibility (medium)

commutant_dimension prose says dimension1exactly for irreducible completely reducible actions. The rational2x2matrixJ=[[0,-1],[1,0]]acts irreducibly overQbut has2dimensional commutantQ[J]. ConverselyE11,E12have scalar commutantdimension1while preserving span(e0)and failing semisimplicity.

Limit: The function actually computes a kernel dimension, which is useful and not shown wrong. The specialized split characteristic0sl2irreducible representations retain the stated dimension1property. No blanket irreducibility certificate should follow for arbitrary input matrices.

Evidence: [code/rust/core_lie_theory/src/su2.rs:15–20](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2.rs:15) (SHA256 `149302c8432180bb3f11e7ddf9fe1381d76db63701a8e2d10fd4009ef3d85c7a`); [code/rust/core_lie_theory/src/su2.rs:417–435](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2.rs:417) (SHA256 `149302c8432180bb3f11e7ddf9fe1381d76db63701a8e2d10fd4009ef3d85c7a`)

### RFA-F022 — Eleven Lie module mutation tests do not exercise their owners (low)

The only inline tests in cayley_unitary,su2_matrix,su2,finite_groupoid_algebra,finite_path_algebra and twisted_abelian_algebra construct literal Result Ok/Err values and assert tags. They do not call the owned mathematical functions; adjacent mutation-census comments supply no executable owner control. The same literal-only pattern occurs in clifford,pauli_symplectic,heisenberg,su_n and lorentz.

Limit: This is limited to these inline bodies; separate integration tests or historical mutation campaigns are not disproved. Exact independent mathematical controls remain separate from native execution coverage.

Evidence: [code/rust/core_lie_theory/src/cayley_unitary.rs:117–132](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/cayley_unitary.rs:117) (SHA256 `8202a444e6d1e8e208880c0ec04622ce189feb40534f4460f7bb7cbaf587f074`); [code/rust/core_lie_theory/src/su2_matrix.rs:143–158](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2_matrix.rs:143) (SHA256 `0cbf52dd64cd75cc85b0d3c686aa56295e275dea1afdaaf76528055d85bd4ddd`); [code/rust/core_lie_theory/src/su2.rs:651–666](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su2.rs:651) (SHA256 `149302c8432180bb3f11e7ddf9fe1381d76db63701a8e2d10fd4009ef3d85c7a`); [code/rust/core_lie_theory/src/finite_groupoid_algebra.rs:245–254](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_groupoid_algebra.rs:245) (SHA256 `1c03090f37adefde8c39605aa167cd8eecdd5ba59aabaf03a61c389240a4d5c5`); [code/rust/core_lie_theory/src/finite_path_algebra.rs:236–245](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_path_algebra.rs:236) (SHA256 `64dc3c651ffeb41b7fa355f4dd21f14182ac6275aed840e640e0d11b234bad9c`); [code/rust/core_lie_theory/src/twisted_abelian_algebra.rs:226–235](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/twisted_abelian_algebra.rs:226) (SHA256 `e6fc9c62da02de42eb5e3a888c69952ebd92c5d25abb294b6bda9b3ac09b49c7`); [code/rust/core_lie_theory/src/clifford.rs:273–288](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/clifford.rs:273) (SHA256 `654f9823822fae39cf63deefe8ce5f664859c411abf4c1940809c110eff485fa`); [code/rust/core_lie_theory/src/pauli_symplectic.rs:331–346](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/pauli_symplectic.rs:331) (SHA256 `9b89d9878a665979c17cdf3c51e8c34522811fc1f48cf89d5b74367b97994e08`); [code/rust/core_lie_theory/src/heisenberg.rs:693–708](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/heisenberg.rs:693) (SHA256 `58fc3142ab285e69f9dc3747af5ec1b806eb867085843aa2df8b726c7fe005c7`); [code/rust/core_lie_theory/src/su_n.rs:449–464](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su_n.rs:449) (SHA256 `9a38043aa2cb8b44be93a1f35cb8ccd7916ae6920c901b9de71799ecd339bafa`); [code/rust/core_lie_theory/src/lorentz.rs:595–610](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lorentz.rs:595) (SHA256 `51a055a3bd057b32a6af62829894c735d0285ccfd2b17ead9d17e24629fd7015`)

### RFA-F023 — Malformed class-equation record divides by zero (medium)

ClassEquation has public fields; holds first accepts centre_order1 plus a zero-size class as summing to order1, then computes order modulo that zero size and panics.

Limit: Standalone public record is forgeable; legitimate conjugacy class sizes from admitted groups are positive. Own bounded arithmetic model, no Rust execution.

Evidence: [code/rust/core_lie_theory/src/finite_group.rs:139–156](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_group.rs:139) (SHA256 `d7ebe04efe35a4f3976016e84d3783642816cffdf9d3eb798c1db76690530a42`)

### RFA-F024 — McKay matrix silently discards extra character values (medium)

mckay_matrix multiplies f by class values with zip before calling strict multiplicity. Any suffix beyond the class count disappears. A legitimate trivial-group table with f=[1,99] therefore has the same matrix as f=[1], despite invalid input length.

Limit: Extra values alone are the counterexample; short vectors are rejected downstream. CharacterTable private construction remains intact.

Evidence: [code/rust/core_lie_theory/src/finite_group.rs:839–896](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_group.rs:839) (SHA256 `d7ebe04efe35a4f3976016e84d3783642816cffdf9d3eb798c1db76690530a42`)

### RFA-F025 — Rational cosine list does not imply rational sine (low)

Finite-order rotation cosine prose additionally says with rational sine, but returned cosines include plus/minus1/2, whose sine squared3/4 has no rational square root.

Limit: Correct Niven rational-cosine list and the separate matrix finite-order decision are not refuted.

Evidence: [code/rust/core_lie_theory/src/finite_order.rs:139–163](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/finite_order.rs:139) (SHA256 `061995d0253dceb91116996147b1e9d85b42582b2a7c2e747fda6ed5cd62f6ea`)

### RFA-F026 — Shape Lie algebra is complexified, not the stated anti-Hermitian real algebra (medium)

shape_lie_algebra claims rational anti-Hermitian shapes but passes the unscaled Hermitian Gell-Mann matrices to StructureConstants<GaussianRat>. For N2, Z*=Z and [X,Y]=2iZ. This is closure over Q(i), with no real compact anti-Hermitian basis admission.

Limit: The complex commutator structure table can be correct. This is a carrier/basis interpretation error, not a failure of the explicit Hermitian Gram or Casimir identities.

Evidence: [code/rust/core_lie_theory/src/su_n.rs:83–126](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su_n.rs:83) (SHA256 `9a38043aa2cb8b44be93a1f35cb8ccd7916ae6920c901b9de71799ecd339bafa`); [code/rust/core_lie_theory/src/su_n.rs:426–439](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/su_n.rs:426) (SHA256 `9a38043aa2cb8b44be93a1f35cb8ccd7916ae6920c901b9de71799ecd339bafa`)

### RFA-F027 — Full PGL does not equal the orthochronous Lorentz component (low)

Module prose identifies SO+(1,2;Q) with PGL(2,Q), but g=diag(-1,1) has adjoint diag(-1,1,-1), which preserves eta and determinant1 while reversing time. The positive-determinant projective subgroup is required; the actual adjoint function documentation correctly states this distinction.

Limit: The actual adjoint construction intentionally accepts both determinant signs. check_proper_orthochronous correctly rejects the time-reversing example.

Evidence: [code/rust/core_lie_theory/src/lorentz.rs:22–24](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lorentz.rs:22) (SHA256 `51a055a3bd057b32a6af62829894c735d0285ccfd2b17ead9d17e24629fd7015`); [code/rust/core_lie_theory/src/lorentz.rs:450–482](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_lie_theory/src/lorentz.rs:450) (SHA256 `51a055a3bd057b32a6af62829894c735d0285ccfd2b17ead9d17e24629fd7015`)

### RFA-F028 — Public holonomy carriers bypass shape and inverse admission (medium)

DiscreteConnection and ExactMatrix expose mutable/deserializable dimensions/data/maps. Reverse transport can change without changing forward state/hash; malformed1x1empty matrix can reach direct indexing in supposedly fallible arithmetic. CellComplex consumers other than guarded cochain_matrices also trust public index maps. Edge-indexed gauge_fixing also trusts public vertex_map indices in edge_endpoints/spanning_forest; its private connection protects values but does not reconstruct the complex.

Limit: Builder-valid objects retain their checked invariants until mutation; cochain_matrices explicitly reconstructs and rejects malformed carriers, so the finding does not apply to that guarded path.

Evidence: [code/rust/core_holonomy/src/connection.rs:40–47](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:40) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/connection.rs:112–125](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:112) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/connection.rs:218–225](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:218) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/matrix.rs:243–266](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:243) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`); [code/rust/core_holonomy/src/matrix.rs:338–370](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:338) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`); [code/rust/core_holonomy/src/laplacian.rs:66–90](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:66) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`); [code/rust/core_holonomy/src/gauge_fixing.rs:77–102](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:77) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:143–148](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:143) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`)

### RFA-F029 — Content hashes use noninjective endpoint encodings (medium)

Valid endpoint pairs(a->b,c)and(a,b->c)serialize to the same edge text a->b->c. With identical matrix values, connection digests coincide; graph digests also coincide when both use the same four-vertex set and their distinct single edge.

Limit: This is an encoding collision, not a cryptographic SHA256collision. It uses only valid builder identifiers and does not require public-field forgery.

Evidence: [code/rust/core_holonomy/src/connection.rs:218–225](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:218) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/graph.rs:233–264](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/graph.rs:233) (SHA256 `ec8ae5aba841586cd21971277fda279a3d973ce20c4d8a123c0f3ef3e48eab3e`); [code/rust/core_holonomy/src/graph.rs:69–114](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/graph.rs:69) (SHA256 `ec8ae5aba841586cd21971277fda279a3d973ce20c4d8a123c0f3ef3e48eab3e`)

### RFA-F030 — Self-loop admission breaks pair-keyed inversion semantics (medium)

set_connection(u,u,[2]) stores forward2 and reverse1/2 under the same key; get_step(u,u)always selects2. Thus the stated U(v,u)=U(u,v)^-1 law fails for an admitted loop. Graph permits loops, counts them once despite incoming+outgoing degree wording, and Laplacian skips them entirely. The newer EdgeConnection.step uses an explicit direction and correctly distinguishes selfloop inverse. Its conversion back to the pair-keyed API still exempts selfloops from refusal.

Limit: The completely reviewed edge-indexed gauge-fixing API handles explicit self-loop orientation correctly; its conversion back to the pair-keyed API still admits the ambiguous loop. This finding is confined to the vertex-pair semantics and its conversion boundary.

Evidence: [code/rust/core_holonomy/src/connection.rs:60–108](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:60) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/connection.rs:112–125](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:112) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/graph.rs:86–114](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/graph.rs:86) (SHA256 `ec8ae5aba841586cd21971277fda279a3d973ce20c4d8a123c0f3ef3e48eab3e`); [code/rust/core_holonomy/src/graph.rs:180–192](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/graph.rs:180) (SHA256 `ec8ae5aba841586cd21971277fda279a3d973ce20c4d8a123c0f3ef3e48eab3e`); [code/rust/core_holonomy/src/laplacian.rs:70–84](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:70) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`); [code/rust/core_holonomy/src/gauge_fixing.rs:351–360](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:351) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:678–693](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:678) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`)

### RFA-F031 — Laplacian construction does not establish its PSD or graph contract (medium)

compute accepts arbitrary invertible transport and arbitrary signed weights. U=2 yields[[1,-2],[-1/2,1]], which is not Hermitian; identity transport with weight-1 yields a negative quadratic form. It also builds nonzero blocks for connection edges absent from CellComplex, invalidating the unconditional trace2d|E|statement.

Limit: The newer gauge_fixing::EdgeConnection::connection_laplacian explicitly computes D*WD and states positivity conditional on positive real weights and conjugation-compatible scalar laws; that stronger mechanism is not refuted. Legacy constructor conditions remain unenforced.

Evidence: [code/rust/core_holonomy/src/laplacian.rs:41–99](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:41) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`); [code/rust/core_holonomy/src/laplacian.rs:102–145](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:102) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`)

### RFA-F032 — Laplacian block orientation conflicts with connection gauge action (high)

Connection transports map u to v and transform g(v)U(u,v)g(u)^-1, but Laplacian block(u,v)stores-U(u,v)instead of reverse transport. Starting from identity edge and rational orthogonal gauges g(a)=I,g(b)=J=[[0,-1],[1,0]], the constructed transformedL differs from G L G^-1 and sends the transported parallel section(1,0,0,1)to(2,0,0,2).

Limit: Valid unitary rational2x2countermodel with positiveunitweight and one edge. Separate gauge_fixing.rs517–627 uses correctly oriented incidence and D*WD and passes the independentcontrol; finding is specific to legacy laplacian.rs.

Evidence: [code/rust/core_holonomy/src/connection.rs:185–215](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:185) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/holonomy.rs:66–88](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/holonomy.rs:66) (SHA256 `90f5b1438a5ca6dab1819c20a79c8ea0376dd75bcb601a641e7c5539fa9c10c2`); [code/rust/core_holonomy/src/laplacian.rs:70–84](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:70) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`); [code/rust/core_holonomy/src/laplacian.rs:116–128](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:116) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`)

### RFA-F033 — Perturbation bound trusts nonnegative weights without checking them (medium)

A four-cycle with alternating weights+1,-1has all weighted diagonal degrees0and a nonzero Hermitian Laplacian. Its certificate reports operator_norm_bound0for epsilon2. Changing every unittransportI to-I gives nonzero Hermitian delta with absolute row sum4, contradicting that numerical bound.

Limit: The control violates the documented nonnegative-weight convention, which compute/certificate do not enforce. For admitted nonnegativeweights and Hermitian perturbations, the written Weyl-Gershgorin bound is appropriate. The unperturbed gap is supplied, not independently measured.

Evidence: [code/rust/core_holonomy/src/laplacian.rs:196–217](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:196) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`); [code/rust/core_holonomy/src/laplacian.rs:220–290](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:220) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`)

### RFA-F034 — Face flatness and arbitrary loop products do not certify pure gauge or homology pairing (medium)

is_flat returns true on every face-free graph regardless of cycle holonomy. A two-cycle graph with noncommuting unipotent transports has a commutator loop with zero H1class but nonidentity transport; cycle_homology_pairing returns that raw matrix despite its H1pairing label.

Limit: Localfaceflatness is valid narrowerpredicate. Newer gauge_fixing::holonomy_verdict explicitly distinguishes FlatNontrivial from GaugeTrivial and computes fundamentalgeneratorresiduals. The qualified Bianchi function is not refuted.

Evidence: [code/rust/core_holonomy/src/holonomy.rs:127–152](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/holonomy.rs:127) (SHA256 `90f5b1438a5ca6dab1819c20a79c8ea0376dd75bcb601a641e7c5539fa9c10c2`)

### RFA-F035 — Nested built-in Gaussian scalar is not a field and rank hides inversion refusal (medium)

GaussianRational<T> implements ExactScalar for every ExactScalar T, including GaussianRational<BigRational>. The nonzero outerelement(inner i,inner1)has norm i²+1=0and refuses inversion; rank of its1x1matrix silently returns0because exact_inv errors are discarded.

Limit: Ordinary QandQ(i)overQare unaffected. Nested built-in instantiation shows the trait bound is insufficient for advertised field elimination; a domain restriction or propagated error is needed.

Evidence: [code/rust/core_holonomy/src/matrix.rs:94–115](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:94) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`); [code/rust/core_holonomy/src/matrix.rs:215–240](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:215) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`); [code/rust/core_holonomy/src/matrix.rs:665–688](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:665) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`)

### RFA-F036 — Several operation-limit parameters are not enforced on the mathematical work (medium)

curvature_commutator names its limits argument _limits and uses unbounded matmul. Path holonomy uses try_identity/matmul without max_dimension or contraction limits; matmul_with_limits itself checks only result rows/columns, admitting arbitrarily wide inner dimension under a small dimension limit. Indexed incidence and D*WD have genuine work checks, but flat_cyclic_gauge_classes allocates faces*z without checked multiplication or its own operation cap; trivial connection allocates identities before dimension admission.

Limit: Checked integer products and allocation failure handling remain useful. This is a declared budget boundary gap, not evidence that ordinary small calculations are wrong.

Evidence: [code/rust/core_holonomy/src/curvature.rs:14–33](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/curvature.rs:14) (SHA256 `073913b9789a90bbe8e40ebfb4529f050c49abaee23eea6282b27b4b4818fa22`); [code/rust/core_holonomy/src/holonomy.rs:72–88](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/holonomy.rs:72) (SHA256 `90f5b1438a5ca6dab1819c20a79c8ea0376dd75bcb601a641e7c5539fa9c10c2`); [code/rust/core_holonomy/src/matrix.rs:382–397](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:382) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`); [code/rust/core_holonomy/src/gauge_fixing.rs:272–277](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:272) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/gauge_fixing.rs:1178–1185](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:1178) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`)

### RFA-F037 — Capacity-wrapper tests are not mathematical owner tests (low)

The appended count/capacity BoundaryRecord tests in connection,curvature,holonomy,laplacian and matrix exercise only unrelated integer admission inequalities. Their mutation-accounting labels do not provide controls for inversion,curvature,holonomy,Laplacian or elimination. Gauge_fixing likewise has only capacity-wrapper inline tests; signed_transport and gauge_quotient append literal Ok/Err tag tests despite their substantive runtime checks. Modular.rs also appends only literal Ok/Err tests; catalog appends only a count/capacity test. These do not establish modular identities or catalog realization.

Limit: These wrapper tests are meaningful for the wrappers themselves. Separate integrations/historical campaigns were not run; graph cochain and functional-orbit inline tests are substantive and are distinguished.

Evidence: [code/rust/core_holonomy/src/connection.rs:323–348](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/connection.rs:323) (SHA256 `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05`); [code/rust/core_holonomy/src/curvature.rs:222–247](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/curvature.rs:222) (SHA256 `073913b9789a90bbe8e40ebfb4529f050c49abaee23eea6282b27b4b4818fa22`); [code/rust/core_holonomy/src/holonomy.rs:268–293](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/holonomy.rs:268) (SHA256 `90f5b1438a5ca6dab1819c20a79c8ea0376dd75bcb601a641e7c5539fa9c10c2`); [code/rust/core_holonomy/src/laplacian.rs:400–425](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/laplacian.rs:400) (SHA256 `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48`); [code/rust/core_holonomy/src/matrix.rs:820–845](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/matrix.rs:820) (SHA256 `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df`); [code/rust/core_holonomy/src/gauge_fixing.rs:1395–1426](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_fixing.rs:1395) (SHA256 `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f`); [code/rust/core_holonomy/src/signed_transport.rs:362–377](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/signed_transport.rs:362) (SHA256 `e4f053f601d75fd0074697ca1e0e60fc7a76f5d4859b827627ae3bdebfc02bbb`); [code/rust/core_holonomy/src/gauge_quotient.rs:728–739](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_holonomy/src/gauge_quotient.rs:728) (SHA256 `fc79543b48941c3d4f4cc897df0b524f5fb4f6444707b38011b329401dd73308`); [code/rust/core_fusion_categories/src/modular.rs:505–520](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/modular.rs:505) (SHA256 `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e`); [code/rust/core_fusion_categories/src/catalog.rs:389–414](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/catalog.rs:389) (SHA256 `3cf82452b5eb56d1331874c8ef82075bcf4953822b6463f6d59317036953071a`)

### RFA-F038 — Root-of-unity helper falsely reports field insufficiency for large exponents (low)

FusionScalar::root_of_unity multiplies k by w/n with checked i64 multiplication before reducing modulo w. For GaussianRat,w4,n1,k=i64MAX, it returns None and the public wrapper reports FieldTooSmall although the requested first root is exactly1.

Limit: Safe refusal rather than false acceptance/panic. Reducing k modulo n before multiplication avoids the spurious refusal; ordinary small exponents and genuine field exclusions are unaffected.

Evidence: [code/rust/core_fusion_categories/src/scalar.rs:63–80](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/scalar.rs:63) (SHA256 `296a92e345edd7dd300c0d2c95c799c826dcaeff91741428c012da887b0d95f3`); [code/rust/core_fusion_categories/src/scalar.rs:93–98](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/scalar.rs:93) (SHA256 `296a92e345edd7dd300c0d2c95c799c826dcaeff91741428c012da887b0d95f3`)

### RFA-F039 — Galois wording conflates changed pivotal signs with fixed associator data (medium)

The dimension prose says the same F data admit Galois-conjugate dimension vectors, and the Z2 test calls rational signs +1 and -1 Galois conjugate. Field automorphisms fix rational1. For the catalog Fibonacci F00=phi^-1, conjugating d=phi to (1-sqrt5)/2 while keeping F fixed gives d²F00²=(7-3sqrt5)/2, not1; true Galois conjugation also changes F. The checker correctly rejects this inconsistent combination.

Limit: Documentation/mathematical characterization defect, not false acceptance by dimension consistency checks. Alternate pivotal characters can produce rational sign changes, but are not Galois automorphisms.

Evidence: [code/rust/core_fusion_categories/src/fusion_category.rs:1049–1087](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:1049) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_category.rs:1351–1355](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:1351) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/catalog.rs:94–101](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/catalog.rs:94) (SHA256 `3cf82452b5eb56d1331874c8ef82075bcf4953822b6463f6d59317036953071a`)

### RFA-F040 — RepS3 example does not test the multiplicity-free admission boundary (low)

The test described as a multiplicity obstruction uses RepS3, whose std tensor std is 1+sgn+std and has no coefficient above1. FSymbols::trivial rejects it because it is not pointed, so this test cannot demonstrate rejection of a genuine multiplicity2 fusion rule. The actual coefficient gate exists and is separate.

Limit: Test adequacy/label issue only. Independent RepA4 table gives a genuine multiplicity2 positive ring for a future gate control; no retained Rust tests executed.

Evidence: [code/rust/core_fusion_categories/src/fusion_category.rs:339–347](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:339) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_category.rs:433–444](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:433) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_category.rs:1295–1300](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_category.rs:1295) (SHA256 `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff`); [code/rust/core_fusion_categories/src/fusion_ring.rs:954–979](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/fusion_ring.rs:954) (SHA256 `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892`)

### RFA-F041 — Unverified modular data can return the wrong Frobenius-Schur indicator (medium)

ModularData::from_ribbon permits degenerate ribbon categories and does not verify modularity. Its frobenius_schur_indicator method nevertheless uses the modular Bantay formula and accepts any result in {-1,0,1} without invoking verify or checking duality. For symmetric pointed Vec(C3), F=R=1 and dimensions1 pass the ribbon equations; S is all ones and singular, yet the method returns1 for both nonselfdual simple labels, whose second indicator is0. The separate verified constructor correctly refuses the singular S.

Limit: Admission/API boundary defect rather than a counterexample on verified modular input. from_ribbon openly documents its weaker status, but the invariant method does not enforce its additional prerequisite. Ground-state and central-charge labels likewise need the modular interpretation premise; no physical observation is established.

Evidence: [code/rust/core_fusion_categories/src/modular.rs:79–102](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/modular.rs:79) (SHA256 `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e`); [code/rust/core_fusion_categories/src/modular.rs:249–294](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/modular.rs:249) (SHA256 `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e`); [code/rust/core_fusion_categories/src/modular.rs:393–447](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/modular.rs:393) (SHA256 `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e`); [code/rust/core_fusion_categories/src/braided.rs:1331–1348](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_fusion_categories/src/braided.rs:1331) (SHA256 `b1d5ed963a67f39e3e3761291c6dda6c2d04c04ea897249afcd43777df676b31`)

## Independent controls

These are exact, bounded audit models; they are not execution of the retained implementation. Each receipt is pinned to its own helper and source ranges. No expensive failure case, unbounded allocation or nonterminating loop was executed.

- **RFA-C001** — scalar_finite_field_factorization_and_crt_independent_controls; status `completed_bounded_with_counterexamples`. Pure Python exact models and independent elementary oracles only; no original Rust imports/execution. All nine receipt checks have explicit rule/status fields. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe01.py` SHA256 `61b60b8dd869d6a2c092e66ff798ceefc9d9df755f5807e17953f7a894be7943`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe01.json` SHA256 `180f21c16274809d5c354c482c333a88ec8211d08bbe806ad46fe3776b657cb1`.
- **RFA-C002** — norm_circle_prefix_and_enclosure_independent_controls; status `completed_bounded_with_counterexample`. Eight exact finite checks; pure Python3.14 rational/integer models only, no original/native execution. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe02.py` SHA256 `b2035b9a4d06886ab661366e2eb46aba74830dd9ea426e21526507d798421b43`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe02.json` SHA256 `5a3d8a6f449ccf0b2c7f444a9158a7fc29177d15a9aba9ec2577374cce0eadce`.
- **RFA-C003** — formal_series_and_shape_independent_controls; status `completed_bounded_with_counterexample`. Four exact independent controls. No original code/native execution. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe03.py` SHA256 `3eed78a028ef7f3e5a4bbe85ccf421abf620aa382f9af852bf89deba03762fff`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe03.json` SHA256 `390924a9c51f6b7da54878d360d9181f4674e5df175312a3bf63c952fc36785a`.
- **RFA-C004** — quadratic_roots_norms_and_sign_independent_controls; status `completed_bounded`. Pure Python rational pairs and independent rational sqrt brackets; no original Rust execution, no compile-fail validation. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe04.py` SHA256 `fcbf756ee94fe82d4a4d3f6ecb638693e564b52f5df5e210a647260eec777603`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe04.json` SHA256 `cf48ad7f3096acce135b5ae8a438d949cf926b7635143f28c8211690080c1244`.
- **RFA-C005** — polynomial_sturm_and_root_boundary_independent_controls; status `completed_bounded_with_counterexample`. Exact Python elementary polynomial models/permutation determinant; no original/native execution. Product-only factor verification countercontrol confirms an explicitly documented limitation. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe05.py` SHA256 `0c80ef97577d654d1ef4f4436462908384765bd294483e698d55572a92e280ba`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe05.json` SHA256 `7aa0a9f9088378a527639e39a6be86f02f74c1c3341eb777a8ac95398d964656`.
- **RFA-C006** — fixed_cyclotomic_exact_models; status `completed_bounded_with_counterexample`. Own exact stdlib Python quotient arithmetic; no original or native execution. Source-specific fields and exponent defect are pinned; analytic positivity not tested. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe06.py` SHA256 `17433e752611d1ee5aba5bb6313166e8c9eb4f05449685f68133789ad723c986`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe06.json` SHA256 `8f4e24b0f20d7c6e2079b9213e1416141e0af3cc9414a482fb7efca69e3eda2d`.
- **RFA-C007** — field_inclusion_and_ordered_admission_controls; status `completed_bounded_with_counterexamples`. Own stdlib exact arithmetic and symbolic loop invariants; no original execution. Public-field counterexamples deliberately bypass constructor normalization. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe07.py` SHA256 `f6ff6818b5c0bfd1a93d3ff66690bd6744804d3f0717230b8858ebca0ee519e0`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe07.json` SHA256 `a0b5795f77f1f9f799d76b9e4a7c985dbfdd1cf2433f045c79a578a02cf3e11b`.
- **RFA-C008** — gf2_and_vanishing_sum_independent_controls; status `completed_bounded_with_counterexample`. Own stdlib finite mathematical models, no retained/native execution. Invalid giant-axis example evaluated symbolically only. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe08.py` SHA256 `e2fdbddd7ebbd3e91a4e57895ee61c553d32a7be41321300a07e2b03b3970230`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe08.json` SHA256 `a4bfa19c18e6645b44cb67eefd2cebe95a7febe82c56c61749e2238eab629d22`.
- **RFA-C009** — lie_and_cayley_exact_independent_controls; status `completed_bounded_with_counterexamples`. Own exact rational matrices/exterior formulas and characteristic2model; no Rust/native execution. Explicitly invalid-complex control is a caller-premise boundary. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe09.py` SHA256 `ce270351cbcd7597d7a8d42f480f9c8d585f57baa25f5e73585b4ed809b12b8d`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe09.json` SHA256 `f6f62bb6aaba193733e157a70bf79dce1741096e9bb03c0c35bc72652fef62bc`.
- **RFA-C010** — group_and_cocycle_independent_controls; status `completed_bounded_with_counterexamples`. Own arithmetic and all512 normalized sign arrays on C2 squared; connected8-arrow groupoid example. No native/original execution or general runtime certification. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe10.py` SHA256 `7b235a7f0d5a00d6796546c1b62d21e662a450364927cbbe8aa69bdedf3d6174`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe10.json` SHA256 `046bea9fe9caf6c179c2e88cb6fa5a0cdfffd5232941ed51436e466ba140a290`.
- **RFA-C011** — weyl_symplectic_characteristic_and_real_form_controls; status `completed_bounded_with_counterexamples`. Own exact exponent/bit/integer models only, dimensions2..5,allbinary2x2/4x4matrices and five small primeCCRcases; no retained native execution. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe11.py` SHA256 `53838b2993ce0774b596786dff99615e251a6950f4dccaf48c4f008cec306e70`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe11.json` SHA256 `353f7f55165372b4392d423def2aa60c3404740b74c5c4fa3be72091a61ec3d8`.
- **RFA-C012** — holonomy_carrier_hash_gauge_and_finite_orbit_controls; status `completed_bounded_with_counterexamples`. Own exact finite matrices/phasefree rational countermodels and byte encodings; no Rust/native/original execution. Signed-weight and nested-scalar controls explicitly expose missing admission premises. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe12.py` SHA256 `9ccdd0fdd166de07ae34df42542cfbf573cde7d1f0c9acc34b19ad6bca2905ed`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe12.json` SHA256 `0ac7ebaf65a2c338fc3f577fed7459ac4371ce6f6458bfe94c113228269d4cb9`.
- **RFA-C013** — complete_signed_graph_quotient_and_indexed_incidence_controls; status `completed_bounded`. All729fourvertexsignedgraphs,125rationalrepresentatives625shifts,1000one-relationcycliccounts and validindexedLaplacianexample; independent finite models, no Rust/native execution. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe13.py` SHA256 `f4312aae011081ef73bb0fc8982b68200673d6a326c48ab8fd3a36bdc2c0f01b`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe13.json` SHA256 `0be98fd05b7d6e0c3caf4503000707780628479eeaa7bff02e48bd28aa306fbf`.
- **RFA-C014** — fusion_ring_exhaustive_small_tables_and_exponent_boundary; status `completed_bounded_with_counterexample`. Own512shape/unit/commutative rank3binarytables,SU2levels1..6,64Isingcounts and exacti64overflowmodel; no category realization or native execution. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe14.py` SHA256 `a8ccfbdbc942d3ecfd7ba0d289c1aa29ab7f49aa8600f3ac53c672c6e33c02d9`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe14.json` SHA256 `31d4b556b77acff3252fdb8289cb4e55f7c5bfbc8cd37ba3601fe7467c52505d`.
- **RFA-C015** — finite_cocycle_gauge_dimension_and_multiplicity_controls; status `completed_bounded_with_counterexample`. Own seven Z2 associator scalars,162 nonzero gauge coboundaries, exact Fibonacci field arithmetic and one valid rank4 multiplicity2 table; no native execution. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe15.py` SHA256 `1fc4d19beff985c0032de033013e11f3ce5e97f7be55e176d27c3f13754924c1`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe15.json` SHA256 `7bd9e71783638d7885a6b37261ad44afc37ce5c21e4926e9a2a211efd7aa3940`.
- **RFA-C016** — closure_modular_Yang_Baxter_and_Racah_index_controls; status `completed_bounded_with_counterexample`. Own exact D12/projectiveD6 closure; all16 C2²bicharacters (8modular); VecC3 indicator counterexample;8Yang,8wrong-parameter,4Hecke,8six-vertex controls;2957 Racah index sextuples. No original/native execution or universal family claim. Helper `dag/reviews/additional_rust_finite_algebra_remaining_probe16.py` SHA256 `d1259beb8d42a86c146313d0799c16b25411f420996bb826f5c0143baf8d75a0`; receipt `dag/reviews/additional_rust_finite_algebra_remaining_probe16.json` SHA256 `66caacfeceb7e70361a2ed5fac537d6afb6e947b2d363a278bf9ef6216711c12`.

## Complete source accounting

Every row below is a direct full body read. The JSON includes substantive chunk assessments for each exact range; no census or parsing pass is promoted to reading credit.

| Path | Lines read | SHA256 |
|---|---:|---|
| code/rust/core_fusion_categories/Cargo.toml | 1–33 | `7308f0d628e1ac3d1fc6e939a48dd7db64b903dfb61a728677d46711040c146b` |
| code/rust/core_fusion_categories/src/braid_group.rs | 1–400, 401–778 | `3d112297ddb2f2991a9e6619c170e4e2973dc5e3502f81f6009f847b03e2f8d6` |
| code/rust/core_fusion_categories/src/braided.rs | 1–415, 416–840, 841–1245, 1246–1637 | `b1d5ed963a67f39e3e3761291c6dda6c2d04c04ea897249afcd43777df676b31` |
| code/rust/core_fusion_categories/src/catalog.rs | 1–414 | `3cf82452b5eb56d1331874c8ef82075bcf4953822b6463f6d59317036953071a` |
| code/rust/core_fusion_categories/src/error.rs | 1–279 | `3fcd3f52db954356f30bf2e56108332359eb8d467c362411f010fadf5b932b87` |
| code/rust/core_fusion_categories/src/fusion_category.rs | 1–470, 471–940, 941–1373 | `210428cf218c07beb25f108707011b41be0f656a9d02f62e4aede9259d5276ff` |
| code/rust/core_fusion_categories/src/fusion_ring.rs | 1–440, 441–880, 881–1326 | `54fa08118afef629c141f2a3cc2c7534d04db77abf673c5bb8ef2535219d1892` |
| code/rust/core_fusion_categories/src/lib.rs | 1–84 | `ca842af5a529d8d0f4be92afb26b4278c540dc3ef0a322bd4367920e147b5436` |
| code/rust/core_fusion_categories/src/modular.rs | 1–520 | `9d9a3a9046fa3b413ec220a356af603c1585bfea0a68ec0e7b80c3467bd7ed2e` |
| code/rust/core_fusion_categories/src/scalar.rs | 1–558 | `296a92e345edd7dd300c0d2c95c799c826dcaeff91741428c012da887b0d95f3` |
| code/rust/core_fusion_categories/src/su2_level.rs | 1–543 | `a120ee244427f238f160328c38fb67dfe0296a00e23e4f8239a70b0024377236` |
| code/rust/core_fusion_categories/src/yang_baxter.rs | 1–420, 421–809 | `62eecc306dcaa11247bcc9cca781b8bf1bc610e296a33ed7bcdbc64e386fe2d0` |
| code/rust/core_holonomy/Cargo.toml | 1–59 | `b03153ba0b7ac0418fb1ee5bf44860f83b0c39c131e5eb8bedc641a52a7e2fb6` |
| code/rust/core_holonomy/src/connection.rs | 1–348 | `12a7f27be85ea84ad41a892507959d04a3afbe14f1ecf6ff8c637c71a9bbbe05` |
| code/rust/core_holonomy/src/curvature.rs | 1–247 | `073913b9789a90bbe8e40ebfb4529f050c49abaee23eea6282b27b4b4818fa22` |
| code/rust/core_holonomy/src/error.rs | 1–341 | `c27abe7b6aee4659b036a12b51e84adc18d567a796220769961c7b53c2e8ffe2` |
| code/rust/core_holonomy/src/functional_graph.rs | 1–119 | `2d3d26191b1b72acb17fb2d8b68724192c6334883f6a1d132162ab6251ebd2c4` |
| code/rust/core_holonomy/src/gauge_fixing.rs | 1–480, 481–960, 961–1426 | `7bc7b2dd5af2da7279919e8cf5fecad5fd765f533c47ce64779fa9af6a5b8f7f` |
| code/rust/core_holonomy/src/gauge_quotient.rs | 1–400, 401–739 | `fc79543b48941c3d4f4cc897df0b524f5fb4f6444707b38011b329401dd73308` |
| code/rust/core_holonomy/src/graph.rs | 1–566 | `ec8ae5aba841586cd21971277fda279a3d973ce20c4d8a123c0f3ef3e48eab3e` |
| code/rust/core_holonomy/src/holonomy.rs | 1–293 | `90f5b1438a5ca6dab1819c20a79c8ea0376dd75bcb601a641e7c5539fa9c10c2` |
| code/rust/core_holonomy/src/laplacian.rs | 1–425 | `d999d9737fb2c589138f2f7b6abc0904b0a5d9f087ba2065d5b70078edf8ce48` |
| code/rust/core_holonomy/src/lib.rs | 1–228 | `6152e9e98e16bf21d06a8f107ba3275b0581594a925270e445d52c6fd45da606` |
| code/rust/core_holonomy/src/matrix.rs | 1–440, 441–845 | `b190e9b65a14fdf29afff84e20e97b42b18afcd6e55b4fd0dbc8549350a431df` |
| code/rust/core_holonomy/src/signed_transport.rs | 1–377 | `e4f053f601d75fd0074697ca1e0e60fc7a76f5d4859b827627ae3bdebfc02bbb` |
| code/rust/core_lie_theory/Cargo.toml | 1–90 | `d7634c5d8f51b0941304bb6228ef1a8f3be4bb9e4b6e291df14daddde3de4f0b` |
| code/rust/core_lie_theory/src/cayley.rs | 1–339 | `1d4e7dd29becef243b69b4c535b29c6c0136df9225d5c82ae3ecb37c7fd0785a` |
| code/rust/core_lie_theory/src/cayley_unitary.rs | 1–132 | `8202a444e6d1e8e208880c0ec04622ce189feb40534f4460f7bb7cbaf587f074` |
| code/rust/core_lie_theory/src/clifford.rs | 1–288 | `654f9823822fae39cf63deefe8ce5f664859c411abf4c1940809c110eff485fa` |
| code/rust/core_lie_theory/src/finite_group.rs | 1–500, 501–1000, 1001–1493 | `d7ebe04efe35a4f3976016e84d3783642816cffdf9d3eb798c1db76690530a42` |
| code/rust/core_lie_theory/src/finite_groupoid_algebra.rs | 1–254 | `1c03090f37adefde8c39605aa167cd8eecdd5ba59aabaf03a61c389240a4d5c5` |
| code/rust/core_lie_theory/src/finite_order.rs | 1–365 | `061995d0253dceb91116996147b1e9d85b42582b2a7c2e747fda6ed5cd62f6ea` |
| code/rust/core_lie_theory/src/finite_path_algebra.rs | 1–245 | `64dc3c651ffeb41b7fa355f4dd21f14182ac6275aed840e640e0d11b234bad9c` |
| code/rust/core_lie_theory/src/heisenberg.rs | 1–380, 381–708 | `58fc3142ab285e69f9dc3747af5ec1b806eb867085843aa2df8b726c7fe005c7` |
| code/rust/core_lie_theory/src/lib.rs | 1–171 | `14b8fc146b655cbd20a71aabfde2e7f1b0d5e4fb9f0fa46891c6351d0277f615` |
| code/rust/core_lie_theory/src/lie_algebra.rs | 1–350, 351–590 | `afd50fc1f2328e9a9693426f6abfcae7c82f3df76d4e6359e7687ae0f79aa0ca` |
| code/rust/core_lie_theory/src/lorentz.rs | 1–610 | `51a055a3bd057b32a6af62829894c735d0285ccfd2b17ead9d17e24629fd7015` |
| code/rust/core_lie_theory/src/pauli_symplectic.rs | 1–346 | `9b89d9878a665979c17cdf3c51e8c34522811fc1f48cf89d5b74367b97994e08` |
| code/rust/core_lie_theory/src/rotation.rs | 1–358 | `5c2245c7c9d39f6a68cb5a6c72cba64e7f63c9df155d9cac4fcd83c1b58a3238` |
| code/rust/core_lie_theory/src/scalar.rs | 1–447 | `bc70a719edd18919293dbd98d5fc3a188f567f9977da1582ea5a158c5a81809a` |
| code/rust/core_lie_theory/src/su2.rs | 1–380, 381–666 | `149302c8432180bb3f11e7ddf9fe1381d76db63701a8e2d10fd4009ef3d85c7a` |
| code/rust/core_lie_theory/src/su2_matrix.rs | 1–158 | `0cbf52dd64cd75cc85b0d3c686aa56295e275dea1afdaaf76528055d85bd4ddd` |
| code/rust/core_lie_theory/src/su_n.rs | 1–464 | `9a38043aa2cb8b44be93a1f35cb8ccd7916ae6920c901b9de71799ecd339bafa` |
| code/rust/core_lie_theory/src/twisted_abelian_algebra.rs | 1–235 | `e6fc9c62da02de42eb5e3a888c69952ebd92c5d25abb294b6bda9b3ac09b49c7` |
| code/rust/core_lie_theory/src/weyl_operators.rs | 1–286 | `cbf76c832bea33ee7773245f2c19354ba4569dfacc3141d12068b83b2e862a0b` |
| code/rust/core_number_theory/Cargo.toml | 1–76 | `4ac25eaf4541944f979ccf2b644ea06c8a054ace8599730da04911f05df5059a` |
| code/rust/core_number_theory/src/algebraic_real.rs | 1–515 | `8b16f01f83d53cf85a6bd3743ea65d03045ddafd98ef0a42efdcfc9752c872f1` |
| code/rust/core_number_theory/src/binary_field.rs | 1–427 | `7549563d8b3af98d07ee7edffa4c80c7c688fb03a343e976fc96763d60ee14b9` |
| code/rust/core_number_theory/src/certified_angles.rs | 1–178 | `a0fcb9fc43501ff03437f5300887c345b5a562ffc6b37efcb5a6cf1bbd6d2b5f` |
| code/rust/core_number_theory/src/character_sums.rs | 1–273 | `3ec26b7e0b3f2ded88c7aa75e635386d989a959f2fc034f588fadae10f50963f` |
| code/rust/core_number_theory/src/circle_haar.rs | 1–251 | `141b0a3eebc2cf2f809a154c5746f08cd5d53d61861fdb97a95c46b22e647ce1` |
| code/rust/core_number_theory/src/cyclotomic.rs | 1–450, 451–900, 901–1215 | `1d120eac163f026e4b24d0da609823e6254193cb6e4d197f059725834a4b8699` |
| code/rust/core_number_theory/src/cyclotomic120.rs | 1–361 | `d09b420e11f4473ad1cb43728b0eeb1579713d93f72ea0b54fd24eab513cc1a6` |
| code/rust/core_number_theory/src/cyclotomic28.rs | 1–350 | `6b81a9c8bf01ceda0d43324029424d10ff3722ea7679e493679fddcfa428749e` |
| code/rust/core_number_theory/src/cyclotomic44.rs | 1–355 | `f82eb3be0d3f82adef58b88bc8ac93ac422365ea96b680a08728810fb1d800e3` |
| code/rust/core_number_theory/src/cyclotomic52.rs | 1–349 | `4ce4933e0bb9d24fab1a3d8b8b37af541d3694e5fbb1bc2fe84bc5ca984abb6e` |
| code/rust/core_number_theory/src/cyclotomic_field.rs | 1–480, 481–980, 981–1480, 1481–1980, 1981–2424 | `ab6d4eb5163ac7bb10b8d0b35ae5b6b295d3f7eaa01394f95a351cb62ce43183` |
| code/rust/core_number_theory/src/cyclotomic_integer.rs | 1–485 | `38cf0656fff0f4357773f2f8265907ff52e79a121ff36169d4105753f4b9df6d` |
| code/rust/core_number_theory/src/cyclotomic_ordered.rs | 1–480, 481–958 | `cca88bfde59478caa76b6e5492e597d7f070685640713585b08762244e757980` |
| code/rust/core_number_theory/src/dyadic_presentation.rs | 1–236 | `510c44b8c2ce8525d5c4bd5394836b3e0249dc755833279fea6a830029e9d654` |
| code/rust/core_number_theory/src/finite_field.rs | 1–459 | `23eceeeeb33157f531554990d8b19c5e455968bc7ec3e171970c8745fde7b650` |
| code/rust/core_number_theory/src/four_squares.rs | 1–166 | `886f8903ab2a97cc8a3f630168473e69512827ed86304f2f571c3906ea10b3a1` |
| code/rust/core_number_theory/src/gaussian_norm.rs | 1–264 | `280c87abd6d873ffcd3f2c44f0c52de7cbf334073c5e2c505571080435c7c075` |
| code/rust/core_number_theory/src/gaussian_regular.rs | 1–166 | `ff5734f946814f8a904be331e9215a75ea614c7bcd8f66c85519f528a3c3165c` |
| code/rust/core_number_theory/src/gf2.rs | 1–480, 481–957 | `39d6a9383a2f87759cc0d8fe837a220da96f3a5d0d806518854474a0533a00b9` |
| code/rust/core_number_theory/src/integer_factorization.rs | 1–289 | `b20c3c6e53044a5f215eeac01fd8e9c3eabb0eabe2f50347f63caf838162b81f` |
| code/rust/core_number_theory/src/lib.rs | 1–159 | `e55138db466ba55f722ba25854a29a52eeeef3cf27f9739bb95a08335766eb96` |
| code/rust/core_number_theory/src/polynomial.rs | 1–500, 501–1000, 1001–1500, 1501–1900, 1901–2281 | `590eb032fb65b99d16572515f1fca20f03219f006132cfef2af2435cdcafe9c0` |
| code/rust/core_number_theory/src/polynomial_factorization.rs | 1–350, 351–631 | `1fa6bd69cdbb0e6f8c198a654e2a5c978647a3c23e865403d3bf5b1f73162d30` |
| code/rust/core_number_theory/src/polynomial_map.rs | 1–167 | `b80cb1754515402a0a0f8657c1bfaa1bc5b62f3c360def3ff63a11643b78bf41` |
| code/rust/core_number_theory/src/power_basis.rs | 1–163 | `6ee507c0195830579f5d7c819e03ea1b8364c743d07e35799e1d48b9bc13276f` |
| code/rust/core_number_theory/src/power_series.rs | 1–230 | `7c8c4f185815295e119a89e842dade357eafc625cb84630f1e489b5fcfe35ac5` |
| code/rust/core_number_theory/src/quadratic.rs | 1–500, 501–1000, 1001–1500, 1501–1937 | `78aebe31aeffd2a86c4dc4b555187b3ff55e400600bd03850492f6e52d1448d4` |
| code/rust/core_number_theory/src/radical_sum.rs | 1–177 | `36b934ebfc6fc5594c120ce361e103056761abd8bafb78c589635ffcfea5e068` |
| code/rust/core_number_theory/src/rational.rs | 1–621 | `49ce8730d2beb1fa9d272a1c157c963a071cd94c885bb062a70eaeaeca3527c0` |
| code/rust/core_number_theory/src/rational_circle.rs | 1–88 | `c9ad54faef3007a103422060e30153c06955013c4802e7fcf68a05bb5c4e9787` |
| code/rust/core_number_theory/src/rational_turns.rs | 1–110 | `25b7c1379ab56c2e2570ec5d2dd795e7665ca190b8a3683dd5ea5f370fc92129` |
| code/rust/core_number_theory/src/real_embedding.rs | 1–480, 481–943 | `b2dbc497543e1414717f434db3201179e891aca5dac7ef27421eabedf912ceb3` |
| code/rust/core_number_theory/src/residue.rs | 1–95 | `ac0e61c5c4c4376901925c11b1d08d88249c687e806b8806b206518de09a7429` |
| code/rust/core_number_theory/src/scalar.rs | 1–509 | `8b96c0bd84a8b6389cdf12d2f429be46a513483c176cb80a570e4a1dae2fa0c0` |
| code/rust/core_number_theory/src/sums_of_squares.rs | 1–168 | `4ad80a76a41b852c210b7920ceb1fb65567ff11ac300357e37289ef2b79d279a` |
| code/rust/core_number_theory/src/test_support.rs | 1–204 | `bd400420029c155e6158924a52057b956480261acacc718ee9d8c328115f8cf8` |
| code/rust/core_number_theory/src/vanishing_sums.rs | 1–428 | `765d3f70c2fa266a9d12aa95d70363e25776d9aa3ed55a19873fbf223697bdab` |

## Dependencies and limits

- code/rust/core_homology/src/finite_rational_homology.rs SHA256 `03515087e482578637e304a3870e7bf69af37215babdd7ed3061a4f71b628c1c`, lines [1, 348]. Previously full body receipt consulted from frozen additional_rust_homology_remaining.json SHA f70224b113d47563ae797832b3b6ba93d17233b9a241bc9ba73380fdcb34d2c0; current dependency pin verified. No additional scope body credit or execution. Private complete rationalcomplex verifies shape/chainlaw and quotient image/kernelbasis; callerGaugeQuotient uses reverseddegreewindow correctly.

- Original Rust/manifests and historical evidence remain unchanged.
- No Rust/Cargo/native/provider or retained program execution, broad suite, credentials or private answer access.
- Only complete displayed source bodies earn full reading credit; parse/census and narrow dependency consultations remain separate.
- Independent exact finite controls are bounded to their declared carrier/input and do not establish general native correctness.
- Original scope has 83 direct full body reads and no template-transfer credit. Exact ranges, individual SHA256 pins and substantive assessments are preserved per file.
- Generic field/ring/involution/equality laws, classical mathematical theorems and imported matrix/category/interval backends are explicit dependencies, not automatically certified by trait names.
- Constructor/shape validation, complete mathematical admission, finite residuals, trusted caller premises and reported physical interpretations remain distinct.
- All16 control groups are independent audit arithmetic models; they neither execute the Rust implementation nor establish unrestricted algorithm correctness or universal runtime budgets.
- This slice is complete; the parent repository-wide every-file audit remains incomplete.
