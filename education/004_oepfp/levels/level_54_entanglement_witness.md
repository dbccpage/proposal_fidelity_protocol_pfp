---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 54: Schmidt Decomposition & Entanglement Witnesses"
kind: grammar-reference
level: 54
epoch: "Epoch IV"
domain: "Quantum Information"
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
evaluator_contract: "SchmidtRankContract"
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

# The Symbol Game Level 54: Schmidt Decomposition & Entanglement Witnesses

**AuthorityEffect:** None.  
**Level:** Level 54 | **Epoch:** Epoch IV | **Domain:** Quantum Information  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Bipartite states over Q(i, √2) with Schmidt rank certifications and entanglement witnesses W`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SCHMIDT_RANK_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Schmidt Rank & Entanglement Witness Evaluator (Q(i, √2))`)  
**Evaluator Contract:** `SchmidtRankContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `SchmidtRankContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 54 establishes the Proposal Fidelity Protocol (PFP) arena for **Schmidt Decomposition & Entanglement Witnesses** within the Quantum Information bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{54} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Bipartite states over Q(i, √2) with Schmidt rank certifications and entanglement witnesses W`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`SchmidtRankContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Schmidt rank r > 1, normalized Bell states over Q(i, √2), and Hermitian witness operators W separating entangled states from the separable convex set.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 54         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `SchmidtRankContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SCHMIDT_RANK_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 54 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_54_entanglement_witness` family schema:

```json
{
  "schema_id": "sg_packet_level_54_entanglement_witness",
  "task_data": {
    "level": 54,
    "epoch": "Epoch IV",
    "domain": "Quantum Information",
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
    "scalar_field": "Q(i, sqrt(2))",
    "bipartite_state": "Bell_Phi_Plus",
    "schmidt_coefficients": ["1/sqrt(2)", "1/sqrt(2)"],
    "schmidt_rank": 2,
    "entanglement_witness_expectation": "-1/2",
    "separable_convex_bound_nonnegative": true,
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
pub struct SchmidtEntanglementPayload {
    pub move_type: MoveType,
    pub scalar_field: String,
    pub bipartite_state: String,
    pub schmidt_coefficients: Vec<String>,
    pub schmidt_rank: u32,
    pub entanglement_witness_expectation: String,
    pub separable_convex_bound_nonnegative: bool,
    pub proposer_signature: String,
}

pub struct Level54Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SchmidtEntanglementPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `SchmidtRankContract`

Referees evaluate Level 54 candidates through Schmidt decomposition over the declared quadratic field extension $\mathbb{Q}(i, \sqrt{2})$:

1. **Declared Field Extension:** Scoped strictly to $\mathbb{Q}(i, \sqrt{2})$ where $[\mathbb{Q}(i, \sqrt{2}) : \mathbb{Q}(i)] = 2$, accommodating normalized Bell states such as $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$.
2. **Schmidt Decomposition:** For bipartite pure state $|\psi\rangle \in \mathcal{H}_A \otimes \mathcal{H}_B$, evaluates Schmidt coefficients $\lambda_k > 0$ such that $|\psi\rangle = \sum_{k=1}^r \lambda_k |u_k\rangle |v_k\rangle$ with $\sum \lambda_k^2 = 1$. Schmidt rank $r > 1$ certifies entanglement.
3. **Entanglement Witness Operator:** Verifies Hermitian operator $W$ satisfying $\operatorname{Tr}(W \rho_{\text{sep}}) \ge 0$ for all states in the convex set of separable states (noting separable states form a convex set, not a polytope), while $\langle \psi | W | \psi \rangle < 0$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff Schmidt coefficients satisfy $\sum \lambda_k^2 = 1$ in $\mathbb{Q}(i, \sqrt{2})$ and witness operator strictly separates the candidate entangled state with negative expectation value.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant maximally entangled state $|\Phi^+\rangle$ with certified Schmidt rank 2 is admitted as an entangled resource survivor, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 54 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SCHMIDT_RANK_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 54, "carrier_match": true, "move": "ASSERT", "scalar_field": "Q(i, sqrt(2))", "bipartite_state": "Bell_Phi_Plus", "schmidt_rank": 2, "entanglement_witness_expectation": "-1/2"}
REFEREE:  ACCEPT -> Status: ExactRepair (Schmidt rank 2 certified over Q(i, sqrt(2)) with negative witness expectation)
  ```

  **Worked check (2026-10-20):** |Φ+⟩ = (|00⟩ + |11⟩)/√2 has Schmidt coefficients 1/√2 and 1/√2, so their squares sum to 1/2 + 1/2 = 1 and the Schmidt rank is 2. The value −1/2 matches the standard witness W = I/2 − |Φ+⟩⟨Φ+|: ⟨Φ+|W|Φ+⟩ = 1/2 − 1 = −1/2, while every separable state has fidelity at most 1/2 with |Φ+⟩ and so gives Tr(W ρ) ≥ 0.

  **Reproducibility gap (2026-10-20):** the packet never names W. Without it the value −1/2 cannot be recomputed; the witness above is the usual choice, not data from this file.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 54, "carrier_match": true, "move": "ASSERT", "scalar_field": "Q(i, sqrt(2))", "bipartite_state": "Product_00", "schmidt_rank": 2, "entanglement_witness_expectation": "0"}
REFEREE:  REFUSED -> Refusal Code: ERR_SCHMIDT_RANK_DEFECT, Status: Refused (separable product state |00⟩ has Schmidt rank 1 != 2)
  ```

  **Worked check (2026-10-20):** |00⟩ = |0⟩ ⊗ |0⟩ has one nonzero Schmidt coefficient (equal to 1), so its Schmidt rank is 1, not the declared 2.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 54, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 54: Schmidt Decomposition & Entanglement Witnesses within the Quantum Information bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`SchmidtRankContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 54 specifies an exact, deterministic evaluation procedure for candidate proposals over `Bipartite states over Q(i, √2) with Schmidt rank certifications and entanglement witnesses W`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
