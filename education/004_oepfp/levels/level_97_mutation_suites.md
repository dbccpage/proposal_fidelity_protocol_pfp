---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 97: Mutation Testing & Mutant Kill Ratio Auditing"
kind: grammar-reference
level: 97
epoch: "Epoch IX"
domain: "Quality Assurance"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "VerificationToolchainModule"
evaluator_contract: "MutationTestingContract"
reachable_terminal_statuses:
  - ExactRepair
  - StabilizedSurvivor
  - OpenObstruction
  - LiftLicenseNeeded
  - Refused
  - Invalid
source_paths:
  - omega_engine_education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 97: Mutation Testing & Mutant Kill Ratio Auditing

**AuthorityEffect:** None.  
**Level:** Level 97 | **Epoch:** Epoch IX | **Domain:** Quality Assurance  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `AST mutant programs, test suite execution receipts, and mutation kill matrices`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_MUTATION_OPERATOR_DEFECT`  
**Evaluator Module:** `VerificationToolchainModule` (`MutationTestingContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `VerificationToolchainModule` or contract `MutationTestingContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 97 establishes the Proposal Fidelity Protocol (PFP) arena for **Mutation Testing & Mutant Kill Ratio Auditing** within the Quality Assurance bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{97} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `AST mutant programs, test suite execution receipts, and mutation kill matrices`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `VerificationToolchainModule` via `MutationTestingContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Auditing test suite mutation kill ratios against configured policy thresholds with explicit accounting of equivalent mutants.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 97        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `MutationTestingContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_MUTATION_OPERATOR_DEFECT`) are emitted exclusively by `MutationTestingContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 97 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_97` schema:

```json
{
  "schema_id": "sg_packet_level_97_quality_assurance",
  "task_data": {
    "level": 97,
    "epoch": "Epoch IX",
    "domain": "Quality Assurance",
    "carrier_digest": "blake3:carrier_level_97..."
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
    "source_digest": "sha256:src_referee_v1",
    "test_suite_digest": "sha256:tests_pfp_v1",
    "mutation_operators": [
      "AOR",
      "COR",
      "ROR",
      "LCR"
    ],
    "total_mutants": 100,
    "equivalent_mutants": 5,
    "testable_mutants": 95,
    "killed_mutants": 91,
    "observed_kill_ratio": "91/95",
    "policy_threshold": "9/10",
    "mutants": [
      {
        "mutant_id": "mut_001",
        "operator": "AOR",
        "status": "killed",
        "killed_by": "test_boundary"
      },
      {
        "mutant_id": "mut_002",
        "operator": "ROR",
        "status": "killed",
        "killed_by": "test_invariant"
      }
    ]
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_97"
  }
}
```

### AST Representation
```rust
pub struct MutationTestingPayload {
    pub source_digest: String,
    pub test_suite_digest: String,
    pub mutation_operators: Vec<String>,
    pub total_mutants: u32,
    pub equivalent_mutants: u32,
    pub testable_mutants: u32,
    pub killed_mutants: u32,
    pub observed_kill_ratio: BigRational,
    pub policy_threshold: BigRational,
    pub mutants: Vec<MutantRecord>,
}
```

---

## 4. Evaluator Module & Objective Metrics: VerificationToolchainModule

Referees evaluate candidates through `MutationTestingContract`:

Referees audit mutation testing suites for mutation score compliance and evidence integrity:
1. **Configured Threshold Evaluation:** Evaluates condition $\frac{M_{\text{killed}}}{M_{\text{testable}}} \ge \tau$ (configured policy $\tau = 0.90$).
2. **Equivalent Mutant Accounting:** Asserts that discounted equivalent mutants are explicitly justified and cataloged.
3. **Execution Receipt Check:** Verifies that each killed mutant is tied to a failing test execution receipt.
4. **Epistemic Fence:** $\tau = 0.90$ is an explicitly configured policy threshold, not a natural mathematical boundary.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Observed kill ratio satisfies configured threshold $\frac{M_{\text{killed}}}{M_{\text{testable}}} \ge \tau = 0.90$, equivalent mutants justified, and test execution receipts verify kills.
- **`StabilizedSurvivor` Admission Criterion:** Audited mutation test certificate recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 97 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_MUTATION_OPERATOR_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 97, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no mutant counts, so the threshold check in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example $M_{\text{testable}} = 100 - 5 = 95$, as recorded, and $M_{\text{killed}} / M_{\text{testable}} = 91/95 \approx 0.958 \ge 9/10$, so the threshold holds. Only 2 of the 91 killed mutants are listed with a killing test, so the receipt check (item 3) cannot be completed from the example, and the 5 equivalent mutants carry no recorded justification. The domain negative vector has $70/100 = 0.7 < 0.9$, so the threshold fails and `Refused` follows; it omits the equivalent-mutant count, so `testable_mutants: 100` is taken as given.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 97, "carrier_match": true, "killed_mutants": 70, "testable_mutants": 100, "policy_threshold": "9/10"}
  REFEREE:  REFUSED -> Refusal Code: ERR_MUTATION_OPERATOR_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 97, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of mutation test execution receipts, kill ratios, and explicit equivalent mutant accounting.
   - A proposed PFP packet envelope, `MutationTestingContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove that a test suite with 90% mutation kill ratio detects 100% of all possible production bugs.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the test suite killed at least the configured fraction of non-equivalent mutants generated by declared operators.
4. **Next test needed:**
   - Execute mutation suite runs across critical normal form parsers in the test harness.
