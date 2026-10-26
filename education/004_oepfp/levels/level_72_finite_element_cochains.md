---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 72: Simplicial Finite Element Meshes & Whitney Forms"
kind: grammar-reference
level: 72
epoch: "Epoch VI"
domain: "Numerical PDE"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "FiniteElementCochainModule"
evaluator_contract: "WhitneyFormContract"
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

# The Symbol Game Level 72: Simplicial Finite Element Meshes & Whitney Forms

**AuthorityEffect:** None.  
**Level:** Level 72 | **Epoch:** Epoch VI | **Domain:** Numerical PDE  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Simplicial mesh complexes with Whitney polynomial differential forms`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_WHITNEY_COMMUTATION_DEFECT`  
**Evaluator Module:** `FiniteElementCochainModule` (`Finite Element Exterior Calculus & Whitney Form Evaluator`)  
**Evaluator Contract:** `WhitneyFormContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `FiniteElementCochainModule` or contract `WhitneyFormContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 72 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 72: Simplicial Finite Element Meshes & Whitney Forms** within the Numerical PDE bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{72} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Simplicial mesh complexes with Whitney polynomial differential forms`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `FiniteElementCochainModule` executing under `WhitneyFormContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of Whitney form interpolation, de Rham reduction integrals, and exterior derivative commutation.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (FiniteElementCochainModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: FiniteElementCochainModule           |
| Packet:               |              | Contract: WhitneyFormContract       |
|  - MoveType           |              |                                      |
|  - Target Fields      |              | Discrepancy Checks:                  |
|  - Witness Artifact   | =====>>>>>   |  1. Syntax / Schema Gate             |
|                       |  (HTTP/Wire) |  2. Primary Domain Invariant Gate    |
| (Zero operational     |              |  3. Budget & Boundary Mask Audit     |
|  authority until      |              |                                      |
|  certified by         | <<<<<=====   | Emits: Immutable Evaluation Receipt  |
|  exact referee)       |   (Receipt)  |  - Disposition (8 Canonical Statuses)|
+-----------------------+              +--------------------------------------+
```

The game follows a strict non-conflation protocol: **proposals are untrusted hypotheses with zero authority until certified by the exact referee**.

---

## 3. Proposal Packet Schema

Proposals targeting Level 72 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `omega-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_72_finite_element_cochains.json",
  "title": "sg_packet_level_72_finite_element_cochains",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "mesh_simplex_dimension": 2,
    "whitney_polynomial_form": "lambda_0 d(lambda_1) - lambda_1 d(lambda_0)",
    "de_rham_reduction_integral": "1",
    "projection_identity_verified": true,
    "commutes_with_exterior_derivative": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct WhitneyFormPayload {
    pub move_type: MoveType,
    pub mesh_simplex_dimension: usize,
    pub whitney_polynomial_form: String,
    pub de_rham_reduction_integral: Rational,
    pub projection_identity_verified: bool,
    pub commutes_with_exterior_derivative: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 72 binds the referee to `FiniteElementCochainModule` under `WhitneyFormContract`:

Referees evaluate Level 72 candidates through Finite Element Exterior Calculus (FEEC):

1. **Whitney Form Construction:** For $k$-simplex $\sigma = [v_0, \dots, v_k]$, defines the Whitney form:
   $$W_{\sigma} = k! \sum_{i=0}^k (-1)^i \lambda_i \, d\lambda_0 \wedge \dots \wedge \widehat{d\lambda_i} \wedge \dots \wedge d\lambda_k$$
2. **De Rham Reduction Projection:** Computes the reduction map $R(\omega)_e = \int_e \omega$ and verifies the projection identity:
   $$R(W(c)) = c \quad \forall c \in C^k(K)$$
3. **Exterior Derivative Commutation:** Verifies that Whitney interpolation commutes with the exterior derivative:
   $$d(W_k(c)) = W_{k+1}(\delta c)$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff Whitney forms satisfy the projection identity $R \circ W = \operatorname{id}$ and commute with the exterior derivative.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff non-conforming mesh boundaries produce bounded interpolation residuals without violating cochain nilpotence.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 72? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `WhitneyFormContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_WHITNEY_COMMUTATION_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 72, "carrier_match": true, "move": "ASSERT", "whitney_polynomial_form": "lambda_0 d(lambda_1) - lambda_1 d(lambda_0)", "de_rham_reduction_integral": "1", "projection_identity_verified": true, "commutes_with_exterior_derivative": true}
REFEREE:  ACCEPT -> Status: ExactRepair (Whitney form projection identity R(W(c)) = c and d(W(c)) = W(delta c) commutation verified)
```

**Worked check (2026-10-20):** on the edge from v_0 to v_1 take λ_1 = t and λ_0 = 1 − t for t in [0, 1]. Then λ_0 dλ_1 − λ_1 dλ_0 = (1 − t) dt + t dt = dt, and its integral over the edge is 1, so R(W(c)) = c on this edge.

### Domain-Negative Test Vector (`ERR_WHITNEY_COMMUTATION_DEFECT`)
```text
PROPOSAL: {"level": 72, "carrier_match": true, "move": "ASSERT", "whitney_polynomial_form": "lambda_0 d(lambda_1)", "de_rham_reduction_integral": "1/2", "projection_identity_verified": false, "commutes_with_exterior_derivative": false}
REFEREE:  REFUSED -> Refusal Code: ERR_WHITNEY_COMMUTATION_DEFECT, Status: Refused (non-antisymmetric form fails projection identity R(W(c)) = 1/2 != 1, commutation with exterior derivative fails)
```

**Worked check (2026-10-20):** λ_0 dλ_1 = (1 − t) dt integrates to 1/2 over the edge, not 1.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 72 under `WhitneyFormContract`.
   - Specified detection of domain discrepancies emitting `ERR_WHITNEY_COMMUTATION_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Finite element exterior calculus with polynomial Whitney forms on simplicial meshes`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `FiniteElementCochainModule` running `WhitneyFormContract` is specified to distinguish valid `Numerical PDE` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
