# C011–C020 substantive checker/spec audit

Pinned corpus: `8050c66900899771766f33e8f5fdd200b7dd9120`. Completed all ten families: **1,284 files**, with **208 full source/spec/test reads** and **1,076 separate automated data dispositions**. No source/evidence edits, provider calls, protected seed or credential access.

**The strongest finding is C019 mathematical unsoundness:** a positive feasible dual is admitted as the exact Phi2 optimum without a primal equality check. A synthetic case with objective identically 2 passes with phi2=1. 29 retained owner-PASS certificates also have nonzero submitted primal/dual gaps.

| Family | Pinned files | Full reads | Data dispositions | Main assessment |
|---|---:|---:|---:|---|
| C011 | 120 | 19 | 101 | Exact weighted-L1 primal/dual certificate is a real reusable mechanism conditional on valid carrier/schema. |
| C012 | 162 | 20 | 142 | Combined exact rank/kernel/cokernel and Fredholm witness mechanism is substantive on valid sheaf inputs; no general higher-cohomology or consensus-system theorem. |
| C013 | 145 | 21 | 124 | Substantive exact SNF and integral homology mechanism, with certificate parsing defects and uneven individual checker completeness. |
| C014 | 160 | 23 | 137 | Real exact weighted Hodge certificate on interpreted finite rational chain complex, conditional on correct input encoding. |
| C015 | 123 | 20 | 103 | Substantive exact persistence reduction on a valid interpreted filtered complex. |
| C016 | 98 | 21 | 77 | Independent quotient-rank computation is substantive; claimed complete submitted certificate is unsound. |
| C017 | 123 | 23 | 100 | Real exact finite-group witness checks with meaningful arithmetic diversity. |
| C018 | 115 | 20 | 95 | Sound packing/exhaustive optimality implication for the admitted simple signed graph; meaningful certified-UNKNOWN design. |
| C019 | 113 | 20 | 93 | Extension and obstruction witnesses are substantive; Phi2 optimum admission is unsound. |
| C020 | 125 | 21 | 104 | Substantive finite F2 filtered-complex page computation and independent subquotient replay. |

703 case/example files were replayed: 694 pass the owner gate; 8 warranted refusals fail and 1 checker execution raises. All 344 retained mutants reject. All 72 answers in 4 JSONL files verify against unique pinned examples. No per-file timeout occurred. Passing a current judge does not override the defects below.

## Findings

**AC1120-F01 — C019 admits suboptimal dual lower bounds as Phi2 optima (high; mathematical_soundness).** Both judges accept Phi2=1 on a two-face zero-boundary complex whose objective is identically 2. Neither reads primal_A; 29 retained owner-PASS certificates also fail the required primal-dual equality.

**AC1120-F02 — C013 accepts noninteger SNF matrices as integer certificates (high; certificate_encoding).** int() truncation validates a different matrix from the supplied one. Checker2 checks homology values while ignoring the supplied SNF. Homology in the counterexample is correct, but its submitted integral certificate is false.

**AC1120-F03 — C016 accepts incomplete cohomology bases (high; certificate_completeness).** Empty H1 bases on two circles pass with rank0. Rank recomputation does not certify basis completeness, image independence, or upper-span witnesses required by CHALLENGE.

**AC1120-F04 — C014 overwrites repeated face incidences instead of adding (high; encoding_adequacy).** The shared parser interprets[(e,+1),(e,-1)] as -1 rather than0; both judges accept a nonnilpotent OOS verdict for a cancelling boundary. The formal Hodge identity applies to the interpreted matrix, not the intended sum.

**AC1120-F05 — C012 first checker omits H0 completeness (medium; individual_checker_soundness).** Independent kernel vectors alone do not span H0. The second checker catches the reproduced empty-basis exploit and the combined gate rejects it; fractional h0_dim still raises.

**AC1120-F06 — C011 accepts unwitnessed refusals and out-of-contract solved inputs (medium; input_and_witness_contract).** Malformed edges=None accepts an invented SELF_LOOP witness. Cycle-rank17, enforced denominator13, selfloop SOLVED and numeric wire fields pass; unhashable vertices raise.

**AC1120-F07 — C012 shared input/refusal checks fail witness binding and bounds (medium; input_and_witness_contract).** Both accept a stalkdimension5 and invented named edge while rejecting warranted duplicate-ID and target-count refusals. Sharing the refusal/parser helpers correlates these failures.

**AC1120-F08 — C013 first checker accepts extra diagonal invariants (medium; individual_checker_soundness).** An appended diagonal value outside the matrix extent creates phantom torsion/rank for checker1. Checker2 rejects the wrong homology, preserving this combined gate; extra unrelated SNF certificates remain unchecked.

**AC1120-F09 — C014 reference fails valid degenerate complexes (medium; producer_completeness).** An isolated vertex crashes and a selfloop produces an incorrect incidence potential; the judge rejects the latter. These are reference producer failures, not an accepted wrong decomposition.

**AC1120-F10 — C015 omits filtration-order and witness validation (high; input_and_witness_contract).** A decreasing filtration passes SOLVED and an invented face witness passes OOS. Out-of-range persistence pairs raise IndexError; five retained warranted UNKNOWN outputs fail both judges.

**AC1120-F11 — C016 refusal and degree4 handling are non-total (medium; runtime_contract).** Three retained poisoned refusals fail checker1 while checker2 accepts; another retained poison raises ValueError in closure. Valid degree(4,0) on S4 raises KeyError5.

**AC1120-F12 — C017 does not enforce its named group and square-grid carrier (medium; scope_and_totality).** Trivial group outside the named set and extra diagonal edges pass. Unhashable group elements throw. Table identities remain valid for the admitted arbitrary group; this is a scope defect, not a demonstrated wrong valid-lattice holonomy.

**AC1120-F13 — C018 narrows advertised certificate methods and omits simple-graph bounds (medium; scope_and_implementation).** The SAT/DRAT/LRAT and block certificate paths are absent; computed blocks are discarded.201vertices and repeated edges pass. TASK UNKNOWN local-optimum/maximal-packing rule differs from CHALLENGE operator-gap comparator.

**AC1120-F14 — C019 integer producer is a bounded heuristic, not a complete solver (medium; producer_completeness).** Only one rational particular solution and eight simple modular candidates are tried.2A0+A1=1 returns UNKNOWN despite integer solution(0,1). Positive-weight premise is also unenforced for EXTENDS.

**AC1120-F15 — C020 silently drops outside-grid cells and omits the dimension cap (medium; encoding_adequacy).** A nonzero cell(6,0) is silently discarded and certified as the zero complex. A five-dimensional(0,0) cell passes despite cap4. Malformed certificate can throw in checker1 before the independent checker runs.

**AC1120-F16 — C017 historical harness evidence has incomplete provenance (medium; historical_evidence).** Four reports and receipts reconcile recorded costs/pass counts and raw report SHA256. Eleven full historical solutions replay with the same pass/fail outcomes; ten baseline/immune raw solutions are absent. Missing shared evaluator source and provider IDs prevent attributing labels/costs to verified live calls.

## Mathematical and evidential limits

**C011.** For valid interpreted graph, let r=c-Dphi, D^T y=0, |y|<=w. For any psi, y^T c=y^T(c-Dpsi)<=sum w|c-Dpsi|. A checked feasible phi with equal primal and dual objectives is therefore globally optimal. This implication requires weak duality only, not trusting the simplex producer or assuming strong duality. Potential checker repeats this core and additionally checks fundamental cycle residuals using the reference graph helper.

**C012.** H0 completeness needs kernel membership plus independence plus dimC0-rankD cardinality. H1 basis requires rank[D|B]=dimC1 and |B|=dimC1-rankD. Gluing Dx=b is direct; nonzero eta^T b with D^T eta=0 proves inconsistency. Checker2 independently recomputes rank and target augmented rank, while checker1 misses H0 cardinality completeness. Combined gate rejects the reproduced incomplete H0 witness.

**C013.** For valid finite free chain complex, integer U,Uinv,V,Vinv with inverse identities and U*d*V diagonal with positive divisibility chain certify cokernel invariant factors. Since ker(d_n) is saturated in free C_n (quotient is im(d_n), free), torsion of C_n/im(d_{n+1}) equals torsion H_n. Betti follows rank-nullity. Checker2 recomputes integer invariant factors and field2 ranks; mere Euler equality or F2 inequality would not determine torsion.

**C014.** For D1D0=0 and positive diagonalW, imD0 and im(W^-1D1^T) are W-orthogonal. A decomposition with harmonic h in both kernels is unique by positive definiteness. Exact harmonic membership, independence and cardinality E-rankD0-rankD1 establish basis completeness. Checker1 implements these; checker2 compares uniquely recomputed normal-equation parts but does not inspect harmonic_basis.

**C015.** For a valid filtered simplicial boundary over F2, upper-unitriangular V preserves the filtration, R=DV changes basis, and unique nonzero column lows yield persistence pairings. Zero R columns not paired as lows give essential classes. Checker2 independently reduces D by sparse XOR. Equal filtration-value births/deaths are retained as index pairs but omitted from value barcodes.

**C016.** A closed product with nonzero pairing against a closed cycle is nonexact. Complete cup-image rank requires bases spanning the input cohomology, an independent image family, and an upper-span certificate for all products. Independent checker instead computes rank(B+products)-rank(B) using its own exact rational cocycle representatives; this can establish the numerical rank without validating submitted basis completeness.

**C017.** Ordered finite-group products certify plaquette nonflatness. A gauge verified on every declared edge proves trivialization. Flatness plus closed generating torus loops with determinant-one winding matrix and nontrivial commuting holonomy certifies the stated global obstruction on a valid lattice. Checker2 uses the faithful left-regular permutation representation L_g L_h=L_gh and independently reconstructs a spanning-tree gauge.

**C018.** Switching gives an upper bound. Each pairwise edge-disjoint odd-negative closed walk contains a negative cycle and requires a distinct deletion, hence packing size is a lower bound. Equality certifies optimality. Exhaustive2^(n-1) enumeration is complete modulo global sign. UNKNOWN certificates establish bounds and local optimality/maximal packing, not global optimality.

**C019.** An exact potential proves extension. A closed cycle with nonzero B pairing proves rational nonextension by annihilating im(d1). An integer modular cycle with nonzero pairing proves integer nonextension. Weighted-L1 optimality additionally requires a primal attaining the feasible dual objective; merely positive dual feasibility proves only a lower bound.

**C020.** For a finite filtered chain complex, Z_r(n,p)={x in F_p C_n: Dx in F_(p-r) C_(n-1)}. The page is Z_r/(Z_(r-1)(n,p-1)+D Z_(r-1)(n+1,p+r-1)). Independent checker explicitly computes these subquotients with XOR bit-vector bases and induced differential ranks modulo the target denominator. Recursion subtracts both outgoing and incoming ranks; E6 stabilizes for the bounded six-column carrier and its degree sums give total homology.

C011–C020 describe formal finite problems. Weighted-L1 weak duality, kernel/cokernel witnesses, integral SNF, Hodge orthogonality, persistence reduction, cup pairing, finite-group holonomy, negative-cycle packing, modular obstructions and filtered subquotients are real reusable mechanisms when their stated premises and encodings hold. They do not certify a physical interpretation, population generalization, an operadic implementation merely from its type, or a model advantage.

C017 has four historical reports and four receipts. Recorded costs, pass rates and raw report digests reconcile. Eleven retained full solutions replay with the same current pass/fail outcomes. Ten baseline/immune records lack full answers and cannot be rescored. No generation IDs/raw provider responses are established; zero recorded cost is not proof of a free call. The shared evaluator imported by Arm5/6 is absent.

Seven manifest reviews reuse the prior structured-evidence audit only for matching bytes: C011–14 declared-reference checks pass with provenance limits; C015–17 each retain five normalized content mismatches. This audit does not reclassify hashes as mathematical evidence or rewrite historical custody.

The executable lower-bound paths, actual Python arithmetic, shared parsers, stale counts/generator recipes, refusal semantics and unimplemented planned Rust/SAT/provider paths are detailed per family in the JSON. No claim is made that the complete pytest suite ran. All owner test sources were read, all pinned mathematical data were replayed, and independent probes include hand-derived d3/d4/d5 staircase controls for both C020 filtrations.

## Artifacts

- `additional_challenges_011_020.json`: claims, dependencies, limits, findings, all source-read records and data disposition index.
- `additional_challenges_011_020_automated.jsonl`: every structured file, checks, checker details and evidence ceiling.
- `additional_challenges_011_020_probes.json` and `_more_probes.json`: full synthetic inputs/certificates and observations.
- `_notes.json`: substantive family analyses; `_emitted_segments.jsonl`: source-read coverage supporting208whole-file reads.
- `_validate.py`, `_records.py`, `_more_probes.py`, `_probes.py`, `_read.py`, `_report.py`: reproducible offline helpers.

All assigned pinned files received an assessment. Open failures, missing historical answer/provider provenance and absent imports remain explicit; none was silently marked semantically certified.
