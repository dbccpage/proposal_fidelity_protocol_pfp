---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 33: Wilsonian Renormalization Flow & Fixed Points"
kind: grammar-reference
level: 33
epoch: "Epoch II"
domain: "Dynamical Systems"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "StatisticalPhysicsModule"
evaluator_contract: "RenormalizationFlowContract"
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

# The Symbol Game Level 33: Wilsonian Renormalization Flow & Fixed Points

**AuthorityEffect:** None.  
**Level:** Level 33 | **Epoch:** Epoch II | **Domain:** Dynamical Systems  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Hamiltonian coupling space with discrete RG step map R_b: K → K'`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SCALE_PARAMETER_DEFECT`  
**Evaluator Module:** `StatisticalPhysicsModule` (`Renormalization Flow & Discrete Coupling Transformation Evaluator`)  
**Evaluator Contract:** `RenormalizationFlowContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `StatisticalPhysicsModule` or contract `RenormalizationFlowContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 33 establishes the Proposal Fidelity Protocol (PFP) arena for **Wilsonian Renormalization Flow & Fixed Points** within the Dynamical Systems bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{33} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Hamiltonian coupling space with discrete RG step map R_b: K → K'`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `StatisticalPhysicsModule` (`RenormalizationFlowContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Discrete RG transformation K' = R_b(K), scale parameter validation, and fixed-point residual certification.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 33         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `StatisticalPhysicsModule` metrics under `RenormalizationFlowContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SCALE_PARAMETER_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 33 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_33_renormalization_flow` family schema:

```json
{
  "schema_id": "sg_packet_level_33_renormalization_flow",
  "task_data": {
    "level": 33,
    "epoch": "Epoch II",
    "domain": "Dynamical Systems",
    "carrier_digest": "blake3:b8d4e9..."
  },
  "protected_boundary": {
    "immutable_slots": ["carrier", "fuel_ceiling", "zero_relation_fences"],
    "max_fuel": 10
  },
  "budget": {
    "turn_fuel_remaining": 10,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "coupling_vector_k": ["1/4", "0"],
    "scale_factor_b": 2,
    "transformed_coupling_k_prime": ["1/16", "0"],
    "flow_beta_vector": ["-3/16", "0"],
    "fixed_point_residual": "1/16",
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
pub struct RenormalizationFlowPayload {
    pub move_type: MoveType,
    pub coupling_vector_k: Vec<Rational>,
    pub scale_factor_b: u32,
    pub transformed_coupling_k_prime: Vec<Rational>,
    pub flow_beta_vector: Vec<Rational>,
    pub fixed_point_residual: Rational,
    pub proposer_signature: String,
}

pub struct Level33Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: RenormalizationFlowPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: StatisticalPhysicsModule

### Contract: `RenormalizationFlowContract`

Referees evaluate Level 33 candidates through discrete coupling transformation dynamics:

1. **Scale Parameter Validation:** Asserts spatial scaling factor $b \in \mathbb{Z}_{> 1}$ satisfies the decimation dilation lower bound.
2. **Discrete Coupling Transformation:** Evaluates rational coupling vector $K \in \mathbb{Q}^d$ and candidate transformed coupling $K' = R_b(K)$ under the algebraic RG step equations:
   $$K' = R_b(K), \quad \Delta K = K' - K$$
3. **Fixed-Point Residual Certification:** Evaluates the distance from $K$ to the fixed point $K^* = R_b(K^*)$, auditing the linear stability matrix $\partial R_b / \partial K$ over $\mathbb{Q}$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff $K' = R_b(K)$ and the discrete beta flow vector matches the declared transformation identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant non-trivial fixed point $K^* = R_b(K^*)$ with certified scaling exponents is admitted as a stable survivor, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 33 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SCALE_PARAMETER_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 33, "carrier_match": true, "move": "ASSERT", "coupling_vector_k": ["1/4", "0"], "scale_factor_b": 2, "transformed_coupling_k_prime": ["1/16", "0"], "flow_beta_vector": ["-3/16", "0"]}
REFEREE:  ACCEPT -> Status: ExactRepair (discrete RG step K' = R_b(K) verified with scale factor b = 2)
  ```

  **Reproducibility gap (2026-10-20):** no packet declares the map $R_b$, so $K' = R_b(K)$ cannot be checked from the data. The numbers fit the assumption $R_2(K) = K^2$ (for example, $b = 2$ decimation of the one-dimensional Ising chain written in the variable $t = \tanh K$), which this file does not state.

  **Worked check under that assumption (2026-10-20):** $R_2(1/4) = 1/16$, matching `transformed_coupling_k_prime`, and $\Delta K = 1/16 - 4/16 = -3/16$, matching `flow_beta_vector`. The fixed points of $K \mapsto K^2$ are $0$ and $1$. The schema's `fixed_point_residual` of $1/16$ equals neither $|R_2(K) - K| = 3/16$ nor the distance $1/4$ from $K$ to the nearest fixed point; it equals the distance from $K'$ to the fixed point $0$. The file should state which of these the field means.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 33, "carrier_match": true, "move": "ASSERT", "coupling_vector_k": ["1/4", "0"], "scale_factor_b": 0, "transformed_coupling_k_prime": ["1/16", "0"]}
REFEREE:  REFUSED -> Refusal Code: ERR_SCALE_PARAMETER_DEFECT, Status: Refused (scale factor b = 0 violates RG dilation bound b > 1)
  ```

  **Worked check (2026-10-20):** Section 4 requires $b \in \mathbb{Z}_{>1}$; $b = 0$ fails it, so the refusal follows from the data without needing $R_b$.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 33, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 33: Wilsonian Renormalization Flow & Fixed Points within the Dynamical Systems bounded context.
   - A proposed PFP packet envelope, `StatisticalPhysicsModule` (`RenormalizationFlowContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 33 specifies an exact, deterministic evaluation procedure for candidate proposals over `Hamiltonian coupling space with discrete RG step map R_b: K → K'`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
