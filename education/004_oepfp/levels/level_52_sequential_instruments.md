---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 52: Sequential Measurements & Non-Commutative Collapse"
kind: grammar-reference
level: 52
epoch: "Epoch IV"
domain: "Quantum Logic"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "QuantumFoundationsModule"
evaluator_contract: "SequentialInstrumentContract"
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

# The Symbol Game Level 52: Sequential Measurements & Non-Commutative Collapse

**AuthorityEffect:** None.  
**Level:** Level 52 | **Epoch:** Epoch IV | **Domain:** Quantum Logic  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Ordered measurement sequences (A, B) with sequential branch weights and commutator metrics`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_MEASUREMENT_ORDER_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Sequential Instrument Composition & Measurement Order Evaluator`)  
**Evaluator Contract:** `SequentialInstrumentContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `SequentialInstrumentContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 52 establishes the Proposal Fidelity Protocol (PFP) arena for **Sequential Measurements & Non-Commutative Collapse** within the Quantum Logic bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{52} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Ordered measurement sequences (A, B) with sequential branch weights and commutator metrics`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`SequentialInstrumentContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Sequential Lüders projections, sequential joint probabilities P(a, b) = ||P_b P_a ψ||^2, and state-dependent order sensitivity.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 52         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `SequentialInstrumentContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_MEASUREMENT_ORDER_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 52 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_52_sequential_instruments` family schema:

```json
{
  "schema_id": "sg_packet_level_52_sequential_instruments",
  "task_data": {
    "level": 52,
    "epoch": "Epoch IV",
    "domain": "Quantum Logic",
    "carrier_digest": "blake3:b8d4e9..."
  },
  "protected_boundary": {
    "immutable_slots": ["carrier", "fuel_ceiling", "zero_relation_fences"],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "initial_state": [{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}],
    "instrument_a": "sigma_z_projectors",
    "instrument_b": "sigma_x_projectors",
    "sequential_outcome_pair": ["z_plus", "x_plus"],
    "joint_probability": "1/2",
    "order_reversal_defect": "1/4",
    "proposer_signature": "untrusted_candidate_token" 
  },
  "witness_data": {
    "replay_trace": ["init", "step_1"],
    "proof_certificate": null
  }
}
```

### AST Representation
```rust
pub struct SequentialInstrumentPayload {
    pub move_type: MoveType,
    pub initial_state: Vec<ComplexRational>,
    pub instrument_a: String,
    pub instrument_b: String,
    pub sequential_outcome_pair: [String; 2],
    pub joint_probability: Rational,
    pub order_reversal_defect: Rational,
    pub proposer_signature: String,
}

pub struct Level52Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SequentialInstrumentPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `SequentialInstrumentContract`

Referees evaluate Level 52 candidates through sequential projection composition:

1. **Sequential Instrument Composition:** Given state $|\psi\rangle$, evaluates instrument $A$ with projectors $\{P_a\}$ followed by instrument $B$ with projectors $\{Q_b\}$.
2. **Sequential Joint Probability:** Computes branch weight $P(a, b) = \| Q_b P_a |\psi\rangle \|^2 \in \mathbb{Q}$.
3. **State-Dependent Order Sensitivity:** Evaluates order-reversal difference $\| Q_b P_a |\psi\rangle - P_a Q_b |\psi\rangle \|^2$; note that $[P_a, Q_b] \ne 0$ permits order dependence but is state-dependent (it vanishes on shared eigenstates).
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff sequential branch weights satisfy the Lüders composition law over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant state-dependent non-commutativity witness $\| Q_b P_a |\psi\rangle - P_a Q_b |\psi\rangle \|^2 > 0$ is certified stable under licensed observation, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 52 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_MEASUREMENT_ORDER_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 52, "carrier_match": true, "move": "ASSERT", "initial_state": [{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}], "joint_probability": "1/2", "order_reversal_defect": "1/4"}
REFEREE:  ACCEPT -> Status: ExactRepair (sequential projection composition and order sensitivity verified over Q)
  ```

  **Worked check (2026-10-20):** with the section 3 instruments, P = P_{z+} = diag(1, 0), Q = Q_{x+} = (1/2)[[1, 1], [1, 1]] and ψ = (1, 0). Then Q P ψ = Q (1, 0) = (1/2, 1/2), so P(z+, x+) = 1/4 + 1/4 = 1/2. In the other order P Q ψ = P (1/2, 1/2) = (1/2, 0). The difference is (0, 1/2), with squared norm 1/4, matching `order_reversal_defect`.

  **Reproducibility gap (2026-10-20):** this proposal omits `instrument_a`, `instrument_b` and `sequential_outcome_pair`; the values above use the section 3 sketch.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 52, "carrier_match": true, "move": "ASSERT", "initial_state": [{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}], "joint_probability": "3/2"}
REFEREE:  REFUSED -> Refusal Code: ERR_MEASUREMENT_ORDER_DEFECT, Status: Refused (sequential joint probability 3/2 > 1 violates probability conservation)
  ```

  **Worked check (2026-10-20):** projectors do not increase norms, so ‖Q_b P_a ψ‖² ≤ ‖ψ‖² = 1. A declared joint probability of 3/2 is therefore not attainable.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 52, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 52: Sequential Measurements & Non-Commutative Collapse within the Quantum Logic bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`SequentialInstrumentContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 52 specifies an exact, deterministic evaluation procedure for candidate proposals over `Ordered measurement sequences (A, B) with sequential branch weights and commutator metrics`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
