---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 56: Environment Tracing & Mixed Density Matrices"
kind: grammar-reference
level: 56
epoch: "Epoch IV"
domain: "Open Quantum Systems"
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
evaluator_contract: "PartialTraceContract"
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

# The Symbol Game Level 56: Environment Tracing & Mixed Density Matrices

**AuthorityEffect:** None.  
**Level:** Level 56 | **Epoch:** Epoch IV | **Domain:** Open Quantum Systems  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Bipartite density matrices ρ_AB over Q(i) with partial trace reductions ρ_A = Tr_B(ρ_AB)`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_JOINT_STATE_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Bipartite Density Matrix & Partial Trace Reduction Evaluator`)  
**Evaluator Contract:** `PartialTraceContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `PartialTraceContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 56 establishes the Proposal Fidelity Protocol (PFP) arena for **Environment Tracing & Mixed Density Matrices** within the Open Quantum Systems bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{56} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Bipartite density matrices ρ_AB over Q(i) with partial trace reductions ρ_A = Tr_B(ρ_AB)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`PartialTraceContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Hermitian PSD density matrices over Q(i), unit trace, subsystem partial trace ρ_A = Tr_B(ρ_AB), and correlation-induced mixing.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 56         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `PartialTraceContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_JOINT_STATE_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 56 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_56_environment_tracing` family schema:

```json
{
  "schema_id": "sg_packet_level_56_environment_tracing",
  "task_data": {
    "level": 56,
    "epoch": "Epoch IV",
    "domain": "Open Quantum Systems",
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
    "joint_dim_a": 2,
    "joint_dim_b": 2,
    "joint_density_matrix": [
      ["1/2", "0", "0", "0"],
      ["0", "0", "0", "0"],
      ["0", "0", "0", "0"],
      ["0", "0", "0", "1/2"]
    ],
    "reduced_density_matrix_a": [
      ["1/2", "0"],
      ["0", "1/2"]
    ],
    "purity_reduced_a": "1/2",
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
pub struct PartialTracePayload {
    pub move_type: MoveType,
    pub joint_dim_a: u32,
    pub joint_dim_b: u32,
    pub joint_density_matrix: Vec<Vec<Rational>>,
    pub reduced_density_matrix_a: Vec<Vec<Rational>>,
    pub purity_reduced_a: Rational,
    pub proposer_signature: String,
}

pub struct Level56Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: PartialTracePayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `PartialTraceContract`

Referees evaluate Level 56 candidates through density operator mechanics and partial trace reductions:

1. **Bipartite Density Operator Validation:** Evaluates joint matrix $\rho_{AB} \in \mathbb{Q}(i)^{d_A d_B \times d_A d_B}$, asserting Hermiticity $\rho_{AB}^\dagger = \rho_{AB}$, positive semi-definiteness, and unit trace $\operatorname{Tr}(\rho_{AB}) = 1$.
2. **Subsystem Partial Trace:** Evaluates reduction over environment $B$:
   $$(\rho_A)_{j,k} = \sum_{m=1}^{d_B} (\rho_{AB})_{(j,m),(k,m)} \in \mathbb{Q}(i)$$
3. **Correlation-Induced Mixing:** Scoped note (corrected 2026-10-20): for a pure joint state, $\rho_A$ is mixed ($\operatorname{Tr}(\rho_A^2) < 1$) exactly when the state is entangled. For a mixed joint state, $\rho_A$ can be mixed without any correlation: the product state $\rho_{AB} = \tfrac{1}{2} I \otimes |0\rangle\langle 0|$ has $\operatorname{Tr}(\rho_A^2) = 1/2$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff joint density matrix is valid and reduced density matrix $\rho_A$ matches $\operatorname{Tr}_B(\rho_{AB})$ identically over $\mathbb{Q}(i)$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant reduced mixed state resulting from partial tracing of an entangled joint system is admitted with verified purity $\operatorname{Tr}(\rho_A^2) < 1$, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 56 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_JOINT_STATE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 56, "carrier_match": true, "move": "ASSERT", "joint_dim_a": 2, "joint_dim_b": 2, "reduced_density_matrix_a": [["1/2", "0"], ["0", "1/2"]], "purity_reduced_a": "1/2"}
REFEREE:  ACCEPT -> Status: ExactRepair (partial trace reduction matches joint density matrix over Q(i))
  ```

  **Worked check (2026-10-20):** with the section 3 matrix ρ_AB = diag(1/2, 0, 0, 1/2) in the basis |00⟩, |01⟩, |10⟩, |11⟩: (ρ_A)_{00} = ρ_{00,00} + ρ_{01,01} = 1/2 + 0 and (ρ_A)_{11} = ρ_{10,10} + ρ_{11,11} = 0 + 1/2, and the off-diagonal sums are 0. So ρ_A = I/2 and Tr(ρ_A²) = 1/4 + 1/4 = 1/2. This ρ_AB is a classically correlated separable mixture, not an entangled state, so it does not meet the `StabilizedSurvivor` clause about entangled joint systems.

  **Reproducibility gap (2026-10-20):** this proposal omits `joint_density_matrix`; the check above uses the section 3 sketch.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 56, "carrier_match": true, "move": "ASSERT", "joint_density_matrix": [["1", "0"], ["1", "0"]]}
REFEREE:  REFUSED -> Refusal Code: ERR_JOINT_STATE_DEFECT, Status: Refused (proposed joint matrix fails Hermiticity: ρ != ρ^dagger)
  ```

  **Worked check (2026-10-20):** entry (0,1) is 0 and entry (1,0) is 1, so ρ ≠ ρ†. The matrix is also 2×2, while two qubits need a 4×4 joint matrix.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 56, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 56: Environment Tracing & Mixed Density Matrices within the Open Quantum Systems bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`PartialTraceContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 56 specifies an exact, deterministic evaluation procedure for candidate proposals over `Bipartite density matrices ρ_AB over Q(i) with partial trace reductions ρ_A = Tr_B(ρ_AB)`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
