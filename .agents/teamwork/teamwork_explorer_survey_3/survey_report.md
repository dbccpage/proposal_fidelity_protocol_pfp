# Anomalon System Survey Report: PFP, Operad Theory, EIS, Prompt Civilization, and Symbol Game

**AuthorityEffect:** None.  
**Investigator:** Teamwork Explorer Survey 3 (`teamwork_explorer_survey_3`)  
**Workspace:** `c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp`  
**Target Repository:** `c:\Users\a343o\source\repos\anomalon`  
**Execution Date:** 2026-11-06  

---

## Executive Summary

This report delivers a code-grounded, verified survey of eight architectural components within the `anomalon` repository:
1. `omega_engine_pfp` (The Proposal Fidelity Protocol & Symbol Game Clean Architecture application and engine).
2. `omega_engine/crates_rs` workspace and specifically the operad crates (`omega_operad_theory` and `omega_operads`).
3. `omega_epistemic_immune_system` (Sovereign Epistemic Immune System, four-gate immune protocol, antibodies, and formulary).
4. `omega_epistemic_operad_theory` (identified in tree as `omega_operad_theory`: 5-tier colored operad hierarchy, Koszul deformation, and algebraic realizations).
5. `omega_epistemic_operads` (identified in tree as `omega_operads`: validated workflow slices, planar substitutions, and immune-guarded composition).
6. `omega_prompt_civilization` (Prompt families, genealogies, Lamarckian cochain tracking, PageRank, and anti-skill pharmacy).
7. `omega_prompt_symbol_game` (identified in tree as `omega_symbol_game`: commit-reveal challenges, dual checker oracles, matched arms, and MCP entrypoints).
8. `omega_prompt_symbol_game_runtime` (identified in tree as `omega_symbol_game_runtime`: strict descent engine turn driver, Cemetery routing, two canonical wire codecs, and exact ℚ/𝔽₂ kernels).

The investigation inspected actual source code, module declarations, JSON/YAML schemas, and integration tests. All findings report verified code behavior rather than docstring aspirations, adhering strictly to Claim Hygiene standards.

---

## 1. Survey of `omega_engine_pfp`

### 1.1 Architecture & Role
- **Location:** `c:\Users\a343o\source\repos\anomalon\omega_engine_pfp`
- **Role:** `omega_engine_pfp` is the combined application coordinating multi-agent cognitive debate, discrete coboundary descent verification, and cryptographic execution receipts. It is structured under Clean Architecture layer boundaries:
  - `domain/`: Pure aggregates, entities, value objects, domain events, and ports. Contains contracts for exact calculations (`domain/contracts/pfp_calculations.py`), runtime definitions (`domain/contracts/pfp_runtime.py`), and cochain complexes (`domain/cochain.py`).
  - `use_cases/`: Thin workflow orchestrators (`execute_stage_pipeline.py`, `pfp_stages.py`, `pfp_prompt.py`, `pfp_proposal.py`, `drive_turn.py`, `scoring.py`, `llm_turn.py`, `code_change.py`).
  - `infrastructure/`: Adapters for frozen runtime replay (`adapters/pfp_frozen_replay.py`), task turn composition (`task_turn.py`), braid tournaments (`braid_tournament.py`), retraction benchmarks (`retraction_benchmark.py`), provider bridges (`providers.py`, `openrouter_seat_gateway.py`), and operad turn execution (`pfp_operad.py`).
  - `packet_schemas/`: JSON schemas defining content-addressed envelopes and receipts.
  - `engine_rs/`: Standalone Rust crate `omega_pfp_engine` providing high-performance local HTTP server and CLI routines.
  - `ffi.py`: The Foreign Function Interface bridge dispatching actions to the native `omega_symbol_game` binary via the OEOS process seam.

### 1.2 The Embedded Rust Engine (`omega_engine_pfp/engine_rs`)
- **Package Name:** `omega_pfp_engine` (binary: `pfp-engine`)
- **Key Responsibilities:**
  1. Powers the "Analyze" button on `anomalon.com/app`. Takes a seed prompt and emits a canonical JSON document (`omega.pfp.beta-run.v1`).
  2. Computes **quantum prompt density** (`density.rs` via `omega_engines::quantum::prompt_density`): eigenvalues of a 128-coordinate matrix constructed from hashed words, positions, and bigrams across up to 16 text slices. Computes purity, Shannon entropy (bounded at 4 bits), and quantum Jensen-Shannon divergence.
  3. Mines **planar colored operad trees** (`mine.rs` via `omega_symbol_game_runtime::operad` and `catalog/prompt_operads.v1.json`): constructs one leaf per clause with exact byte offsets, detects anti-pattern witnesses, calculates the $L_1$ residual sum, and pairs anti-patterns with healthy unary endomorphisms ($A \circ H = \emptyset$).
  4. Manages the **PFP prompt template & turn binding** (`turn.rs` via `omega_prompt_civilization::forge` and `omega_symbol_game_runtime::pfp_task_turn`).
  5. Implements **Paper Review v0** (`review.rs`): 3-stage bounded review pipeline (`plan` -> `section` -> `assemble`) utilizing host checks (`catalog/review_checks.v1.json`), claims-hygiene phrase checks, and dual producer/critic seats.
  6. Enforces funding policies (`policy.rs`, `work.rs`) across `byok`, `sponsor_free`, `work_anthropic`, and `offline` lanes with strict token reservations and price catalog bounds (`catalog/work_prices.v1.json`).

### 1.3 Packet Schemas & Receipts (`omega_engine_pfp/packet_schemas`)
All schemas enforce `AuthorityEffect: None` and content-addressing:
- `packet_envelope_v2.schema.json` (`omega.symbol-game.packet-envelope.v2`): Wraps either an LLM turn or code-change proposal with domain canonical SHA-256 digests.
- `llm_turn_v1.schema.json`: Model turn payload produced by `LlmTurnPayloadV1`.
- `code_change_proposal_v1.schema.json`: Produced by `CodeChangeProposalPayloadV1`.
- `prompt_artifact_v1.schema.json`: Produced by `compile_prompt_artifact`.
- `candidate_artifact_v1.schema.json`: Untrusted producer deliverables.
- `coboundary_score_v1.schema.json`: Carries canonical exact rational strings `"p/q"` (floats rejected).
- `elimination_receipt_v1.schema.json`: Verifiable proof that an identified obstruction was contractively eliminated.
- `evaluation_receipt_v1.schema.json`: Sovereign host verdict.
- `kill_condition_refusal_map_v1.json`: Closed dictionary mapping kill conditions to host refusals and obstruction families.

### 1.4 Native Bridge (`omega_engine_pfp/ffi.py`)
`RustSymbolGameHost` delegates to `omega_engine_operating_system.adapters.rust_host.ffi`. It locates `omega_symbol_game` and invokes native runtime actions:
- Wire codecs: `canonical_wire`, `canonical_unwire`, `canonical_json`, `canonical_bytes_hex`, `domain_digest`.
- Evidence & Patches: `parse_unified_diff`, `create_code_change_proposal`, `submit_patch_candidate`, `evaluate_patch_gates`, `intake_research_sources`.
- Exact Mathematics: `exact_determinant`, `exact_is_positive_definite`, `exact_ldlt`, `exact_rank`, `exact_leading_minors`, `exact_char_poly`, `exact_verify_boundary_closed`, `exact_verify_simplicial_boundary_law`, `exact_ordered_loop_product`, `exact_is_ordered_closure`.
- Dual Optimization: `verify_l1_certificate`, `exact_solve_l1_primal_dual`, `functional_evaluate`, `functional_verify`.
- Tapes & Fences: `ddc_verify_tape`, `prime_admit`, `prime_replay_decide`, `prime_descent`, `lggr_classify`, `lggr_soundness`.
- Immune & Verification: `pharmacy_detect`, `stabilizer_solve`, `stabilizer_check`, `lean_scan_sources`, `lean_audit_report`, `evaluate_prompt_cochain`.

---

## 2. Survey of `omega_engine/crates_rs` & The Operad Crates

### 2.1 Workspace Overview
`omega_engine/crates_rs` contains 56 workspace crates covering exact algebraic foundations, finite quantum mechanics, discrete topology, certified solvers, and execution runtimes. Key workspace members include `omega_kernel`, `omega_types`, `omega_functional`, `omega_solvers`, `omega_wdp`, `omega_epistemic_immune_system`, `omega_prompt_civilization`, `omega_symbol_game`, and the operad crates.

### 2.2 Dual Operad Crate Architecture
Operad mechanics are cleanly separated into theoretical foundations (`omega_operad_theory`) and domain/workflow applications (`omega_operads`).

#### A. `omega_operad_theory`
- **Location:** `omega_engine/crates_rs/omega_operad_theory`
- **Description:** 5-tier colored operad hierarchy:
  1. *Tier 1: Foundation (`foundation/`)*
     - `OperadColour`: Validated type/color identifier from admitted finite color palettes (`ADMITTED_FINITE_COLOURS`).
     - `OperadSignature`: Ordered sequence of input colors mapping to a single output color.
     - `Operation`: Atomic generator with `OperationId`, signature, arity, and `is_identity` predicate.
     - `PlanarTree`: Planar tree representation with strictly ordered input slots, open leaves (`OpenLeaf`), and internal nodes (`TreeChild`).
     - `PlanarColoredOperad` & `SymmetricColoredOperad`: Operads enforcing closed or open universes, identity corollas, and composition laws.
  2. *Tier 2: Realization (`realization/`)*
     - `OperadAlgebra`: Multi-sorted algebra evaluating tree terms into concrete carrier values.
     - `OperadicModule`: Endofunctor action over operad colors.
     - `StructuralAssociativityWitness`: Verifies that $(a \circ_i b) \circ_j c = a \circ_i (b \circ_{j-i+1} c)$ for planar composition.
  3. *Tier 3: Deformation (`deformation/`)*
     - `QuadraticOperad`, `QuadraticRelation`, `ColouredCooperad`, `KoszulDualBuilder`, `BarCobarResolution`: Implements algebraic operad deformation and Koszul duality.
  4. *Tier 4: Geometric (`geometric/`)*
     - `LittleDisksConfiguration`, `RectilinearDisk`: Little $n$-disks topological operad $D_n$ and homology operads $H_*(D_n)$ (associative, commutative, Gerstenhaber).
  5. *Tier 5: Applications (`applications/`)*
     - `OEASWorkflowOperad`: Workflow composition operad over admitted port colors (`OEAS_ADMITTED_PORT_COLOURS`).
     - `AgentCapabilitySlice`: Typed agent skill/capability boundaries.
  6. *Kernel Subsystem (`kernel/`)*
     - Implements execution licenses (`ActionLicense`, `AgentLicense`), term representations (`OperationTerm`, `LicensedTerm`, `NormalizedTerm`), proof obligations (`ProofObligation`, `ObligationBundle`), and 2-cell homotopy paths (`Path2`, `Homotopy2Cell`, `WhiskerPath2`).

#### B. `omega_operads`
- **Location:** `omega_engine/crates_rs/omega_operads`
- **Description:** Validated workflow and skill domain slices over sovereign operad kernels.
  - `planar.rs`: Implements planar tree substitutions `substitute(theta, index, phi)` and operation representations.
  - `workflow.rs`: Validates declared workflow pipelines against required keys (`workflow_id`, `source_colours`, `target_colour`, `pipeline`, `authority_effect`), checking color compatibility along composition steps. Emits `WorkflowReport` and `WorkflowFinding`.
  - `skill_garden.rs`: Culls inactive, superseded, or redundant skills from candidate libraries.
  - `immune_guards.rs`: **The critical bridge between operads and epistemic immunity.** Enforces `immune_guarded_substitute(...)` and `allosteric_consensus_substitute(...)`. Before allowing a planar substitution $\theta \circ_i \phi$, the engine queries `dyn ImmuneScreenPort`. If a danger gate or allosteric quorum blocks the operation, the substitution fails closed with `DANGER_GATE_SUPPRESSION` or `ALLOSTERIC_QUORUM_NOT_MET`.

---

## 3. Deep Dive: `omega_epistemic_immune_system`

### 3.1 Architectural Philosophy
- **Location:** `omega_engine/crates_rs/omega_epistemic_immune_system`
- **Core Claim:** Epistemic immunity is modeled as a formal biological immune system with central tolerance, two-signal activation gating, clonal selection, and authenticated formulary admission.
- **AuthorityEffect:** Strictly `"None"`.

### 3.2 The Four-Gate Protocol
The crate implements four immutable constitutional gates:

```
[Defect Observed]
       │
       ▼
[Gate 1: AntiSkillSpecV2::propose] ──► Status: PROPOSED (Immature)
       │
       ▼
[Gate 2: ThymusGate Negative Selection]
       │   ├── Matches Self Sample ──► RETIRED (Killed by Central Tolerance)
       │   └── Zero Reactivity to Self
       ▼
   Status: CANDIDATE
       │
       ▼
[Gate 3: Formulary / Authenticated Admission]
       │   └── Ed25519 Signed Attestation from Trusted Key Policy
       ▼
   Status: ADMITTED
       │
       ▼
[Gate 4: TwoSignalDangerGate]
       ├── Signal 1 (Pattern Match) ONLY ──► HOLD (HoldUncorroborated)
       └── Signal 1 + Signal 2 (Independent Danger) ──► ACTIVE FINDING
```

#### Gate 1: Defect Harvesting (`anti_skill.rs`)
- Newly harvested defect motifs are instantiated via `AntiSkillSpecV2::propose(...)`.
- **Constitutional Invariant (IMMUNE-001):** The constructor unconditionally sets `status: AntiSkillStatus::Proposed`. There is deliberately no constructor argument or public method to mint an `Admitted` anti-skill directly.
- Generates an immutable ID prefixed with `ab_` (e.g., `ab_3f8a92...`) by SHA-256 hashing schema version, pattern, failure class, and target scope.
- **12 Failure Classes (`FailureClass`):**
  1. `SemanticHallucination`
  2. `ApproximateContradiction`
  3. `ToyPromotion` (promoting toy models to universal theorems)
  4. `UnmechanizedProofClaim` (unverified informal proof claims)
  5. `SelfContradiction`
  6. `DualityGapNonZero` (non-zero primal-dual quotient gap)
  7. `BoundaryLeakage` (unauthorized information crossing isolation fences)
  8. `UnboundPortAssumption` (assuming unverified inputs)
  9. `CounterfeitExactness` (floating point masquerading as exact rationals)
  10. `SycophanticAgreement`
  11. `StructuralNonFit`
  12. `StaleCensusReference`

#### Gate 2: Central Tolerance Thymus Screen (`thymus.rs`)
- `ThymusGate` holds a sealed self-panel (`self_panel: Vec<String>`, with SHA-256 integrity digest `self_panel_hash`).
- Baseline self-panel protects core engineering truths: `"AuthorityEffect: None"`, `"exact rational duality gap is zero"`, `"verify_simplicial_boundary_law succeeds"`, `"Lean 4 lake build complete with 0 errors"`, etc.
- **Law 2:** If the anti-skill regex pattern matches ANY sample in the self-panel, `spec.retire()` is executed immediately, returning `ThymusVerdict::SelfReactive`.
- If and only if the detector exhibits zero reactivity across all self samples, it advances to `AntiSkillStatus::Candidate` (`ThymusVerdict::Survived`).

#### Gate 3: Authenticated Formulary Admission (`formulary.rs`, `authenticated.rs`)
- Candidate detectors cannot activate without external admission.
- `authenticated.rs` enforces Ed25519 signature verification using `ed25519_dalek::{Signature, VerifyingKey}` against a configured `TrustPolicy` (`POLICY_SCHEMA`).
- Admission requires an `Attestation` binding `spec_id`, `rule_digest`, `source_digest`, `subject_digest`, and `context_digest`.
- Successful verification transitions the detector to `AntiSkillStatus::Admitted`.

#### Gate 4: Two-Signal Danger Gating (`danger_gate.rs`)
- **Constitutional Invariant (IMMUNE-002):** Activation requires the strict conjunction of four predicates:
  $$\text{externally\_admitted}(g) \land \text{detector\_match}(g, \text{subject}) \land \text{independent\_danger}(s, c) \land \neg\text{suspended}(g)$$
- **Signal 1:** Regex pattern match on candidate text.
- **Signal 2 (`IndependentDangerSignal`):** External corroborating signal from an orthogonal host sensor:
  - `NonZeroDualityGap`
  - `FloatInExactChannel`
  - `InvalidSignature`
  - `BoundaryLeakageDetected`
  - `TestRegressionObserved`
  - `UnmechanizedProofClaim`
  - `AdversarialPromptInfiltration`
- **Anti-Collusion Rule:** A detector match cannot serve as its own danger signal. If Signal 1 matches without Signal 2, `TwoSignalDangerGate::evaluate` returns `DangerGateVerdict::HoldUncorroborated` (`reason: "TWO_SIGNAL_CONJUNCTION_UNSATISFIED_NO_INDEPENDENT_DANGER"`). This prevents `TWO_SIGNAL_COLLAPSE`.

#### Regulation & Feedback (`regulation.rs`, `clonal_selection.rs`)
- `TregSupervisor` tracks detector telemetry (`DetectorTelemetry`: activations, confirmed hits, false positives). If a detector's false positive rate breaches declared thresholds, it is automatically moved to `AntiSkillStatus::Suspended`.
- `clonal_selection.rs` implements affinity maturation: detectors that consistently corroborate true defects with zero false positives are selected for broader deployment across candidate pools.

---

## 4. Deep Dive: `omega_prompt_civilization`

### 4.1 Architecture & Role
- **Location:** `omega_engine/crates_rs/omega_prompt_civilization`
- **Role:** Models the evolution, genealogy, society structure, and metabolic selection of prompts, alongside the anti-skill pharmacy.

### 4.2 Prompt Families (`prompt_family.rs`)
A `PromptFamily` is the formal data structure tracking prompt evolution:
- **Core Types:**
  - `PromptFamily`: `readers: Vec<Reader>`, `nodes: Vec<PromptNode>`, `calls: Vec<CallRecord>`, `steps: Vec<RepairStep>`, `terminal: Option<Terminal>`.
  - `PromptNode`:
    - `prompt_digest`: SHA-256 digest of prompt content.
    - `relation`: Exact relationship tag (`"root"`, `"contains"`, `"repaired_from"`).
    - `parent_id`: Node ID of the parent prompt.
    - `shape`: Compact geometric bucketing (`byte_bucket`, `line_bucket`, `fence_count`, `question_count`).
    - `domain_labels`: List of `DomainLabel`s (`label`, `proposer_reader`, `status: proposed | checked`, `check_receipt`).
  - `CallRecord`: Execution record of an individual LLM turn (`bout_id`, `request_digest`, `reader_digest`, `leg_index`, `outcome`, `cost_microusd`, `input_tokens`, `output_tokens`, `ddc_letter`, `residual_colour`, `reply_digest`).
  - `RepairStep`: Step transforming an input prompt to an output prompt (`input_node_id`, `output_node_id`, `ddc_letter`, `residual_before`, `residual_after`, `call_ids`, `fitness`).

### 4.3 Prompt Sieve & Nested Ingestion
- **Seed Ingestion:** A seed prompt enters as a `PromptNode` with `relation: "root"` and `parent_id: None`.
- **Nested Prompts ("Prompts containing prompts"):** When a prompt contains nested sub-prompts or sub-tasks, they are parsed and added as child `PromptNode`s with `relation: "contains"` and `parent_id` referencing the enclosing prompt node.
- **Evolution Management:** When an obstruction or defect is repaired, a new child node is added with `relation: "repaired_from"`. The transition is recorded in a `RepairStep` that binds the exact Discrete Deformation Calculus (DDC) letter, residual reduction, and fitness delta.
- **Domain Lineage:** Lineages, domains, subdomains, and sub-subdomains are tracked via `domain_labels` on each node. Unchecked labels remain `"proposed"`; verified labels carry a `"check_receipt"` from an independent checker oracle.

### 4.4 Selection, Metabolism & Lamarckian Evolution
- **Lamarckian Tracking (`lamarckian.rs`):** Tracks cochain histories and residual reductions across turns (`LamarckianCochainTrackerV1`, `CochainResidualV1`). Mutations that successfully lower topological obstruction norms are rewarded.
- **Pareto Fitness (`fitness.rs`):** Multicriteria optimization over cost (micro-USD), token efficiency, and checker accuracy. Computes exact rational Pareto frontiers (`compute_pareto_fronts_rational`).
- **Exact PageRank (`rank.rs`):** Resolves prompt influence and centrality using exact rational PageRank calculations (`ExactPageRankSolverV1`).
- **Prompt Societies (`society.rs`, `ecology.rs`, `metabolism.rs`):** Manages multi-agent prompt societies (`PromptCivilizationV1`, `PromptSocietyV1`) subject to migration policies, token budgets, and metabolic pruning.

### 4.5 The Anti-Skill Pharmacy (`pharmacy.rs`)
- Separates detection from repair: `Finding` identifies defect locations and failure classes; it never returns or launders a repaired payload.
- Detects 12 experimental failure classes:
  - `SelfCertification`: Model declaring its own correctness.
  - `FakeReceipt`: Forged or fabricated cryptographic digests.
  - `ConclusionPreload`: Prompt embedding the required answer.
  - `SchemaSemanticLaundering`: Valid JSON masking invalid semantics.
  - `TheoremNameLaundering`: Citing named theorems without meeting hypotheses.
  - `OptimalityHallucination`: Claiming optimality without a loss function or bound.
  - `ComplexityHallucination`: Claiming asymptotic complexity without cost models.
  - `BranchDropExhaustion`: Claiming case exhaustion while dropping branches.
  - `PersonaAuthorityLeak`: Roleplay personas asserting administrative authority.
  - `PrivateCotDependency`: Asserting conclusions dependent on unrevealed scratchpad tokens.
  - `VersionDuplication`: Presenting identical bytes under different versions.
  - `DetectRepairCoupling`: Coupling a finding directly with a fix.
- Routing Dispositions: Findings map to `Disposition::Refuse`, `Disposition::Hold`, or `Disposition::Diag`.

---

## 5. Deep Dive: `omega_prompt_symbol_game`

### 5.1 Architecture & Role
- **Location:** `omega_engine/crates_rs/omega_symbol_game` (in workspace as `omega_symbol_game`)
- **Role:** Native host implementing the Symbol Game campaign runner, commit-reveal protocols, matched arms evaluation, and MCP server.

### 5.2 Game Rules & Commit-Reveal Protocol (`challenge.rs`)
The Symbol Game evaluates candidate solutions against challenges through a strict four-stage commit-reveal lifecycle:
1. **Commitment (`JudgeCommitmentV1`):** The judge operator commits to the challenge manifest (containing hidden test cases) by publishing its SHA-256 digest (`manifest_sha256`), operator ID, and version timestamp before the solver begins.
2. **Execution & Freezing (`FreezeRecordV1`):** The solver candidate executes in a sandboxed environment (`omega_sandbox`). Upon completion, the solver deliverable is frozen and hashed (`solver_deliverable_sha256`), binding it to the judge's commitment hash.
3. **Reveal & Verification (`JudgePacketV1`):** The hidden test cases are revealed to the evaluation engine alongside dual independent checkers (`checker_a_id`, `checker_b_id`).
4. **Scoring Receipt (`ChallengeScoreReceiptV1`):** Emits the final cryptographic receipt recording total cases, correct cases, wrong cases, and detailed case outcomes.

### 5.3 Winning Conditions & Dual Checker Oracles
Winning and failing conditions are governed by `evaluate_dual_checkers(...)`:
- `DisjointOutcome::Correct`: Both independent checkers return `Ok(true)`.
- `DisjointOutcome::Wrong`: Both independent checkers return `Ok(false)`.
- **The CheckerDefectPause Invariant:** If the two checkers disagree (one returns `Ok(true)` and the other returns `Ok(false)`), or if either checker throws an exception/error, **the candidate is NEVER penalized as `Wrong`**. Instead, execution enters `DisjointOutcome::CheckerDefectPause`. This guarantees that judge/checker defects cannot corrupt candidate evaluation.
- Failure modes: `SolverCrash`, `SolverTimeout`, `DeclaredOutOfScope`, `ScoringFault`.

### 5.4 Matched Arms Evaluation (`arms.rs`)
To prevent confounding factors in prompt and model evaluations, `check_arm_matching(arms: &[ArmSpecV1])` enforces strict baseline invariance:
- All arms must have IDENTICAL: `model_id`, `temperature_str`, `max_tokens`, `budget_micro_usd`, and `specification_hash`.
- ONLY `intervention_name` and `arm_id` may differ.
- Any discrepancy raises a typed `ArmMismatchError`.

### 5.5 Interfaces & CLI Entrypoints (`main.rs`, `mcp.rs`, `invoke.rs`)
- Binary: `omega_symbol_game`
- Flags:
  - `--mcp`: Runs the Model Context Protocol (MCP) server over stdin/stdout.
  - `--describe`: Outputs host capability descriptors.
  - `--describe-runtime`: Advertises all supported runtime action adapters derived directly from `invoke.rs`.
  - `invoke`: High-speed JSON action dispatcher over stdin/stdout.

---

## 6. Deep Dive: `omega_prompt_symbol_game_runtime`

### 6.1 Architecture & Role
- **Location:** `omega_engine/crates_rs/omega_symbol_game_runtime`
- **Role:** Execution state machine, round loop, strict descent turn driver, and exact mathematical kernels.

### 6.2 Strict Descent Turn Driver (`driver.rs`)
`driver.rs` enforces the fundamental mathematical invariant of the Symbol Game:
- **State Representation (`EngineTurnStateV1`):**
  - `round_seq`: Monotonic sequence counter.
  - `specification_digest`: Specification hash.
  - `current_phi1`: $\Phi_1$ boundary defect norm (integer/rational).
  - `current_gamma2`: $\Gamma_2$ curvature norm.
  - `open_defect_count`: Active defect count.
  - `cemetery_count`: Number of rejected moves.
- **The Strict Descent Contract:**
  A candidate move `DriverMovePacket` is accepted IF AND ONLY IF the metric tuple:
  $$(\Phi_1, \Gamma_2, \text{open\_defects})$$
  is componentwise non-increasing ($\le$) with at least **one strict decrease** ($<$).
- **Outcomes (`StepOutcome`):**
  - `Accepted`: Emits a `DdcStepRowV1` transition on the DDC tape and updates `EngineTurnStateV1`.
  - `RejectedNonDescent`: Move resulted in flat or increasing obstruction norms. Emits a `CemeteryRowV1` into the cemetery ledger.
  - `RejectedMalformed`: Move violated syntax or schema constraints. Emits a `CemeteryRowV1`.

### 6.3 Dual Canonical Encodings (`canonical.rs`, `packet_wire.rs`)
The runtime explicitly separates two wire encodings to prevent cross-language digest divergence:
1. `omega-sorted-json-no-float-v1` (Digest Envelope): Sorted-key JSON object refusing floats and non-ASCII characters. Used by `RoundRecord::seal` and host request addressing.
2. `omega-canonical-v1` (Typed Wire Format): Tagged tree in `canonical.rs` that explicitly encodes type tags:
   - Integers (`"i:..."`)
   - Rationals (`"r:p/q"`)
   - Binary data (`"b:..."`)
   - Structured lists and maps
   Framed with length-delimited domain digests via `domain_digest(domain, value)`.

### 6.4 Python Parity Task Turn (`pfp_task_turn.rs`)
- Implements exact byte-level parity with Python's PFP `PreparedTaskTurn`.
- Formats input prompts using `sorted_ascii_json` (separators `(‘,’, ‘:’)` with sorted keys).
- Strips bare `expected` fields from public cases while strictly rejecting hidden test labels (`expected_*`, `*_expected`, `ground_truth`, `solution`, etc.).
- Replays stored completions against retained `raw_reply_hex` and `raw_reply_sha256` to ensure that replay never calls external providers.

### 6.5 Exact Mathematical Kernels
- `f2.rs`: Exact $\mathbb{F}_2$ linear algebra, matrix Gaussian elimination, and gauge trichotomy classification (`GaugeBoard`).
- `rational.rs`: Exact rational linear programming duality and $L_1$ quotient distance certification over $\mathbb{Q}$ using `num_rational::BigRational`.
- `cochain.rs`: Finite cell complexes, coboundary operators, and cochain evaluation.

---

## 7. Synthesis and Cross-System Architectural Topology

The surveyed components form a coherent, self-reinforcing epistemic architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        omega_engine_pfp                                │
│  (Clean Architecture Application, Orchestration, EngineRS Beta App)   │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │ FFI via IPC                     │ pfp_task_turn
                   ▼                                 ▼
┌───────────────────────────────────┐    ┌───────────────────────────────┐
│        omega_symbol_game          │    │  omega_symbol_game_runtime    │
│  (Host CLI, MCP, Challenge Suite, │◄───┤  (Turn Driver, Strict Descent,│
│   Dual Checkers, Matched Arms)    │    │   Cemetery, F2/Rational, DDC) │
└──────────────────┬────────────────┘    └───────────────┬───────────────┘
                   │                                     │
                   ▼                                     ▼
┌───────────────────────────────────┐    ┌───────────────────────────────┐
│     omega_prompt_civilization     │    │       omega_operads &         │
│  (Prompt Families, Genealogy,     │◄───┤     omega_operad_theory       │
│   Lamarckian Descent, Pharmacy)   │    │  (Colored Operads, Workflows, │
└──────────────────┬────────────────┘    │   Koszul Duality, Substitutions)
                   │                     └───────────────┬───────────────┘
                   ▼                                     │
┌────────────────────────────────────────────────────────┴───────────────┐
│                   omega_epistemic_immune_system                        │
│   (Thymus Negative Selection, Two-Signal Danger Gating, Formulary)    │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Prompt Sieve to Civilization:** Incoming seed prompts are parsed into `PromptNode`s in `omega_prompt_civilization`. Nested prompts become child nodes (`contains`); repairs become lineage edges (`repaired_from`). Lamarckian cochain trackers record metric descents.
2. **Anti-Skill Pharmacy to EIS:** Defect detectors in `pharmacy.rs` identify 12 failure classes. Newly proposed detectors must pass the `ThymusGate` in `omega_epistemic_immune_system` against clean self-samples before advancing to candidate status, and require signed external attestations to enter the formulary.
3. **Immune Fencing of Operadic Workflows:** In `omega_operads`, planar tree substitutions ($\theta \circ_i \phi$) are gated by `ImmuneScreenPort`. Substitutions cannot execute if danger gates detect uncorroborated defects or allosteric quorums fail.
4. **Symbol Game Retraction Loop:** The `omega_symbol_game_runtime` turn driver receives untrusted candidate proposals, checks them against dual checker oracles (`omega_symbol_game`), and enforces strict monotonic descent in $(\Phi_1, \Gamma_2, \text{defects})$. Non-improving moves are routed to the Cemetery; valid moves emit cryptographic DDC tape receipts.
5. **Zero Authority Guarantee:** Across all eight components, every output envelope, receipt, and descriptor explicitly declares `AuthorityEffect: None`. No component mints administrative or execution authority without external compiled verification.

---

## 8. Defensible Boundary Claims

1. **What this code supports:**
   - Formal multi-gate epistemic defect screening separating detection from repair.
   - Exact rational and $\mathbb{F}_2$ computation with zero floating-point contamination.
   - Strict descent state tracking routing non-contractive proposals to cemetery rows.
   - Cross-language byte-level parity between Python PFP and Rust Symbol Game task turns.
   - Dual-oracle evaluation preventing judge errors from penalizing candidates (`CheckerDefectPause`).

2. **What this code does NOT support:**
   - Universal proof of prompt optimality (the $L_1$ residual only certifies absence of mined catalog patterns).
   - Automated self-admission of antibodies (central tolerance and external admission are strictly mandatory).
   - Equivalence of string pattern matches with mathematical proof verification.
