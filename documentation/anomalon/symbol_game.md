# Symbol Game and Strict Descent Runtime: `omega_symbol_game` and `omega_symbol_game_runtime`

**AuthorityEffect:** None  
**Status:** Code-Grounded Reference Documentation  
**Repository Paths:**
- `omega_symbol_game`: `c:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\omega_symbol_game`
- `omega_symbol_game_runtime`: `c:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\omega_symbol_game_runtime`
**Governing Standard:** Commit-Reveal Challenge Protocol, Dual Oracles, Strict Retraction Descent, and Exact Mathematical Kernels  

---

## 1. Architectural Role and Division of Labor

The Symbol Game represents the core evaluation and retraction harness of the Anomalon architecture. Its execution is cleanly split across two crates:
1. **`omega_symbol_game` (Host & Orchestrator):** Manages the commit-reveal challenge lifecycle, sandboxed candidate execution, dual checker oracle coordination, matched arms evaluation, CLI entrypoints, and the Model Context Protocol (MCP) server.
2. **`omega_symbol_game_runtime` (State Machine & Mathematical Kernels):** Enforces strict descent turn driving, non-improving cemetery routing, dual wire serialization codecs, and exact mathematical kernels over $\mathbb{Q}$ and $\mathbb{F}_2$.

Every message, packet envelope, and score receipt emitted across both crates declares `AuthorityEffect: None`.

---

## 2. Deep Dive: `omega_symbol_game`

### 2.1 The Commit-Reveal Challenge Protocol (`src/challenge.rs`)
To prevent data contamination, prompt preloading, and retrospective grading bias, challenges are evaluated through an immutable four-stage commit-reveal lifecycle:

```
[Phase 1: Commitment]
  Judge publishes JudgeCommitmentV1 (manifest_sha256)
               │
               ▼
[Phase 2: Execution & Freezing]
  Candidate executes sandboxed via omega_sandbox
  Candidate output sealed in FreezeRecordV1 (deliverable_sha256)
               │
               ▼
[Phase 3: Reveal]
  Judge publishes JudgePacketV1 revealing hidden cases & dual checkers
               │
               ▼
[Phase 4: Dual Oracle Scoring]
  Checkers A & B evaluate candidate against hidden cases
  Emits ChallengeScoreReceiptV1
```

#### Protocol Stages & Data Structures
1. **`JudgeCommitmentV1` (Commitment Phase):**
   - The evaluation host commits to the challenge test suite before solver candidate dispatch:
     ```rust
     pub struct JudgeCommitmentV1 {
         pub challenge_id: String,
         pub manifest_sha256: String,
         pub committed_at_utc: String,
         pub operator: String,
         pub version: String,
         pub authority_effect: String,
     }
     ```
   - Emits a cryptographic `commitment_hash()`.
2. **`FreezeRecordV1` (Freezing Phase):**
   - Candidate executes in isolation via `omega_sandbox`.
   - The resulting deliverable bytes are frozen and hashed into `solver_deliverable_sha256`, cryptographically binding the deliverable to `judge_commitment_hash`.
3. **`ParticipantPacketV1` vs `JudgePacketV1` (Reveal Phase):**
   - Solvers receive only `ParticipantPacketV1`, containing public example cases, prompt templates, token limits, and `judge_commitment_hash`.
   - Upon deliverable freezing, the host reveals `JudgePacketV1`, exposing `hidden_cases` alongside the identities of two independent checker oracles (`checker_a_id`, `checker_b_id`).
4. **`ChallengeScoreReceiptV1` (Scoring Phase):**
   - Emits the final immutable score receipt recording total cases, correct cases, wrong cases, active defect pauses, and per-case outcome records.

### 2.2 Dual Checker Oracles & The `CheckerDefectPause` Invariant
Case evaluations are governed by `evaluate_dual_checkers(...)` across two distinct oracles:
- `DisjointOutcome::Correct`: Both independent checkers return `Ok(true)`.
- `DisjointOutcome::Wrong`: Both independent checkers return `Ok(false)`.

#### The `CheckerDefectPause` Invariant
If the two checkers disagree (e.g., Checker A returns `Ok(true)` while Checker B returns `Ok(false)`), or if either checker throws an internal error or execution fault:
- **The candidate is NEVER penalized as `Wrong`.**
- Execution immediately enters `DisjointOutcome::CheckerDefectPause { checker_a_result, checker_b_result, detail }`.
- **Rationale:** Prevents flaws, ambiguities, or drift in evaluation oracles from penalizing candidate solvers. Scoring pauses until human or formal arbitration resolves the oracle dispute.

Additional failure outcomes include:
- `SolverCrash { exit_code, error }`: Non-zero process exit or panic.
- `SolverTimeout { limit_ms }`: Execution exceeded hard wall-clock limits.
- `DeclaredOutOfScope { reason }`: Explicit refusal by candidate to answer out-of-scope tasks.
- `ScoringFault { error }`: Failure in score serialization or ledger persistence.

### 2.3 Matched Arms Evaluation (`src/arms.rs`)
To ensure causal validity in model and prompt comparisons, `check_arm_matching(arms: &[ArmSpecV1])` enforces strict baseline invariance:
- All arms in an experimental cohort must have **IDENTICAL**:
  - `model_id`
  - `temperature_str`
  - `max_tokens`
  - `budget_micro_usd`
  - `specification_hash`
- **Permitted Variance:** ONLY `intervention_name` and `arm_id` may differ.
- If any baseline parameter diverges, evaluation halts with a typed `ArmMismatchError` (`ModelMismatch`, `TemperatureMismatch`, `MaxTokensMismatch`, `BudgetMismatch`, `SpecificationMismatch`).

### 2.4 Interfaces: CLI, Dispatcher, and MCP (`src/main.rs`, `src/invoke.rs`, `src/mcp.rs`)
The binary `omega_symbol_game` provides three invocation surfaces:
- **CLI (`main.rs`):** Standard argument parser for offline campaign execution, audit runs, and benchmark validation.
- **Action Dispatcher (`invoke.rs`):** High-speed JSON action dispatcher over standard I/O used by Python's `RustSymbolGameHost` seam (`ffi.py`). Advertises capabilities via `--describe-runtime`.
- **Model Context Protocol (`mcp.rs`):** Native MCP server over stdin/stdout via `--mcp`, exposing tool interfaces for tool-calling agents.

---

## 3. Deep Dive: `omega_symbol_game_runtime`

### 3.1 Strict Descent Turn Driver (`src/driver.rs`)
The turn driver implements the fundamental mathematical contract of the Symbol Game: candidate proposals advance the system frontier if and only if they strictly reduce topological obstruction mass.

#### Engine State (`EngineTurnStateV1`)
```rust
pub struct EngineTurnStateV1 {
    pub round_seq: u64,
    pub specification_digest: String,
    pub current_phi1: u64,
    pub current_gamma2: u64,
    pub open_defect_count: u64,
    pub previous_code: Option<String>,
    pub previous_diff: Option<String>,
    pub open_obligations: Vec<String>,
    pub promoted_operands: Vec<String>,
    pub cemetery_count: u64,
}
```

#### The Strict Descent Contract
When a candidate submits a proposal packet `DriverMovePacket { candidate_id, proposed_diff, declared_phi1, declared_gamma2, ... }`, the driver evaluates:

```rust
let non_increasing = candidate.declared_phi1 <= state.current_phi1
    && candidate.declared_gamma2 <= state.current_gamma2;
let strict_decrease = candidate.declared_phi1 < state.current_phi1
    || candidate.declared_gamma2 < state.current_gamma2;

if !non_increasing || !strict_decrease {
    let cemetery = CemeteryRowV1 {
        candidate_id: candidate.candidate_id.clone(),
        round_seq: state.round_seq,
        rejection_reason: "NON_DESCENDING_CANDIDATE".to_string(),
        attempted_diff: candidate.proposed_diff.clone(),
        phi1_before: state.current_phi1,
        gamma2_before: state.current_gamma2,
        phi1_after: candidate.declared_phi1,
        gamma2_after: candidate.declared_gamma2,
        authority_effect: "None".to_string(),
    };
    return StepOutcome::RejectedNonDescent { cemetery_row: cemetery, ... };
}
```

- **Contract Rule:** Obstruction mass $(\Phi_1, \Gamma_2)$ must be componentwise non-increasing ($\le$) with at least **one strict decrease** ($<$).
- **Accepted Moves:** Emits a `DdcStepRowV1` transition on the DDC tape, updates `EngineTurnStateV1`, and increments `round_seq`.
- **Non-Decreasing Moves:** Routed to `CemeteryRowV1`. The move is permanently recorded in the cemetery ledger to prevent cycle traps, and `cemetery_count` increments without state advancement.

### 3.2 Dual Canonical Wire Encodings (`canonical.rs`, `packet_wire.rs`)
To prevent cross-language serialization drift between Python and Rust, the runtime defines two distinct canonical wire codecs:

1. **`omega-sorted-json-no-float-v1` (`packet_wire.rs`):**
   - Sorted-key JSON encoding that strictly refuses IEEE-754 floats and non-ASCII characters.
   - Enforces key sorting, compact delimiters `(',', ':')`, and ASCII encoding.
   - Used for top-level request addressing, digest envelopes, and audit logs.
2. **`omega-canonical-v1` (`canonical.rs`):**
   - Strongly-typed wire encoding using explicit value prefixes:
     - Integers: `["omega-canonical-v1", "i", "<decimal>"]`
     - Exact Rationals: `["omega-canonical-v1", "r", "<numerator>/<denominator>"]`
     - Binary Blobs: `["omega-canonical-v1", "b", "<hex>"]`
     - Structured Lists & Maps: `["omega-canonical-v1", "l", [...]]` and `["omega-canonical-v1", "m", [...]]`
   - Integrates length-delimited domain digests via `domain_digest(domain, value)`:
     $$\mathrm{digest} = \mathrm{SHA256}(\text{len}(\text{domain}) \,\|\, \text{domain} \,\|\, \text{len}(\text{wire}) \,\|\, \text{wire})$$

### 3.3 Exact Mathematical Kernels

#### A. Exact $\mathbb{F}_2$ Linear Algebra & The Gauge Trichotomy (`src/f2.rs`)
Implements exact modular arithmetic over the Galois field $\mathbb{F}_2 = \{0, 1\}$ without floating point:
- **`F2Matrix`:** Dense matrix representation in row-major order with explicit wire validation (`F2MatrixWire`).
- **The Gauge Trichotomy:** Given boundary operators $D_0 \in \mathbb{F}_2^{E \times V}$ and $D_1 \in \mathbb{F}_2^{F \times E}$ with $D_1 \cdot D_0 = 0$, and a parity cochain $a \in \mathbb{F}_2^E$, exactly one of three cases holds, each bearing an explicit mathematical witness:
  1. **`LocalCurvature`:** $\kappa = D_1 \cdot a \neq 0$. Witnessed by the non-zero syndrome $\kappa$. No vertex gauge transformation can remove this defect because $D_1 \cdot D_0 = 0$.
  2. **`GaugeExact`:** $\kappa = 0$ and $D_0 \cdot \lambda = a$ is solvable. Witnessed directly by the gauge vector $\lambda \in \mathbb{F}_2^V$.
  3. **`GlobalH1Obstruction`:** $\kappa = 0$ and $a \notin \mathrm{im}(D_0)$. Witnessed by a dual separator $z \in \ker(D_0^T)$ such that $\langle a, z \rangle = 1$. Over $\mathbb{F}_2$, $\mathrm{im}(D_0)^\perp = \ker(D_0^T)$, ensuring that this separator witness always exists.

#### B. Exact Rational LP Duality & $L_1$ Quotient Norms (`src/rational.rs`)
Computes linear programming duality and $L_1$ quotient distances over the field of exact rationals $\mathbb{Q}$ using `num_rational::BigRational`:
- **The Host Discipline:** The host verifies candidate certificates; it does not perform heuristic search. A candidate proposes primal-dual pairs $(p, y)$ or $(x, u)$; the host checks feasibility and exact numerical equality.
- **Duality Verification:** Verifies that the primal and dual objective values coincide:
  $$c^T x = b^T y$$
  An exact match certifies zero duality gap without numerical tolerances or $\epsilon$-thresholds.

#### C. Prompt Cochain Complexes (`src/cochain.rs`)
Evaluates oriented finite cell complexes $C^0 \to C^1 \to C^2$ over $\mathbb{Q}$:
- **Primary Quotient Obstruction:**
  $$\Phi_1(c) = \min_{a \in C^0} \|c - d_0 a\|_1$$
- **Secondary Closure Defect:**
  $$\Gamma_2(c) = \|d_1 c\|_1$$
- **Four-Way Typed Dispositions:**
  - `ExactCoboundary`: $\Phi_1 = 0$, $\Gamma_2 = 0$.
  - `ClosedNonExactClass`: $\Phi_1 > 0$, $\Gamma_2 = 0$.
  - `NonClosedEdgeData`: $\Gamma_2 > 0$ (implies $\Phi_1 > 0$).
  - `Refusal`: $\Phi_1 = 0$, $\Gamma_2 > 0$ (`IMPOSSIBLE_PROFILE` for a valid complex), dimension mismatch, chain law violation ($d_1 \circ d_0 \neq 0$), or budget exhaustion.
- **The Prime Triad:**
  - `Prime 000`: Admission before measurement (freezes source bytes, verifies matrix dimensions, confirms $d_1 d_0 = 0$).
  - `Prime 001`: Descent soundness (verifies adapter descent and preservation of protected answers).
  - `Prime 002`: Residual-aware continuation and budget halting predicate.

### 3.4 Python Parity Task Turn (`src/pfp_task_turn.rs`)
Maintains byte-level parity with Python's `PreparedTaskTurn`:
- Formats input prompts using sorted ASCII JSON key order.
- Strips bare expected fields from public cases while rejecting reserved label tokens (`expected_*`, `*_expected`, `ground_truth`, `solution`).
- Binds replay executions to retained `raw_reply_hex` and `raw_reply_sha256`, supporting deterministic offline replay under declared assumptions.

---

## 4. Defensible Claims and Safety Boundaries

1. **What this code supports:**
   - Complete commit-reveal integrity preventing post-hoc challenge tampering.
   - Immunity of candidate scoring to judge/checker defects via the `CheckerDefectPause` invariant.
   - Monotonicity of system state via strict descent checks and cemetery routing under declared metrics.
   - Exact mathematical certification over $\mathbb{Q}$ and $\mathbb{F}_2$ with zero floating-point noise.

2. **What this code does NOT support:**
   - Broad proof of code optimality (descent confirms only reduction relative to declared obstruction metrics $\Phi_1$ and $\Gamma_2$).
   - Autonomous oracle generation (checkers and test manifests must be committed by external operators prior to solver runs).
