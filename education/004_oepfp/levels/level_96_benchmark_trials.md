---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 96: Hermetic Benchmark Trials & Variance Analysis"
kind: grammar-reference
level: 96
epoch: "Epoch IX"
domain: "Empirical Evaluation"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "VerificationToolchainModule"
evaluator_contract: "BenchmarkAnalysisContract"
reachable_terminal_statuses:
  - ExactRepair
  - StabilizedSurvivor
  - OpenObstruction
  - LiftLicenseNeeded
  - Refused
  - Invalid
source_paths:
  - education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 96: Hermetic Benchmark Trials & Variance Analysis

**AuthorityEffect:** None.  
**Level:** Level 96 | **Epoch:** Epoch IX | **Domain:** Empirical Evaluation  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Hermetic benchmark execution suites, repeated trial manifests, and statistical dispersion records`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_TRIAL_MANIFEST_DEFECT`  
**Evaluator Module:** `VerificationToolchainModule` (`BenchmarkAnalysisContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `VerificationToolchainModule` or contract `BenchmarkAnalysisContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 96 establishes the Proposal Fidelity Protocol (PFP) arena for **Hermetic Benchmark Trials & Variance Analysis** within the Empirical Evaluation bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{96} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Hermetic benchmark execution suites, repeated trial manifests, and statistical dispersion records`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `VerificationToolchainModule` via `BenchmarkAnalysisContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Auditing repeated benchmark trial variance, confidence intervals, and statistical dispersion in hermetic environments.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 96        ┌──────────────────────────┐
│     Untrusted Neural     ├────────────────────────────────────────►│    Deterministic Host    │
│    Proposer (Player)     │◄────────────────────────────────────────┤      Checker (Rust)      │
└──────────────────────────┘          Typed Terminal Receipt         └────────────┬─────────────┘
                                                                                  │
                                             Emits Immutable Verification Receipt ▼
                                                                     ┌──────────────────────────┐
                                                                     │   Residual Loss Ledger   │
                                                                     │  (Zero Authority Mints)  │
                                                                     └──────────────────────────┘
```

1. **Untrusted Proposer Role:** Submits candidate move proposals formatted as typed wire envelopes. Proposer outputs carry zero ambient trust and cannot mutate board configuration directly.
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `BenchmarkAnalysisContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_TRIAL_MANIFEST_DEFECT`) are emitted exclusively by `BenchmarkAnalysisContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 96 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_96` schema:

```json
{
  "schema_id": "sg_packet_level_96_empirical_evaluation",
  "task_data": {
    "level": 96,
    "epoch": "Epoch IX",
    "domain": "Empirical Evaluation",
    "carrier_digest": "blake3:carrier_level_96..."
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "benchmark_id": "bmk_homology_solve_v1",
    "corpus_digest": "sha256:corpus_pfp_test_v1",
    "environment_digest": "sha256:env_pinned_hw_v1",
    "seed": 1337,
    "repetitions": 10,
    "timing_samples_ns": [
      10200,
      10150,
      10300,
      10250,
      10180,
      10220,
      10290,
      10170,
      10240,
      10210
    ],
    "mean_ns": 10221,
    "std_dev_ns": 49,
    "ci_method": "bootstrap_percentile_95"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_96"
  }
}
```

### AST Representation
```rust
pub struct BenchmarkAnalysisPayload {
    pub benchmark_id: String,
    pub corpus_digest: String,
    pub environment_digest: String,
    pub seed: u64,
    pub repetitions: u32,
    pub timing_samples_ns: Vec<u64>,
    pub mean_ns: u64,
    pub std_dev_ns: u64,
    pub ci_method: String,
}
```

---

## 4. Evaluator Module & Objective Metrics: VerificationToolchainModule

Referees evaluate candidates through `BenchmarkAnalysisContract`:

Referees audit empirical benchmark trials for reproducibility and statistical dispersion:
1. **Sample Size Adequacy:** Asserts repetition count satisfies minimum empirical threshold ($K \ge 10$).
2. **Dispersion Bound:** Verifies that coefficient of variation is within stability limits: $\sigma / \mu \le 0.15$.
3. **Environment Parity:** Confirms hardware and OS configuration match pinned `environment_digest`.
4. **Reproducibility:** Replays benchmark sampling under pinned seed to verify timing distribution consistency.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Repetitions $K \ge 10$, coefficient of variation $\sigma / \mu \le 0.15$, and environment and corpus digests match declared benchmark configuration.
- **`StabilizedSurvivor` Admission Criterion:** Hermetic benchmark trial receipt certified under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 96 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_TRIAL_MANIFEST_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 96, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no samples or digests, so the checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example the ten samples sum to $102210$, so $\mu = 10221$ ns exactly, as recorded. The squared deviations sum to $22090$. The population standard deviation is $\sqrt{22090/10} = \sqrt{2209} = 47$ ns exactly; the sample standard deviation is $\sqrt{22090/9} \approx 49.54$ ns. The recorded `std_dev_ns: 49` therefore matches the sample deviation truncated (rounding gives 50); the packet should state which estimator and rounding it uses. Either way the coefficient of variation is about $49.54 / 10221 \approx 0.0048 \le 0.15$, and $K = 10 \ge 10$, so both thresholds hold. The bootstrap interval is not given, so it cannot be checked. The domain negative vector has $K = 3 < 10$, so the sample-size check fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 96, "carrier_match": true, "repetitions": 3}
  REFEREE:  REFUSED -> Refusal Code: ERR_TRIAL_MANIFEST_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 96, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of benchmark trial sample size, statistical variance bounds, and environment parameter pinning.
   - A proposed PFP packet envelope, `BenchmarkAnalysisContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove identical benchmark latency across uncalibrated cloud virtual machines or variable clock rates.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the benchmark trial met statistical stability and sample size criteria in the controlled test harness.
4. **Next test needed:**
   - Execute benchmark trial sweeps with bootstrap confidence intervals on solver operations.
