---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 48: Exact Finite Inner-Product State Spaces & Normalization"
kind: grammar-reference
level: 48
epoch: "Epoch IV"
domain: "Quantum State Space"
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
evaluator_contract: "StateNormalizationContract"
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

# The Symbol Game Level 48: Exact Finite Inner-Product State Spaces & Normalization

**AuthorityEffect:** None.  
**Level:** Level 48 | **Epoch:** Epoch IV | **Domain:** Quantum State Space  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Finite state vectors |ψ⟩ ∈ Q(i)^d with exact rational squared norm ⟨ψ|ψ⟩ = 1`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_STATE_VECTOR_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Exact Finite Inner-Product State Vector Normalization Evaluator`)  
**Evaluator Contract:** `StateNormalizationContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `StateNormalizationContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 48 establishes the Proposal Fidelity Protocol (PFP) arena for **Exact Finite Inner-Product State Spaces & Normalization** within the Quantum State Space bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{48} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Finite state vectors |ψ⟩ ∈ Q(i)^d with exact rational squared norm ⟨ψ|ψ⟩ = 1`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`StateNormalizationContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Finite state vectors in Q(i)^d with exact rational inner products and unit squared norm condition ⟨ψ|ψ⟩ = 1.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 48         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `StateNormalizationContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_STATE_VECTOR_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 48 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_48_finite_hilbert_states` family schema:

```json
{
  "schema_id": "sg_packet_level_48_finite_hilbert_states",
  "task_data": {
    "level": 48,
    "epoch": "Epoch IV",
    "domain": "Quantum State Space",
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
    "dimension": 2,
    "state_vector": [
      {"real": "3/5", "imag": "0"},
      {"real": "0", "imag": "4/5"}
    ],
    "squared_norm": "1",
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
pub struct StateVectorPayload {
    pub move_type: MoveType,
    pub dimension: u32,
    pub state_vector: Vec<ComplexRational>,
    pub squared_norm: Rational,
    pub proposer_signature: String,
}

pub struct Level48Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: StateVectorPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `StateNormalizationContract`

Referees evaluate Level 48 candidates through exact finite inner-product state space mechanics over $\mathbb{Q}(i)$:

1. **Finite State Space Characterization:** Scoped as an exact finite inner-product space $\mathbb{Q}(i)^d$ (not a complete Hilbert space, as $\mathbb{Q}(i)$ is incomplete and lacks arbitrary square roots).
2. **Hermitian Inner Product:** For $|\phi\rangle, |\psi\rangle \in \mathbb{Q}(i)^d$, computes:
   $$\langle \phi | \psi \rangle = \sum_{k=1}^d \phi_k^* \psi_k \in \mathbb{Q}(i)$$
3. **Exact Rational Squared Norm:** Asserts unit squared norm over $\mathbb{Q}$:
   $$\langle \psi | \psi \rangle = \sum_{k=1}^d |\psi_k|^2 = 1$$
   States whose normalization requires square roots not in $\mathbb{Q}(i)$ are represented as unnormalized rays or rejected.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff amplitude entries lie in $\mathbb{Q}(i)^d$ and the squared norm evaluates to 1 identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an unnormalized ray carrying an exact rational squared norm tag $N = \|\psi\|^2 \ne 1$ is admitted as an unnormalized state representative, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 48 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_STATE_VECTOR_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 48, "carrier_match": true, "move": "ASSERT", "dimension": 2, "state_vector": [{"real": "3/5", "imag": "0"}, {"real": "0", "imag": "4/5"}], "squared_norm": "1"}
REFEREE:  ACCEPT -> Status: ExactRepair (state vector in Q(i)^2 satisfies exact rational normalization ⟨ψ|ψ⟩ = 1)
  ```

  **Worked check (2026-10-20):** $\psi = (3/5,\ (4/5)i)$ gives $\langle \psi | \psi \rangle = |3/5|^2 + |(4/5)i|^2 = 9/25 + 16/25 = 1$. The negative vector $\psi = (1/2, 1/2)$ gives $1/4 + 1/4 = 1/2 \ne 1$. Its normalization would need the factor $\sqrt{2} \notin \mathbb{Q}(i)$, so under Section 4 it can only be carried as an unnormalized ray with norm tag $1/2$.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 48, "carrier_match": true, "move": "ASSERT", "dimension": 2, "state_vector": [{"real": "1/2", "imag": "0"}, {"real": "1/2", "imag": "0"}], "squared_norm": "1/2"}
REFEREE:  REFUSED -> Refusal Code: ERR_STATE_VECTOR_DEFECT, Status: Refused (state vector squared norm 1/4 + 1/4 = 1/2 != 1)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 48, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 48: Exact Finite Inner-Product State Spaces & Normalization within the Quantum State Space bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`StateNormalizationContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 48 specifies an exact, deterministic evaluation procedure for candidate proposals over `Finite state vectors |ψ⟩ ∈ Q(i)^d with exact rational squared norm ⟨ψ|ψ⟩ = 1`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
