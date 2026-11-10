# Remaining PFP domain: completed scoped audit

Original inventory commit: `8050c66900899771766f33e8f5fdd200b7dd9120`. Scope: **427 files, 2,913,844 bytes**. Final accounting: **426 full body reviews (70,549 lines), one bounded generated-data assessment (6,007 lines), zero pending paths**. This completes only the declared slice; the repository-wide audit remains incomplete.

The [JSON report](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/dag/reviews/additional_pfp_domain_remaining.json) is the authoritative per-file/hash/range/claim/control record. [The durable read ledger](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/dag/reviews/additional_pfp_domain_remaining_read_ledger.json) records incremental body reads; automated parsing is not credited as full reading. [Final reconciliation](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/dag/reviews/additional_pfp_domain_remaining_final_validation.json) pins this report and confirms all427 original hashes still match frozen scope and inventory.

## Mathematical and operational assessment

PFP has reusable finite mechanisms here: exact rational normalization and matrix arithmetic, conditional weighted-L1 primal/dual certificates, source-bound finite lift replay, explicit typed refusals, frozen claim/witness separation, deterministic finite enumeration, and tree-based coboundary repair. Each needs its own premises. The finite lift checker admits its carrier and predicates; bare assertion still has a singleton self-relation. Irreflexivity, distinct vertices, cost grammar, observation map and authority are additional structure, not consequences of the inscription `<>`.

The strongest weaknesses occur at certificate boundaries. Several records accept declared success, source hashes or host labels without replaying the claimed computation; some lose operative data during canonicalization. Concrete counterexamples include stale verified receipts, scalar zero-gap checks without feasibility, false exactness after float conversion, unsound sort pruning, phantom stage residuals, missing native-result type checks and unbound summary hashes. Findings are local to the pinned owner and tested input; downstream callers may impose additional restrictions.

EIS/PCIV and operadic/normal-form components supply useful schema, provenance, composition and finite relation machinery, but their semantic claims are not licensed by naming alone. Protected-query preservation requires actual source and observation binding. Operadic composition requires carrier/slot laws and cannot inherit them from a generic AST. Role declarations do not authenticate independent observers. Budget, refusal and evidence levels must survive the full call chain.

The higher-stage physical vocabulary is particularly conditional. Regge checks accept a supplied closure boolean without holonomy matrices; Hodge checks use Euclidean transpose while ignoring supplied metric matrices; zeta checks trust an exactness flag and a constant coefficient. The cochain solver does perform an exact graph construction, but its positive fundamental-cycle sum is basis-dependent, not the weighted-L1 optimum Phi1 or the first homology of a filled complex. The synthetic hook installs the solver answer directly; it is not a live-model experiment.

## Findings to prioritize

- **PFPDOMAIN-F006: Replacing candidate or verifier preserves a stale verified receipt.** Starting from a bound complete quartet, submit_candidate with a new candidate or bind_verifier with a new verifier returns Ok but retains the old receipt and is_verified flag. is_complete remains true although the receipt no longer binds the current object. These public mutators violate the aggregate consistency claim without requiring direct field mutation; rechecking validate_invariants would reveal the mismatch but the methods do not call it.
- **PFPDOMAIN-F010: Shared-kernel score silently rounds positive floating residuals to zero.** The class advertised as zero-float exact arithmetic admits float and calls Fraction(str(val)).limit_denominator(). A positive1e-12 input becomes rational zero in phi1 and combined_score while caller is_exact=True survives. This is not the separate stronger entity class used by ScoringPort; no native scoring caller was exercised.
- **PFPDOMAIN-F025: Sealed self-panel loaders do not bind content.** SelfPanel.load_canonical trusts supplied content and seal digests after length checks, even nonhex unrelated values, and silently replaces declared count with actual entries count. ThymusGate(sequence_of_entries) seals only entry IDs, so changing contents preserves the seal. This affects custody evidence for the finite negative-selection panel, independently of whether supplied strings are actually healthy.
- **PFPDOMAIN-F027: Current self-panel content hashes disagree for25 fixtures.** Recomputing UTF-8 SHA256 for all1000 stored fixture contents finds25 mismatches. The1000 entries reduce to40 distinct base strings after removing the declared synthetic index/hash suffix, each repeated25 times. The finite fixture corpus is not1000 independent verified proofs; its category labels and Lean-looking assertions do not establish correctness. The loader trust gap in F025 means these mismatches do not trigger refusal.
- **PFPDOMAIN-F028: Ensemble enforces per-member rather than declared total budget.** Header promises <=70B total parameters for all ensemble members; constructor checks each member independently. Two70B members from different lineages are accepted for140B total. NaN also passes both positivity and ceiling comparisons. Lineage cap and parameter metadata remain caller-supplied.
- **PFPDOMAIN-F033: Entropy cocycle verification is an unconditional true stub.** EntropyCocycle.coboundary_is_nilpotent claims to verify an information-cohomology identity but returns True without any operator. Constructor merely rejects floats; negative degree and a string coefficient are accepted and obtainTrue. No constructed differential or theorem makes this a certificate.
- **PFPDOMAIN-F039: Annihilator accepts a false inequality as a refutation.** AnnihilatorDecoy.evaluate ignores its stored refutation_witness and only requires supplied evaluation text to contain!=. A matching decoy is Neutralized by the false statement1 != 1. This is marker checking, not refutation or a mathematical annihilator certificate.
- **PFPDOMAIN-F042: Stage frame binds candidate ID but not selected body or continuation history.** StageFrame validates stage4 candidate_id membership among stage2 candidates, but accepts a different candidate body under thatID. A frame can also continue after a prior StageResult.controller_continue=False because that field is not linked to continuation. Synthetic schema control accepts value999 under theID whose stage2 value was1.
- **PFPDOMAIN-F044: BQNF certified repairs omit group and predicate effects.** Moving amount 10 from group A to B yields certified new-group delta zero, rather than A minus 10/B plus 10. AVG inserts an unpaid row despite status = paid predicate. The evaluator accepts these boundary declarations yet ignores group relocation and AVG filtering; certified true overstates the finite update semantics.
- **PFPDOMAIN-F047: Zero-gap verifier does not bind feasibility or objective values.** ZFNF defaults absent feasibility to true and never recomputes objective scalars from witnesses. Scalars 7/7 alone yield CertifiedOptimalZeroGap; feasible witnesses with actual objectives 1/1 also certify claimed 999/999. Equal scalars are insufficient to establish optimality of a bound problem.
- **PFPDOMAIN-F049: Reconciliation authorizes an unauthenticated verifier label and unsealed loss ledger.** An outcome=verified dictionary is treated as an authenticated target verifier. A ledger containing only erased_attributes passes integrity with no entries or digest. Together these yield certified and authorized true for an empty quotient projection. This is a domain return value; no external authorization operation was exercised.
- **PFPDOMAIN-F051: 5NF projection synthesis invents a lossy cyclic-key decomposition.** With candidate keys AB, AC and BC and no declared join dependency, synthesis returns those pair projections precisely when keys do not imply their join. The four even-parity binary triples satisfy all three keys, yet their projections join to eight rows. Cyclic keys alone do not justify the generated lossless-reconstruction claim.
- **PFPDOMAIN-F053: MVD chase turns exhausted work into non-implication.** For heading ABC, decomposition AB/BC and FD B→C, max_iterations=1 skips the FD phase and returns is_implied false; budget two returns true. The result has no unknown/status alternative. This differs from the FD-only chase, which preserves BudgetUnknown for zero budget.
- **PFPDOMAIN-F065: Proposal evaluator certifies strict descent without descent or exactness.** Equal masses are admissible and labelled Strict descent verified. require_exactness=True does not prevent float1e-12 being rounded to exact zero; max_proposals=0 does not prevent selecting a candidate. Those config fields are unused. The evaluator checks a tolerance-bounded reported scalar change, not strict descent of reconstructed residuals.
- **PFPDOMAIN-F071: Airy floating underflow is labelled exact.** Nonzero lambda=minimum positive binary64 and z=1+2^-52 have strictly positive exact rational lambda*(z²-1), but computed residual is0. With other four slots at1, projector empty-obstruction branch labels this exact. Canonical float encoding preserves representation, not exact polynomial evaluation. Large finite overflow controls are separately refused.
- **PFPDOMAIN-F072: Local lab reports controls that it does not run.** solve sets packet blockers empty, adapter.sound=True and detector.adequate=True; cases_checked only counts declarations. Synthetic invalid packet validator and inconsistent detector case are never invoked while locally_resolved and evidence_valid are true. Candidate path further uses representative mass comparison without protected-skeleton/retraction validation. This finding concerns this lab owner, with outer gates assessed separately.
- **PFPDOMAIN-F080: Closed research terminal guard does not require zero residual.** The guard admits FINITE_RESIDUAL_CLOSED with a C,E,I,T sequence whose E decreases2→1 and terminal residual remains1. Native-chain checks enforce decrease/continuity/effect labels but do not require terminal zero or independently recompute equations. OESOS roots are optional; if supplied, their declared exact receipt is checked, not a fresh mathematical replay. This bounds the claim: full artifact replay was not executed and foreign grammar remains a separate assumption.
- **PFPDOMAIN-F096: Stage7 summary can contradict its validated host replay.** WitnessReplay recomputes outcomes and ChallengeReplay enforces dense indices, but Stage7Response accepts a different demo_id, checked_count=0 and empty obstruction_indices while its host replay has one checked open obstruction. The wrapper does not bind summaries to its nested replay.
- **PFPDOMAIN-F100: Pending master horizon can exert terminal authority without receipt.** A pending proposal with CertifiedTerminal authority and no receipt passes. Receipt-less path returnsOk unless requested green, and pending receipts also lack the red/green authority restrictions. This breaks the claimed proposal non-authority boundary.
- **PFPDOMAIN-F102: Hodge checker ignores declared inner products.** A valid Euclidean decomposition with exact=(1,0),coexact=(0,1) passes despite supplied positive-definite M1=[[2,1],[1,2]], for which their weighted inner product is1. All three metric matrices are ignored; weighted adjoints and complex nilpotence are unverified.
- **PFPDOMAIN-F103: Regge checker accepts absent geometry and nonsymmetric Gram.** Empty simplices/hinges with supplied negative determinant and closure=True pass without any rotation matrices. Optional [[1,100],[0,1]] Gram also passes positive leading minors though x=(1,-1) has xTGx=-98; symmetry and4D shape are missing. No exact holonomy or length-to-Gram binding is performed.
- **PFPDOMAIN-F109: Accepted down-map can break edge involution.** A four-edge involution with pairs a-b,c-d projects a,c to x, b to y,d to z. With no protected state pairs the down-map accepts, but its resulting reversal map fails involution. Preserving declared state distinctions does not preserve edge algebra.
- **PFPDOMAIN-F114: Sort pruning can falsely certify finite exhaustion.** For unary witness form1 sorted by claimform0 with only datum0 in the sort, a Closure with empty body demands form1(datum1). pruning_sound skips integer head arguments and returnsTrue; pruned search reports CLOSED, unpruned search finds NewInst(1,(1,)) at cost1. Independent count matches the wrong pruned class, so counting alone does not prove sound pruning.
- **PFPDOMAIN-F115: Stage certifier accepts fabricated exhaustion and phantom residual.** A proposal supplies nonexistent residual ID, fake source exhaustion/family digest, self-declared nontrivial/down evidence and a datum addition that leaves its real requirement false; all11 certify conditions pass. licensed also accepts11duplicate condition1 records, and execute trusts those records under a supplied granted Licence. No source/receipt binding is checked at execution; this is not a claim of bypassing an external authenticated human licence.
- **PFPDOMAIN-F116: Caller prior score can turn an unchanged state into descent.** execute_retraction_turn trusts prior_score. Increasing its active_count by1 and supplying empty delta produces DESCENT with an unchanged child state. Evidence hashes omit actual source regime and port proof, so trusted caller caching must be explicit or recomputed.
- **PFPDOMAIN-F117: Cochain exactness assumes unenforced antisymmetry.** Claims c(a,b)=0 and c(b,a)=1 coexist; get prefers the requested orientation. The triangle solver still reports exact coboundary because chosen cycles use only one orientation. The constructor checks Fraction values but not antisymmetry, loops or carrier membership; zero selected-cycle sum cannot certify malformed full claims.

## Scope and evidence limits

The panel assessment parses all1000 objects and recomputes content hashes:40 base texts appear25 times each, and25 stored content hashes disagree with current bytes. Fixture labels such as clean proof are not checked Lean proofs or reliable empirical ground truth. No panel text was compiled, and no private grading material was accessed.

All143 controls are bounded offline checks on read-vetted owners or explicitly isolated unchanged functions.26 receipt files record runtime and source bindings. A missing NumPy dependency limited the AST/numerical lane; nothing was installed. No broad native builds, retained executable replay, model calls, credentials or private benchmark/answer/seed access occurred. Original sources and historical evidence remain unchanged. Exact details and transformations are in the probe receipts.

## Claims and reusable mechanisms

### PFPDOMAIN-CL01 — Exact arithmetic is conditional on representation and supplied algorithm contracts

Fraction and Q arithmetic can make rational equality a decision rather than a tolerance, but the repository has different wire dialects and exactness does not verify the upstream model. Linear algebra ports validate input shape/type yet trust returned calculations; method names and runtime protocols are not proof witnesses.

Evidence: [pfp/domain/shared_kernel/exact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/exact.py:43), [pfp/domain/exact/linalg.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/linalg.py:26), [pfp/domain/ports/exact_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/exact_ports.py:23).

### PFPDOMAIN-CL02 — Status-bearing records must remain distinct from host verification

Domain Result, EvaluationVerdict, GenesisCycleVerdict, SmithNormalFormResult, DualCertificate and VERIFIED receipts are primarily data containers. Several constructors enforce only syntax or partial consistency and default evidence-ceiling strings do not validate arithmetic, provenance or authority. Complete lifecycle success is unsound under the demonstrated stale-binding mutations until a caller adds the missing invariant checks.

Evidence: [pfp/domain/kernel/result.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/kernel/result.py:81), [pfp/domain/homology/cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/cochain.py:142), [pfp/domain/aggregates/cycle_balance_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/cycle_balance_aggregate.py:104).

### PFPDOMAIN-CL03 — DDC tape summaries are endpoint bookkeeping, not replay certificates

DDCTape.is_fuel_conserved checks initial fuel minus total costs against only the final recorded fuel; per-step fuel and carrier transitions can be inconsistent while both fuel and monotone summary properties are true and final_status defaults PASS. The independent control exhibits that boundary. No primitive semantics, history alignment or proof of executed steps is implemented by these records.

Evidence: [pfp/domain/homology/ddc.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/ddc.py:27).

### PFPDOMAIN-CL04 — Score result exactness is narrower than a repair certificate

The stronger score record refuses inexact residuals and requires zero post-norm plus digest syntax for an exact flag, but it does not recompute residual_drop or normalized_efficiency, bind a residual to a supplied cochain, or replay a dual witness. A5-to4 transition with claimed drop999 is representable. The injected host evaluator remains responsible for arithmetic, model and witness correctness; the weaker shared-kernel namesake has different semantics.

Evidence: [pfp/domain/entities/coboundary_score.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/coboundary_score.py:129), [pfp/domain/ports/scoring_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/scoring_port.py:17).

### PFPDOMAIN-CL05 — Boundary grammar, byte custody and semantic fidelity are separate contracts

parse_boundary refuses empty <> and proves only membership in its bounded nonempty ASCII tree grammar. CompilationReceipt supplies a useful exact byte-cover/hash/codebook mechanism, conditional on caller-chosen spans, but does not prove semantic labels or question equivalence. ExpansionNode proves finite occurrence counts and depth, not that decomposed prompts preserve a task. Wiki/spec dialect comparisons remain documentation claims owned by the parent audit.

Evidence: [pfp/domain/rewriting/rewrites.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/rewrites.py:39), [pfp/domain/rewriting/rewriting_types.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/rewriting_types.py:74), [pfp/domain/rewriting/prompt_containment.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/prompt_containment.py:57).

### PFPDOMAIN-CL06 — Transport identity does not confer verification or authority

The typed canonical packet/candidate mechanism binds declared fields and rejects mismatched serialized IDs. It explicitly treats proposals and evaluation summaries as transport requiring independent admission/replay. Constructor-level validation is weaker than from_dict, while legacy narrative/trace layers can label zero supplied scores as exact or successful without replay. Reusable custody mechanisms must be kept separate from those display assertions and from proof of detector adequacy.

Evidence: [pfp/domain/entities/packet_envelope.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/packet_envelope.py:1), [pfp/domain/entities/candidate_artifact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/candidate_artifact.py:74), [pfp/domain/bridge/trace_policy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/trace_policy.py:28).

### PFPDOMAIN-CL07 — Exact weighted-L1 duality is a real conditional optimality mechanism

The certificate predicate checks rational dimensions, z=omega-Dalpha, D^T W=0, |W|<=w, sign alignment and equal primal/dual reported objectives. These imply global minimization by the dual lower bound for every alternative alpha. It establishes the supplied finite optimization problem, not source interpretation, unique solution or semantic repair; zero weights yield a seminorm and permit nonzero residual at zero optimum.

Evidence: [pfp/domain/dual_witness/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/dual_witness/models.py:15).

### PFPDOMAIN-CL08 — Tower lift lower bounds depend on explicit cardinality and distinctness

Exhausting all2 and16 binary relations on canonical one/two-element carriers confirms the supplied predicates: no irreflexive witnessed pair on one element, no path2/cycle3 with three distinct vertices on two. This is a finite combinatorial consequence of admitted definitions, not a derivation of the carrier/logic/stages from primitive difference. Stored receipt pins alone do not bind counts or target witnesses.

Evidence: [pfp/domain/tower_lift/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower_lift/models.py:16).

### PFPDOMAIN-CL09 — Fixed-interval clonal decay has an exact telescoping implementation

For a fixed positive tau and nonnegative initial affinity, the floor-difference exponent makes consecutive decay calls telescope to the same result as one call covering their sum. A7-step tiny rational control gives5/8 from5 at tau2. Inactivity uses the independent half_life_runs threshold; this is deterministic bookkeeping, not biological validation or learned affinity.

Evidence: [pfp/domain/immune/clonal_selection.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/clonal_selection.py:339).

### PFPDOMAIN-CL10 — Registered ground-step joins have a precise finite certificate boundary

TarskiPolygraph validates each supplied tail path against exact rule/location/source/result registry entries, continuity and common endpoint. Altered locations are refused. The apex is only type-checked and initial peak edges are absent, so this proves tail joinability only, conditional on the supplied registry; it does not prove a critical peak exists, complete critical-pair enumeration or global confluence.

Evidence: [pfp/domain/decoding/polygraph.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/polygraph.py:111).

### PFPDOMAIN-CL11 — Finite rational coboundary nilpotency is an actual reusable mechanism

For valid finite triangular carriers, d1(d0f) expands to(fw-fv)-(fw-fu)+(fv-fu)=0. The implementation handles reversed edges, and allvertex-basis audit plus linearity establishes the identity for all rational0-cochains on that fixedcarrier. Tiny3-cycle audit passes3basis-face evaluations. This is admitted combinatorial algebra, not a primitive or physical derivation; the receipt has no custodyseal.

Evidence: [pfp/domain/ddc/coboundary.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/coboundary.py:38).

### PFPDOMAIN-CL12 — Pinned finite deciders preserve evidence levels

Explicit modular arithmetic and finite permutation order/iteration are independently computed from parsed operands and supplied host pins. Two disjoint cycles of lengths2/3 give order6. Positive, wrong, undefined and unsupported statements receive rederived, contradicted, refused and uncheckable outcomes respectively. Unknown rows do not inflate hallucination counts; producer-authored carriers cap complete results at self-consistency. Host pin custody and complete row accounting remain external obligations.

Evidence: [pfp/domain/row_rederivation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/row_rederivation.py:284), [pfp/domain/presentation_pins.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/presentation_pins.py:70), [pfp/domain/calculus_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/calculus_receipt.py:261).

### PFPDOMAIN-CL13 — Finite sign algebra is reusable under explicit carrier assumptions

BSS solves exact signed-edge parity constraints; all 27 three-vertex matrices agree with exhaustive eight-gauge search and obstruction cycles have odd sign parity. The separate BQNF finite-weight gate checks closed opposite equal-weight involution pairs and all negative coverage, leaving nonnegative survivors. These establish conditional finite-carrier results, not a universal physical sign-problem solution. C3 arithmetic checks constants and finite path counts; the integrated path bounds remain supplied mathematical premises.

Evidence: [pfp/domain/normal_forms/quantum_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/quantum_forms.py:30), [pfp/domain/normal_forms/bqnf_fsign.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/bqnf_fsign.py:60).

### PFPDOMAIN-CL14 — Finite relational closure and synthesis have explicit evidence limits

Attribute closure is monotone saturation on finite attributes. FD chase merges finite symbols and returns unknown when unsaturated at budget; stable failure yields a tableau countermodel under valid heading/dependency premises. Minimal cover and 3NF synthesis preserve all subset closures and checked losslessness/dependencies for 64 small theories. This supports reusable mechanisms, while declared JDs, complete theories and exponential resource limits remain assumptions.

Evidence: [pfp/domain/normal_forms/relational.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational.py:48), [pfp/domain/normal_forms/relational_advanced.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational_advanced.py:132).

### PFPDOMAIN-CL15 — Smith and simplicial computations are exact conditional finite algebra

The reviewed integer Smith reducer agrees with independent determinantal-divisor formulas on 625 two-by-two matrices. Explicit chain products can verify nilpotency on a valid finite simplicial carrier. Euler equality in this owner is derived from the same rank formulas and supplies no independent validation; carrier closure and valid integer rectangular input remain separate obligations.

Evidence: [pfp/domain/normal_forms/topology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/topology.py:32).

### PFPDOMAIN-CL16 — Explicit finite tower checks are stronger than catalogue labels

The L1 checker verifies residual equals host cochain minus a gradient, positive rational weights, complete divergence-free capacity-bounded dual flow and recomputed equal objectives. Weak duality then proves global optimum on that finite graph. Other small owners compute rational stochastic/Bayes/spin values, compatible finite function gluing, the singleton old-context left inverse and finite birth/death cardinality. These are reusable conditional mechanisms; they do not establish the101 catalogue obligations, physical theories, forced genesis or arbitrary oracle hierarchy separation.

Evidence: [pfp/domain/tower/checks.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/checks.py:183), [pfp/domain/tower/updown_maps.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/updown_maps.py:38), [pfp/domain/tower/alternation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/alternation.py:39), [pfp/domain/tower/tower_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/tower_policies.py:116).

### PFPDOMAIN-CL17 — Finite quantum algebra is independent of physical and certificate labels

Pauli tensor multiplication and commutation agree with explicit4x4 matrices on all256 two-qubit pairs. GF2 RREF plus rigorous fixed-coordinate branch-and-bound agrees with exhaustive syndrome-compatible search on512 tiny cases. For a complete kernel and positive supplied weights, the affine coset exhausts every same-syndrome vector, supporting a finite optimum. C029 code geometry and original matching-certificate obligations remain outside this independent check.

Evidence: [pfp/domain/quantum/pauli.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/pauli.py:78), [pfp/domain/quantum/c029_coset.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/c029_coset.py:15).

### PFPDOMAIN-CL18 — Prompt compression revalidates preserved provider inputs

The compression owner preserves UTF8 source spans, shared environments and explicit per-turn schema overrides while recomputing digest bindings at expansion. A Unicode two-turn control roundtrips and refuses a nested environment mutation. Its claim is storage deduplication only; expanded provider requests, semantics and author authentication are not improved or certified.

Evidence: [pfp/domain/prompts/compression.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/compression.py:88), [pfp/domain/prompt_representations/common.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/common.py:60).

### PFPDOMAIN-CL19 — Host codecs and protected-query comparisons have distinct scopes

Executable SQLitev2 safely renders declared span text as UTF8 hex data with fixed table/DDL, preserving quotes, Unicode and NUL in a synthetic in-memory roundtrip. Historical v1 is explicitly wire-only in its Python owner. The symbolic design note correctly requires an additional exact ordered slot/role/text comparison: schema-valid encoding is not semantic preservation, independent task acceptance or authenticated source evidence.

Evidence: [pfp/domain/prompt_representations/relational_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/relational_prompt_representation.py:134), [pfp/domain/prompt_representations/symbolic_constraint_binding_v001.md](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/symbolic_constraint_binding_v001.md:18).

### PFPDOMAIN-CL20 — Transport reconciliation is useful without granting mathematical authority

Evidence transport reparses closed schemas and reconciles packet/runtime/parent/event/candidate identities; its verifier is internal custody, not independent equation or solver replay. ResearchStep explicitly revalidates mutable fields at replay conversion. These reusable boundaries remain narrower than proof or authority, and the builder unresolved names/recursive fields omission are separate concrete defects.

Evidence: [pfp/domain/entities/oesos_evidence_bundle.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/oesos_evidence_bundle.py:427), [pfp/domain/entities/research_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/research_packets.py:332).

### PFPDOMAIN-CL21 — Explicit refusal ceilings and source-bound finite transport are reusable

Code-change evaluation retains budget/source/verifier obstructions even for declared PASS gates and does not author VerifiedProposal. Research family laws reserve broad continuum/full Chern-Simons families to refusal and bind finite carrier/protected-boundary/source/initial identities. These mechanisms improve scope and custody discipline while leaving independent checker adequacy, source transcription and program/scientific correctness external.

Evidence: [pfp/domain/aggregates/code_change_bind.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_bind.py:466), [pfp/domain/aggregates/code_change_attestation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_attestation.py:16), [pfp/domain/aggregates/research_claim.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/research_claim.py:695).

### PFPDOMAIN-CL22 — Declared role separation and trusted-oracle comparison remain distinct

ThreeRoleGate checks host scope/admitted-root membership and declared pairwise role/principal separation; it neither authenticates independent actors nor evaluates claims. Pilot gates enforce useful finite integer/list/schema comparisons against supplied oracle data, while oracle adequacy and source binding remain external. Neither role separation nor answer matching establishes PFP as a universal scientific verifier.

Evidence: [pfp/domain/provenance/three_role_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/provenance/three_role_gate.py:15), [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py:429).

### PFPDOMAIN-CL23 — Finite lift certificates preserve explicit admissions

The finite lift owner enumerates the declared singleton/two-point relation spaces and recomputes count, obstruction, canonical target witness and digest. Bare assertion admits a singleton self-relation; irreflexivity and three distinct vertices are additional predicates. This is useful replayable finite necessity relative to supplied goals, not a derivation of those goals or an arbitrary Genesis tower.

Evidence: [pfp/domain/mssn_research/grammar/lift_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/lift_policies.py:86).

### PFPDOMAIN-CL24 — Exact arithmetic mechanisms remain useful within scoped contracts

Phi4 checks primal residual, dual cycle/capacity and zero exact Fraction gap, which certifies weighted-L1 optimality for admitted dimensions and nonnegative weights. BQNF repair recomputes omega=d0 alpha; frontier conditioning recomputes rational normalization. These reusable finite checks require source/representation/observation binding separately, and higher-stage physical labels do not supply it.

Evidence: [pfp/domain/mssn_research/grammar/quantifier_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/quantifier_policies.py:54), [pfp/domain/mssn_research/grammar/rewriting_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/rewriting_policies.py:170), [pfp/domain/mssn_research/grammar/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/entities.py:81).

### PFPDOMAIN-CL25 — Declared finite search and canonicalization are reusable with validated premises

Finite reading-ladder leaf weights matched all9 deterministic tables, and refined versus brute structural isomorphism agreed for all256pairs of two-point binary relations. Search hashes/counts and replayed histories are useful custody mechanisms, but source-domain validity, pruning soundness and complete operational keys remain separate obligations. No general minimality or infinite theorem follows from this finite control.

Evidence: [pfp/domain/solvers/ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/ladder.py:97), [pfp/domain/solvers/iso.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/iso.py:134), [pfp/domain/solvers/search.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/search.py:324).

### PFPDOMAIN-CL26 — Tree integration supplies an exact finite repair theorem under graph assumptions

On a connected oriented simple graph with an antisymmetric rational cochain, integrating a fixed spanning tree and replacing every chord by potential difference yields a coboundary. Fundamental cycles decouple the chord equations. This is an explicit finite linear construction; its positive cycle-basis norm is basis-dependent, not Phi1 L1 optimum or H1 of a filled simplicial complex. The hook directly installs this answer and does not establish model adherence.

Evidence: [pfp/domain/solvers/simplicial_cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/simplicial_cochain.py:11), [pfp/domain/solvers/cochain_gradient_hook.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/cochain_gradient_hook.py:308).

### PFPDOMAIN-CL27 — PFP authority separation is an interface obligation, not granted by labels

The domain contains explicit None ceilings, typed refusals, frozen claims, source digests and human-licence concepts. Their sound use depends on validated constructors, literal checker outputs, complete source/claim/proof binding and authenticated host policy. A report label such as Certificate, Exact, CertifiedTerminal or all_passed is not independently justified when the owner accepts declared flags, phantom IDs or omitted operative fields. Findings identify concrete local gaps rather than reject the general separation principle.

Evidence: [pfp/domain/solvers/stage.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/stage.py:243), [pfp/domain/mssn_research/grammar/authority_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority_policies.py:30), [pfp/domain/stages/demos.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/demos.py:48).

## Complete finding register

### PFPDOMAIN-F001 — Distinct-root count fails at repeated-root endpoints

root_count documents distinct roots in(lo,hi] but misses squarefree normalization/endpoint handling. For(x-1)^2(x-2), observed0 instead of1 on(1,3] and2 instead of1 on(0,1]. isolate and Alg constructors squarefree their input or reject repeated factors, so these examples refute the public root_count contract without automatically refuting those guarded paths.

Evidence: [pfp/domain/exact/poly.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/poly.py:103).
Controls: PFPDOMAIN-C001.
Limit: No native/provider execution; scoped Python3.14.2 probe with read-vetted modules and inert namespace packages.

### PFPDOMAIN-F002 — A frozen algebraic number retains mutable polynomial input

Alg accepts a list because it only compares trim(poly) with tuple(poly), then stores the original mutable object. Mutating the caller list from x-1 to x-2 changes alg_equal results while the Alg instance remains the same frozen object. Primary internal constructors use tuples; the malformed-but-accepted public constructor path is the demonstrated failure.

Evidence: [pfp/domain/exact/alg.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/alg.py:62).
Controls: PFPDOMAIN-C002.
Limit: No native/provider execution; scoped Python3.14.2 probe with read-vetted modules and inert namespace packages.

### PFPDOMAIN-F003 — RationalWire accepts multiple canonical input spellings

from_wire advertises canonical parsing but accepts whitespace, leading zeros, denominator-one and nonreduced fractions, negative denominator, plus sign and negative zero. It normalizes all through Fraction, unlike the strict shared rational parser. This is a representation-binding gap at the public API; no workflow exploitation is demonstrated.

Evidence: [pfp/domain/exact/wire.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/wire.py:18).
Controls: PFPDOMAIN-C003.
Limit: No native/provider execution; scoped Python3.14.2 probe with read-vetted modules and inert namespace packages.

### PFPDOMAIN-F004 — Scalar duality-gap equality is not an optimality certificate

RationalDualityGap permits inconsistent fields via its constructor and compute sets is_optimal solely from equality of two scalar objectives. Feasible primal/dual witnesses and the same constrained problem are absent. An inconsistent(1,0,0,True) record is accepted. Equal values can be an arithmetic gap result only; optimality requires separately validated feasibility and weak duality. No concrete workflow accepting this record has yet been found.

Evidence: [pfp/domain/exact/wire.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/wire.py:62).
Controls: PFPDOMAIN-C004.
Limit: No native/provider execution; scoped Python3.14.2 probe with read-vetted modules and inert namespace packages.

### PFPDOMAIN-F005 — Empty boundary-matrix transpose loses declared shape

BoundaryMatrix(0,2,()).transpose() returns0-by-0 rather than2-by-0. The constructor explicitly supports nonnegative dimensions with zero rows, so this is a supported empty-dimension case, not malformed data. Transpose involution and subsequent shape-sensitive chain operations can fail.

Evidence: [pfp/domain/homology/cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/cochain.py:24).
Controls: PFPDOMAIN-C005.
Limit: Read-vetted Python3.14.2 modules under inert namespace packages; no native or provider execution, and no claim that an external production caller was exercised.

### PFPDOMAIN-F006 — Replacing candidate or verifier preserves a stale verified receipt

Starting from a bound complete quartet, submit_candidate with a new candidate or bind_verifier with a new verifier returns Ok but retains the old receipt and is_verified flag. is_complete remains true although the receipt no longer binds the current object. These public mutators violate the aggregate consistency claim without requiring direct field mutation; rechecking validate_invariants would reveal the mismatch but the methods do not call it.

Evidence: [pfp/domain/aggregates/cycle_balance_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/cycle_balance_aggregate.py:104).
Controls: PFPDOMAIN-C006, PFPDOMAIN-C007.
Limit: Read-vetted Python3.14.2 modules under inert namespace packages; no native or provider execution, and no claim that an external production caller was exercised.

### PFPDOMAIN-F007 — Quartet constructor omits verifier-to-problem binding

The constructor synchronizes digests and validates candidate and receipt references but never compares verifier.problem_digest with the attached problem. A receipt can correctly bind the supplied candidate/problem/verifier hashes while the verifier contract names another problem, and is_complete is true. bind_verifier checks this relation, demonstrating inconsistent entry paths.

Evidence: [pfp/domain/aggregates/cycle_balance_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/cycle_balance_aggregate.py:53), [pfp/domain/entities/cycle_balance.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/cycle_balance.py:250).
Controls: PFPDOMAIN-C008.
Limit: Read-vetted Python3.14.2 modules under inert namespace packages; no native or provider execution, and no claim that an external production caller was exercised.

### PFPDOMAIN-F008 — Complete quartet accepts a mismatched receipt self-digest

ReceiptEntity accepts an existing Sha256Digest without recomputing it. Quartet checks only reference hashes, then copies the caller-provided VERIFIED status; a receipt with all-zero wrong self-digest and null terminal/witness fields yields is_complete true. This is a demonstrated receipt-integrity/assurance gap, not a claim that content hashes should prove mathematical correctness. Actual host/native verification must remain a separate trusted input.

Evidence: [pfp/domain/entities/cycle_balance.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/cycle_balance.py:273), [pfp/domain/aggregates/cycle_balance_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/cycle_balance_aggregate.py:69).
Controls: PFPDOMAIN-C009.
Limit: Read-vetted Python3.14.2 modules under inert namespace packages; no native or provider execution, and no claim that an external production caller was exercised.

### PFPDOMAIN-F009 — Canonical digest and normal-form IDs accept a trailing newline

Sha256Digest validates with regex.match and a dollar anchor, which permits a final newline; a65-character value is accepted despite the exactly64-hex contract. NormalFormId similarly accepts nf.test.example followed by newline. General string IDs separately reject trailing whitespace. This establishes inconsistent canonical representation validation, not a forged matching SHA256.

Evidence: [pfp/domain/value_objects/identifiers.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/identifiers.py:15).
Controls: PFPDOMAIN-C011.
Limit: Read-vetted Python3.14.2 modules under inert namespace packages; no native or provider execution, and no claim that an external production caller was exercised.

### PFPDOMAIN-F010 — Shared-kernel score silently rounds positive floating residuals to zero

The class advertised as zero-float exact arithmetic admits float and calls Fraction(str(val)).limit_denominator(). A positive1e-12 input becomes rational zero in phi1 and combined_score while caller is_exact=True survives. This is not the separate stronger entity class used by ScoringPort; no native scoring caller was exercised.

Evidence: [pfp/domain/shared_kernel/coboundary_score.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/coboundary_score.py:1), [pfp/domain/ports/scoring_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/scoring_port.py:7).
Controls: PFPDOMAIN-C012.
Limit: Focused Python3.14.2 source-loaded controls; no native/provider execution.

### PFPDOMAIN-F011 — Score wire decoding promotes nonempty false strings to true

Entity CoboundaryScoreResult.from_dict applies bool to is_legal and is_exact_candidate. Both string false values become True; with zero exact post-norm and a syntactically valid digest the record accepts both flags. Strict literal-boolean validation already exists in this package but is not used here. This identifies malformed-input admission, not verification of the digest witness or an exercised production scoring path.

Evidence: [pfp/domain/entities/coboundary_score.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/coboundary_score.py:152), [pfp/domain/validation/validation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/validation/validation.py:143).
Controls: PFPDOMAIN-C013.
Limit: Focused Python3.14.2 source-loaded controls; no native/provider execution.

### PFPDOMAIN-F012 — Byte-exact compilation receipt does not bind semantic role letters

A constraint span with exact bytes/digest/coverage is accepted with task-letter q or unsupported letter z in BoundaryWire. The regex permits every lowercase letter and receipt validation checks symbol count/order/ranges/text but never compares role annotations. Its byte-preservation guarantee survives this counterexample; interpreting the receipt as preserving role semantics does not.

Evidence: [pfp/domain/rewriting/rewriting_types.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/rewriting_types.py:23).
Controls: PFPDOMAIN-C016.
Limit: Python3.14.2/Pydantic2.13.5 controls over source-loaded owners; no whole application or model behavior claim.

### PFPDOMAIN-F013 — Wire codec loses recursive AST structure and has noninjective rendering

A nested App f(App g(Atom x)) renders (f (g x)) but the parser makes two atom arguments, so parse(serialize(term)) differs from term for an admitted recursive model. Atom value () and Void render identically. No escaping, recursive tokenization or profile budget enforcement repairs this in WireCodec.

Evidence: [pfp/domain/rewriting/wires.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/wires.py:21).
Controls: PFPDOMAIN-C017.
Limit: Python3.14.2/Pydantic2.13.5 controls over source-loaded owners; no whole application or model behavior claim.

### PFPDOMAIN-F014 — AST dependency projection omits relative imports and can resolve exact targets to ancestors

PythonSourceParser ignores ImportFrom when module=None and drops its level; from .. import infrastructure yields no dependency. The builder resolver returns the first prefix/suffix match, so known pkg is selected for target pkg.infrastructure.b even when that exact module exists. These omissions/misbindings affect the intended architecture-defect projection; named PHI/GAMMA2 evaluator still refuses without its native owner.

Evidence: [pfp/domain/ast_cochain/ast_source_parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_source_parser.py:55), [pfp/domain/ast_cochain/ast_dependency_complex.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_dependency_complex.py:48).
Controls: PFPDOMAIN-C018, PFPDOMAIN-C019.
Limit: NumPy absent. Parser/topology owners and exact resolver method AST were executed; graph matrices, numerical evaluators and applications were not.

### PFPDOMAIN-F015 — ByteSpanVO slices codepoints rather than bytes

ByteSpanVO documents half-open byte offsets, but slice applies those offsets to Python str. On éx, span[0,2) should select UTF8 bytes for é; it returns éx. The byte-exact CompilationReceipt uses encoded bytes and is not affected by this separate helper.

Evidence: [pfp/domain/value_objects/topology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/topology.py:55).
Controls: PFPDOMAIN-C020.
Limit: NumPy absent. Parser/topology owners and exact resolver method AST were executed; graph matrices, numerical evaluators and applications were not.

### PFPDOMAIN-F016 — Step-packet compiler cannot serialize the current exact score type

ObstructionScore normalizes phi/gamma to Fraction even for integer zero. compile_step_packet places these fields directly into json.dumps, which raises Object of type Fraction is not JSON serializable for a valid zero score. No packet or downstream verification is produced on this normal current-type path.

Evidence: [pfp/domain/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/models.py:187), [pfp/domain/bridge/symbol_game_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_packets.py:64).
Controls: PFPDOMAIN-C021.
Limit: Read-vetted source loading and exact isolated display methods on Python3.14.2. No model, native solver, external pharmacy or artifact sink invoked.

### PFPDOMAIN-F017 — Dialogue templates assert test and solver success without corresponding evidence

generate_round_debate given a zero score emits statements that a linear solver confirmed exactness, the test suite passed and Unicode/empty-input probes succeeded. It runs none of those checks and takes no test/solver receipts. These deterministic fictional beats can enter the normal emitter as supplied character dialogue, so preserving existing beats does not turn their claims into verified evidence. Some zero-phi branches also ignore nonzero gamma/count.

Evidence: [pfp/domain/bridge/symbol_game_dialogue.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_dialogue.py:43), [pfp/domain/bridge/symbol_game_emitter.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_emitter.py:148).
Controls: PFPDOMAIN-C022.
Limit: Read-vetted source loading and exact isolated display methods on Python3.14.2. No model, native solver, external pharmacy or artifact sink invoked.

### PFPDOMAIN-F018 — Trace input/title helpers discard current frozen packet payloads

PacketEnvelopeV2 always freezes mapping payloads into typed canonical nodes. _packet_initial_input accepts only dict and thus turns both alpha and beta content in the same task into task:test; _packet_title likewise returns empty. Trace fingerprint/perception then describe a fallback label rather than original content when this orchestration path is used. Exact helper controls establish the representation mismatch; no trace was written.

Evidence: [pfp/domain/entities/packet_envelope.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/packet_envelope.py:155), [pfp/domain/bridge/symbol_game_emitter.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_emitter.py:156), [pfp/domain/bridge/symbol_game_uns_renderer.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_uns_renderer.py:142), [pfp/domain/bridge/unified_oe_trace.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/unified_oe_trace.py:89).
Controls: PFPDOMAIN-C023.
Limit: Read-vetted source loading and exact isolated display methods on Python3.14.2. No model, native solver, external pharmacy or artifact sink invoked.

### PFPDOMAIN-F019 — Gate receipt factory default stores a dataclass Field

GateReceiptV1.create uses field(default_factory=dict) as a regular function default. Omitting retained_metrics creates a receipt with a Field object and to_dict raises Field object is not iterable. The dataclass constructor itself has a correct dict factory; failure is specific to the public create factory.

Evidence: [pfp/domain/entities/gate_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/gate_receipt.py:41).
Controls: PFPDOMAIN-C024.
Limit: Focused Python3.14.2 controls over read-vetted local declaration modules; no provider, adapter, native process or storage execution.

### PFPDOMAIN-F020 — Declared learning repository package export cannot resolve

pfp.domain.ports advertises ILearningRepository in __all__, but does not import it or list it in _LAZY_IMPORTS. Access raises AttributeError immediately. Separate typed and generic owner modules exist; neither is selected by this advertised package entry point.

Evidence: [pfp/domain/ports/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/__init__.py:24).
Controls: PFPDOMAIN-C025.
Limit: Focused Python3.14.2 controls over read-vetted local declaration modules; no provider, adapter, native process or storage execution.

### PFPDOMAIN-F021 — V1 decode receipt omits its honored flag from wire identity

Two otherwise identical DecodeControlReceipt values with honored=True and honored=False serialize and hash identically because to_dict omits honored. Thus retained wire/digest cannot distinguish the objects own applied-control outcome flag. V1 remains metadata-only and V2 has a separate replay contract; this finding does not claim provider enforcement was measured.

Evidence: [pfp/domain/ports/decode_control_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/decode_control_port.py:77).
Controls: PFPDOMAIN-C026.
Limit: Focused Python3.14.2 controls over read-vetted local declaration modules; no provider, adapter, native process or storage execution.

### PFPDOMAIN-F022 — Proofreading admits arithmetic-looking pseudo-prose without a mathematical check

The HopfieldNinioProofreader describes preventing pseudo-proofs and surviving orthogonal deformation, but its actual predicate is marker/buzzword detection plus caller-supplied residual. Appending the false equation1=2 to gauge-invariance/topological-protection prose changes DISSOCIATED_DURING_DELAY to CATALYTIC_ADMISSION at default zero residual. No equation truth, proof, deformation or kinetic process is checked. This is heuristic evidence, not proof admission.

Evidence: [pfp/domain/biochem/proofreading.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/biochem/proofreading.py:86).
Controls: PFPDOMAIN-C029.
Limit: Focused local Fraction/text controls, not a test of model, physical biochemical behavior or a downstream host gate.

### PFPDOMAIN-F023 — Proofreading accepts negative parameters and emits contradictory measurements

Negative deformation_factor is admitted and copied as delta; the receipt reason still states measured Delta Phi_1=-1 >0. A negative initial residual on unflagged text is silently rewritten as zero in the admission receipt. Energy_per_delay is also unconstrained in sign. Thus accepted input values can violate the record own claimed nonnegative defect/dissipation semantics.

Evidence: [pfp/domain/biochem/proofreading.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/biochem/proofreading.py:93).
Controls: PFPDOMAIN-C030.
Limit: Focused local Fraction/text controls, not a test of model, physical biochemical behavior or a downstream host gate.

### PFPDOMAIN-F024 — Seven-point coordinator bypasses reported delay and quorum

evaluate_candidate_move reports quorum and proofreading but does not use either to condition quarantine or recruitment. The exact method returns quarantine=True and4 effectors on the first observation with detector_votes=0, QUIESCENT quorum and proofreading_confirmed=False. Thymus is constructed but never consulted. This contradicts the header claim of multi-step delay before irreversible action; actual host enforcement is outside this method.

Evidence: [pfp/domain/immune/turn_loop_wiring.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/turn_loop_wiring.py:3).
Controls: PFPDOMAIN-C031.
Limit: Only read-vetted local Python owners or explicitly listed isolated AST methods; no EIS, native/provider or host effect execution.

### PFPDOMAIN-F025 — Sealed self-panel loaders do not bind content

SelfPanel.load_canonical trusts supplied content and seal digests after length checks, even nonhex unrelated values, and silently replaces declared count with actual entries count. ThymusGate(sequence_of_entries) seals only entry IDs, so changing contents preserves the seal. This affects custody evidence for the finite negative-selection panel, independently of whether supplied strings are actually healthy.

Evidence: [pfp/domain/immune/thymus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/thymus.py:25).
Controls: PFPDOMAIN-C032.
Limit: Only read-vetted local Python owners or explicitly listed isolated AST methods; no EIS, native/provider or host effect execution.

### PFPDOMAIN-F026 — Parent-child purge receipt accepts an unrelated parent

check_kill_condition never compares clone.parent_id with the supplied parent.rule_id. A matching clone naming actual_parent yields a purge receipt naming unrelated. No deletion occurs in this domain function; a caller honoring the receipt needs its own parent binding and effect authorization.

Evidence: [pfp/domain/immune/clonal_selection.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/clonal_selection.py:276).
Controls: PFPDOMAIN-C033.
Limit: Only read-vetted local Python owners or explicitly listed isolated AST methods; no EIS, native/provider or host effect execution.

### PFPDOMAIN-F027 — Current self-panel content hashes disagree for25 fixtures

Recomputing UTF-8 SHA256 for all1000 stored fixture contents finds25 mismatches. The1000 entries reduce to40 distinct base strings after removing the declared synthetic index/hash suffix, each repeated25 times. The finite fixture corpus is not1000 independent verified proofs; its category labels and Lean-looking assertions do not establish correctness. The loader trust gap in F025 means these mismatches do not trigger refusal.

Evidence: [pfp/domain/immune/self_panel.json](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/self_panel.json), [pfp/domain/immune/thymus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/thymus.py:116).
Controls: .
Limit: No full body reading of JSON, no claim about original generation or every possible seal preimage, no fixture execution.

### PFPDOMAIN-F028 — Ensemble enforces per-member rather than declared total budget

Header promises <=70B total parameters for all ensemble members; constructor checks each member independently. Two70B members from different lineages are accepted for140B total. NaN also passes both positivity and ceiling comparisons. Lineage cap and parameter metadata remain caller-supplied.

Evidence: [pfp/domain/ensemble/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ensemble/models.py:3).
Controls: PFPDOMAIN-C035.
Limit: Small synthetic local inputs; no provider, host authority, actual model-size or deployment behavior evaluated.

### PFPDOMAIN-F029 — Reviewed promotion asserts unperformed holdout passes

CivilizationState.promote_to_reviewed requires only current CANDIDATE tier and returns a reason claiming passed negative-selection holdout banks; it accepts no receipt or test input. The subsequent ADMITTED method correctly refuses all signatures, so this finding concerns false review evidence, not an admitted-authority bypass.

Evidence: [pfp/domain/civilization/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/civilization/models.py:140).
Controls: PFPDOMAIN-C036.
Limit: Small synthetic local inputs; no provider, host authority, actual model-size or deployment behavior evaluated.

### PFPDOMAIN-F030 — Elenchus reports ten checked rules beyond its implemented predicate

Interrogation claims theorem laundering and re-export boundary laundering detection, but the body implements praise/urgency waiver regexes only and always fills all ten PRIME labels as checked. A synthetic text explicitly proposing a re-export shim and ungrounded theorem claim proceeds. This does not establish semantic defense or contradiction extraction.

Evidence: [pfp/domain/civilization/elenchus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/civilization/elenchus.py:40).
Controls: PFPDOMAIN-C037.
Limit: Small synthetic local inputs; no provider, host authority, actual model-size or deployment behavior evaluated.

### PFPDOMAIN-F031 — Decoding modules import absent Result names

antimorphism and token_frontier import Failure/Success/err/ok; polygraph imports err/ok. The owning result module defines Ok/Err/Refusal/Result only. All three exact module imports fail against the pinned owner, before their public behavior is reachable.

Evidence: [pfp/domain/decoding/antimorphism.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/antimorphism.py:11), [pfp/domain/decoding/token_frontier.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/token_frontier.py:12), [pfp/domain/decoding/polygraph.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/polygraph.py:11), [pfp/domain/mssn_research/shared_kernel/result.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/shared_kernel/result.py:1).
Controls: PFPDOMAIN-C038.
Limit: F032/F034 are isolated exact method-body controls with only broken Result imports omitted; F031 records current import blocker. No production package-wide execution or model decoding.

### PFPDOMAIN-F032 — Protected distinctions are not transported by down-map

down_map projects states while retaining original protected pair labels. a/b→x/y passes, then x/y→z passes because the second check still tests a/b. Thus legal successive reductions can collapse the images of a protected distinction.

Evidence: [pfp/domain/decoding/antimorphism.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/antimorphism.py:93).
Controls: PFPDOMAIN-C039.
Limit: F032/F034 are isolated exact method-body controls with only broken Result imports omitted; F031 records current import blocker. No production package-wide execution or model decoding.

### PFPDOMAIN-F033 — Entropy cocycle verification is an unconditional true stub

EntropyCocycle.coboundary_is_nilpotent claims to verify an information-cohomology identity but returns True without any operator. Constructor merely rejects floats; negative degree and a string coefficient are accepted and obtainTrue. No constructed differential or theorem makes this a certificate.

Evidence: [pfp/domain/decoding/cohomology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/cohomology.py:98).
Controls: PFPDOMAIN-C040.
Limit: F032/F034 are isolated exact method-body controls with only broken Result imports omitted; F031 records current import blocker. No production package-wide execution or model decoding.

### PFPDOMAIN-F034 — Probability conditioning accepts negative masked weights

Normalization checks only positive total and retained/candidate probabilities, not global nonnegative base weights. [-1,2,1] with only token2 admitted yields retained mass1/2 and constrained probability1 despite an invalid original distribution.

Evidence: [pfp/domain/decoding/token_frontier.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/token_frontier.py:105).
Controls: PFPDOMAIN-C042.
Limit: F032/F034 are isolated exact method-body controls with only broken Result imports omitted; F031 records current import blocker. No production package-wide execution or model decoding.

### PFPDOMAIN-F035 — DDC incidence export does not honor reversed boundary edges

Complex constructor admits a face whose boundary edge is present only in reverse orientation. Direct d1 handles it with negation, but build_incidence_d1 emits the absent forward edge key. The3-cycle factory with face yields incidence(v0,v2) although carrier has(v2,v0), so exported matrix coordinates disagree with the executable operator.

Evidence: [pfp/domain/ddc/complex.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/complex.py:110), [pfp/domain/ddc/coboundary.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/coboundary.py:51).
Controls: PFPDOMAIN-C044.
Limit: Read-vetted tiny Python controls only; no Rust calculator, provider, cost-bearing operation or disabled cascade substituted.

### PFPDOMAIN-F036 — Lyapunov tracker checks less than advertised descent

Tracker documents V=Phi+Gamma nonincrease on E/M/Lambda, but record_step checks only Phi on E/M and is_strictly_monotonic trusts stored delta. An exact synthetic trace C,E,Lambda with V1,10,19 reportsTrue. This trace defect is separate from cascade.solve, which currently refuses immediately at the unavailable functional boundary.

Evidence: [pfp/domain/ddc/dda.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/dda.py:82), [pfp/domain/ddc/triad.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/triad.py:107).
Controls: PFPDOMAIN-C045.
Limit: Read-vetted tiny Python controls only; no Rust calculator, provider, cost-bearing operation or disabled cascade substituted.

### PFPDOMAIN-F037 — Exact micro-USD conversion rounds through binary float

MicroUsdSpend.from_usd converts Decimal tofloat before multiplying/rounding. Decimal9007199254.740993 should yield9007199254740993microUSD but returns9007199254740994; tiny negative amount rounds tozero. BoundedTemperature separately admitsNaN. These violate the constructors described exact/nonnegative or bounded input contract; no real spend occurred.

Evidence: [pfp/domain/value_objects/numerics.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/numerics.py:49).
Controls: PFPDOMAIN-C046.
Limit: Read-vetted tiny Python controls only; no Rust calculator, provider, cost-bearing operation or disabled cascade substituted.

### PFPDOMAIN-F038 — DDC float ingress can erase a nonzero cochain

_to_fraction deliberately approximates floats with denominator<=1e6;1e-12 becomesFraction0. The module describes exact preservation with zero floating error, but that claim holds only after rational input/normalization. No assertion is made that valid Fraction inputs lose precision.

Evidence: [pfp/domain/ddc/cochains.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/cochains.py:1).
Controls: PFPDOMAIN-C046.
Limit: Read-vetted tiny Python controls only; no Rust calculator, provider, cost-bearing operation or disabled cascade substituted.

### PFPDOMAIN-F039 — Annihilator accepts a false inequality as a refutation

AnnihilatorDecoy.evaluate ignores its stored refutation_witness and only requires supplied evaluation text to contain!=. A matching decoy is Neutralized by the false statement1 != 1. This is marker checking, not refutation or a mathematical annihilator certificate.

Evidence: [pfp/domain/operad/prompt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/prompt.py:220).
Controls: PFPDOMAIN-C047.
Limit: Domain/schema controls only. Outer callers may impose stronger binding/effect checks; no host authority, native pipeline or provider execution occurred.

### PFPDOMAIN-F040 — Null graft bypasses slot typing and changes output colour

OperadTreeNode.graft returns immediately for a NullTree child, before slot bounds or colour validation, and uses child target colour. A RationalValue null grafted at nonexistent slot99 of a RationalValue→TargetResult operator is accepted and returns RationalValue, breaking expected output-colour preservation.

Evidence: [pfp/domain/operad/prompt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/prompt.py:94).
Controls: PFPDOMAIN-C048.
Limit: Domain/schema controls only. Outer callers may impose stronger binding/effect checks; no host authority, native pipeline or provider execution occurred.

### PFPDOMAIN-F041 — Row cardinality does not establish ledger coverage

CalculusReceipt detects too few rows using count alone and never validates distinct original row indices. Two copies of row1 with declared_row_count2 yield PASS under host-carrier authority, even though row2 is unrepresented. The useful uncertainty/refusal precedence works for honest rows; upstream one-to-one enumeration remains required.

Evidence: [pfp/domain/calculus_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/calculus_receipt.py:299).
Controls: PFPDOMAIN-C049.
Limit: Domain/schema controls only. Outer callers may impose stronger binding/effect checks; no host authority, native pipeline or provider execution occurred.

### PFPDOMAIN-F042 — Stage frame binds candidate ID but not selected body or continuation history

StageFrame validates stage4 candidate_id membership among stage2 candidates, but accepts a different candidate body under thatID. A frame can also continue after a prior StageResult.controller_continue=False because that field is not linked to continuation. Synthetic schema control accepts value999 under theID whose stage2 value was1.

Evidence: [pfp/domain/contracts/staged_operad.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/staged_operad.py:26).
Controls: PFPDOMAIN-C050.
Limit: Domain/schema controls only. Outer callers may impose stronger binding/effect checks; no host authority, native pipeline or provider execution occurred.

### PFPDOMAIN-F043 — Adjacent normal-form registry rejects its own nine-entry YAML

The strict index requires ten exact contract IDs including nf.experimental.qm_classical, but the adjacent YAML declares nine and omits that ID. Validation of the exact parsed YAML fails the complete-canonical-set check. The alternate types registry requires nine, leaving callers with incompatible contracts.

Evidence: [pfp/domain/normal_forms/nf_domain_index.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/nf_domain_index.py:29), [pfp/domain/normal_forms/nf_domain_index.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/nf_domain_index.yaml:1).
Controls: PFPDOMAIN-C052.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F044 — BQNF certified repairs omit group and predicate effects

Moving amount 10 from group A to B yields certified new-group delta zero, rather than A minus 10/B plus 10. AVG inserts an unpaid row despite status = paid predicate. The evaluator accepts these boundary declarations yet ignores group relocation and AVG filtering; certified true overstates the finite update semantics.

Evidence: [pfp/domain/normal_forms/bqnf_validator.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/bqnf_validator.py:208).
Controls: PFPDOMAIN-C054.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F045 — Finite meron cancellation admits negative survivors and overwritten sectors

MIC converts sectors into a dictionary without duplicate-ID rejection and does not require nonnegative magnitudes. A single sign +1, weight -1 row returns MeronExactCancellation with survivor sum -1. Duplicate IDs silently change the original signed sum, so declared table preservation is not established.

Evidence: [pfp/domain/normal_forms/quantum_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/quantum_forms.py:230).
Controls: PFPDOMAIN-C055.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F046 — Simplex verifier accepts edges outside its vertex carrier

TSNF builds a zero edge boundary when either endpoint is absent but records no defect. Vertices [0] with edge (1,2) is accepted as TSNF with b1=1. Nilpotency and the algebraically dependent Euler check cannot substitute for closure of the supplied simplicial carrier.

Evidence: [pfp/domain/normal_forms/topology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/topology.py:152).
Controls: PFPDOMAIN-C057.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F047 — Zero-gap verifier does not bind feasibility or objective values

ZFNF defaults absent feasibility to true and never recomputes objective scalars from witnesses. Scalars 7/7 alone yield CertifiedOptimalZeroGap; feasible witnesses with actual objectives 1/1 also certify claimed 999/999. Equal scalars are insufficient to establish optimality of a bound problem.

Evidence: [pfp/domain/normal_forms/tower_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/tower_forms.py:101).
Controls: PFPDOMAIN-C059.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F048 — Hodge exactness accepts a non-gradient labelled vector

DHNF checks reconstruction and pairwise orthogonality of supplied vectors, but never tests whether d0_p belongs to a coboundary image or h to a harmonic kernel. A triangle vector with circulation 3 assigned wholly to d0_p yields HodgeDecomposedExact, although every vertex gradient has circulation zero.

Evidence: [pfp/domain/normal_forms/tower_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/tower_forms.py:209).
Controls: PFPDOMAIN-C060.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F049 — Reconciliation authorizes an unauthenticated verifier label and unsealed loss ledger

An outcome=verified dictionary is treated as an authenticated target verifier. A ledger containing only erased_attributes passes integrity with no entries or digest. Together these yield certified and authorized true for an empty quotient projection. This is a domain return value; no external authorization operation was exercised.

Evidence: [pfp/domain/normal_forms/reconciliation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/reconciliation.py:146).
Controls: PFPDOMAIN-C061.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F050 — Account and currency concatenation aliases distinct reconciliation keys

Reconciliation uses account_id + colon + currency as a product key without escaping or type restrictions. Source pair (a:b,c) and target pair (a,b:c) both map to a:b:c, so equal amounts across different accounts/currencies reconcile and authorize.

Evidence: [pfp/domain/normal_forms/reconciliation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/reconciliation.py:281).
Controls: PFPDOMAIN-C062.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F051 — 5NF projection synthesis invents a lossy cyclic-key decomposition

With candidate keys AB, AC and BC and no declared join dependency, synthesis returns those pair projections precisely when keys do not imply their join. The four even-parity binary triples satisfy all three keys, yet their projections join to eight rows. Cyclic keys alone do not justify the generated lossless-reconstruction claim.

Evidence: [pfp/domain/normal_forms/relational.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational.py:767).
Controls: PFPDOMAIN-C064.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F052 — Relational validators omit heading and single-projection coverage checks

FD chase drops determinant attributes outside the heading, turning Z→B on heading AB into an unconditional merge and accepting the A/B decomposition. check_lossless_decomposition separately accepts a lone projection A of heading AB without checking coverage. Invalid inputs should not receive a mathematical losslessness verdict.

Evidence: [pfp/domain/normal_forms/relational.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational.py:314).
Controls: PFPDOMAIN-C065.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F053 — MVD chase turns exhausted work into non-implication

For heading ABC, decomposition AB/BC and FD B→C, max_iterations=1 skips the FD phase and returns is_implied false; budget two returns true. The result has no unknown/status alternative. This differs from the FD-only chase, which preserves BudgetUnknown for zero budget.

Evidence: [pfp/domain/normal_forms/relational_extensions.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational_extensions.py:238), [pfp/domain/normal_forms/relational.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational.py:472).
Controls: PFPDOMAIN-C066.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F054 — Temporal decomposition drops alternate-key attributes

Given heading ABCD with keys A and B and nonprime C,D, temporal_6nf_decompose returns AC and AD, losing B. temporal_key_attrs is unused. The returned schemas are therefore not even a covering decomposition, before any claimed 6NF or interval semantics are assessed.

Evidence: [pfp/domain/normal_forms/relational_advanced.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational_advanced.py:262).
Controls: PFPDOMAIN-C067.
Limit: Read-vetted finite controls on Python 3.14.2. No provider, native proof, external authority or original-file mutation. Stronger caller constraints may narrow admitted inputs.

### PFPDOMAIN-F055 — Computed stage status is selected without running evidence

stage_status claims to run evidence but only checks a fixed level set; no binding callback or fixture executes. Replacing the in-memory stage35 binding with a raising checker leaves its call count zero and returned/registry status COMPUTED. The grade therefore reports static catalogue membership rather than successful observed evidence.

Evidence: [pfp/domain/tower/stage_status.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/stage_status.py:35), [pfp/domain/tower/registry.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/registry.py:68).
Controls: PFPDOMAIN-C069.
Limit: Bounded pure domain controls; no provider/native run or original mutation. Entry points have distinct scopes, and structural output alone is not proof authority.

### PFPDOMAIN-F056 — Postfix profile bypasses the shared nesting ceiling

Postfix limits stack width but not AST depth. A tiny65-application postfix input is accepted; emitting it to raw wire and parsing again fails the depth64 limit. Accepted transport ASTs therefore need not lie inside the raw bounded codec domain.

Evidence: [pfp/domain/tower/wire.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/wire.py:23).
Controls: PFPDOMAIN-C071.
Limit: Bounded pure domain controls; no provider/native run or original mutation. Entry points have distinct scopes, and structural output alone is not proof authority.

### PFPDOMAIN-F057 — Tower semantic parser accepts degenerate lift and invalid metric declarations

The semantic parser accepts a first uplift with two identical0 generators, while the structural profile rejects it. It also accepts a metric triangle represented by three duplicate foreign edges, and a triangle with lengths1,1,3. Counting positive edge records does not establish complete incidence or realizable simplex geometry. Stronger geometry checks elsewhere are not automatically invoked by this entry point.

Evidence: [pfp/domain/tower/parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/parser.py:282), [pfp/domain/tower/profile.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/profile.py:59).
Controls: PFPDOMAIN-C072.
Limit: Bounded pure domain controls; no provider/native run or original mutation. Entry points have distinct scopes, and structural output alone is not proof authority.

### PFPDOMAIN-F058 — Toy RGB channels retain green after failed re-verification

Both RGB implementations add green on true but never discard it on false. Re-verifying the same ID true then false leaves green present while the stored blue verdict is false. Callbacks are bool-coerced, so the string false is also accepted. Claims and proof bodies are not bound or signed by these sets.

Evidence: [pfp/domain/sn_tower/sn_realizations.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_realizations.py:137), [pfp/domain/sn_tower/sn_verification.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_verification.py:116).
Controls: PFPDOMAIN-C074.
Limit: Toy domain owners only. No external session, host authorization, provider or retained program executed.

### PFPDOMAIN-F059 — Simplex shadow boundary fails on admitted degenerate endpoints

Simplex1 accepts identical endpoints then constructs {v:1,u:-1}; dictionary overwrite yields coefficient minus1 rather than cancelling v-u to zero. The S5 triangle orientation check separately accepts three identical vertices because it only checks boundary tuple length. Distinctness is not enforced in these constructors/checkers.

Evidence: [pfp/domain/sn_tower/sn_realizations.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_realizations.py:13), [pfp/domain/sn_tower/sn_core.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_core.py:111).
Controls: PFPDOMAIN-C075.
Limit: Toy domain owners only. No external session, host authorization, provider or retained program executed.

### PFPDOMAIN-F060 — Dagger checker ignores arrow-label failure of involution

For label f^dagger^dagger, applying dagger twice produces f, while verify_double_dagger returns true because it compares endpoints only. Thus the full dataclass arrow does not satisfy the claimed dagger involution on unrestricted admitted labels.

Evidence: [pfp/domain/sn_tower/sn_realizations.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_realizations.py:102).
Controls: PFPDOMAIN-C076.
Limit: Toy domain owners only. No external session, host authorization, provider or retained program executed.

### PFPDOMAIN-F061 — Single-use session permits repeated sends

SessionChannel accepts two sends in succession before one receive. send only checks is_closed, ignores current SENT state and drops payload. Its state machine enforces closure after receive but not the advertised single-use send protocol.

Evidence: [pfp/domain/sn_tower/sn_applications.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_applications.py:26).
Controls: PFPDOMAIN-C077.
Limit: Toy domain owners only. No external session, host authorization, provider or retained program executed.

### PFPDOMAIN-F062 — Symplectic decoder silently maps nonbinary entries to Pauli Z

from_symplectic_vector applies modulo2 without checking integer/binary domain. Input [0.5,0] for one qubit is accepted as Z, although it is not a vector in F2 squared and does not roundtrip. Valid binary Pauli algebra controls pass separately.

Evidence: [pfp/domain/quantum/pauli.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/pauli.py:118).
Controls: PFPDOMAIN-C080.
Limit: Pure finite owners on Python3.14.2. No candidate dispatched, provider called or external authority exercised. Consumers may revalidate or impose stronger domain restrictions.

### PFPDOMAIN-F063 — Hamiltonian explicit IDs collide with implicit term indices

parse_challenge deduplicates only IDs explicitly present in mapping rows. An implicit first-term index0 and second explicit id0 are both retained, yielding term_ids=(0,0). Consumers that use IDs for witness binding need an additional uniqueness check.

Evidence: [pfp/domain/quantum/hamiltonian.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/hamiltonian.py:184).
Controls: PFPDOMAIN-C081.
Limit: Pure finite owners on Python3.14.2. No candidate dispatched, provider called or external authority exercised. Consumers may revalidate or impose stronger domain restrictions.

### PFPDOMAIN-F064 — Sealed prompt envelope permits stale hash and authority mutation

PacketEnvelope verifies hash and authority only on construction; its model and nested dictionaries remain mutable. Changing candidate x from1 to2 and authority_effect fromNone toGranted leaves the original envelope hash intact. This is a stale seal on the object, before any caller revalidation. The serializer also accepts NaN despite standards-style canonical JSON labels.

Evidence: [pfp/domain/prompts/packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/packets.py:16).
Controls: PFPDOMAIN-C082.
Limit: Pure finite owners on Python3.14.2. No candidate dispatched, provider called or external authority exercised. Consumers may revalidate or impose stronger domain restrictions.

### PFPDOMAIN-F065 — Proposal evaluator certifies strict descent without descent or exactness

Equal masses are admissible and labelled Strict descent verified. require_exactness=True does not prevent float1e-12 being rounded to exact zero; max_proposals=0 does not prevent selecting a candidate. Those config fields are unused. The evaluator checks a tolerance-bounded reported scalar change, not strict descent of reconstructed residuals.

Evidence: [pfp/domain/evaluator.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/evaluator.py:27).
Controls: PFPDOMAIN-C083.
Limit: Pure finite owners on Python3.14.2. No candidate dispatched, provider called or external authority exercised. Consumers may revalidate or impose stronger domain restrictions.

### PFPDOMAIN-F066 — Structured representation does not bind segment text to source bytes

A complete numeric span over source α accepts segment text changed. Two spans may split its UTF8 encoding at byte1. The source hash is correct, but the validator never compares segment text with source slices, contrary to YAML SourceByteFidelity. Numerical coverage is not content preservation.

Evidence: [pfp/domain/prompt_representations/structured_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/structured_prompt_representation.py:70), [pfp/domain/prompt_representations/structured_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/structured_prompt_representation.yaml:26).
Controls: PFPDOMAIN-C085.
Limit: Model/schema boundary only. No provider request or mathematical solver ran. Host compilation and source comparison can impose stronger contracts.

### PFPDOMAIN-F067 — Symbolic and relational formats accept unbound source hashes

Both formats accept a syntactically valid arbitrary source digest unrelated to their span/codebook text. Symbolic also accepts arbitrary legend despite its YAML canonical-legend invariant. Slot totality is real but cannot establish protected query content or source custody; a separate comparison is required.

Evidence: [pfp/domain/prompt_representations/symbolic_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/symbolic_prompt_representation.py:40), [pfp/domain/prompt_representations/symbolic_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/symbolic_prompt_representation.yaml:25), [pfp/domain/prompt_representations/relational_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/relational_prompt_representation.py:52).
Controls: PFPDOMAIN-C086.
Limit: Model/schema boundary only. No provider request or mathematical solver ran. Host compilation and source comparison can impose stronger contracts.

### PFPDOMAIN-F068 — Egraph schema accepts contradictory and overlapping equivalence classes

Classes e9={1,2} and e10={1} are accepted. Neither equality of1 and2, disjointness, sequential IDs, saturation nor preserved constraints is checked, despite model/spec certification language. A referenced class ID is not an equation proof.

Evidence: [pfp/domain/prompt_representations/egraph_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/egraph_prompt_representation.py:1), [pfp/domain/prompt_representations/egraph_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/egraph_prompt_representation.yaml:15).
Controls: PFPDOMAIN-C087.
Limit: Model/schema boundary only. No provider request or mathematical solver ran. Host compilation and source comparison can impose stronger contracts.

### PFPDOMAIN-F069 — Diagram schema admits absent box ports and reversed boundaries

A box input references missing while the only wire runs OUT→IN; the diagram is accepted. Validation checks endpoint names but never ties box input/output declarations to wires or enforces direction. It therefore cannot certify the advertised typed wire-and-box composition.

Evidence: [pfp/domain/prompt_representations/diagram_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/diagram_prompt_representation.py:27).
Controls: PFPDOMAIN-C088.
Limit: Model/schema boundary only. No provider request or mathematical solver ran. Host compilation and source comparison can impose stronger contracts.

### PFPDOMAIN-F070 — Cochain prompt schema accepts nonexistent carrier references

One vertex v, degenerate face(v,v,v), no edges, a cochain on absent→absent, a nonexistent face key and a nonexistent span simplex are accepted together. Rational spelling and endpoint membership do not establish a simplicial complex or cochain domain, let alone its Hodge/curvature semantics.

Evidence: [pfp/domain/prompt_representations/cochain_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/cochain_prompt_representation.py:51).
Controls: PFPDOMAIN-C089.
Limit: Model/schema boundary only. No provider request or mathematical solver ran. Host compilation and source comparison can impose stronger contracts.

### PFPDOMAIN-F071 — Airy floating underflow is labelled exact

Nonzero lambda=minimum positive binary64 and z=1+2^-52 have strictly positive exact rational lambda*(z²-1), but computed residual is0. With other four slots at1, projector empty-obstruction branch labels this exact. Canonical float encoding preserves representation, not exact polynomial evaluation. Large finite overflow controls are separately refused.

Evidence: [pfp/domain/entities/airy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/airy.py:89), [pfp/domain/entities/airy_projector.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/airy_projector.py:89).
Controls: PFPDOMAIN-C091, PFPDOMAIN-C092.
Limit: Read-vetted synthetic local controls with documented unused-import removal or selected unchanged definitions; no native/foreign/provider execution and no repository repair.

### PFPDOMAIN-F072 — Local lab reports controls that it does not run

solve sets packet blockers empty, adapter.sound=True and detector.adequate=True; cases_checked only counts declarations. Synthetic invalid packet validator and inconsistent detector case are never invoked while locally_resolved and evidence_valid are true. Candidate path further uses representative mass comparison without protected-skeleton/retraction validation. This finding concerns this lab owner, with outer gates assessed separately.

Evidence: [pfp/domain/entities/lab.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/lab.py:98).
Controls: PFPDOMAIN-C093.
Limit: Read-vetted synthetic local controls with documented unused-import removal or selected unchanged definitions; no native/foreign/provider execution and no repository repair.

### PFPDOMAIN-F073 — Solver registry identity covers IDs only

Two solvers sharing ID but differing family/version/determinism produce the same registry hash, and identity validation always returnsTrue. Manifests and implementation changes therefore are not attested by this receipt field. Deepcopy isolation does not supply source identity or justify unconditional promotion isolation.

Evidence: [pfp/domain/entities/lab.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/lab.py:139).
Controls: PFPDOMAIN-C094.
Limit: Read-vetted synthetic local controls with documented unused-import removal or selected unchanged definitions; no native/foreign/provider execution and no repository repair.

### PFPDOMAIN-F074 — Evidence bundle builder has unresolved runtime type names

RuntimeProblemIdentityV1.from_problem and build_oesos_evidence_bundle reference RuntimeProblem, and builder references RunReceipt, without an import or definition anywhere in the module. Future annotations defer annotations only; exact-type checks raiseNameError at use. The isolated unchanged builder confirms the first unresolved name. Bundle data parsing remains a separate reachable path.

Evidence: [pfp/domain/entities/oesos_evidence_bundle.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/oesos_evidence_bundle.py:10).
Controls: PFPDOMAIN-C095.
Limit: Read-vetted synthetic local controls with documented unused-import removal or selected unchanged definitions; no native/foreign/provider execution and no repository repair.

### PFPDOMAIN-F075 — Recursive authority scan skips ordinary fields mappings

The visitor skips key fields during every mapping traversal, including ordinary mappings without a dataclass tag. A payload containing fields:{authority_effect:Granted} passes while the same nested authority under payload is refused. Candidate/runtime/event recursive none-authority checks can therefore miss this nested declaration; this does not itself grant external authority.

Evidence: [pfp/domain/entities/oesos_evidence_bundle.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/oesos_evidence_bundle.py:139).
Controls: PFPDOMAIN-C096.
Limit: Read-vetted synthetic local controls with documented unused-import removal or selected unchanged definitions; no native/foreign/provider execution and no repository repair.

### PFPDOMAIN-F076 — Routing update references an undefined terminalizer

TERMINALIZER_ID is used in projector config/skeleton/packet payload but absent from module definitions/imports. Accessing config_digest raisesNameError. Later integration also supplies no raw mass to current lab comparison and calls a missing _apply_verified_local_policy method, so finite search prose is not evidence that this full update path works.

Evidence: [pfp/domain/aggregates/learning_policy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/learning_policy.py:217).
Controls: PFPDOMAIN-C098.
Limit: Selected unchanged local definitions or full module with documented foreign-import removal. No foreign DFA, full artifact execution, original modification or native/provider call.

### PFPDOMAIN-F077 — Learning corpus digest omits metadata-only corpus contents

FrozenCorpus.create accepts corpus_sha256/sample_ids, but digest includes corpus_id and populated runtime cases only. Two same-ID metadata corpora with different hashes/sample IDs have identical digest. Thus this API cannot use digest as a binding to its declared samples, although populated runtime-labelled cases do participate.

Evidence: [pfp/domain/aggregates/learning_policy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/learning_policy.py:52).
Controls: PFPDOMAIN-C097.
Limit: Selected unchanged local definitions or full module with documented foreign-import removal. No foreign DFA, full artifact execution, original modification or native/provider call.

### PFPDOMAIN-F078 — Aggregate research compatibility dataclasses omit entity guards

ResearchSeedPacket/ResearchProposal/ResearchStepPacket in research_claim are distinct unvalidated mutable dataclasses, unlike entities/research_packets. They accept negative budgets/indices, empty claims, parent traversal and Granted authority. FrozenCorpus here also only syntax-checks corpus hash. Names alone do not transfer the stronger entity contract; no downstream promotion was attempted.

Evidence: [pfp/domain/aggregates/research_claim.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/research_claim.py:1168), [pfp/domain/entities/research_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/research_packets.py:221).
Controls: PFPDOMAIN-C099.
Limit: Selected unchanged local definitions or full module with documented foreign-import removal. No foreign DFA, full artifact execution, original modification or native/provider call.

### PFPDOMAIN-F079 — Semantic evidence float tag collides with user mapping

Sanitizing float1.0 yields the same object as sanitizing an ordinary mapping containing $float_hex with1.0.hex(). Hence distinct declared evidence has the same semantic evidence/root representation without any SHA attack. Raw artifact hashes retain the difference, but semantic identity is not injective modulo only declared occurrence fields.

Evidence: [pfp/domain/aggregates/research_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/research_run_root.py:288).
Controls: PFPDOMAIN-C100.
Limit: Selected unchanged local definitions or full module with documented foreign-import removal. No foreign DFA, full artifact execution, original modification or native/provider call.

### PFPDOMAIN-F080 — Closed research terminal guard does not require zero residual

The guard admits FINITE_RESIDUAL_CLOSED with a C,E,I,T sequence whose E decreases2→1 and terminal residual remains1. Native-chain checks enforce decrease/continuity/effect labels but do not require terminal zero or independently recompute equations. OESOS roots are optional; if supplied, their declared exact receipt is checked, not a fresh mathematical replay. This bounds the claim: full artifact replay was not executed and foreign grammar remains a separate assumption.

Evidence: [pfp/domain/aggregates/research_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/research_run_root.py:630).
Controls: PFPDOMAIN-C101.
Limit: Selected unchanged local definitions or full module with documented foreign-import removal. No foreign DFA, full artifact execution, original modification or native/provider call.

### PFPDOMAIN-F081 — Machine reply residual colour is unchecked

validate_machine_reply_fields accepts RESIDUAL_COLOUR=Exact without any dual witness and accepts an arbitrary colour string. The field can be required yet only presence is checked; the declared enum/dual-witness refusal constants do not enforce this boundary. Claimed-result evaluation still retains a separate claim-evaluator obstruction, so this is not a proven semantic promotion.

Evidence: [pfp/domain/aggregates/llm_turn_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/llm_turn_run_root.py:653).
Controls: PFPDOMAIN-C102.
Limit: Actual read-vetted Python modules imported through hash guard; all34 transitive domain imports bound to full-read hashes. No provider/foreign/native import, model calls or downstream promotion.

### PFPDOMAIN-F082 — Host-status block can omit expected candidate and root

With host_status phase and explicit expected candidate/run-root IDs, ABSENT values pass. Comparisons run only when the value is already present and non-ABSENT, so expected identity is not a presence requirement. Proposal-phase ABSENT is separately intentional.

Evidence: [pfp/domain/aggregates/llm_turn_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/llm_turn_run_root.py:739).
Controls: PFPDOMAIN-C103.
Limit: Actual read-vetted Python modules imported through hash guard; all34 transitive domain imports bound to full-read hashes. No provider/foreign/native import, model calls or downstream promotion.

### PFPDOMAIN-F083 — Turn content task_id property references a nonexistent field

A normally bound LlmTurnContentArtifactV1 raisesAttributeError on task_id because fallback reads task_packet_id while its field is packet_id. Explicit_task_id bypasses fallback but is unvalidated/unbound to content identity.

Evidence: [pfp/domain/aggregates/llm_turn_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/llm_turn_run_root.py:215).
Controls: PFPDOMAIN-C104.
Limit: Actual read-vetted Python modules imported through hash guard; all34 transitive domain imports bound to full-read hashes. No provider/foreign/native import, model calls or downstream promotion.

### PFPDOMAIN-F084 — Prompt direct ID override and nested mutability weaken object contract

Direct PromptArtifact accepts arbitrary explicit_artifact_id and returns it instead of computed content address. Strict from_dict correctly rejects the resulting mismatch. The frozen constructor also accepts an open_obstructions list which can mutate after validation and accepts negative hint magnitude. Dynamic digest changes with list mutation; no stale-hash claim is made.

Evidence: [pfp/domain/aggregates/prompt_artifact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/prompt_artifact.py:107).
Controls: PFPDOMAIN-C105, PFPDOMAIN-C106.
Limit: Actual read-vetted Python modules imported through hash guard; all34 transitive domain imports bound to full-read hashes. No provider/foreign/native import, model calls or downstream promotion.

### PFPDOMAIN-F085 — Prompt audit is a fixture-specific heuristic

Nonsingular x+y=5,2x+4y=10 is refused as singular because one literal equation matches; singular x+2y=5,3x+6y=15 is unflagged. Reversed balanced delimiters >< also pass. Coefficient/substring and delimiter counts are not determinant or grammar checks, despite broad allperturbed prompts fail-closed prose.

Evidence: [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py:13).
Controls: PFPDOMAIN-C107.
Limit: Synthetic independent examples and read-vetted gate owner. No retained private benchmark, provider or original source execution outside pure domain functions.

### PFPDOMAIN-F086 — Intermediate witness check accepts negated bindings and unknown checker

The text saying x=1 and y=2 are both false passes the binding regex; an unknown checker with nonempty text also gets ACCEPTED. Neither substitution nor semantic truth of intermediates is tested. This may be a lexical extraction control, but its verified wording is too strong.

Evidence: [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py:720).
Controls: PFPDOMAIN-C108.
Limit: Synthetic independent examples and read-vetted gate owner. No retained private benchmark, provider or original source execution outside pure domain functions.

### PFPDOMAIN-F087 — Graph oracle comparison conflates boolean and integer fields

The graph-facts gate accepts integer1/0 in boolean fields and True as edge_count1 because nested dictionary equality equates these values. It validates required keys but not their types. Trusted expected-answer equality also remains distinct from independent topology checking.

Evidence: [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py:275).
Controls: PFPDOMAIN-C109.
Limit: Synthetic independent examples and read-vetted gate owner. No retained private benchmark, provider or original source execution outside pure domain functions.

### PFPDOMAIN-F088 — Determinant sign-flip fixture and diagnostic are arithmetically wrong

For [[3,7],[2,5]], ad-bc=1 and bc-ad=-1, not-11. The fixture calls-11 a sign flip and runtime reserves that diagnosis for-11; actual-1 receives arithmetic-error code. Both are correctly refused against1, so defect concerns explanation and mutation classification, not false acceptance.

Evidence: [pfp/domain/fixtures/negative_mutation_fixtures.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/fixtures/negative_mutation_fixtures.yaml:337), [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py:669).
Controls: PFPDOMAIN-C110.
Limit: Synthetic independent examples and read-vetted gate owner. No retained private benchmark, provider or original source execution outside pure domain functions.

### PFPDOMAIN-F089 — Pilot aggregate equality bypasses checker type restrictions

PilotAggregate._answer_matches returnsTrue directly for extracted True and expected1, while the linalg gate refuses boolean candidates. Therefore its ACCEPTED invariant does not preserve the checker representation rules as claimed; Python equality short-circuits the fallback. Probe exercises unchanged comparison method, not full state transitions.

Evidence: [pfp/domain/aggregates/pilot_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/pilot_aggregate.py:35), [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py:421).
Controls: PFPDOMAIN-C111.
Limit: Synthetic independent examples and read-vetted gate owner. No retained private benchmark, provider or original source execution outside pure domain functions.

### PFPDOMAIN-F090 — Ladder progression rule accepts a net collapse

H2 retains rates 0.9,0.1,0.2 as progression because it excludes only all-flat and strictly decreasing sequences. This does not establish accuracy rising then saturating.

Evidence: [pfp/domain/pilots/certified_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/certified_ladder.py:469).
Controls: PFPDOMAIN-C112.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F091 — Ladder statistics accept nonfinite and negative evidence

H3,H4,H5,H10 retain NaN inputs because ordered comparisons with NaN are false. DebtMetric accepts negative debt and H6 retains negative failure counts. These arithmetic summaries need finite/range/count premises before their verified prose is justified.

Evidence: [pfp/domain/pilots/certified_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/certified_ladder.py:167).
Controls: PFPDOMAIN-C113.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F092 — Ladder report can pass with no tested hypotheses

H12 retains an empty suite mapping and build_evaluation_report([]) returns PASS with total zero. The report has no H0-H13 completeness, uniqueness or status/refuted consistency condition. This is vacuous aggregation, not evidence of all ladder hypotheses.

Evidence: [pfp/domain/pilots/certified_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/certified_ladder.py:744).
Controls: PFPDOMAIN-C114.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F093 — H0 trusts supplied outcome summary flags

A record with expected REFUSED, pass1 ACCEPTED, pass2 REFUSED, passes_match=True and cheat_accepted=False is retained. The rule never derives flags from statuses, so typed records alone cannot support the claimed deterministic rejection.

Evidence: [pfp/domain/pilots/certified_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/certified_ladder.py:380).
Controls: PFPDOMAIN-C115.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F094 — Equal control items can have unequal Python hashes

P0ControlItem compares payload dictionaries by mapping equality but hashes str(payload), which retains insertion order. Two equal dictionaries in different insertion orders yield equal objects with different hashes, violating Python hashed collection requirements. This is not a stable cryptographic digest.

Evidence: [pfp/domain/pilots/certified_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/certified_ladder.py:221).
Controls: PFPDOMAIN-C116.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F095 — Demo receipt permits contradictory success and authority fields

DemoRunReceipt accepts all_passed=True with a failed CheckResult and defaults terminal_status to Exact; authority_effect also accepts Granted. Schema construction does not reconcile checks, terminal or authority, so a receipt needs external host validation.

Evidence: [pfp/domain/stages/demos.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/demos.py:48).
Controls: PFPDOMAIN-C117.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F096 — Stage7 summary can contradict its validated host replay

WitnessReplay recomputes outcomes and ChallengeReplay enforces dense indices, but Stage7Response accepts a different demo_id, checked_count=0 and empty obstruction_indices while its host replay has one checked open obstruction. The wrapper does not bind summaries to its nested replay.

Evidence: [pfp/domain/stages/stages.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/stages.py:431).
Controls: PFPDOMAIN-C118.
Limit: Pure synthetic controls on unchanged read-vetted functions; no empirical experiment or downstream host integration claim.

### PFPDOMAIN-F097 — Packet atom factory bypasses its wire admission

Packet.atom(z,stage1) validates as Certificate although from_wire(<z>,stage1) refuses the inactive glyph. validate only round-trips and checks declared stage; it does not rerun AST admission or semantic arity.

Evidence: [pfp/domain/mssn_research/packets/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/entities.py:72), [pfp/domain/mssn_research/packets/parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/parser.py:102).
Controls: PFPDOMAIN-C119.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F098 — Quantifier budget trusts declared alternation count

A polarity mask with14 switches passes when alternation_count=0. Two variables each bounded10 pass step_budget10 despite100 Cartesian assignments. Per-variable bounds alone do not implement an evaluation budget or enforce mask consistency.

Evidence: [pfp/domain/mssn_research/grammar/quantification.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/quantification.py:91), [pfp/domain/mssn_research/grammar/quantifier_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/quantifier_policies.py:26).
Controls: PFPDOMAIN-C120.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F099 — Phi4 dimension refusal is bypassed by eager helper evaluation

An empty dual vector triggers IndexError in _check_dual_cycle before the earlier dimension-error Result is returned, because all helper calls in checks tuple evaluate eagerly. A valid exact unit-objective certificate passes; the issue is malformed-input handling, not a demonstrated feasible false optimum.

Evidence: [pfp/domain/mssn_research/grammar/quantifier_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/quantifier_policies.py:70).
Controls: PFPDOMAIN-C121.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F100 — Pending master horizon can exert terminal authority without receipt

A pending proposal with CertifiedTerminal authority and no receipt passes. Receipt-less path returnsOk unless requested green, and pending receipts also lack the red/green authority restrictions. This breaks the claimed proposal non-authority boundary.

Evidence: [pfp/domain/mssn_research/grammar/authority_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority_policies.py:30).
Controls: PFPDOMAIN-C122.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F101 — Ind-object check omits target and relation preservation

A source generator maps to nonexistent target with no target stage record and an unverified text witness, yet passes. Source records are optional and relation_set never checked. Forward/injective labels do not prove a conservative presentation morphism or filtered diagram.

Evidence: [pfp/domain/mssn_research/grammar/authority_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority_policies.py:108).
Controls: PFPDOMAIN-C123.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F102 — Hodge checker ignores declared inner products

A valid Euclidean decomposition with exact=(1,0),coexact=(0,1) passes despite supplied positive-definite M1=[[2,1],[1,2]], for which their weighted inner product is1. All three metric matrices are ignored; weighted adjoints and complex nilpotence are unverified.

Evidence: [pfp/domain/mssn_research/grammar/authority.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority.py:358), [pfp/domain/mssn_research/grammar/authority_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority_policies.py:226).
Controls: PFPDOMAIN-C124.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F103 — Regge checker accepts absent geometry and nonsymmetric Gram

Empty simplices/hinges with supplied negative determinant and closure=True pass without any rotation matrices. Optional [[1,100],[0,1]] Gram also passes positive leading minors though x=(1,-1) has xTGx=-98; symmetry and4D shape are missing. No exact holonomy or length-to-Gram binding is performed.

Evidence: [pfp/domain/mssn_research/grammar/spectral_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/spectral_policies.py:97).
Controls: PFPDOMAIN-C125.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F104 — Zeta exactness check accepts floating coefficients

Coefficients(1,0.5), no traces and no transfer matrix pass with the default exactness flag. Only constant normalization/fence/flag are checked, so exact integer polynomial preservation and spectral correspondence are not established.

Evidence: [pfp/domain/mssn_research/grammar/spectral_geometry.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/spectral_geometry.py:62), [pfp/domain/mssn_research/grammar/spectral_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/spectral_policies.py:24).
Controls: PFPDOMAIN-C126.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F105 — Peak joining verifies string continuity without rewrite validity

Invented rule names/redex locations and unrelated peak apex pass when path endpoints meet. No ruleset/presentation replay or apex-to-branch evidence is checked; this supports endpoint consistency rather than semantic local confluence.

Evidence: [pfp/domain/mssn_research/grammar/rewriting_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/rewriting_policies.py:32), [pfp/domain/mssn_research/grammar/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/entities.py:308).
Controls: PFPDOMAIN-C127.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F106 — DDA proof policy trusts a default true flag

A made-up transition with empty context/receipts, negative declared cost and default has_host_proof=True passes. The checker verifies only truthiness, parent digest length and positivebudget; no host proof, hash or transition replay occurs.

Evidence: [pfp/domain/mssn_research/grammar/rewriting.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/rewriting.py:206), [pfp/domain/mssn_research/grammar/rewriting_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/rewriting_policies.py:98).
Controls: PFPDOMAIN-C128.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F107 — Grammar frontier does not bind emissions or parser transitions

Stage1 frontier accepts emitted z and invented parser-state label when rational probabilities normalize. The arithmetic checks are useful but evaluate_frontier delegates without consulting active alphabet or parsing transitions; grammar licensing prose exceeds this boundary.

Evidence: [pfp/domain/mssn_research/grammar/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/entities.py:81).
Controls: PFPDOMAIN-C129.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F108 — Unsupported finite lift goal raises rather than refuses

Stage0 with DIRECTED_CYCLE_THREE raises ValueError despite public Result return contract. Supported stage0 irreflexive replay and forged-digest refusal both work; the limitation is the unhandled stage/goal cross-product.

Evidence: [pfp/domain/mssn_research/grammar/lift_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/lift_policies.py:120).
Controls: PFPDOMAIN-C130.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F109 — Accepted down-map can break edge involution

A four-edge involution with pairs a-b,c-d projects a,c to x, b to y,d to z. With no protected state pairs the down-map accepts, but its resulting reversal map fails involution. Preserving declared state distinctions does not preserve edge algebra.

Evidence: [pfp/domain/mssn_research/grammar/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/entities.py:502).
Controls: PFPDOMAIN-C131.
Limit: Direct read-vetted domain policies on synthetic bounded values. No claim about external host repair, physical correctness or native equivalence.

### PFPDOMAIN-F110 — Finite structure validator admits wrong-arity out-of-carrier tuples

A unary relation on one element accepts tuple(99,100) via from_json/validate. Tuple relation names and duplicate rows are checked, but arity, element bounds and declared sorts are not. Later hosting may refuse, but this validator is not a complete finite-structure admission boundary.

Evidence: [pfp/domain/solvers/structure.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/structure.py:237).
Controls: PFPDOMAIN-C132.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F111 — Solver admission misses negative form and witness-instance capability

AdmitInst(-1,(0,)) is accepted using Python negative indexing, retaining form-1 in state. Separately, a stage with no item capabilities admits NewInst on an existing witness form because witness_inst is never tested. The latter is an actual capability-boundary omission, not just malformed state construction.

Evidence: [pfp/domain/solvers/regime.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/regime.py:126), [pfp/domain/solvers/regimek.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/regimek.py:137), [pfp/domain/solvers/stage.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/stage.py:34).
Controls: PFPDOMAIN-C133.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F112 — Unknown requirement and truthy native report can satisfy

refutation falls through empty for unknown requirement objects, so satisfies returnsTrue. A synthetic homology adapter returning boundary_law_verified="false" also satisfies through truthiness. Unbound ports correctly refuse, a positive boundary retained; installed adapter outputs still need exact type and certificate contracts.

Evidence: [pfp/domain/solvers/kinds.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/kinds.py:423).
Controls: PFPDOMAIN-C134.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F113 — Extended regime canonical key omits operative data

Holonomy req_json serializes only word and omits tables; canonical_k therefore equates otherwise identical regimes carrying different matrices. It also omits new_forms_allowed, which changes available response classes. These keys are incomplete for operational identity even when structural isomorphism itself is correct.

Evidence: [pfp/domain/solvers/kinds.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/kinds.py:520), [pfp/domain/solvers/search.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/search.py:193).
Controls: PFPDOMAIN-C135.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F114 — Sort pruning can falsely certify finite exhaustion

For unary witness form1 sorted by claimform0 with only datum0 in the sort, a Closure with empty body demands form1(datum1). pruning_sound skips integer head arguments and returnsTrue; pruned search reports CLOSED, unpruned search finds NewInst(1,(1,)) at cost1. Independent count matches the wrong pruned class, so counting alone does not prove sound pruning.

Evidence: [pfp/domain/solvers/search.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/search.py:52).
Controls: PFPDOMAIN-C136.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F115 — Stage certifier accepts fabricated exhaustion and phantom residual

A proposal supplies nonexistent residual ID, fake source exhaustion/family digest, self-declared nontrivial/down evidence and a datum addition that leaves its real requirement false; all11 certify conditions pass. licensed also accepts11duplicate condition1 records, and execute trusts those records under a supplied granted Licence. No source/receipt binding is checked at execution; this is not a claim of bypassing an external authenticated human licence.

Evidence: [pfp/domain/solvers/stage.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/stage.py:243).
Controls: PFPDOMAIN-C137.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F116 — Caller prior score can turn an unchanged state into descent

execute_retraction_turn trusts prior_score. Increasing its active_count by1 and supplying empty delta produces DESCENT with an unchanged child state. Evidence hashes omit actual source regime and port proof, so trusted caller caching must be explicit or recomputed.

Evidence: [pfp/domain/solvers/retraction.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/retraction.py:236).
Controls: PFPDOMAIN-C138.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F117 — Cochain exactness assumes unenforced antisymmetry

Claims c(a,b)=0 and c(b,a)=1 coexist; get prefers the requested orientation. The triangle solver still reports exact coboundary because chosen cycles use only one orientation. The constructor checks Fraction values but not antisymmetry, loops or carrier membership; zero selected-cycle sum cannot certify malformed full claims.

Evidence: [pfp/domain/solvers/simplicial_cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/simplicial_cochain.py:281).
Controls: PFPDOMAIN-C139.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F118 — Gradient guidance misreports reverse-stored edge values

A valid cochain stored as c(b,a)=-2 gives c(a,b)=2, but generated guidance says a->b=0 because it reads the repaired dictionary directly with zero default. The solver itself computes correct oriented values; the prompt guidance loses that representation convention.

Evidence: [pfp/domain/solvers/cochain_gradient_hook.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/cochain_gradient_hook.py:180).
Controls: PFPDOMAIN-C140.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F119 — Hook counts an actual descent as stationary and overstates its comparison

The runner updates current_phi before passing it as prior to record_turn_step. A strict3→2 descent leaves receipt stationary_count0 but hook count1. Its narrowest_claim also asserts hinted prevention for an unhinted one-turn incomplete run; deterministic first-chord subtraction is not observed model behavior or cross-cycle interference.

Evidence: [pfp/domain/solvers/cochain_gradient_hook.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/cochain_gradient_hook.py:220).
Controls: PFPDOMAIN-C141.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

### PFPDOMAIN-F120 — Cochain evidence hash does not bind input claims or trace

Opposite initial triangle cochains produce the same evidence digest when task/id/mode, absolute initial/final sums and turn counts coincide. The digest excludes carrier structure, initial claims, turn records and hook configuration; it is summary custody, not replay source binding.

Evidence: [pfp/domain/solvers/cochain_gradient_hook.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/cochain_gradient_hook.py:387).
Controls: PFPDOMAIN-C142.
Limit: Read-vetted unchanged local owners on bounded synthetic data. No paid/live models, private state, native adapters or external authorization used.

## Per-file coverage

| Original path | SHA256 | Disposition and read ranges |
|---|---|---|
| [pfp/domain/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/__init__.py) | `5d816e837addd480d6aa2f25e88ccabc16ef281ce066f1deecbbdad31e56e19f` | Full body: 1–416 |
| [pfp/domain/admission.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/admission.yaml) | `ea679d2048acc1e5efe2480b9ff57a985c7b3d04640c5dbdd2e42e86807c904a` | Full body: 1–142 |
| [pfp/domain/aggregates/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/__init__.py) | `faabf281eaeb3f2c0414850d06c6866a0cd2373c0f4ad80c735cdf5b4b19d146` | Full body: 1–58 |
| [pfp/domain/aggregates/base.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/base.py) | `a394433d95eb3451ab1430666ad60b0f03e95083213383590e41aa185857b1c2` | Full body: 1–21 |
| [pfp/domain/aggregates/code_change_attempt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_attempt.py) | `1d508f500cc506b7c42b80667ee1a52c0ea13b5a19bb323dbf2b3d1dca9144e0` | Full body: 1–120 |
| [pfp/domain/aggregates/code_change_attestation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_attestation.py) | `c3e64797f7d47c27fe86e986fd1b8550c2540856dd28df6c3024fc193fc9649d` | Full body: 1–135 |
| [pfp/domain/aggregates/code_change_bind.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_bind.py) | `4c90e5912db583422405e2ebba4deed6a9e999187187357ce9ebfe86b2c460e4` | Full body: 1–641 |
| [pfp/domain/aggregates/code_change_gate_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_gate_receipt.py) | `93fd90176ddc734f05ddfd9d76e6c7339c05f86c4531135bbe3ca463069246ba` | Full body: 1–163 |
| [pfp/domain/aggregates/code_change_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_packets.py) | `37cc27ba82414ef1054c7f01b730773377e6e4d5392d37f5dae2a6f9406923ff` | Full body: 1–29 |
| [pfp/domain/aggregates/code_change_patch.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_patch.py) | `b549b91d5bf7e92ebcf7ee3de41fab096474249357812e7d588d95a291dffde4` | Full body: 1–148 |
| [pfp/domain/aggregates/code_change_proposal.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_proposal.py) | `e1bc529aba5fc43f2115d007d340b0d032ea712bbda1be3bf9594d5cef6bfbd7` | Full body: 1–212 |
| [pfp/domain/aggregates/code_change_repair.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_repair.py) | `244fab9d4c2c2ca1b0b5e076bc7973c001d027e186e1d214efe6568bfc8c7f9d` | Full body: 1–92 |
| [pfp/domain/aggregates/code_change_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_root.py) | `09de9d53f54ea520a1230aec8a4e53ee54ee03258dfd4cddcd262e060e69ee44` | Full body: 1–240 |
| [pfp/domain/aggregates/code_change_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_run_root.py) | `e78d118f59e53e96f692484b681cf4583f648e3453269ba674e21a8a1846595c` | Full body: 1–12 |
| [pfp/domain/aggregates/code_change_wire.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/code_change_wire.py) | `0a267470ad324c15e925191299ff25dffcaa9961e807590037568318a5d1e338` | Full body: 1–234 |
| [pfp/domain/aggregates/cycle_balance_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/cycle_balance_aggregate.py) | `01b2eac1d6e58588d9b8ea78413d2f417a1abb9b19d3a7f236442968a12e8b15` | Full body: 1–201 |
| [pfp/domain/aggregates/learning_policy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/learning_policy.py) | `74d17dc28832bc7f7e94504d11c155b2c2bc0543f22984f70375b87f569b268d` | Full body: 1–648 |
| [pfp/domain/aggregates/llm_turn_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/llm_turn_run_root.py) | `bec5ef97c0717292cb4aa1a262b5ccb1716123aa567e65a7dda3ea7cd39fcad1` | Full body: 1–1413 |
| [pfp/domain/aggregates/pilot_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/pilot_aggregate.py) | `71a39799c6f21abe7a5e80826797cdf8261592b89d7718ccad7effc0beb91e32` | Full body: 1–161 |
| [pfp/domain/aggregates/prompt_artifact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/prompt_artifact.py) | `aa7e9315ee45cc3f8b8582c6fbc615689fdaa45b75e248b834a5d2283567546a` | Full body: 1–1035 |
| [pfp/domain/aggregates/research_claim.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/research_claim.py) | `85022c70441952fa7de5b017d69548908cf35e78f84c99a8ed0625cb2826e0c5` | Full body: 1–1477 |
| [pfp/domain/aggregates/research_run_root.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/research_run_root.py) | `19cb82e8d0fa40eace26475f982375fee34c8eda4b58e1dd2ab6565feb4cc8d6` | Full body: 1–1345 |
| [pfp/domain/aggregates/rewriting_aggregate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/aggregates/rewriting_aggregate.py) | `1682aaf86199b167dabf2f020ee151613fb4fb251b6c1772c7adfd8c2b9f9821` | Full body: 1–66 |
| [pfp/domain/ast_cochain/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/__init__.py) | `2e14f204f4ad3338498aaa1b1c7bc0f53127fb20ae5d23069c14a06aaeba96ba` | Full body: 1–52 |
| [pfp/domain/ast_cochain/ast_cochain_extractor.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_cochain_extractor.py) | `3cafafd991dbb763b62e761830dc513cb026e0d8bffef623a9fce7c5390c00ed` | Full body: 1–40 |
| [pfp/domain/ast_cochain/ast_dependency_complex.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_dependency_complex.py) | `3a344b9ba3f20ec60f05163859cf3be2a26e689bb7a3ea24291f7fc90b754c08` | Full body: 1–155 |
| [pfp/domain/ast_cochain/ast_metrics_evaluator.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_metrics_evaluator.py) | `70d4f9d2fd00b7bfd8c38ddac0b7fe9c45e324ee6ac7a852eb0acb97accfd11e` | Full body: 1–55 |
| [pfp/domain/ast_cochain/ast_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_models.py) | `94f06c5132653197f243266e2249c1cb06199ae9f57a7d441817c4f76ca29b19` | Full body: 1–45 |
| [pfp/domain/ast_cochain/ast_source_parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/ast_source_parser.py) | `8fc57d0c438f6a85c2af5b0b325d34ebae150f46d17d9473364504b1cada5922` | Full body: 1–67 |
| [pfp/domain/ast_cochain/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ast_cochain/models.py) | `0ae0611402c7d1bcf07730d262b7b7fc3f26b30b8799ab14b4f6e159e73e3991` | Full body: 1–97 |
| [pfp/domain/biochem/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/biochem/__init__.py) | `dbc40cb443db7e3408349cfa687f09860c95d4ecc089448ed3763d22e8d4fb1d` | Full body: 1–43 |
| [pfp/domain/biochem/allostery.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/biochem/allostery.py) | `a35eb2c2adf82b1d29b2375df247220d8f0dd6d455e9cf273e7eafdbbdbe565a` | Full body: 1–165 |
| [pfp/domain/biochem/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/biochem/errors.py) | `c635b280c11cc8abde553d60df948fbfd7f98faf774fcd5e50d7326fc9c16549` | Full body: 1–37 |
| [pfp/domain/biochem/proofreading.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/biochem/proofreading.py) | `b43424bfbe5ad2990c49cfeee42e96d79e7050857e6e0778635f7cc21b120d8a` | Full body: 1–183 |
| [pfp/domain/bridge/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/__init__.py) | `56ab1508bfb7ee5a9b5ad4e99eb71772de3531cfb4b59dd2cc63a018ab1ffa40` | Full body: 1–64 |
| [pfp/domain/bridge/ast_cochain_extractor.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/ast_cochain_extractor.py) | `bbf8dcb3178c15bc43c3bc751d23a786706b1b8bcc354ceccbd84d10fd5899f2` | Full body: 1–58 |
| [pfp/domain/bridge/ast_dependency_complex.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/ast_dependency_complex.py) | `f00a2855338a49768223bf22eff9d492a762d93db8578bc6123df8c9bf96bb76` | Full body: 1–11 |
| [pfp/domain/bridge/ast_metrics_evaluator.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/ast_metrics_evaluator.py) | `3de1eda5d96bcbea366ffa442464e1ee59af88c50992222948c31b8b7be16bdc` | Full body: 1–8 |
| [pfp/domain/bridge/ast_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/ast_models.py) | `c0f1154a6334e5d9a6330d200c8076848fa3b05f57e8a711e207624659dd8f64` | Full body: 1–9 |
| [pfp/domain/bridge/ast_source_parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/ast_source_parser.py) | `8a53190eae12d30cafe0988fd1e3269c44da7cfa97aedb8137dc63a85e8f77e3` | Full body: 1–6 |
| [pfp/domain/bridge/pharmacy_catalog.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/pharmacy_catalog.py) | `4da8365e2e50921532a028cf76512f2119bf521a93dbc55316700fcdbe448609` | Full body: 1–6 |
| [pfp/domain/bridge/pharmacy_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/pharmacy_models.py) | `95044a23799c31f77b64300beb7ea75e08ea38e5f2545ca56f357a2ddc0ac8c2` | Full body: 1–20 |
| [pfp/domain/bridge/pharmacy_seeder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/pharmacy_seeder.py) | `7e6de1a32476a8288d55bc702c9bc43f9f55c7900326e311cdd991ef174407cc` | Full body: 1–64 |
| [pfp/domain/bridge/pharmacy_templates.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/pharmacy_templates.py) | `9c4f191b462f75784cc8c539685536ebf5c3dc4c897e64b4c46f3b2959f0da1d` | Full body: 1–6 |
| [pfp/domain/bridge/real_evaluators.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/real_evaluators.py) | `19a3c23dd3bcd5f605d35f1faac1e24af4055f6cf5f860026e75c6c736579e66` | Full body: 1–195 |
| [pfp/domain/bridge/sbe.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/sbe.py) | `6332e80010ee8727b92638aa26c918519eac21f7243091b72b654978fab8919b` | Full body: 1–250 |
| [pfp/domain/bridge/sbe_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/sbe_models.py) | `b5f5b6cdfc0e4351db6b21da04cddc5a8e90305c0100b51d57741bae30b7c4eb` | Full body: 1–9 |
| [pfp/domain/bridge/sbe_projection.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/sbe_projection.py) | `fe88f5464f31a896a72a5d5c0f6635eade7ef4b8319cbf1ee9de1e70715a6f71` | Full body: 1–9 |
| [pfp/domain/bridge/symbol_game_artifacts.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_artifacts.py) | `392de3f109b6fec5f8f21b5e23cf1566bc7f16455f44265b9c72f1341b82db33` | Full body: 1–6 |
| [pfp/domain/bridge/symbol_game_dialogue.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_dialogue.py) | `91ab4b7104bd8db5134026fc57676226a9296889731b55866a613abdb1d83089` | Full body: 1–166 |
| [pfp/domain/bridge/symbol_game_emitter.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_emitter.py) | `74e14cbd33cde1ea60187e43968ad370915fc33c840cbeb3b3af52e9582c4e09` | Full body: 1–216 |
| [pfp/domain/bridge/symbol_game_engine.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_engine.py) | `f3d2615b3902713111bbc254be924d7066d67902f8580795a22c7448f63d44ed` | Full body: 1–16 |
| [pfp/domain/bridge/symbol_game_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_models.py) | `5654cba5664adb4db83c234ce9943d7119d27f3f1e416acf0e9198a2b9bbc122` | Full body: 1–36 |
| [pfp/domain/bridge/symbol_game_packet_ledger.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_packet_ledger.py) | `2d32217f17ebaf9038eb3556db2f6259ee13aea3b04989945a39867934ff4689` | Full body: 1–72 |
| [pfp/domain/bridge/symbol_game_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_packets.py) | `82017ec3c242761c3974428a0714c98a9d70057cb5fa7dc1639f9c4dc2593be7` | Full body: 1–125 |
| [pfp/domain/bridge/symbol_game_uns_renderer.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/symbol_game_uns_renderer.py) | `27b3d89865663a1de1eb380aedfa84f3b6cfb4bf1336eac4cf44615d72e7bcfd` | Full body: 1–149 |
| [pfp/domain/bridge/trace_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/trace_models.py) | `31264216fe50d4b1f0b6acb77edd1f2ce8ee75fea402a0b9d39e4d2f64df2495` | Full body: 1–41 |
| [pfp/domain/bridge/trace_policy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/trace_policy.py) | `9e139fa0b8977b3c58633ec69d858385fd32df2e01482c27ff79c8c58e54617e` | Full body: 1–73 |
| [pfp/domain/bridge/unified_oe_trace.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/bridge/unified_oe_trace.py) | `47e77a17d3aac7472b4a513a5ded1a8bc8423ece679a70b93ca97b6d27d3ee69` | Full body: 1–146 |
| [pfp/domain/calculus_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/calculus_receipt.py) | `5aa637897b43ed92fd5b7739e1eb905203fde2c31754e5db15190d46912b5f30` | Full body: 1–419 |
| [pfp/domain/canonical.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/canonical.py) | `579804fdcc5ea66e7e0d0e0378dfff8266251d8f9b1a6d61f8325ee393699ab3` | Full body: 1–276 |
| [pfp/domain/carrier_decoding.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/carrier_decoding.py) | `fbe9721d928460aff54b1072e3bfde77866b23ed6156eabe725901af7574bd39` | Full body: 1–384 |
| [pfp/domain/civilization/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/civilization/__init__.py) | `6941dde2d59133a8594cbec39fa5928f702f538b24552702caf14d59e80b3514` | Full body: 1–26 |
| [pfp/domain/civilization/elenchus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/civilization/elenchus.py) | `c5ff400d68f3859d7279051c4b9929537dd78e029d27fc8895d2fabb5b3c3df7` | Full body: 1–123 |
| [pfp/domain/civilization/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/civilization/models.py) | `7fc083d195db33da65f9fcb07fe8f68e2919e44a48435c9eb126e4d3f1a37f3f` | Full body: 1–216 |
| [pfp/domain/claim_hygiene/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/claim_hygiene/__init__.py) | `6d83724f522a99da6ca2246e6c1b99635b888f3e2af4fc1959c12d35b8b66c77` | Full body: 1–20 |
| [pfp/domain/claim_hygiene/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/claim_hygiene/models.py) | `675e1840e52d08ce72efe8ab97741c256a2229819a9753dbc97244ed471e756e` | Full body: 1–123 |
| [pfp/domain/cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/cochain.py) | `91054aff7f1ac01c3fcb4c5ff397bbce0b97c8272a21eecbf9dc62df2bcbecd7` | Full body: 1–493 |
| [pfp/domain/cohomology/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/cohomology/__init__.py) | `4e5815c7ba0cf2fc0d3f5b2b7d2d79b193e2b02964006244f6fbc0214d4fc047` | Full body: 1–38 |
| [pfp/domain/cohomology/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/cohomology/models.py) | `54edc089b5f813daa439d558a9dc0bc22cebddca426fef95a6fad01fa5bf78a1` | Full body: 1–90 |
| [pfp/domain/contracts/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/__init__.py) | `3c3795dd6c983827a26d74ae6768b2876c4ff407d2612aa3c9d2ee4a08982b4d` | Full body: 1–57 |
| [pfp/domain/contracts/cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/cochain.py) | `1e1f7266e4bdd75a8b70d479d6c0966006fffbaae89e3739d6045c3ae0932f88` | Full body: 1–174 |
| [pfp/domain/contracts/contracts.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/contracts.py) | `1aede1770e82ff1f60dba29cb08c446ebe4ce436504f9390e161bd4a9fd4dd71` | Full body: 1–63 |
| [pfp/domain/contracts/gate_types.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/gate_types.py) | `16ce964b05b96bedee3046618c77f82d68cdb23ee29763be55b791f2a6f31ebf` | Full body: 1–110 |
| [pfp/domain/contracts/gates.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/gates.py) | `609ffdf03f916354144dcbcab8af605bd9fbabcafb2e4e1f0520243070b6d6d5` | Full body: 1–89 |
| [pfp/domain/contracts/pfp_calculations.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/pfp_calculations.py) | `aac96607caf9effbed5703a68311c1070eed22546710c7bc2ee594756260dc5a` | Full body: 1–37 |
| [pfp/domain/contracts/pfp_runtime.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/pfp_runtime.py) | `691b5ba54621962a62d5b369f6cc2059ed12016f46c05cdeaa2065856fcd6832` | Full body: 1–148 |
| [pfp/domain/contracts/schema_register.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/schema_register.py) | `b52daa95a82e1f98e8fcd9a01d1e4ff45dda1d97086e24dfe03adf43b03e7c94` | Full body: 1–71 |
| [pfp/domain/contracts/schemas.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/schemas.py) | `7321f5c04c05453d2b84adc9a353609c32ab8336f4fed61bc4deedf893f0ed91` | Full body: 1–46 |
| [pfp/domain/contracts/staged_operad.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/contracts/staged_operad.py) | `eb049f7ece4e90e4e78aee32bd22360d50310a1de148d7fef5ced8e6536156ae` | Full body: 1–174 |
| [pfp/domain/curriculum/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/curriculum/__init__.py) | `dfaa29ec5990c62751316e129406643ada3785d98de0f578782c809163c054fc` | Full body: 1–18 |
| [pfp/domain/curriculum/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/curriculum/models.py) | `9fe8bef8655d602bad6320214df52a22671183526353513d90c7470c10716fc0` | Full body: 1–42 |
| [pfp/domain/ddc/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/__init__.py) | `4bd491d20e9d5d3ec8e2d63c34b43857ffdd181f41916f11ae93cfce2802ed66` | Full body: 1–74 |
| [pfp/domain/ddc/coboundary.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/coboundary.py) | `e0e94b330ec8796fcbbd9d03542ca282e1f7d82d3335a62574a7a669a05e1659` | Full body: 1–138 |
| [pfp/domain/ddc/cochains.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/cochains.py) | `15e25854ca13b582a75ed157ab91437e6f967708574fca8a72bd52ee64ab813f` | Full body: 1–272 |
| [pfp/domain/ddc/complex.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/complex.py) | `48f863a22512161b3cd0d5887ca01f2b128e251d19e9fa44607abeb87425801f` | Full body: 1–272 |
| [pfp/domain/ddc/dda.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/dda.py) | `849a27384cf0fc140a9a632f4d0c18e4a1bb51772ac88d4a54fb0f4288b0f627` | Full body: 1–433 |
| [pfp/domain/ddc/triad.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/triad.py) | `094a170ecd8b609358d9d2ea3e13fa13d9f47932185eb830f729b3610c4724f2` | Full body: 1–113 |
| [pfp/domain/ddc/visualize.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ddc/visualize.py) | `51644b734912b48ed71790b9249b6a87d4d75b5da689d318b5d50a41706e206e` | Full body: 1–245 |
| [pfp/domain/decoding/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/__init__.py) | `07997256b5c28b0676b7e293093020329aa1eabc084c44fa1de0100d5740851a` | Full body: 1–61 |
| [pfp/domain/decoding/antimorphism.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/antimorphism.py) | `79e599156d37980f7ddcb6cf3607f256241579b56d0ed1195ad0048d14223a1c` | Full body: 1–206 |
| [pfp/domain/decoding/cohomology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/cohomology.py) | `ad3ef2cb72681193c52d68b3d847e49a47744690221e634ced2519b2e327df45` | Full body: 1–208 |
| [pfp/domain/decoding/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/errors.py) | `775c5e76d72f5160ba4c43162474eec603609f7a37d188488cec1b6a8c0c627e` | Full body: 1–69 |
| [pfp/domain/decoding/polygraph.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/polygraph.py) | `e49fe82d6da5b3152bb7ef06398c4a5779c809f97a1d786c528c0af32ac89a40` | Full body: 1–209 |
| [pfp/domain/decoding/token_frontier.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/token_frontier.py) | `6957ab5c07c2c4e2a35c0a447cfb2056ac88651c466024297d342a18d66bbcfb` | Full body: 1–270 |
| [pfp/domain/decoding/vocabulary.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/decoding/vocabulary.py) | `c5b3b99290a19683b9dea10535ef420cb91545620d6a74665e71905199db3533` | Full body: 1–114 |
| [pfp/domain/demos.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/demos.py) | `9a812696195725ba4c7fadd4d8b3d3bf3603ea1b8db9837f9768b49213dbbf92` | Full body: 1–80 |
| [pfp/domain/diff_parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/diff_parser.py) | `5457e1df7c00b8d6e6ad0439f10920628ab3d356f7386ce10f469d4dde93f88c` | Full body: 1–291 |
| [pfp/domain/documentation_integrity/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/documentation_integrity/__init__.py) | `b664cdbb48d03019d0c6aaa47449430c72205c117998e9be54c55f2168b23aa3` | Full body: 1–20 |
| [pfp/domain/documentation_integrity/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/documentation_integrity/models.py) | `d497f0ad78764258ca2833348dd56ca6a779956416fe8ccd22d4d3cdb74e6cf2` | Full body: 1–61 |
| [pfp/domain/documentation_integrity/policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/documentation_integrity/policies.py) | `b189314352e93bab836f912857b01aaed0d97893b72e12d61f6f5d9e81ee6564` | Full body: 1–44 |
| [pfp/domain/documentation_integrity/ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/documentation_integrity/ports.py) | `c1e5da22035b40aac779af6bd2993c275a4b437cf7f06b708985a6f72e841c2f` | Full body: 1–37 |
| [pfp/domain/dual_witness/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/dual_witness/__init__.py) | `6a0f07375c1c0f04a8ca7e6640cf7428c75d3d82298aa8ecdddc18a626c6bc8c` | Full body: 1–12 |
| [pfp/domain/dual_witness/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/dual_witness/models.py) | `6ec1d752cdf73cfe3b116957fa0b0a286bbd0aeb4d0964614f01c0b99f5dc3aa` | Full body: 1–142 |
| [pfp/domain/ensemble/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ensemble/__init__.py) | `35d3ddbade3864cc009616f77bc8dd342c4b558d8a6cb0e924203286cc31f2cf` | Full body: 1–19 |
| [pfp/domain/ensemble/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ensemble/models.py) | `affc40924c9d9828e7f8e9dd3a86b328f9747e3f048a43fd196581b9b00bcb9d` | Full body: 1–182 |
| [pfp/domain/entities/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/__init__.py) | `0f29c2f07d31fc7f26ed1414f21799f9b03f7d0a8f623bb6247187cf0d115bf9` | Full body: 1–94 |
| [pfp/domain/entities/airy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/airy.py) | `3df6b0a2bf8851acb7d3281f5878cef551668d063d97af142fc13cad4df05c45` | Full body: 1–182 |
| [pfp/domain/entities/airy_projector.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/airy_projector.py) | `b01e3bc105acdf2cd44bc72387c7814f5627bc587b7e06d6e093a7eedadcadad` | Full body: 1–141 |
| [pfp/domain/entities/base.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/base.py) | `a99826e4fe408eccab28d9ef345c20a6f20d75f1aa3eafa9009abb8228687e58` | Full body: 1–32 |
| [pfp/domain/entities/candidate_artifact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/candidate_artifact.py) | `6b8793469f350dd06286ba38619e2f3af7962f83b49f18cf64a7a791723369d2` | Full body: 1–251 |
| [pfp/domain/entities/coboundary_score.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/coboundary_score.py) | `842d7bb043a79b1e0b206a128a976df36fe4a287ffb2134e738d1271d2c86bd7` | Full body: 1–331 |
| [pfp/domain/entities/cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/cochain.py) | `bb5285913ab06c53c6a894aba6599a6123a0dde3023408033b761a8f1d3b81b5` | Full body: 1–86 |
| [pfp/domain/entities/cochain_projector.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/cochain_projector.py) | `84fb2ca5b549b02c9ccd5a04fd0359f2e18b099d0af928d7b136a87166f7bc3d` | Full body: 1–120 |
| [pfp/domain/entities/cycle_balance.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/cycle_balance.py) | `2de5c0ce63ea1df18daea2b8e8c284fa684afec6223f7930134a35afd28c6482` | Full body: 1–350 |
| [pfp/domain/entities/gate_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/gate_receipt.py) | `b1fa3ff1bc0b829fe9273d60b52945937506257327e97aeb26421ffa27fc89cd` | Full body: 1–76 |
| [pfp/domain/entities/lab.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/lab.py) | `523d252e95b891e7889c7f73f3e000f0742cbe6257b6a098fadc9a73a7e4d5a2` | Full body: 1–291 |
| [pfp/domain/entities/obstruction.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/obstruction.py) | `df9648231056159be208fe4ca753af3c0e853ea927c9f7f8c5b25c4564d372cd` | Full body: 1–202 |
| [pfp/domain/entities/obstruction_ledger_event.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/obstruction_ledger_event.py) | `f90b8a9d9116ee426f02e1a1f2c3c24a39cb5e2a568230f1af08bcc87585d80c` | Full body: 1–7 |
| [pfp/domain/entities/oesos_evidence_bundle.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/oesos_evidence_bundle.py) | `3f8726ced6df162ed2007f0a7563619a14bd81124a54eb4ff4a27ff4c0435f26` | Full body: 1–766 |
| [pfp/domain/entities/packet_envelope.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/packet_envelope.py) | `d42a69bd8fbbd2af98f0fb1c9a979c13803229b0c19a8a39cb444f2000bedb9c` | Full body: 1–493 |
| [pfp/domain/entities/problem.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/problem.py) | `a7ca88999a6670d77d09c7b1398ceae4cdd5e3ce363b5f43149aacc71af15a2a` | Full body: 1–231 |
| [pfp/domain/entities/process_event.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/process_event.py) | `f89b9b64b96f1070736a8a22ee0f99cbe438bf2f4025113a2ba251318a82ed7f` | Full body: 1–11 |
| [pfp/domain/entities/projection_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/projection_receipt.py) | `255f0d8221f15765a1471b9aa5e8be64ce4042dc123f6db5294f4f41c69a50e9` | Full body: 1–157 |
| [pfp/domain/entities/research_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/research_packets.py) | `1dcb0842d9b991425b58bc571b467b71ee8d4b2ecf55d7b00c964f52f3a064b6` | Full body: 1–401 |
| [pfp/domain/entities/source_artifact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/entities/source_artifact.py) | `2cc64279e35b9a21f8643363c50ebc5100e2eaa2894d5c828048d42b0a0de964` | Full body: 1–21 |
| [pfp/domain/errors/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/errors/__init__.py) | `61e91c029b2dcee98405f5adaa10e2fbd808a807555094919a19794c6944182f` | Full body: 1–39 |
| [pfp/domain/errors/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/errors/errors.py) | `b192ede252f0ada044e04090ef5a94d13740038f0d08a16f05a337ce895402a6` | Full body: 1–49 |
| [pfp/domain/evaluator.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/evaluator.py) | `28567553810ec4773e24e317665754c977131c26be05d97a201dbe8f9f9de52c` | Full body: 1–165 |
| [pfp/domain/events/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/events/__init__.py) | `f6147e26531302025933342f43355e58632272cbf1c7ea9546616f08948f24e4` | Full body: 1–19 |
| [pfp/domain/events/events.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/events/events.py) | `03f8ce9af8feaaa3f7bee2dbc6b19a4b88083cd06a350cb84129a68c94d4b9a0` | Full body: 1–87 |
| [pfp/domain/exact/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/__init__.py) | `93458c67e1f8bd82bbcaf685c6a9ce8f97bbcc9ada9b2790cf6ffba2c187fa9b` | Full body: 1–62 |
| [pfp/domain/exact/alg.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/alg.py) | `7b11f457e4dde54646e2fe640e30836e1b8a736137cdc6208d2eca6f2585a469` | Full body: 1–161 |
| [pfp/domain/exact/digest.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/digest.py) | `37bceff8e68e9b5606a32d97d477b17fe9ba289b652f67594f5a7917a79c77aa` | Full body: 1–71 |
| [pfp/domain/exact/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/errors.py) | `c5b3480bc566982069e759d397033779091da76ceba2c50b647226f0c4e53b0f` | Full body: 1–25 |
| [pfp/domain/exact/linalg.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/linalg.py) | `2b96b628cda0fc5ad223b6a040fe53aff0b1eb17e19bc00a08c7c744a9327abe` | Full body: 1–130 |
| [pfp/domain/exact/poly.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/poly.py) | `054e76f14e87586e43534e19dc7942340f94e258e7d38253d88293d923abad04` | Full body: 1–160 |
| [pfp/domain/exact/wire.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/exact/wire.py) | `c7817f0cda296b3ca23b1b166389cc0df3a1a698f137ef24e9785ce4c0a4ad04` | Full body: 1–102 |
| [pfp/domain/finite_gauge/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/finite_gauge/__init__.py) | `4c94d96654ca5d2ae70c9c27667033fadf9cb2d715af701e0cafab9ed0582bf8` | Full body: 1–32 |
| [pfp/domain/finite_gauge/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/finite_gauge/models.py) | `5acd095e80b013f62e647a6e447ad1421ce8f540b46c16ddd4b134cc9053ca65` | Full body: 1–246 |
| [pfp/domain/fixtures/negative_mutation_fixtures.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/fixtures/negative_mutation_fixtures.yaml) | `a9e1677cc86ede7681661c299fd53f78d8460ef710b5c0e6766f599498ded3dd` | Full body: 1–390 |
| [pfp/domain/fixtures/three_role_provenance_fixtures.json](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/fixtures/three_role_provenance_fixtures.json) | `af8d5e17b448cab5146476c385cbe590888fa7e7af06b05aa541b6ce562715f5` | Full body: 1–583 |
| [pfp/domain/genesis/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/genesis/__init__.py) | `b11bfe415b2362ce71b9c93a8cb202432d04c3a9a2463a8f3ac2762db3bc2d3d` | Full body: 1–14 |
| [pfp/domain/genesis/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/genesis/models.py) | `db22e8fa800d1d48ffa432d5a3b2e954f11f2a88f907a382502d6337a69bacb2` | Full body: 1–87 |
| [pfp/domain/glyph_calculus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/glyph_calculus.py) | `802ecbd2491b26d82e4240e205af4419ab0af878cf195422fae60ec405749672` | Full body: 1–349 |
| [pfp/domain/homology/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/__init__.py) | `759b903e06bb15e0b4269fa219b5c1d4da1bd2bedb6ff0dde580b9233e1514d7` | Full body: 1–54 |
| [pfp/domain/homology/carrier.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/carrier.py) | `6f7d90fa85f3e7305ff500ca0018d66a78330a6e9551cc1a429c785cedd18f0c` | Full body: 1–85 |
| [pfp/domain/homology/cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/cochain.py) | `0806de070dfb7a11ce7200b7efb1c7a69212180fc148472a7e13708638d77166` | Full body: 1–162 |
| [pfp/domain/homology/cycle_balance.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/cycle_balance.py) | `f298b643a0be437d9aa286106b3c9b02179d7303017225af43ee305744d45a80` | Full body: 1–240, 241–427 |
| [pfp/domain/homology/ddc.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/ddc.py) | `3eb969ed19db2a08cc84e890766d5ea90df9f67dd04b28338c414c34da4df2a6` | Full body: 1–74 |
| [pfp/domain/homology/qddc.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/homology/qddc.py) | `7377aa76acba01960fc3c68970674b05068e5f06b44446345c8b31a9ae705e70` | Full body: 1–154 |
| [pfp/domain/immune/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/__init__.py) | `27b56fa50d829e0ae1c02a2687a3eaf99c8f6265b2cbb551c077fd129655c72c` | Full body: 1–98 |
| [pfp/domain/immune/allostery.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/allostery.py) | `4a22cc7a270475358bdf8e3d1b0ac1319787597736c681d8df806f04a5bf4919` | Full body: 1–64 |
| [pfp/domain/immune/clonal_selection.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/clonal_selection.py) | `ec8392a7894b2fddd84fbb9c8f5264b28ce6484d25df41b6b784a82d3f7f107f` | Full body: 1–373 |
| [pfp/domain/immune/complement.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/complement.py) | `80c274d3a0a7d1c118cbaf0d36cfdbd7523a1d0b097766a13e9991dd8cbb726e` | Full body: 1–70 |
| [pfp/domain/immune/danger_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/danger_gate.py) | `946bb772a8542b886ddcd0c4ab27ad3fee90bedea10aa673f09fe7c192748d97` | Full body: 1–290 |
| [pfp/domain/immune/mhc.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/mhc.py) | `acfc0066384a7e73e3ea220c9c410142afc571c56c9c75fc0dec2e42d047af62` | Full body: 1–55 |
| [pfp/domain/immune/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/models.py) | `2bcde05acc336853219878ea35300d1b9a57c6c79057c3ce461594ac2fa7dc09` | Full body: 1–250, 251–651 |
| [pfp/domain/immune/proofreading.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/proofreading.py) | `b8ba349debf5faf86f3030bb52e23fa77196ff21cefc417511a2e5a390a3c65a` | Full body: 1–35 |
| [pfp/domain/immune/thymus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/thymus.py) | `3e31c4893979725e24e2b9ae666c946fc662b316514becfa3db13b662f5dfc54` | Full body: 1–416 |
| [pfp/domain/immune/treg.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/treg.py) | `ff9ad583cb724cf2562ad5ea08a43d6f9d3927ae2f923f21ecc42820ad280ec0` | Full body: 1–24 |
| [pfp/domain/immune/turn_loop_wiring.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/turn_loop_wiring.py) | `c4d932f8b28683b067b0b62eca3297832b87f06f266a917512b5df5f088d9ca1` | Full body: 1–134 |
| [pfp/domain/invariants.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/invariants.py) | `7e29e5cb0e298aa767aaba21a5a7d7fb036cee9f4bbc5be7800e54a12dfe692b` | Full body: 1–120 |
| [pfp/domain/kernel/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/kernel/__init__.py) | `763edf9cff61c8e44bf0de559effc5182d5680398636934bab89bf720bf4b401` | Full body: 1–48 |
| [pfp/domain/kernel/ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/kernel/ports.py) | `1bf0032d484e8e0c78de23923b820776c65e8f924882d505003443a53cef7589` | Full body: 1–147 |
| [pfp/domain/kernel/result.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/kernel/result.py) | `d33fbf1395041d4736f73c15347d58d937080d9753a01aa63d7728bdf6f315ff` | Full body: 1–241 |
| [pfp/domain/lean_bridge/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/lean_bridge/__init__.py) | `8bc055991b2545c6adb9643178cbb9d56010f1afc8bdbb7e942b11e400b7704d` | Full body: 1–16 |
| [pfp/domain/lean_bridge/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/lean_bridge/models.py) | `565aa731803674349a4b08121716853b84ccc2b4d2e91d4c10927168c0d2a19c` | Full body: 1–112 |
| [pfp/domain/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/models.py) | `202239622c9123c46c14b9158be55d52cc61643f9eaab05075a12fcb003da460` | Full body: 1–333 |
| [pfp/domain/modes.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/modes.py) | `7adab7fd2582f8b541c569f892177e7ca02119e6554f7aaa5fa47aca160d07af` | Full body: 1–72 |
| [pfp/domain/mssn_research/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/__init__.py) | `0bae81c461ab927cdf2ef4ece6730c4c456a4290db1003da1bf0830413830b56` | Full body: 1–1 |
| [pfp/domain/mssn_research/grammar/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/__init__.py) | `368e403a7c7c8e26c724396e750129874f217281b1b7c38e320e81f94e099b67` | Full body: 1–5 |
| [pfp/domain/mssn_research/grammar/authority.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority.py) | `4fe8266295c654451876d694dfdc64737d8975df3fdb384e48df2277c24b6b6e` | Full body: 1–401 |
| [pfp/domain/mssn_research/grammar/authority_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/authority_policies.py) | `1a768be921ada6260163d61703ecc7b06b18d2821a5590d229939236196e6e7f` | Full body: 1–358 |
| [pfp/domain/mssn_research/grammar/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/entities.py) | `e05e1f87f662695728857ca654aee79c333040b652eb5a164a72acff415c5e4c` | Full body: 1–270, 271–545, 546–802 |
| [pfp/domain/mssn_research/grammar/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/errors.py) | `b11b1eba3cdca6cf41c32bc9180d53a8cb54e8fb25e78824228b5330cc41ee0e` | Full body: 1–183 |
| [pfp/domain/mssn_research/grammar/exact_structures.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/exact_structures.py) | `2043edb148f01461500c3b29532a2062e97d5f476e2382eb9cc00e4f86329b39` | Full body: 1–618 |
| [pfp/domain/mssn_research/grammar/foundational_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/foundational_policies.py) | `c302becd398afdfc5fb2ecc5665ff0cdebb330b659897250e2ca0b3c6e22dae9` | Full body: 1–272 |
| [pfp/domain/mssn_research/grammar/lexical.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/lexical.py) | `dccc1aca533f3c4b44bb9c87b371dedc5327f6c38f024d804fc9094289c26898` | Full body: 1–253 |
| [pfp/domain/mssn_research/grammar/lift_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/lift_policies.py) | `d2e010768708d456031486a672f1f9218fd98bd451adb2164cb4f1caf04dd877` | Full body: 1–361 |
| [pfp/domain/mssn_research/grammar/ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/ports.py) | `05aa95cfeac9b5c0b01472f66ae55a4f56244982c48fe4de1faf6271dce1632e` | Full body: 1–27 |
| [pfp/domain/mssn_research/grammar/quantification.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/quantification.py) | `1beea02da28a5ed17556e3ce70f8cd51ed29c3f13b31d20196fb8996a4c0035a` | Full body: 1–233 |
| [pfp/domain/mssn_research/grammar/quantifier_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/quantifier_policies.py) | `d801f80b1257ea4d3a12927b00ef995481a914749d3b2aacf968028f68ac5568` | Full body: 1–155 |
| [pfp/domain/mssn_research/grammar/rewriting.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/rewriting.py) | `97128bdd6584ea79314806dd28d7b4e500246eabf1bac0994f23fe258f257120` | Full body: 1–395 |
| [pfp/domain/mssn_research/grammar/rewriting_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/rewriting_policies.py) | `2efe8af28284c4922cd78c8203c6d6d498e140d27ce224dd3be35cc0a666a222` | Full body: 1–209 |
| [pfp/domain/mssn_research/grammar/spectral_geometry.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/spectral_geometry.py) | `805d49d08a3b7b62e6f20472ed9dc463575d8d2f29ee62be85a0b097c3b47a2f` | Full body: 1–344 |
| [pfp/domain/mssn_research/grammar/spectral_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/grammar/spectral_policies.py) | `36bab2ae42b79bd35a56f3ebb966d321f24f28038246f7ffef1f72f6a0360470` | Full body: 1–152 |
| [pfp/domain/mssn_research/packets/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/__init__.py) | `b8864c63b38f4870bc0e72ed5bd3cd4cf6024ee6dd38f4236b41bee4fa332a80` | Full body: 1–1 |
| [pfp/domain/mssn_research/packets/entities.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/entities.py) | `d77c2ff7f9e1c08020986e97d1cc36f0a048b82c8c41df319e3bb318ae5918bd` | Full body: 1–189 |
| [pfp/domain/mssn_research/packets/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/errors.py) | `b2dd36d7c78fd657fc9d7e7d11314f6f46fb3992c4f05d3be9b7925640fc407e` | Full body: 1–43 |
| [pfp/domain/mssn_research/packets/invariants.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/invariants.py) | `c9e8aa83c45add59940ce83742f2d2b8ab10b075bb4349d3a62a985f955acc92` | Full body: 1–130 |
| [pfp/domain/mssn_research/packets/parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/parser.py) | `85d8aca7303683ca1a036b4ae280181aab9cb6cea66b1d08a16b38c5a4f8b737` | Full body: 1–176 |
| [pfp/domain/mssn_research/packets/value_objects.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/packets/value_objects.py) | `8542de5b5827606b3765d2d66cbc569d9351a7ce9a73aa2dece579c6c142b0d9` | Full body: 1–164 |
| [pfp/domain/mssn_research/shared_kernel/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/shared_kernel/__init__.py) | `e945ab4538191da67f6a7dd89c5b935d00b35eb0625b3d8285c151309dd99896` | Full body: 1–1 |
| [pfp/domain/mssn_research/shared_kernel/result.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/shared_kernel/result.py) | `e73da3906755d9945b9a63dd553764632f1c4a70add5a34701554bb77c090d9d` | Full body: 1–113 |
| [pfp/domain/mssn_research/shared_kernel/value_objects.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/mssn_research/shared_kernel/value_objects.py) | `e28e9c0ffa64592c02d39007c480eed0d069ef13eec31d86d762448706153b0e` | Full body: 1–160 |
| [pfp/domain/normal_forms/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/__init__.py) | `50506dd71764d4bcafb321869d2a5e3d8722f57ef65936829ffa227b3d2071b0` | Full body: 1–54 |
| [pfp/domain/normal_forms/asrf.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/asrf.py) | `38f1cb6949ee16b76b431246c077385be4374a3cb948fa4ee4fa66fbbb031ac1` | Full body: 1–189 |
| [pfp/domain/normal_forms/bqnf_fsign.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/bqnf_fsign.py) | `f1cd933b9ff4730c5fecddc9ba431bce70dbcc7c1563a65e3dc67cf1d7fdad77` | Full body: 1–571 |
| [pfp/domain/normal_forms/bqnf_validator.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/bqnf_validator.py) | `3b07e5e0c1f5fe32e6e3e195c6fcf0ae1a825cf9bcd1212b520a3fc1920d8caa` | Full body: 1–326 |
| [pfp/domain/normal_forms/contract_validation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/contract_validation.py) | `1a133504838581215c74fec60459ea3b4402269cbc2170b60173887f8c130e2f` | Full body: 1–322 |
| [pfp/domain/normal_forms/contracts.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/contracts.py) | `24df4ab5829441822508029cdfe4e0e7ce311d70ea0de7d35581d4a905164d7f` | Full body: 1–94 |
| [pfp/domain/normal_forms/examples.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/examples.py) | `cd7e577b38568fc362cf96ad7d664f683aa1279bef609551f0a8f3fdd8f1fa82` | Full body: 1–66 |
| [pfp/domain/normal_forms/fixture_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/fixture_ports.py) | `212f35875ef0a1273a21acedef8110775486eeba23dc154b8c5f775800b49dda` | Full body: 1–55 |
| [pfp/domain/normal_forms/nf_domain_index.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/nf_domain_index.py) | `e48049d766e18c6872ade353f52637736751dbf3bbed0c6cd5604ecc3be6cc30` | Full body: 1–100 |
| [pfp/domain/normal_forms/nf_domain_index.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/nf_domain_index.yaml) | `9cfcd40455d85fdd0c0a2c28594ac4afda98fe4e63a4bf41d484b597abae402b` | Full body: 1–59 |
| [pfp/domain/normal_forms/quantum_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/quantum_forms.py) | `7d88bfb349531689834fe6198ba689c87f15c7ed2e0a8564ff57ba28aca20314` | Full body: 1–469 |
| [pfp/domain/normal_forms/reconciliation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/reconciliation.py) | `7b5d311c14bc1c6b0e6e552f0442142275e89e38b185842a62b9edf4f62c9a50` | Full body: 1–399 |
| [pfp/domain/normal_forms/relational.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational.py) | `9238df7ef4d0d152831c16029afc319114f40ec320d2b5052dc680f2f678dab1` | Full body: 1–220, 221–1027 |
| [pfp/domain/normal_forms/relational_advanced.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational_advanced.py) | `f5a21448c9fe8c326796d4a612efa6269c526775e1284c3de3ebc0ea12f880d1` | Full body: 1–303 |
| [pfp/domain/normal_forms/relational_extensions.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/relational_extensions.py) | `a772b1d78e4827528fc0282f51d2c83bac661b1fafca2e3304afc5a59b0629d7` | Full body: 1–503 |
| [pfp/domain/normal_forms/topology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/topology.py) | `c4b9d1d6cc41a989069f93cae8e4cd996fcec29589b60b47115109c70974ed6a` | Full body: 1–372 |
| [pfp/domain/normal_forms/tower_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/normal_forms/tower_forms.py) | `933b2c69040761a2489257c8d8f7b7ec5106a220d5040b9e16ab057582649792` | Full body: 1–245 |
| [pfp/domain/operad/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/__init__.py) | `9ab96e332765e2fbb1588d3ea7e3ed9923bf734b624cb1856db107f9789ecae8` | Full body: 1–61 |
| [pfp/domain/operad/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/errors.py) | `aed311a837c914ce30ac080cdcf189d50e59c138533e13211c3ab9d6819901f4` | Full body: 1–62 |
| [pfp/domain/operad/graft.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/graft.py) | `6213916ac0550ad54ad29bd18b92a2d891c7c9a9bb7ff65145de2236a352dc02` | Full body: 1–105 |
| [pfp/domain/operad/morphisms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/morphisms.py) | `3ab6cf9b1e8f3a16132dee0731d739013fbf19b5990cf804ad556afd5bca699c` | Full body: 1–235 |
| [pfp/domain/operad/operad.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/operad.py) | `9a05ebba8d13c5632277c3b02c361bc7bfbcc575cdb41e93444209e7491ae85d` | Full body: 1–151 |
| [pfp/domain/operad/polarity.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/polarity.py) | `1c693a3e51b8487f8f3b51705e0b49b9f377f9e45c4570fee86b4141d6e08f82` | Full body: 1–41 |
| [pfp/domain/operad/prompt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/operad/prompt.py) | `07d67562c62a325ece2cf9b4229ab671e47b18906939fcfab3e8e1eaaf57844a` | Full body: 1–306 |
| [pfp/domain/packet_codec.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/packet_codec.py) | `3ea6661c9ce87d57ec7a43dd854c336bc113e3eb3992066e14a7dd89a6896204` | Full body: 1–139 |
| [pfp/domain/pfp_ingress.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pfp_ingress.py) | `5f5345a791f65c475544c93c44c7965937c8b3ab68d415c21d746c41b522a98a` | Full body: 1–65 |
| [pfp/domain/pilots/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/__init__.py) | `7fc53aaa99ba1594ba791d2339530a38af7b52532a9c02d0bb9f18696cd4f55c` | Full body: 1–71 |
| [pfp/domain/pilots/certified_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/certified_ladder.py) | `5fcda31d5960dcb48bbb3081033e77d05169c262af424dcd4c63de8f458673ec` | Full body: 1–812 |
| [pfp/domain/pilots/dimension_models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/dimension_models.py) | `27377e80739011ef2e4212ac52914c583a5a4c962fac289331f1888dac710919` | Full body: 1–147 |
| [pfp/domain/pilots/fail_closed_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/fail_closed_gate.py) | `59d9dfd9736307ae142f19e70ed3910a22ff2b38b2b0d5e16ce89f7c19ec9ca8` | Full body: 1–761 |
| [pfp/domain/pilots/management_ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/management_ladder.py) | `7f8c72aa8ce975d92670a973d8887e297409af72a31282927529485b11e13eb4` | Full body: 1–112 |
| [pfp/domain/pilots/pilot.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/pilots/pilot.py) | `187c31e67a6378fb4a81ad80c64f1439a0c40cd547f4f26fd120c6494d630aeb` | Full body: 1–101 |
| [pfp/domain/ports/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/__init__.py) | `1af3a60da3657a851cea8e5b66a4601a7e63337e19e45c55b0b6a246c7819611` | Full body: 1–79 |
| [pfp/domain/ports/ast_cochain_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/ast_cochain_ports.py) | `aa17333fa10ba43fab3f56d8ffd8d127b73dfb55aeb8bacc24d34cbaca199b76` | Full body: 1–33 |
| [pfp/domain/ports/biochem_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/biochem_ports.py) | `19283ef3948499792a85f8ff91ac9f5c77378c90ea71878854e63db6ba2edad4` | Full body: 1–48 |
| [pfp/domain/ports/cec_bridge.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/cec_bridge.py) | `b1fc3b1ca7381c94a232b857037dd54b1a8ebc74cef59c534ef803994de0d109` | Full body: 1–12 |
| [pfp/domain/ports/code_change_repository.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/code_change_repository.py) | `cafae4d13649698ad64bc06b0df7c432f7043823774bcaa063c02679d2b943ff` | Full body: 1–44 |
| [pfp/domain/ports/cohomology_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/cohomology_port.py) | `0cb36f691cc1b9036da165099ac5964efe90459daa20b97a18a61cf027d73d2b` | Full body: 1–36 |
| [pfp/domain/ports/decode_control_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/decode_control_port.py) | `6cb5320e805cb237c04c1a6f603928083c7e39dceadf05191d7ccb7e395e04d9` | Full body: 1–177 |
| [pfp/domain/ports/decoding_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/decoding_ports.py) | `cb6ff0920b300aedb6494c358bcfa2b1f067686cf01a6ea3b0f5a699935b7fff` | Full body: 1–118 |
| [pfp/domain/ports/exact_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/exact_ports.py) | `428ee4f6f202ad348dd24be4b99144ce680bf6fbc0272d3aa812963031707183` | Full body: 1–171 |
| [pfp/domain/ports/finite_gauge.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/finite_gauge.py) | `09492835ce7de648584ec11f938451a1a8322c351b7a7e7ed14b3d1c76125544` | Full body: 1–35 |
| [pfp/domain/ports/flagship_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/flagship_ports.py) | `52a9e7f10f27a154c29563970d0642e128e5ef50e58173b75f39b6b48862a492` | Full body: 1–68 |
| [pfp/domain/ports/genesis_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/genesis_ports.py) | `74619f90dfd281662bbcdd3f3607f02b6f7f485dce9af0c8708547a2e4aea3c0` | Full body: 1–49 |
| [pfp/domain/ports/lean_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/lean_port.py) | `6b693989c283d0e5e910a1aa7b49b0661439d8d8c188dcc88cb3033e5b727756` | Full body: 1–27 |
| [pfp/domain/ports/learning_repository.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/learning_repository.py) | `87a364c8029cefddd072e5beccf55da2ed89845d43c1dabcf7ca4513e85be6db` | Full body: 1–23 |
| [pfp/domain/ports/operad_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/operad_ports.py) | `ecbf3ceaa547f7f0ed2dfff4c3c2213d36c393c058d1f1f72295d9eb2c21212b` | Full body: 1–40 |
| [pfp/domain/ports/ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/ports.py) | `d879ee26bb6875ebe67a19c49875c473ad10ce1de744fe3f3a61facce7741274` | Full body: 1–210 |
| [pfp/domain/ports/process_sandbox.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/process_sandbox.py) | `dcfdff36c1845193d6b5fab8b2a8cf53d487d07f90b06e419fd353f9d79cdbff` | Full body: 1–70 |
| [pfp/domain/ports/prompt_cochain_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/prompt_cochain_port.py) | `df8e80a56c4285e2007bba28e7122659ff097a6c9bbf305f136cabe909914bbf` | Full body: 1–23 |
| [pfp/domain/ports/prompt_repository.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/prompt_repository.py) | `c7c15c159fafa355ebc6063605bb09540630b93bf6f29be51d4b95b2b61c9649` | Full body: 1–23 |
| [pfp/domain/ports/protocols.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/protocols.py) | `237b5734614304b27c733baef9dde0aac6584c827dd2e965360e96005df9b334` | Full body: 1–42 |
| [pfp/domain/ports/reply_control_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/reply_control_port.py) | `a2ed5eba9406519c44b84b12da122414d13e15984a30ba65495a347b3e92cfe4` | Full body: 1–14 |
| [pfp/domain/ports/research_repository.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/research_repository.py) | `1eddae880c37c257d4a5379cdff260080ab3b06b012e485403e12a8d17dab84c` | Full body: 1–24 |
| [pfp/domain/ports/run_artifact_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/run_artifact_port.py) | `358bfd98585c71b5365080b612e601b105bb0a001972587323580eeb101dfe8f` | Full body: 1–48 |
| [pfp/domain/ports/run_recorder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/run_recorder.py) | `60545f74d0dce854abfc36e4a74b1d96bfe34200271140315b175e040b49056d` | Full body: 1–179 |
| [pfp/domain/ports/scoring_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/scoring_port.py) | `423cb39ecca82fe0f46d5cfccb8cbab80d2101aec00103d50e0c1d73af26574f` | Full body: 1–40 |
| [pfp/domain/ports/stabilizer_port.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/stabilizer_port.py) | `d77375ac5a694a7c043c6bfeecae67d3fc613d4af621ebb6bb6a51a6dfc3b106` | Full body: 1–26 |
| [pfp/domain/ports/tower_lift_ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/tower_lift_ports.py) | `c8f9c7870b4afb97c8aaa830ccf17862ebe4e799866afad8ce4f052bb5672827` | Full body: 1–43 |
| [pfp/domain/ports/turn_repository.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/ports/turn_repository.py) | `bc1a2799a79346a560db6356bf37097a85e3147392e93f49e64f73cd72fb159b` | Full body: 1–30 |
| [pfp/domain/presentation_pins.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/presentation_pins.py) | `afa2d6ee44de87a5ee9dc51dbfc7d8015b37dcee39da599aa915ad708a8d498d` | Full body: 1–264 |
| [pfp/domain/prompt_representations/README.md](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/README.md) | `cbaf13a5699d9126642e0035e11bd8b60f09a1f7f1276aaffad9c4cb6ae76d3c` | Full body: 1–67 |
| [pfp/domain/prompt_representations/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/__init__.py) | `911e37f4870517a5a030eb959743e974c54ba3b036b2f779d92a5264cfa46d61` | Full body: 1–83 |
| [pfp/domain/prompt_representations/cochain_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/cochain_prompt_representation.py) | `3fc89ab325feacc5eadc71f3fe0be5eff77e259e24f81f3ed161cc33aaa9d6e4` | Full body: 1–178 |
| [pfp/domain/prompt_representations/cochain_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/cochain_prompt_representation.yaml) | `d64406955aa1dd9372118387de996979e7f4acda96843253fe5a62fe69660a95` | Full body: 1–131 |
| [pfp/domain/prompt_representations/common.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/common.py) | `d686590cfa1d63b7b57c6bc1b839dac20ae71c3c6da3db4032f486dbd9b0d786` | Full body: 1–84 |
| [pfp/domain/prompt_representations/diagram_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/diagram_prompt_representation.py) | `cfcc1da09e80004643869bb45b01e9d0a8fe46ed00ec55803fa65f0feaddc4e2` | Full body: 1–164 |
| [pfp/domain/prompt_representations/diagram_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/diagram_prompt_representation.yaml) | `9fc812a94c42fad7037e193270dd5e88c259ef3a457171f8625b795b6b895776` | Full body: 1–160 |
| [pfp/domain/prompt_representations/egraph_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/egraph_prompt_representation.py) | `ab56ac950cb2acd714b6549bf407c4ff3975c2a8735353a96917be179db1b7fb` | Full body: 1–126 |
| [pfp/domain/prompt_representations/egraph_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/egraph_prompt_representation.yaml) | `e7992370390b62df3e44bfa83f3e9e5ac20c9bfac5dac22fe8b2d4b03550671b` | Full body: 1–117 |
| [pfp/domain/prompt_representations/operadic_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/operadic_prompt_representation.py) | `b7047c55b966cb46a992ddcc9c25d3e581702528abaeeb2fa31b433493fdee9e` | Full body: 1–141 |
| [pfp/domain/prompt_representations/operadic_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/operadic_prompt_representation.yaml) | `8e4dfb84be59c0666ea2bd79aad94a100308b81de838422d8e7263896ce73ffc` | Full body: 1–179 |
| [pfp/domain/prompt_representations/raw_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/raw_prompt_representation.py) | `3881e60ea8cec63fbf311cf6612ac424df4f585526c07a7552cb663dffaeffc8` | Full body: 1–89 |
| [pfp/domain/prompt_representations/raw_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/raw_prompt_representation.yaml) | `bc735bf5e799d491107f9477d2b1987633c13f0cadd8c4d9afe953c77bf0c71d` | Full body: 1–76 |
| [pfp/domain/prompt_representations/relational_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/relational_prompt_representation.py) | `7823447afa2a1f1c2d9b38e35a0313e064bc76cc972b70ff10c85212beec44dc` | Full body: 1–158 |
| [pfp/domain/prompt_representations/relational_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/relational_prompt_representation.yaml) | `45bda4f1edfdeda80ab3d33dbc9d5f1cd34b3375698bca070a95fdc4b572058e` | Full body: 1–107 |
| [pfp/domain/prompt_representations/structured_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/structured_prompt_representation.py) | `93615f3fa6a3b1d6855f9e7830b7e1efb3f4310715b04288ba91d235be4182be` | Full body: 1–147 |
| [pfp/domain/prompt_representations/structured_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/structured_prompt_representation.yaml) | `441cd642c5af869fef6e87a3e5844dfa27ee5a806f5da70eab36768867cbd2ea` | Full body: 1–100 |
| [pfp/domain/prompt_representations/symbolic_constraint_binding_v001.md](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/symbolic_constraint_binding_v001.md) | `957e552de81464d80c6abaea7ea09edaa9313def411212aaf8331c41cc5d9484` | Full body: 1–63 |
| [pfp/domain/prompt_representations/symbolic_prompt_representation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/symbolic_prompt_representation.py) | `aa214361174785900e54b54bf9c8483f7082cb16e06e5be165eaba481aa9331a` | Full body: 1–139 |
| [pfp/domain/prompt_representations/symbolic_prompt_representation.yaml](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompt_representations/symbolic_prompt_representation.yaml) | `a132ae3cf874a7b766ad76246c984748a7fbaf91598c46aca3890d15b5173a2d` | Full body: 1–91 |
| [pfp/domain/prompts/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/__init__.py) | `6aa52012dad366ff5ab663fe7aa448968b481c7d67733472c5c9050fdeb3974e` | Full body: 1–43 |
| [pfp/domain/prompts/compression.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/compression.py) | `03f0b6c7559e88c9cee672b7368af1e0303dd3714f884799965f7da765c335d8` | Full body: 1–190 |
| [pfp/domain/prompts/packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/packets.py) | `96e00050f8ea185bc2e4fe8339e7ab2ad6236a34e6b24927d82e4817538e9365` | Full body: 1–73 |
| [pfp/domain/prompts/pfp_prompt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/pfp_prompt.py) | `2f00ba3ed317b482b38064801857ca41793604175e18e156c3bbad58847661f7` | Full body: 1–55 |
| [pfp/domain/prompts/prompts.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/prompts/prompts.py) | `78cc121730696330e9ae61066b3d6f8812f71b02133a1bf1d5f4bc25657eefe4` | Full body: 1–62 |
| [pfp/domain/provenance/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/provenance/__init__.py) | `da7f9de20f2e07856de76e51317e3a41bafa86c43bcb9c525b4c0d6b98db2186` | Full body: 1–38 |
| [pfp/domain/provenance/three_role_gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/provenance/three_role_gate.py) | `a2128acc7b8d888fc74f90d6cf10814a1924406829724512c175f696a93b3c18` | Full body: 1–343 |
| [pfp/domain/quantum/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/__init__.py) | `7c2bc7939eed2b7149dd25ada05eef0afa2a55e473595ad27fa59855bb03dd2a` | Full body: 1–40 |
| [pfp/domain/quantum/c029_coset.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/c029_coset.py) | `c656e310e2926c20fa54cf26a6cec50dedab226fa5d549bdd9a0f91c8bfc02e7` | Full body: 1–175 |
| [pfp/domain/quantum/hamiltonian.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/hamiltonian.py) | `356aa5c29ce0d831b1c8054af674684487b18cf9ba76f1779c5e45dd634c0977` | Full body: 1–276 |
| [pfp/domain/quantum/pauli.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/quantum/pauli.py) | `a24c7c671d761405761ccf8fb513fe2f6332f9aa2e371ba3e2b73764cbbdecc8` | Full body: 1–139 |
| [pfp/domain/representation/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/representation/__init__.py) | `558bf254c714cc4831ba3b7b0713ee4dfcdf88f7b6fab7f06331a11fd247b64a` | Full body: 1–13 |
| [pfp/domain/representation/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/representation/models.py) | `0f0109a432df51bd46b5b9234fe1b0d92d5bde21695dab660ca7c97ba284a3cd` | Full body: 1–99 |
| [pfp/domain/representation/ports.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/representation/ports.py) | `ca20f7e379a5b1bd49c5f238f57f25df081abf2093e3b2b4824ecd3500a4a8c0` | Full body: 1–28 |
| [pfp/domain/rewriting/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/__init__.py) | `f42d0f37986c9de198aa3a1bedab6d72e8a67aa4a83394dce77816749ef94bbe` | Full body: 1–62 |
| [pfp/domain/rewriting/prompt_containment.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/prompt_containment.py) | `6fc1976290260b286a4dcf91e7a53ac98b96acc4fee9a1c331db74b49f7e5503` | Full body: 1–81 |
| [pfp/domain/rewriting/rewrites.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/rewrites.py) | `8b39d479c102a317d33084c60d239ebcd3278dd1c45575b54c3caa96236c810e` | Full body: 1–150 |
| [pfp/domain/rewriting/rewriting_types.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/rewriting_types.py) | `e9dc137a5e98cbd76fda54c75fbc96d0ef6cd14d80c154285ce4fcbd19abe8ee` | Full body: 1–167 |
| [pfp/domain/rewriting/wires.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/rewriting/wires.py) | `7451f591cadf88184be6ef3a8e25e5783766e6bde50cb9db8e5754618dae1cf3` | Full body: 1–118 |
| [pfp/domain/row_rederivation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/row_rederivation.py) | `544cef19ab740fd44ec9565ba4f99a8b26f98978c50e0205f0b73f24b6c6789b` | Full body: 1–519 |
| [pfp/domain/sandbox/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sandbox/__init__.py) | `45791201e87093cd557ab34740e4b3bcf6c3865b1de024735ab21c104117ee19` | Full body: 1–18 |
| [pfp/domain/sandbox/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sandbox/models.py) | `a062927a25a8176d4d7b8a24af03862164b576e34346663c63f9219952f7bff8` | Full body: 1–75 |
| [pfp/domain/shared_kernel/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/__init__.py) | `e72761212049d9f6c58fe3ace568c3da7d6ce2a1a1a0d334abb62d8482e67a6b` | Full body: 1–192 |
| [pfp/domain/shared_kernel/authority_effect.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/authority_effect.py) | `48a51a1cf08a0a446473582e391e813589c5f87a99ebbbd192e2d362d68199b7` | Full body: 1–22 |
| [pfp/domain/shared_kernel/budget.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/budget.py) | `1113d4b9160454325b8b2cb1c75f7524fd8c592b9249c8bcb5e6b307ca36655c` | Full body: 1–137 |
| [pfp/domain/shared_kernel/byte_payload.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/byte_payload.py) | `7133d6c5f98d972091e5d42fc46ee6e3f2475c51d1cddadaab461d4fd948da9b` | Full body: 1–56 |
| [pfp/domain/shared_kernel/bytes.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/bytes.py) | `78d4611542d572b0953be28d2c4b097a179218bccf707be8cecf047a9dfee7ae` | Full body: 1–72 |
| [pfp/domain/shared_kernel/canonical.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/canonical.py) | `d7170c6f8f37d12489843dccd63162b471afea062d3df6b8bce1119e99ab7918` | Full body: 1–505 |
| [pfp/domain/shared_kernel/coboundary_score.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/coboundary_score.py) | `fbf0173f1a07d86c6b3c164e5323e3af483ff7ab5cb67897ab0943d8365dfa4e` | Full body: 1–88 |
| [pfp/domain/shared_kernel/code.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/code.py) | `7d870f2db4e4d1bfb2e0f700c92073c1f3c3addadf699fc6d5be6f6fb3c4864e` | Full body: 1–62 |
| [pfp/domain/shared_kernel/content_digest.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/content_digest.py) | `16d572bb281c31ae25486a0cd12f06104b293822faa4875c2eb71233914cb07f` | Full body: 1–70 |
| [pfp/domain/shared_kernel/data.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/data.py) | `d3b9ab0e651233f59aa9346df812277e069fb9a74a7e6f3f61c499aeb4ac3220` | Full body: 1–97 |
| [pfp/domain/shared_kernel/demand_item.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/demand_item.py) | `82acf3f5b6b2faf8fe77cb848a080add7e0e6952d002fd65ce1d7e3248bef293` | Full body: 1–58 |
| [pfp/domain/shared_kernel/description.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/description.py) | `0cf0cdc74935fc5c57106fa901cd3f575543f800fb4253136e1542efedf3458c` | Full body: 1–61 |
| [pfp/domain/shared_kernel/disposition.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/disposition.py) | `9d9ed367291905918636372f55243090395aa6b74e35a48242645dc878c56c35` | Full body: 1–90 |
| [pfp/domain/shared_kernel/exact.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/exact.py) | `c9d2d9c957f05c728b195c015408cb2391153a726d7fd8a2b369d29f52586e8e` | Full body: 1–134 |
| [pfp/domain/shared_kernel/field.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/field.py) | `e10ff39daca6255b22e90973879d43092e1ac68c84c6c08382632bed3b2aa3d4` | Full body: 1–57 |
| [pfp/domain/shared_kernel/gate.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/gate.py) | `3997749961509c98f593500486defa8cac5e24c3374a4fccdce0128d8c056444` | Full body: 1–32 |
| [pfp/domain/shared_kernel/hash.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/hash.py) | `39024ddebcf13a8c473a097ffa183f3c86b38384d75acdaa5d2969ac144534c2` | Full body: 1–88 |
| [pfp/domain/shared_kernel/id.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/id.py) | `031d40063a492d3b744a43705e9ec682abcd6a6c77ca62a446525c0e79af886f` | Full body: 1–156 |
| [pfp/domain/shared_kernel/key.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/key.py) | `119f08328650d6106d1f46ff42d70094d1299b3ae5d5bfb7452b96647736c8a0` | Full body: 1–82 |
| [pfp/domain/shared_kernel/key_type.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/key_type.py) | `ed100799f1a9e7324a8a86d5a058e715b3719447cef2bc9a49e4bbced88eafdb` | Full body: 1–38 |
| [pfp/domain/shared_kernel/kill_condition.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/kill_condition.py) | `f9742a60d0f864617f96bd20bde75de244546338380c05cb8c41433da21fc00b` | Full body: 1–82 |
| [pfp/domain/shared_kernel/kind.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/kind.py) | `526bf1cb99195b43e11c4f4553048346007fb6e7766df1b83be6f99c5c437f0a` | Full body: 1–124 |
| [pfp/domain/shared_kernel/llm_payload.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/llm_payload.py) | `118daa94f3f1f42540b5c2099a0c77177163b5a3780f8270c97a926c2384eaad` | Full body: 1–541 |
| [pfp/domain/shared_kernel/media_type.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/media_type.py) | `017264fb069c3c21ddd527bfaafc46041028c17d431dbc9dd3052f595907fdc8` | Full body: 1–64 |
| [pfp/domain/shared_kernel/objective_typed.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/objective_typed.py) | `4214a9faf608804399f0eb408d0166f4fde2c8f1549534c3cf165ee30ea023a5` | Full body: 1–75 |
| [pfp/domain/shared_kernel/obstruction.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/obstruction.py) | `20475b617001e4278326cac535561fa66517d4403c62dd5d65569dbe07ec609b` | Full body: 1–97 |
| [pfp/domain/shared_kernel/patch.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/patch.py) | `e2a061f622c3862116663e0cd3a3772f726e69287048bc548a64bb76e79e5471` | Full body: 1–66 |
| [pfp/domain/shared_kernel/path.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/path.py) | `52d3a210912f167b5c6e29916440f70264ab0b0938d7062b444b5703de0d792d` | Full body: 1–149 |
| [pfp/domain/shared_kernel/path_manifest.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/path_manifest.py) | `0af63522b43f6ce7faf8a723d11e7c659fd7795e947e12b5df838865e53a9f3e` | Full body: 1–51 |
| [pfp/domain/shared_kernel/regime.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/regime.py) | `9f944811cdc069395dc301fc964d6f3bc4beccf034312c2930d1516d3442676e` | Full body: 1–88 |
| [pfp/domain/shared_kernel/required_reply_fields.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/required_reply_fields.py) | `d87550772bd12d92d2e2cfecf6ef9f63d9bfbb6cbb92b23c5216173aae985428` | Full body: 1–73 |
| [pfp/domain/shared_kernel/research_digest.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/research_digest.py) | `e5d5f7d8b1da1ac96ab46fd746c6b9ea708c40c47bbb84f1c9e1d102186190d6` | Full body: 1–26 |
| [pfp/domain/shared_kernel/residual_colour.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/residual_colour.py) | `ae320f91fa0a3ede049d26c2069f7bbf88cdb713148de28f17f2dcf0dc98d2ea` | Full body: 1–16 |
| [pfp/domain/shared_kernel/residual_drop.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/residual_drop.py) | `6d2fae4a032f39d30b8860a893a2ab53344b8ae6c810c96194704ff2e96f8862` | Full body: 1–98 |
| [pfp/domain/shared_kernel/result.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/result.py) | `425b0f362d96ee992a35ac951402cb42a78ce9ad104c222fa9b7dccbb8aef2cb` | Full body: 1–112 |
| [pfp/domain/shared_kernel/revision.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/revision.py) | `af5b4a12db264a8367d704b7ee3156a53e0985f61828dc48aa025822b8931100` | Full body: 1–50 |
| [pfp/domain/shared_kernel/schema.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/schema.py) | `65b16da4dbcfc8036b322d01b6ae795b62ee8afab3d9389a37ba729091d24eb2` | Full body: 1–57 |
| [pfp/domain/shared_kernel/severity.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/severity.py) | `59208d0ec8f82ece509637ae4a1cf29b2501b0d736c4b09a2fc5df2b55369daf` | Full body: 1–100 |
| [pfp/domain/shared_kernel/summary.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/summary.py) | `7709959a79296c413f314b2ec101655834ab3ad6ea29c0e20d2f1a94f4a2f913` | Full body: 1–61 |
| [pfp/domain/shared_kernel/task_objective.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/task_objective.py) | `b5923c43978aaed63629a0469011b3d7c2f8ed22d7c7fc4b00b25673e173f0cf` | Full body: 1–52 |
| [pfp/domain/shared_kernel/turn.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/turn.py) | `667e440124d4c8af94688b6404bf6fab5535fcbdb8fc2e35752fd6326f4c48b9` | Full body: 1–74 |
| [pfp/domain/shared_kernel/turn_type.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/turn_type.py) | `171094240f8431f5dc634d911eeb74450eaffa3cf543c3f7139ba90853baa5a4` | Full body: 1–66 |
| [pfp/domain/shared_kernel/wire_key.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/wire_key.py) | `db42739d75d688851eb2662476f1ebd15b5f62db07b062d4309e343ae06606ef` | Full body: 1–54 |
| [pfp/domain/shared_kernel/yaml_strict.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/shared_kernel/yaml_strict.py) | `53a3203f3275a4c6b9c95d2f739d3da8716bfff607e4693321a03bc7bac80a1a` | Full body: 1–124 |
| [pfp/domain/sn_tower/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/__init__.py) | `53c5dafcd42a326c9942381f527da31994f5617a0ce0dcf34a6c7f2f66ce3c81` | Full body: 1–70 |
| [pfp/domain/sn_tower/sn_applications.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_applications.py) | `9e4eff23af00f3d93598ef92381d2acbd99ad1ac579305f3822ceec29f691894` | Full body: 1–106 |
| [pfp/domain/sn_tower/sn_core.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_core.py) | `2650053fc95d67a9e9be3c4ec87c4b9b6c8d42674ee8ccd8b92a78c2f2d068aa` | Full body: 1–194 |
| [pfp/domain/sn_tower/sn_realizations.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_realizations.py) | `e569bdd995bb128800af317c7e1ff50c2739f6363de6e208533440837028150a` | Full body: 1–235 |
| [pfp/domain/sn_tower/sn_verification.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sn_tower/sn_verification.py) | `6452db0fca5a77ab5d8bd9a493c2a0e1522d56e43dc83e6bccd1240567dcfdf3` | Full body: 1–146 |
| [pfp/domain/solvers/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/__init__.py) | `c4d1dc3302e9462316f92f8d945316e5707da6b0d0f3070a599a09a9221865c8` | Full body: 1–221 |
| [pfp/domain/solvers/canon.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/canon.py) | `4412d93cb22f293f18740820a29657a907c25449f0e944ec16ca6d88bd70c1de` | Full body: 1–84 |
| [pfp/domain/solvers/cochain_gradient_hook.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/cochain_gradient_hook.py) | `dff6fed793dc1184cf7c8cf6b9f7d36bf0eb56d5a7e27debb756ad14b89874d2` | Full body: 1–447 |
| [pfp/domain/solvers/encoding.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/encoding.py) | `f206f7261a3c8e2d17f250c32bc8ae73b8c194bc81be63478a0c7fa056ca2b93` | Full body: 1–187 |
| [pfp/domain/solvers/errors.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/errors.py) | `f595206eea582dcf3f06a8e1808f498466f21ad6ba89736f6b1eba631eed666e` | Full body: 1–52 |
| [pfp/domain/solvers/guards.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/guards.py) | `d752df1cd8f4f7876eb4f44654ea978901fde9c16ae343bddf658ba4b63166fa` | Full body: 1–103 |
| [pfp/domain/solvers/iso.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/iso.py) | `ba8bc98444caab2722e7dd81b111bac0f5ac9c2a5796df711f7c4f837f928bca` | Full body: 1–298 |
| [pfp/domain/solvers/kinds.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/kinds.py) | `9d133a2a191c279257511fa9b742407daadefd74f1b97975fdd32f378eab9698` | Full body: 1–618 |
| [pfp/domain/solvers/ladder.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/ladder.py) | `db054c54305c9772997920948e62d45c973bd4dafc928365f60668ebda48f8a7` | Full body: 1–216 |
| [pfp/domain/solvers/regime.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/regime.py) | `9859efc74194d3d3af6d0ff27f075d12aaa088c8fbd5b1425c0c3e21ea4c67f2` | Full body: 1–386 |
| [pfp/domain/solvers/regimek.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/regimek.py) | `30d12d98792383a8c6b79c67f0755f33c973e553eedc4f60982a607359682068` | Full body: 1–203 |
| [pfp/domain/solvers/retraction.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/retraction.py) | `a8d68f3b7ad15d3ee013ca66d7eae69b251dcb9c9015c68ef1e1e461ba90c939` | Full body: 1–514 |
| [pfp/domain/solvers/search.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/search.py) | `6f6f1e305969ff98eed3f6bc6df6493b10ea41102ec1f6a679feace0b09c82e5` | Full body: 1–395 |
| [pfp/domain/solvers/simplicial_cochain.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/simplicial_cochain.py) | `178f08c3e237ff46ae399514d087ba00cac89900c038a15c647c6cc25b71de66` | Full body: 1–566 |
| [pfp/domain/solvers/stage.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/stage.py) | `6a98c2a5fc629c7f3d90b4343c05d1570f24065dfccf758f86e6dcb22d4b30d9` | Full body: 1–351 |
| [pfp/domain/solvers/structure.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/solvers/structure.py) | `12b3e0ca32b3ef655a832f4695834af75fcc96068c71e33127c8042308608d57` | Full body: 1–331 |
| [pfp/domain/sovereignty/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sovereignty/__init__.py) | `1b24ba94f30beb353b83d78a10d08255fd1480663cb88135b1ccc8bb7d9f8d61` | Full body: 1–18 |
| [pfp/domain/sovereignty/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/sovereignty/models.py) | `a3dc5166c8f09fa68108e5180c8ac60ef3b86ffc607a605257c3b8487d55b24e` | Full body: 1–123 |
| [pfp/domain/stages/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/__init__.py) | `f7deadddf2c2dff39d5d2449f4e5867a4c51dbe0285c4c89821f4e3a9705d2f1` | Full body: 1–83 |
| [pfp/domain/stages/cartesian_matrix_types.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/cartesian_matrix_types.py) | `03ab1eda1b220c9a7adf8ac6400d7d21acf3105a615b1a80aa846de9b8e3c759` | Full body: 1–61 |
| [pfp/domain/stages/demos.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/demos.py) | `5ccc5bd1a42c585b6b227e6c9dcbeb254e3db0713410e2e444c2a437df4c43ae` | Full body: 1–75 |
| [pfp/domain/stages/mode_catalog.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/mode_catalog.py) | `c3d3580cc3f6310b7563e4e86f5b4dd8a7928b69af748936e04612de1a6e7856` | Full body: 1–118 |
| [pfp/domain/stages/modes.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/modes.py) | `b85b5ea41257c08c3cabadb56d172f05ec0fd8a3a2eab150aa526d07626112c4` | Full body: 1–96 |
| [pfp/domain/stages/stages.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/stages/stages.py) | `9fafb52c29dd336f70947b545171cdba74af2f099176a0093d723907c3faa8b7` | Full body: 1–544 |
| [pfp/domain/survivor_dedup.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/survivor_dedup.py) | `77ee4c8cbc33d4839e9650224a516dd185ef6fcda5b38fc91c329ccfd015f5fa` | Full body: 1–37 |
| [pfp/domain/synthesis/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/synthesis/__init__.py) | `fb681ff1f1b574834ca89777deeade60b04eb8ead3ec33c358bcc6f2f9a5ab79` | Full body: 1–11 |
| [pfp/domain/synthesis/module_dag.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/synthesis/module_dag.py) | `90e5ec2cf22052d621b94c5a63b4cabe8430bd980b04521b85c7291d4aa794b4` | Full body: 1–66 |
| [pfp/domain/synthesis/retraction_context.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/synthesis/retraction_context.py) | `77a2c4af3421d1210f665812f073d8b618860f3ca0ed0cc7ed17bb1bc2e56028` | Full body: 1–54 |
| [pfp/domain/task_families/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/task_families/__init__.py) | `87e7cb0ed114c052bcace84c0141e388cd5361cd3c9c1284576e889f1b5514cf` | Full body: 1–26 |
| [pfp/domain/task_families/task_family_types.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/task_families/task_family_types.py) | `10d6d5c4aa6baa7016c292246f165e13c10ec0366156051017f67843b8a74cdf` | Full body: 1–99 |
| [pfp/domain/tower/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/__init__.py) | `3e717c44c509da4d58a666455c0b5f0e2795bf7f13fdc99ed3be802394ffb3f4` | Full body: 1–1 |
| [pfp/domain/tower/alternation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/alternation.py) | `2ddd520635a1bc1aae29609f92a0ae100fac57f8d44389c6d96a1953ed70aeb7` | Full body: 1–198 |
| [pfp/domain/tower/cells.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/cells.py) | `336d4927583f526c62d1a2d524239f415593166fa22885a8c0527517d105189f` | Full body: 1–121 |
| [pfp/domain/tower/checks.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/checks.py) | `6627a425488e3dac3aedfa3db5608298e1cbab078c82e91dcda15941e91bc2af` | Full body: 1–379 |
| [pfp/domain/tower/golden_corpus.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/golden_corpus.py) | `aca88a49f5741e79bfa4202c2a67c050ec605658c0896702f1de485e9767f756` | Full body: 1–98 |
| [pfp/domain/tower/grammar.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/grammar.py) | `34279e8dc4f4e66499314d53844653e95d79c4047471ad6fbbdb40ea0c17b50a` | Full body: 1–333 |
| [pfp/domain/tower/level_engine.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/level_engine.py) | `429048b3cd36305e2a9c6973fc65e6f5ace5360dd26494ad092901348ad00c1d` | Full body: 1–25 |
| [pfp/domain/tower/parser.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/parser.py) | `bdd23514af5295b1106f1a82c44a0d4eaca3e7e9f72df02292ab28c99d904722` | Full body: 1–684 |
| [pfp/domain/tower/profile.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/profile.py) | `101e8427c1ba1531e0570879a9bc1c4d6e04f629d2220d1c34c6e64fc5587c1d` | Full body: 1–109 |
| [pfp/domain/tower/registry.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/registry.py) | `ec2e18d9dcdc90e75a34d9f44cd120d6cbff61406caca62d771776710b8b656b` | Full body: 1–934 |
| [pfp/domain/tower/stage_status.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/stage_status.py) | `96be7130f765bde46e6cbc4a381658eb1ccd307981969ca5dbc6cbec05e47fe9` | Full body: 1–67 |
| [pfp/domain/tower/tower_policies.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/tower_policies.py) | `1c8d496bcdfefb22636bb2bd605c92c2be95a91cd936b0fd31cb8c5e804be13d` | Full body: 1–136 |
| [pfp/domain/tower/updown_maps.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/updown_maps.py) | `c662176dfa22168cdf5cf36725964ce366858fb7f15f4bd723b12cbebb261774` | Full body: 1–66 |
| [pfp/domain/tower/wire.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower/wire.py) | `96fd1206e0783a0addaabc48ecefb6b773f84d3ff49f65fe410ac0f0df96a210` | Full body: 1–351 |
| [pfp/domain/tower_lift/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower_lift/__init__.py) | `c7eea8ccfafc1972f0453fadc8e307780860a0c06238c581ec11e04cca29b8da` | Full body: 1–20 |
| [pfp/domain/tower_lift/models.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/tower_lift/models.py) | `d0029c623a748c5937a350669ce87471dce63d39d0d593503d67a3a3793d4377` | Full body: 1–131 |
| [pfp/domain/type_register/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/type_register/__init__.py) | `6dc51c18191809bd262515fa35e504a7ea6be1536a76564330b1f54e0cd972a4` | Full body: 1–1 |
| [pfp/domain/type_register/type_register.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/type_register/type_register.py) | `d45b874eff2407445a4d9b64458a86775d24cdc0b438faff077b501428e4119b` | Full body: 1–139 |
| [pfp/domain/types/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/__init__.py) | `058c935eb2b3c025a49fdea9f0bf2d132234c781ca06f5ae0bd65549450401c8` | Full body: 1–252 |
| [pfp/domain/types/base.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/base.py) | `4ba9a33d5a0b04a111512bd64e54f65c32c4e7569b8675fedb93b4e8603ff307` | Full body: 1–228 |
| [pfp/domain/types/cycle_balance.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/cycle_balance.py) | `415a4eb765b6aabbe60b98e889aa7f2c9322b3ee4f7154d6f5c6bd75fe07672b` | Full body: 1–170 |
| [pfp/domain/types/modes.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/modes.py) | `940ac2aa50c796ab4471732de7b3a795aa227cde04ec0b1f273f55c4c30d1b28` | Full body: 1–83 |
| [pfp/domain/types/normal_forms.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/normal_forms.py) | `3d6fff7cc68c73328dea0a565556d6e1223f059c5397814248e3845da3eba0df` | Full body: 1–74 |
| [pfp/domain/types/pilot_comparison.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/pilot_comparison.py) | `49d35e7566aee0e52bcff195b6f8015085adc787eb3740296c9e5ccc4f4e504e` | Full body: 1–85 |
| [pfp/domain/types/pilot_response.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/pilot_response.py) | `252da43691d1958df37b82d374eb80326ecb92ff8bce3897b3b78c4e0c676b4f` | Full body: 1–166 |
| [pfp/domain/types/pilot_spec.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/pilot_spec.py) | `ec59ea120f68c3bd0f8d20ba6679f403eb36d2ea1e936e5db503c66750c35a23` | Full body: 1–173 |
| [pfp/domain/types/prompt_templates.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/prompt_templates.py) | `6b086d7d7828f04eda87497baa4afc16524e0c877e8be51085f66ec9d1fd6731` | Full body: 1–246 |
| [pfp/domain/types/rewrite_test_plan.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/rewrite_test_plan.py) | `b812dca589f3e8efb5c2be7b1b7c3a426a27fa7344bfa8ba194478412a2457b9` | Full body: 1–87 |
| [pfp/domain/types/rewriting.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/rewriting.py) | `4971fe6e2d0c7fdf40e575847b27df76283c8d4552798109426b92bd03ef9641` | Full body: 1–82 |
| [pfp/domain/types/schemas.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/schemas.py) | `1162b5ce9e964076c02142e736b592a8cc486392c4a971b7f063c9be6d3eb2fa` | Full body: 1–37 |
| [pfp/domain/types/seed_prompts.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/seed_prompts.py) | `e173b6e37640362c4edee1eb216f4398a44c3653de36bbedaea1bd102434fbbd` | Full body: 1–88 |
| [pfp/domain/types/stages.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/stages.py) | `ea4034a4c73b39a1c923223e2d8e5ea6e976863f30ba8da16da5699ee2c8d8b9` | Full body: 1–83 |
| [pfp/domain/types/task_packets.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/task_packets.py) | `225bd64ef92b830f878f6192b893ad5d19412efbe774709108c426f77f29afee` | Full body: 1–82 |
| [pfp/domain/types/test_spec.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/test_spec.py) | `984953b4b11ff5d41667e2cb9129fe73a5d8bd52229bbc39a26eb2e55497d44c` | Full body: 1–60 |
| [pfp/domain/types/type_register.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/types/type_register.py) | `dd7f97c8013a60514eb77695ee19f8382a14a46cf07655691644aa1d6861c630` | Full body: 1–72 |
| [pfp/domain/validation/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/validation/__init__.py) | `f53b8a79704587d694987dfc66f0e0f73d0d3626ff47024da0a52a1b8fae5a69` | Full body: 1–73 |
| [pfp/domain/validation/validation.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/validation/validation.py) | `b2e32517e4a2438392b3a8e005d3001858fd656eb1671606d984babe168f3278` | Full body: 1–247 |
| [pfp/domain/value_objects/__init__.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/__init__.py) | `b1d7a16773f11a79c14ad636523bed3575c1205a9673880ab158575ede9d8d9b` | Full body: 1–321 |
| [pfp/domain/value_objects/base.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/base.py) | `4602c4fac9f97dbbb24c0e6a88153212d542a4102c5dba2f96a1bdddabe07ccd` | Full body: 1–35 |
| [pfp/domain/value_objects/cycle_balance.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/cycle_balance.py) | `fdaf931bd404ef9866ec955f4193439e6ed3ff6c3e01d00141d99287672c239a` | Full body: 1–218 |
| [pfp/domain/value_objects/functional_receipt.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/functional_receipt.py) | `0d9ef30651378564f2bf7e070195f9cdfc4e91fbe8e98bf88297132547507ba5` | Full body: 1–65 |
| [pfp/domain/value_objects/identifiers.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/identifiers.py) | `3bc11f01315c8a4c95321b58339c63359ebbb1e01abf64c8db55acdae21719ed` | Full body: 1–273 |
| [pfp/domain/value_objects/numerics.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/numerics.py) | `06e0a4fe07dfea4acb67ab1b17988ce2114fbd220bebdad4ad1c99a041af64fd` | Full body: 1–165 |
| [pfp/domain/value_objects/seat_turn.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/seat_turn.py) | `9935764c78e6854acaf8f5479bf50732e991ba1c7f598414f58c809ab44fda56` | Full body: 1–96 |
| [pfp/domain/value_objects/task_family_tokens.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/task_family_tokens.py) | `8b2be05ce34097c7c056585c94ce9d7c45e29fabfee6176a19e954c899fb7b17` | Full body: 1–127 |
| [pfp/domain/value_objects/taxonomy.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/taxonomy.py) | `a478edc394eaf180f89eed741a316b95a161ddafae875fcc0758cf028bb2c808` | Full body: 1–275 |
| [pfp/domain/value_objects/topology.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/topology.py) | `5745e0443672f68c92fbf63305595650d1aae7e6de059d73a7f01de38cd21cfa` | Full body: 1–105 |
| [pfp/domain/value_objects/wire_keys.py](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/value_objects/wire_keys.py) | `1ca89928cdf2dfbe1c870d8ffe253dba07ffd934b08ded102a4252b0c3279b6e` | Full body: 1–141 |
| [pfp/domain/immune/self_panel.json](C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/pfp/domain/immune/self_panel.json) | `d405f3acd3d0d16ad9e6b0df9d59e8069fe1c10a939d51b1a410e21adb6c10af` | Bounded schema/custody/base-text assessment; not full body |

Every full-file substantive assessment and chunk-level range is retained in JSON. No pending path remains in this declared slice. Broader semantic, physical and repository audit obligations remain open.
