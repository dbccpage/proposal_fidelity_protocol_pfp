---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 49: Qubit States & Pauli/Bloch Representation"
kind: grammar-reference
level: 49
epoch: "Epoch IV"
domain: "Qubit Geometry"
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
evaluator_contract: "BlochQubitContract"
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

# The Symbol Game Level 49: Qubit States & Pauli/Bloch Representation

**AuthorityEffect:** None.  
**Level:** Level 49 | **Epoch:** Epoch IV | **Domain:** Qubit Geometry  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Two-level qubit states in Q(i)^2 with rational Bloch vectors and Pauli representations`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SPIN_BASIS_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Two-Level Qubit State & Rational Bloch Vector Evaluator`)  
**Evaluator Contract:** `BlochQubitContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `BlochQubitContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 49 establishes the Proposal Fidelity Protocol (PFP) arena for **Qubit States & Pauli/Bloch Representation** within the Qubit Geometry bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{49} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Two-level qubit states in Q(i)^2 with rational Bloch vectors and Pauli representations`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`BlochQubitContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Two-level states in Q(i)^2, density matrix ρ = 1/2(I + r · σ), and rational Bloch coordinates r in Q^3.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 49         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `BlochQubitContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SPIN_BASIS_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 49 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_49_spin_one_half_states` family schema:

```json
{
  "schema_id": "sg_packet_level_49_spin_one_half_states",
  "task_data": {
    "level": 49,
    "epoch": "Epoch IV",
    "domain": "Qubit Geometry",
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
    "qubit_state_vector": [
      {"real": "1", "imag": "0"},
      {"real": "0", "imag": "0"}
    ],
    "bloch_coordinates": ["0", "0", "1"],
    "density_matrix_trace": "1",
    "bloch_vector_length_sq": "1",
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
pub struct BlochQubitPayload {
    pub move_type: MoveType,
    pub qubit_state_vector: [ComplexRational; 2],
    pub bloch_coordinates: [Rational; 3],
    pub density_matrix_trace: Rational,
    pub bloch_vector_length_sq: Rational,
    pub proposer_signature: String,
}

pub struct Level49Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: BlochQubitPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `BlochQubitContract`

Referees evaluate Level 49 candidates through two-level qubit geometry and rational Bloch coordinates:

1. **Two-Level State Representation:** Evaluates two-level state vector $|\psi\rangle = c_0 |0\rangle + c_1 |1\rangle \in \mathbb{Q}(i)^2$ with $|c_0|^2 + |c_1|^2 = 1$.
2. **Rational Density Matrix & Bloch Vector:** Computes density operator $\rho = |\psi\rangle\langle\psi|$ and projects onto Pauli basis:
   $$\rho = \frac{1}{2}(I + r_x \sigma_x + r_y \sigma_y + r_z \sigma_z), \qquad r_k = \operatorname{Tr}(\rho \sigma_k) \in \mathbb{Q}$$
3. **Bloch Ball Boundary & Discrete Rotations:** Asserts $|\vec{r}|^2 = r_x^2 + r_y^2 + r_z^2 \le 1$. Scoped disclaimer: arbitrary continuous phase rotations do not preserve $\mathbb{Q}(i)$; only gates whose matrix entries lie in $\mathbb{Q}(i)$, such as the Pauli gates and the phase gate $S = \operatorname{diag}(1, i)$, preserve this carrier. *(Corrected 2026-10-20: the earlier text said "discrete rational Clifford gates". The Clifford group is not contained in this carrier: the Hadamard gate has entries $\pm 1/\sqrt{2} \notin \mathbb{Q}(i)$.)*
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff qubit density operator is Hermitian positive semi-definite with unit trace and Bloch vector satisfies $|\vec{r}|^2 \le 1$ identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a completely mixed state $\rho = \frac{1}{2} I$ (with $\vec{r} = \vec{0}$) is certified as an invariant maximum-entropy qubit survivor, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 49 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SPIN_BASIS_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 49, "carrier_match": true, "move": "ASSERT", "qubit_state_vector": [{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}], "bloch_coordinates": ["0", "0", "1"], "bloch_vector_length_sq": "1"}
REFEREE:  ACCEPT -> Status: ExactRepair (qubit state |0⟩ maps to rational Bloch pole (0,0,1) with unit norm)
  ```

  **Worked check (2026-10-20):** for $|\psi\rangle = c_0|0\rangle + c_1|1\rangle$, $r_x = 2\operatorname{Re}(c_0^* c_1)$, $r_y = 2\operatorname{Im}(c_0^* c_1)$ and $r_z = |c_0|^2 - |c_1|^2$. With $c_0 = 1$, $c_1 = 0$: $\vec r = (0, 0, 1)$ and $|\vec r|^2 = 1$; $\rho = \operatorname{diag}(1, 0)$ has trace 1. In the negative vector $(1,1,1)$ has $|\vec r|^2 = 3 > 1$, and it also differs from the $(0,0,1)$ computed from the same state vector, so the refusal follows on either check.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 49, "carrier_match": true, "move": "ASSERT", "qubit_state_vector": [{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}], "bloch_coordinates": ["1", "1", "1"], "bloch_vector_length_sq": "3"}
REFEREE:  REFUSED -> Refusal Code: ERR_SPIN_BASIS_DEFECT, Status: Refused (Bloch vector squared length 3 > 1 exceeds physical Bloch ball boundary)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 49, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 49: Qubit States & Pauli/Bloch Representation within the Qubit Geometry bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`BlochQubitContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 49 specifies an exact, deterministic evaluation procedure for candidate proposals over `Two-level qubit states in Q(i)^2 with rational Bloch vectors and Pauli representations`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
