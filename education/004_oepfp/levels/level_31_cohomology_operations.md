---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 31: Steenrod Squares & Cohomology Operations"
kind: grammar-reference
level: 31
epoch: "Epoch I"
domain: "Algebraic Topology"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "CohomologyOperationsModule"
evaluator_contract: "SteenrodF2Contract"
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

# The Symbol Game Level 31: Steenrod Squares & Cohomology Operations

**AuthorityEffect:** None.  
**Level:** Level 31 | **Epoch:** Epoch I | **Domain:** Algebraic Topology  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Stable cohomology operations Sq^k: H^n(X, 𝔽₂) → H^{n+k}(X, 𝔽₂)`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_OPERATION_DEGREE_DEFECT`  
**Evaluator Module:** `CohomologyOperationsModule` (`Steenrod Mod-2 Cohomology Operation Evaluator (𝔽₂)`)  
**Evaluator Contract:** `SteenrodF2Contract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CohomologyOperationsModule` or contract `SteenrodF2Contract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 31 establishes the Proposal Fidelity Protocol (PFP) arena for **Steenrod Squares & Cohomology Operations** within the Algebraic Topology bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{31} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Stable cohomology operations Sq^k: H^n(X, 𝔽₂) → H^{n+k}(X, 𝔽₂)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CohomologyOperationsModule` (`SteenrodF2Contract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Evaluation of stable Steenrod operations Sq^k over 𝔽₂ cochains, degree shifts, instability bounds, and Adem relations.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 31         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `CohomologyOperationsModule` metrics under `SteenrodF2Contract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_OPERATION_DEGREE_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 31 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_31_cohomology_operations` family schema:

```json
{
  "schema_id": "sg_packet_level_31_cohomology_operations",
  "task_data": {
    "level": 31,
    "epoch": "Epoch I",
    "domain": "Algebraic Topology",
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
    "degree_k": 1,
    "input_degree_n": 1,
    "cochain_f2": [1, 0, 1, 1],
    "output_degree": 2,
    "instability_bound_satisfied": true,
    "adem_relation_witness": "Sq1_x_equals_x_cup_x",
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
pub struct SteenrodF2Payload {
    pub move_type: MoveType,
    pub degree_k: u32,
    pub input_degree_n: u32,
    pub cochain_f2: Vec<u8>,
    pub output_degree: u32,
    pub instability_bound_satisfied: bool,
    pub adem_relation_witness: String,
    pub proposer_signature: String,
}

pub struct Level31Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SteenrodF2Payload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: CohomologyOperationsModule

### Contract: `SteenrodF2Contract`

Referees evaluate Level 31 candidates through mod-2 algebraic topology operations strictly over $\mathbb{F}_2$ (GF(2) binary field, avoiding rational cochain conflation):

1. **Mod-2 Degree Shift & Linearity:** Evaluates $Sq^k\colon H^n(X, \mathbb{F}_2) \to H^{n+k}(X, \mathbb{F}_2)$, asserting linear operation over binary cochains and degree match:
   $$\deg(Sq^k(c)) = n + k$$
2. **Instability Conditions:** Audits axiomatic constraints:
   $$Sq^0 = \mathrm{id}, \quad Sq^k(x) = 0 \; (k > \deg(x)), \quad Sq^{\deg(x)}(x) = x \smile x$$
3. **Adem Relations Over $\mathbb{F}_2$:** For $0 < a < 2b$, evaluates the mod-2 Adem expansion:
   $$Sq^a Sq^b = \sum_{c=0}^{\lfloor a/2 \rfloor} \binom{b - 1 - c}{a - 2c} Sq^{a + b - c} Sq^c \pmod 2$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the operation strictly satisfies $\mathbb{F}_2$ cochain linearity, correct degree shift $n+k$, instability vanishing, and Adem relation identities.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a non-zero value of the primary operation $Sq^1$ on a degree-1 class, $Sq^1(x) = x \smile x \ne 0 \in H^2(X, \mathbb{F}_2)$, certifies a non-trivial topological obstruction (for $x = w_1$ of a closed manifold it shows $w_1 \ne 0$, hence non-orientability, as for $\mathbb{RP}^2$), recording zero authority minted. *(Corrected 2026-10-20: $Sq^1$ is a primary, not a secondary, operation. The converse fails: the Klein bottle has $w_1 \ne 0$ but $w_1 \smile w_1 = 0$.)*

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 31 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_OPERATION_DEGREE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 31, "carrier_match": true, "move": "ASSERT", "degree_k": 1, "input_degree_n": 1, "output_degree": 2, "cochain_f2": [1, 0, 1], "instability_bound_satisfied": true}
REFEREE:  ACCEPT -> Status: ExactRepair (Steenrod Sq^1 over F_2 satisfies degree shift 1+1=2 and instability cup square)
  ```

  **Worked check (2026-10-20):** degree: $n + k = 1 + 1 = 2$, matching `output_degree`. Instability: $k = \deg x = 1$, so $Sq^1(x) = x \smile x$ is the required value, not zero.

  **Reproducibility gap (2026-10-20):** `cochain_f2` lists three bits (four in the schema example) with no cell complex, no cocycle check and no cup-product structure, so the value $x \smile x$ cannot be recomputed from the packet.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 31, "carrier_match": true, "move": "ASSERT", "degree_k": 2, "input_degree_n": 1, "output_degree": 4, "cochain_f2": [1, 0, 1]}
REFEREE:  REFUSED -> Refusal Code: ERR_OPERATION_DEGREE_DEFECT, Status: Refused (operation output degree 4 violates Steenrod degree shift n + k = 1 + 2 = 3)
  ```

  **Worked check (2026-10-20):** $n + k = 1 + 2 = 3 \ne 4$, so the degree refusal follows. Instability also gives $Sq^2(x) = 0$ for $\deg x = 1 < 2$.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 31, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 31: Steenrod Squares & Cohomology Operations within the Algebraic Topology bounded context.
   - A proposed PFP packet envelope, `CohomologyOperationsModule` (`SteenrodF2Contract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 31 specifies an exact, deterministic evaluation procedure for candidate proposals over `Stable cohomology operations Sq^k: H^n(X, 𝔽₂) → H^{n+k}(X, 𝔽₂)`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
