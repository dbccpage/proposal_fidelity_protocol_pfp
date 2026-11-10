# C021–C030 substantive source and retained-evidence audit

Pinned source: `8050c66900899771766f33e8f5fdd200b7dd9120`. All ten requested families exist. Read all 236 pinned Python/Markdown files (32,795 lines); separately checked all 1032 JSON/JSONL files. Every one of the 1,268 inventory paths has a disposition and matches its original raw SHA256.

All 97 retained JSONL answers verify against their uniquely bound public examples. Cases: 481 verified and six independently unavailable. Mutants: 464 jointly rejected,50rejected by disagreement, one caught checker exception. No timeouts. No provider/network calls, protected seed/private access, source changes or historical rewrites.

Fixture success does not establish universal checker soundness. The source arguments and exact controls below expose failures outside the retained positive panel.

| Family | Full source files | Case/mutant/record dispositions | Finite mechanism |
|---|---:|---|---|
| C021 | 24 | case_certificate_verified: 56, manifest_bounded_custody_recheck: 1, mutation_rejected: 51, accounting_template_only: 1, answers_verified: 1 | Commuting signed-Pauli spectral minimum with exact algebraic and matrix certificates |
| C022 | 29 | case_certificate_verified: 57, manifest_bounded_custody_recheck: 1, mutation_rejected: 52, accounting_template_only: 1, answers_verified: 1 | Stabilizer code distance by explicit lower-weight symplectic search |
| C023 | 22 | case_certificate_verified: 56, manifest_bounded_custody_recheck: 1, mutation_rejected: 40, accounting_template_only: 1, answers_verified: 1 | Clifford circuit synthesis checked by Pauli conjugation |
| C024 | 26 | case_certificate_verified: 50, manifest_bounded_custody_recheck: 1, mutation_rejected: 39, accounting_template_only: 1, answers_verified: 1 | Local-complementation orbit witnesses and cut-rank separation |
| C025 | 25 | case_certificate_verified: 31, manifest_bounded_custody_recheck: 1, mutation_rejected: 55, accounting_template_only: 1, answers_verified: 1 | Exact cyclotomic mutually unbiased basis certificates |
| C026 | 22 | case_certificate_verified: 41, manifest_bounded_custody_recheck: 1, mutation_rejected: 49, mutation_rejected_by_paired_disagreement: 6, accounting_template_only: 1, answers_verified: 1 | Common kernel or left-inverse certificate for projector constraints |
| C027 | 23 | independent_verification_unavailable: 6, case_certificate_verified: 34, manifest_bounded_custody_recheck: 1, mutation_rejected: 50, mutation_rejected_by_paired_disagreement: 3, accounting_template_only: 1, answers_verified: 1 | Finite ray colouring, parity obstruction and bounded exhaustive refutation |
| C028 | 22 | case_certificate_verified: 44, manifest_bounded_custody_recheck: 1, mutation_rejected_by_paired_disagreement: 22, mutation_rejected: 33, checker_exception_caught: 1, accounting_template_only: 1, answers_verified: 1 | Binary-encoding Majorana representation and rational fermion Hamiltonian expansion |
| C029 | 21 | case_certificate_verified: 57, manifest_bounded_custody_recheck: 1, mutation_rejected: 37, mutation_rejected_by_paired_disagreement: 19, accounting_template_only: 1, answers_verified: 1 | Minimum-weight binary correction via graph T-join and matching |
| C030 | 22 | case_certificate_verified: 55, manifest_bounded_custody_recheck: 1, mutation_rejected: 58, accounting_template_only: 1, answers_verified: 1 | Exact contraction replay and independent subset dynamic programs |

## Findings

**AC2130-F01 — Answer identity and trace metadata are not bound by their validators (medium).** Both checkers accept wrong output id; tracer integrity accepts changed authority_effect because it reconstructs constant None. Correct finite energy is not falsified; identity/trace claims are weaker than their labels.

**AC2130-F02 — Unused CNF distance encoding does not exclude the stabilizer span (medium).** Without logical_basis, nonidentity stabilizer ZI satisfies the CNF intended to encode a nontrivial logical. Unused by active solver/judges; no current dual-judge acceptance exploit claimed.

**AC2130-F03 — Reference search failure rejects valid bounded Clifford circuits (high).** For X->-Y,Z->+X, circuit S,H uses2gates. Reference reports best8 and UNKNOWN, causing primary rejection while independent dense checker accepts. Nine of24one-qubit minimum-budget controls exhibit this completeness failure. Failure is valid-certificate rejection; normalized UNKNOWN is an accepted search refusal, not a proof of impossibility.

**AC2130-F04 — Out-of-scope witness content can be invented (medium).** Both judges accept a nonexistent defect kind/edge for a self-loop-invalid graph. Input really is out of scope; false explanatory witness rather than false membership verdict.

**AC2130-F05 — Exact fixed-basis matcher rejects a valid cyclotomic MUB (high).** Q(zeta16) rotated B0 equals submitted first basis, yet matcher rejects because individual coordinate modulus squared is irrational; only total norm needs rationality. Secondary accepts; paired gate rejects valid output. Exact overlap criterion itself is not refuted.

**AC2130-F06 — Unchecked negative weights invalidate groundspace interpretation (high).** H=diag(-1,0) is admitted with zero-energy kernel|1> although ground energy is-1. Positive-weight premise is essential. Input violates declared positivity domain; this is missing ingress enforcement, not failure of the PSD/kernel theorem.

**AC2130-F07 — Retained physical fixture descriptions are false (medium).** Entangled-only-kernel fixture has product vectors|010>,|100>; each pair of the pairwise-satisfiable-frustrated fixture is already inconsistent, with exact checked left inverse. Actual finite kernel/left-inverse computations remain meaningful; labels are not mathematical evidence.

**AC2130-F08 — Duplicate-ray colour assignments are overwritten (high).** Both checkers admit conflicting duplicate colours and even discarded value99 on[e1,e1,e2,e3]. Underlying configuration is colourable; submitted assignment is not a well-defined binary ray function.

**AC2130-F09 — Six retained cases lack bounded secondary verification (medium).** Peres33 and60ray nonparity cases raise IndependentVerificationUnavailable; never count these as mathematical failures or successful proof checks. No noncolourability conclusion is inferred from the unavailable secondary result.

**AC2130-F10 — Singular-encoding witness permits the zero F2 class (medium).** Both judges accept kernel_vector[2,0] as nonzero over F2 because Python nonzero test precedes modulo2 action. Encoding is genuinely singular; defect is certificate truthfulness and binary domain admission.

**AC2130-F11 — Advertised matching dual violates weak duality (high).** Six-vertex K3,3 shortest-path metric admits every advertised constraint for y=1/2,z_{0,1,2}=1 with objective4 although a perfect matching costs3. Internal odd-set dual sign is reversed. Exact counterexample to advertised dual theorem; not asserted to be one of the retained toric/rotated lattices.

**AC2130-F12 — Unbounded blossom node ids fabricate optimality certificates (high).** Odd set[-3,-2,-1] adds arbitrary objective with no edge constraints. Primary accepts weight3 although weight1 correction exists. Secondary uses shared reference matching, rejects this suboptimal case, but both accept bogus dual and ignored pair fields on a true minimum. Paired gate rejects demonstrated suboptimal correction. Do not upgrade that protection to independent proof or authentic submitted dual.

**AC2130-F13 — One-tensor lower-bound witness proves a false impossibility (high).** For tensors={A:[i]},dim(i)=2,B=0 both judges accept UNKNOWN open_size2 and correct SOLVED empty order cost0. There is no final contraction when N=1. In-domain counterexample to refusal soundness, independent of reference status agreement.

**AC2130-F14 — Published contraction names disagree with the checker protocol (medium).** TASK uses concatenated names AB/ABC while both replay implementations create @step:N. Published valid cost8448 example is rejected until renamed. Collision-free reserved naming is useful, but must be specified consistently.

**AC2130-F15 — Toric2x2 fixture does not encode its advertised code (medium).** Five independent stabilizer generators on8qubits imply k=3, not standard toric [[8,2,2]] k=2; measured distance2 does not validate the physics label. Finite distance computation can remain correct for the actually supplied stabilizer code.

**AC2130-F16 — Toric parity refusal trusts a label without checking the incidence premise (medium).** Hz=[[1]],syndrome[1],code=toric,distance3 accepts odd-parity impossibility though correction[0] solves supplied linear system. Synthetic input is not a toric lattice. Shows absent validation of the premise needed to interpret its supplied matrix as one.

## Mathematical assessments and reuse boundaries

### C021: Commuting signed-Pauli spectral minimum with exact algebraic and matrix certificates

For n qubits and commuting Hermitian signed Paulis, an independent binary symplectic basis of rank k has 2^k joint eigenvalue characters, each of multiplicity 2^(n-k). Phase-correct decomposition expresses every term in that basis. Enumerating all characters gives the exact rational minimum of H=sum w(I-sP)/2 and its degeneracy. Separately, exact Gaussian-rational Schur elimination of H-EI establishes positive semidefiniteness and nullity. Those two finite implications justify the numerical minimum under the declared Hilbert-space representation.

Algebraic enumeration and dense rational spectral calculation are distinct routes. Both now also check basis/decomposition/minimizer structure; spectral header saying otherwise is stale. Optional NumPy diagnostic does not gate exact acceptance.

Read all tests including adversarial matrix pivots, complex rank, k=0/k=n, phase traps, degeneracy, input types and 500-case random panel. One challenger oracle is floating eigvalsh despite exact wording; challenger2 final tests print blind spots without asserting secondary rejection. Full pytest suite not run; all pinned fixtures and mutants replayed.

Positive control: XX, ZZ, YY with all positive targets on two qubits gives exact energy1, degeneracy3; phase-flipped decomposition is rejected.

Reusable mechanism: Phase-aware finite character enumeration paired with exact PSD/nullity checking.

- Both output checkers ignore answer id and accept reversed minimizer order despite sorted-output contract; solver accepts empty input id that judges reject.
- DDC trace includes timestamps, and integrity verifier hashes a constant authority_effect=None instead of checking the stored authority field; tampered authority field still reports VALID_CHAIN. Hash consistency is not operation truth.
- README/TEST_READY contain historical counts and absent governance/E2E paths; participant runner invokes supplied code in-process without sandbox enforcement. Its RFC8785 claim is stronger than ordinary json.dumps canonicalization.

### C022: Stabilizer code distance by explicit lower-weight symplectic search

For independent commuting Pauli generators spanning isotropic S with 1<=dim S<n, logical operators are vectors in S-perp outside S. A candidate logical of weight d plus exhaustive exclusion of every lower weight establishes distance d. Generator independence excludes -I relations, so phases do not change this distance calculation. Search is bounded at one million lower-weight candidates; unavailable search is not a proof.

Primary uses integer bitmask span reduction; secondary uses vector rank. Shared schema guard remains. Exact checker bounds n<=20; secondary alone omits that bound. No LRAT certificate is used: current TASK requires lower_bound=null.

Meaningful alternate Shor logical and five-qubit false distance5 controls, stale LRAT rejection, and retained mutants. Tests and generators fully read; no full test-run claim.

Positive control: Alternate Shor logical verifies; five-qubit XXXXX weight5 is rejected because a weight3 logical exists.

Reusable mechanism: Independent lower-weight enumeration with an explicit verification-work ceiling.

- README and TEST_READY still advertise LRAT/CaDiCaL behavior withdrawn in current TASK; unused DPLL engine produces no proof.
- Unused CNF encoder without logical_basis excludes only identity, not stabilizer span: ZI satisfies its distance encoding for stabilizer ZI. This is not on the active judge path.
- Reference infers n from word length and ignores declared num_qubits; whitespace/case normalization exceeds strict checker ingress. Unhashable status can raise before typed rejection.
- Generator toric_2x2 has five independent generators on eight qubits, encoding k=3, not standard [[8,2,2]]. Pool consists mainly of permutations of 5/7/9/8-qubit examples, not broad n<=20,d<=7 coverage.
- Local-Hadamard generator swaps X/Z without Y sign change; distance is still preserved, but signed-code conjugation claim is inaccurate.

### C023: Clifford circuit synthesis checked by Pauli conjugation

H, S and CNOT conjugation of the 2n Pauli generators determines the Clifford automorphism and hence unitary up to global phase. Exact gate replay against an admitted symplectic signed tableau certifies a supplied circuit within gate bound. Failure of one synthesis algorithm to meet a bound is not a proof that no shorter circuit exists.

Primary first calls reference synthesis and requires matching status, then simulates. Secondary is NumPy complex128 tolerance1e-6 for n<=5, and uses the same reference Tableau primitives backwards above5; refusals delegate to primary. Independence is therefore limited.

All source/test files read. Independent one-qubit BFS enumerated all24 Clifford maps and minimum circuits. All24 pass with ample budget, but9 minimum-budget valid circuits are rejected because reference status is UNKNOWN. Existing fixtures set budgets from reference counts and miss this boundary.

Positive control: All24 one-qubit Clifford maps independently generated by BFS verify at budget100.

Reusable mechanism: Exact conjugation replay, after removing dependence of candidate admission on reference search success.

- Example X -> -Y, Z -> +X has valid two-gate S,H circuit; budget2 causes primary rejection while secondary accepts. Reference emits UNKNOWN with best_gate_count, forbidden by its own strict UNKNOWN schema. Stripping that field yields accepted refusal even though a solution exists.
- Random-walk tableau generator is not a uniform Clifford-group sampler; malformed poison inputs do not realize all planned valid sign/order adversaries.
- DDC tracer is imported but not actually used by synthesis; runner provides no isolation or runtime guard.

### C024: Local-complementation orbit witnesses and cut-rank separation

A sequence of exact local complementations on a labelled simple graph is a constructive orbit-membership witness. Cut rank over F2 is invariant under local complementation by elementary row/column transformations, so a subset with different cut ranks proves nonmembership. Equal cut ranks are not sufficient for membership. Exhaustive orbit closure proves nonmembership only when traversal truly exhausts the finite orbit.

Primary calls reference solve and fixes status/equivalence before replay. Secondary performs exact integer NumPy GF2 checks but shares graph/schema helpers. Search uses bounded bidirectional BFS25000states and cut probes, not planned Bouchet linear-system solver.

Read LC involution, P4 all16cut-rank tests, orbit exhaustion and budget controls, all mutations. Some budget tests monkeypatch solver rather than stress natural large orbit.

Positive control: Star on3vertices becomes triangle by local complement at centre0; both checkers pass.

Reusable mechanism: Constructive orbit replay and exact invariant separation, with explicit search exhaustion versus fuel exhaustion.

- For a self-loop-invalid input, both checkers accept an invented witness kind naming a nonexistent edge. Refusal status is appropriate, witness is false.
- Reference status gate and canonical exhausted-orbit count can reject alternate valid witnesses; bounded search failure is not a universal nonmembership theorem.
- Boolean vertex indices accepted in primary produce a secondary NumPy disagreement; paired gate rejects this probe. Generator selects reference-solvable cases; old counts are stale.

### C025: Exact cyclotomic mutually unbiased basis certificates

In Q(zeta_m), positive rational vector norm declarations must equal exact inner products; within-basis orthogonality and d*|<v,w>|^2=||v||^2||w||^2 across bases establish the finite MUB predicate after normalization. Cyclotomic reduction modulo Phi_m and complex conjugation supply exact arithmetic. GF9 trace, odd-prime chirps, GR(4,r) constructions and tensor products generate examples; generation is separate from certificate verification.

Primary exact polynomial arithmetic is substantive. Secondary projector/overlap computation is ordinary complex128 at1e-9, not high precision or exact; refusals delegate to primary.

Read field, cyclotomic, construction, dual, hygiene and runner tests. Replayed all retained certificates/mutants. Exact Q(zeta16) rotation supplies a valid fixed-basis counterexample missed by fixtures.

Positive control: a=cos(pi/8), b=sin(pi/8) in Q(zeta16); B0={(a,b),(-b,a)}, B1={(a-b,a+b),(a+b,b-a)} have squared norms 1 and 2 respectively and exact MUB overlap; unfixed certificate passes.

Reusable mechanism: Exact cyclotomic norm and overlap verification; phase/permutation matching needs correction.

- Fixed-first-basis comparison rejects a valid rotated basis when individual coordinate squared moduli are irrational, even though full vector norms are rational and the output basis equals the required basis. Secondary accepts; same MUB without fixed constraint passes primary.
- k=0 empty bases are accepted outside promised k>=2. Fixed-input norm2 metadata is ignored; replacing it by999 leaves acceptance.
- Reference fixed-basis construction assumes uniform vector norms using the first norm. Reference d10,k>=4 refusal conflicts with checker SOLVED expectation outside promised corpus.
- OPEN_PROBLEM is a policy refusal, not a nonexistence certificate. Solver emits trace exact/residual0 labels without invoking independent checker; some mutations fail id binding before intended semantic corruption.

### C026: Common kernel or left-inverse certificate for projector constraints

For positive weights and correctly embedded Hermitian idempotents P_i, H=sum w_i P_i is PSD and ker H=intersection ker P_i, since each nonnegative expectation must vanish. A rank-complete independent basis annihilated by every P_i certifies that kernel. For stacked constraint matrix M, L*M=I proves zero common kernel. These are finite Gaussian-rational linear-algebra implications; zero energy is the ground energy only under positivity.

Primary stack-rank certificate and secondary Hamiltonian kernel use different matrices, but share Gaussian-rational, Kronecker and projector validators. Secondary uses exact elimination, not planned LDL. Refusals delegate.

Read arithmetic, Kronecker, rank, dual, hygiene and packet tests. Exact probes validate negative-weight failure, empty-term full kernel, and false entangled/pairwise-satisfiable fixture descriptions.

Positive control: Positive H=diag(1,0) has verified zero-energy kernel|1>; empty H has verified full two-dimensional kernel.

Reusable mechanism: Rank-complete common-kernel witnesses and exact left-inverse impossibility witnesses, with positivity/domain admission.

- Neither positive weights, distinct support sites nor20term cap are enforced. H=diag(-1,0) is accepted with zero-energy kernel|1> as the purported groundspace, although true ground energy=-1.
- Empty term list makes reference solver raise IndexError; supplied identity basis correctly certifies full kernel and is accepted. Matrix shape problems can raise rather than return typed refusal.
- poison_01_entangled_only_kernel returns computational product basis |010>,|100>. Every pair of the three poison_02_pairwise_satisfiable_frustrated constraints already has a checked left inverse, so the pairwise-satisfiable description is false.
- Cluster-labelled fixture uses single-qubit minus projectors and toric-labelled fixture disjoint p00/p11 constraints; these labels are not proofs of those models. Wire parsing len2 can accept two-character strings; Boolean output field may accept integer0/1.

### C027: Finite ray colouring, parity obstruction and bounded exhaustive refutation

Exact Q(sqrt2) arithmetic identifies projective rays, orthogonality and d-ray contexts. A consistent {0,1} ray assignment with exactly one1 per context (and at most one among orthogonal pairs) is a finite noncontextual colouring. Odd many selected contexts with each ray appearing evenly gives contradiction mod2. Exhaustive noncolourability over a specified finite subset is valid only if actually completed. This does not by itself establish an empirical contextuality result or derive physics.

Secondary has separately implemented exact arithmetic/context construction. Nonparity verification exhaustively enumerates at most20merged rays; beyond that raises IndependentVerificationUnavailable. No LRAT/CaDiCaL proof implementation is present despite plan.

Read meaningful independent parity, nonorthogonality, subset-binding and unavailable-bound tests, plus ray/field tests. All retained cases/mutants attempted; six Peres-related cases explicitly exceed independent enumeration capability.

Positive control: Consistent duplicate-ray assignment[0,0,1,0] passes; exact odd-context/even-incidence parity certificates are meaningful finite obstructions.

Reusable mechanism: Exact ray quotient, parity contradiction and bounded independent verification with explicit unavailable status.

- Both raw-input colouring paths overwrite earlier duplicate-ray assignments; [1,0,1,0] on [e1,e1,e2,e3] passes, as does [99,0,1,0]. Invalid witness accepted, although the underlying configuration is colourable.
- Primary ignores subset in some refutation checks; secondary subset binding protects paired acceptance. Criticality/deletion certificates are absent from output contract.
- A refutation kind is a label causing search rerun, not a retained proof object. Six unavailable cases are pending independent verification, not false certificates or successful negative controls.

### C028: Binary-encoding Majorana representation and rational fermion Hamiltonian expansion

For invertible binary M, encoded occupation state is |Mn>. Majorana even/odd operators have fixed bit-flip column M e_j and parity characters derived from prefix rows of M^-1, with odd factor i. Signed-Pauli CAR and exact basis action establish the representation; expansion of fermion monomials then gives rational Pauli Hamiltonian coefficients. For N11/12 the actual1024samples have augmented GF2 ranks12/13. Since signed-Pauli phase ratios on binary linear encodings are affine characters, these full ranks exclude every nontrivial affine phase mismatch; this closes this specific finite Majorana check under admitted representation premises.

Primary compares full H coefficient dictionary to shared reference expander and uses full basis N<=10, fixed samples above10 for Majoranas. Secondary checks independent Fock Hamiltonian action, all columns N<=6 and256samples above6, but does not validate candidate Majorana list; shares inversion/fraction and delegates refusals. General Hamiltonian sampling has no analogous proof supplied here.

Read CAR, mapper, inversion, Pauli, expansion and packet tests. All retained outputs replayed. One mutant triggers caught string IndexError rather than normal rejection. Exact singular-witness probe and augmented-rank closure executed.

Positive control: Singular [0,1] kernel witness verifies; augmented sample ranks are exactly N+1 for both admitted sampled sizes.

Reusable mechanism: Exact CAR/action checking and algebraic closure of affine-character samples, plus separately bounded Fock-action diagnostics.

- Singular witness [2,0] is accepted as a nonzero F2 vector although it represents zero; no binary witness-value check. Correct [0,1] control passes.
- N0 empty encoding is accepted beyond promised N>=1. Binary matrix values and some dimension consistency are incompletely admitted; malformed matrices may raise. TASK id alternative conflicts with schema requiring case_id.
- Hamiltonian exact comparison shares reference expansion, so repeated code agreement is not independent proof. Large-N secondary samples remain bounded evidence.
- Generator imaginary hopping conjugate for t_im=1/2 incorrectly becomes0 (latent helper defect; retained imaginary examples use1). Planned characteristic-polynomial controls absent.

### C029: Minimum-weight binary correction via graph T-join and matching

For nonnegative weighted graph-incidence Hz with one endpoint column for boundary edges or two for interior edges, correction syndrome is an odd-degree boundary condition. Shortest-path perfect matching of defects (with appropriate boundary copies) computes a minimum T-join; path overlaps can be removed modulo2 without increasing cost. A genuinely feasible matching dual attaining the correction weight would certify optimality. The advertised internal-odd-set dual is not such a dual: for primal x(E(S))<=(|S|-1)/2, plus-sign z in edge constraints/objective must be nonpositive. Positive z requires a different cut formulation.

Primary independently checks syndrome/weight but uses shared graph distances and an invalid dual formula. Secondary calls the SAME solve_min_weight_decoding as the reference, rather than independent coset enumeration; it rejects demonstrated suboptimal weight3 against reference weight1, but cannot authenticate submitted dual certificate.

Read all graph, simplex, matching, dual, hygiene and packet tests. Existing dual test checks first5base and silently skips missing cases. Exact K3,3 metric counterexample refutes dual theorem; out-of-range blossom reproductions distinguish first-checker unsoundness from paired rejection.

Positive control: Retained interior-pair case correction[4] has exact weight1; replacing by[0,3,4] gives same syndrome weight3 and paired gate rejects despite primary acceptance.

Reusable mechanism: Exact syndrome/weight replay and bounded matching search; replace dual formulation and enforce graph/lattice premises before certificate reuse.

- Complete six-vertex metric with within-part distance2 and cross distance1 admits advertised y=1/2,z_{0,1,2}=1, claimed dual4, while cross perfect matching costs3. This is a theorem counterexample, not an assertion that this metric is a retained lattice.
- Odd-set vertex ids are not checked for membership/distinctness. Set[-3,-2,-1] adds arbitrary objective without constraining any edge. Bogus pairs/boundary fields are ignored. Both judges accept fabricated certificate on a correct minimum; primary alone accepts suboptimal correction.
- code/distance label does not validate lattice, incidence column weights, positive edge weights or matrix shape. Toric-labelled Hz=[[1]],s=[1] accepts odd-parity impossibility although correction[0] exists. This violates encoding premises, not toric parity mathematics.
- Graph silently ignores columns with0 or>2ones; negative weights invalidate Dijkstra assumptions. No negative-weight execution was attempted. Exact simplex fallback/unbounded cases not independently certified.
- Zero syndrome returns before checking certificate contents. Correctness then depends on nonnegative weights. Generator controls do not bind a transported correction proof, and reference matching search is exponential.

### C030: Exact contraction replay and independent subset dynamic programs

For indices occurring once or twice, contracting live disjoint tensor groups costs product of union dimensions and leaves symmetric-difference indices. Induction over n-1 merges proves exact total work and final open-leg set. Every binary contraction tree splits into two proper subtrees, so subset recurrence cost(A)+cost(B)+product(legs(A) union legs(B)) enumerates all trees; enforcing size at every merged subset yields an exact optimum for N<=12. For N>=2 final-step cost is at least the product P of all open-leg dimensions, so P>B or final size P>S proves infeasibility.

Primary bitmask bottom-up DP and secondary frozenset recursive DP are distinct and import no reference solver. Both exact replay arithmetic is integer; shared envelope schema remains. Primary/secondary reproduce the same one-tensor lower-bound premise error.

Read exact DP, arithmetic, heuristics, refusal controls and hygiene tests. Replayed all fixtures including costs>2^64. New one-tensor positive/negative pair demonstrates incompatible accepted conclusions; naming control tests the published example.

Positive control: Reserved-name chain order has exact optimal cost8448 and passes both independent DPs; invalid final size from low-level DP is rejected.

Reusable mechanism: Collision-free live-tensor replay, exact tree optimality DP and size lower-bound witnesses with N>=2 admission.

- N1 has no final contraction. Both checkers accept UNKNOWN with open_size2>B0 and also correct SOLVED empty order cost0 for the same admitted input.
- TASK and CHALLENGE specify concatenated output names (AB); actual solver/checkers require @step:N. Published three-tensor valid order is rejected until renamed.
- Exported reference DP omits final size bound and can return infeasible order; top-level open-size precheck and both final checkers protect normal admission.
- Heuristic helper tracks minimum-cost order independently of feasibility when cost_bound=None, so found_valid can refer to a different order; generator does not verify ok before creating bounds. Several supposed feasible large size-bound cases are actually refused by valid final-open-size witness.
- Generator tree_d3_b2 is15tensors despite comment trimmed to10; future regeneration can enter expensive unbounded DP. Planned Rust/beam/annealing is Python multi-start greedy. Runner has no per-case isolation/60second enforcement.

## Custody, unsupported verification and evidence ceilings

Fresh manifest checks: {'declared_lf_match': 1053, 'declared_lf_mismatch': 156, 'unresolved_outside_original_inventory': 40}. All ten prior manifest record hashes match current bytes. C021 aggregate ordered-lines digest differs under its own explicit definition. Other mismatches remain after declared CRLF→LF normalization; outside-inventory references stay unresolved. Every manifest is explicitly regenerated, not a pre-run commitment. Ten accounting templates have no calls and consistent zero totals.

The seven unsupported mathematical-verification outcomes are listed with exact paths/hashes in `remaining_unsupported_files`: six C027 nonparity cases exceed the independent20ray limit; the C028 constant-answer mutant causes IndexError. Missing external historical manifest targets are separately enumerated in the custody ledger.

- All236 pinned Python/Markdown files were fully read, including tests and generator write/delete branches; generators/runners were not invoked to alter originals. Full source read does not mean formally proved correct.
- All1022JSON and10JSONL files have separate automated dispositions; all97JSONL answers were bound uniquely to pinned examples and replayed. Reference output is never itself a soundness proof.
- No full pytest suite was run. Bounded owner calls have20second per-file/per-answer subprocess limits; no retained execution timeout occurred. Synthetic probes use only harmless public fixture contexts and exact small controls.
- No network/provider/model calls, benchmark seed/private storage/key access, pilot edits or original source/evidence modifications. socket connection methods blocked in helper workers.
- Six C027 cases remain independently unavailable; one C028 mutant produces caught IndexError. These are explicitly not counted as mathematical rejection.
- Retained mutation rejection measures this finite panel only;50mutants produce checker disagreement rather than agreement of rejection. No population false-positive/false-negative rate, universal soundness or proof of independent implementations inferred.
- Manifest SHA checks establish byte custody at a convention, not runtime provenance, pre-run commitment or mathematical validity. Stored answer files are historical fixtures, not live model evidence.
- No general quantum-mechanics derivation, physical realizability, operational quantum advantage, model improvement, statistical superiority, economic budget enforcement or executable PFP/EIS/PCIV/operad integration is established by these challenge labels.

Per-file owner hashes and complete/partial-read distinctions are in [the JSON report](additional_challenges_021_030.json); data checks remain separate in [the automated ledger](additional_challenges_021_030_automated.jsonl). Exact synthetic cases and outcomes are retained in the four `additional_challenges_021_030_probes_*.json` artifacts.
