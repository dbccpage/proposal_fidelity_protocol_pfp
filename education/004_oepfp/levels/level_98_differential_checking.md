---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 98: Differential Fuzzing & Dual-Engine Parity"
kind: grammar-reference
level: 98
epoch: "Epoch IX"
domain: "Security Testing"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "VerificationToolchainModule"
evaluator_contract: "DifferentialCheckingContract"
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

# The Symbol Game Level 98: Differential Fuzzing & Dual-Engine Parity

**AuthorityEffect:** None.  
**Level:** Level 98 | **Epoch:** Epoch IX | **Domain:** Security Testing  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Dual independent execution engines, canonical input vectors, and output comparison matrices`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_CHECKER_PAIR_DEFECT`  
**Evaluator Module:** `VerificationToolchainModule` (`DifferentialCheckingContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `VerificationToolchainModule` or contract `DifferentialCheckingContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 98 establishes the Proposal Fidelity Protocol (PFP) arena for **Differential Fuzzing & Dual-Engine Parity** within the Security Testing bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{98} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Dual independent execution engines, canonical input vectors, and output comparison matrices`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `VerificationToolchainModule` via `DifferentialCheckingContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying output parity between independent implementations under canonical differential inputs.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 98        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `DifferentialCheckingContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_CHECKER_PAIR_DEFECT`) are emitted exclusively by `DifferentialCheckingContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 98 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_98` schema:

```json
{
  "schema_id": "sg_packet_level_98_security_testing",
  "task_data": {
    "level": 98,
    "epoch": "Epoch IX",
    "domain": "Security Testing",
    "carrier_digest": "blake3:carrier_level_98..."
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
    "engine_a": "core_linear_algebra_rust_v1",
    "engine_b": "numpy_reference_v1_26",
    "input_digest": "sha256:input_canonical_simplex_01",
    "output_a_digest": "blake3:out_a_001_exact",
    "output_b_digest": "blake3:out_b_001_exact",
    "comparison_rule": "exact_rational_match",
    "divergence_witness": null
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_98"
  }
}
```

### AST Representation
```rust
pub struct DifferentialCheckingPayload {
    pub engine_a: String,
    pub engine_b: String,
    pub input_digest: String,
    pub output_a_digest: String,
    pub output_b_digest: String,
    pub comparison_rule: String,
    pub divergence_witness: Option<String>,
}
```

---

## 4. Evaluator Module & Objective Metrics: VerificationToolchainModule

Referees evaluate candidates through `DifferentialCheckingContract`:

Referees evaluate differential testing results across independent execution engines:
1. **Engine Independence Check:** Confirms that Engine A and Engine B represent distinct codebases/architectures.
2. **Canonical Input Evaluation:** Executes both engines on the identical canonical input vector.
3. **Output Normalization:** Applies declared comparison rules to normalize representations over $\mathbb{Q}$.
4. **Parity Assertion:** Asserts exact equivalence $O_A = O_B$; any discrepancy produces a divergence witness.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Both engines declared and independent, canonical input evaluated on both, outputs normalized and compared, and exact parity verified ($O_A = O_B$).
- **`StabilizedSurvivor` Admission Criterion:** Differential parity certificate recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 98 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_CHECKER_PAIR_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 98, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no engines, input or outputs, so the parity check in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only. In the section 3 schema example the output digests are placeholder labels, and the pairing is questionable: `engine_b` is NumPy, whose default arithmetic is IEEE-754 floating point, so `comparison_rule: "exact_rational_match"` needs a declared conversion from its floats to rationals (or a NumPy object array of exact fractions) before an exact comparison means anything. The domain negative vector reports differing output digests and a divergence witness, so parity fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 98, "carrier_match": true, "output_a_digest": "sha256:diff_a", "output_b_digest": "sha256:diff_b", "divergence_witness": "divergence_at_cell_3"}
  REFEREE:  REFUSED -> Refusal Code: ERR_CHECKER_PAIR_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 98, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of output parity between dual independent execution engines on canonical inputs.
   - A proposed PFP packet envelope, `DifferentialCheckingContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove mathematical correctness if both independent engines share an identical specification defect.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that two distinct implementations produced identical normalized outputs on the tested inputs.
4. **Next test needed:**
   - Execute differential testing runs between Rust and Python normal form evaluators.
