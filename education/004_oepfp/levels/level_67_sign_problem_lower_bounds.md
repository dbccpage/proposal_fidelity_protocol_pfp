---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 67: Fermion Sign Problem & NP-Hardness Barriers"
kind: grammar-reference
level: 67
epoch: "Epoch V"
domain: "Computational Complexity"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "ComputationalComplexityModule"
evaluator_contract: "ComplexityReductionContract"
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

# The Symbol Game Level 67: Fermion Sign Problem & NP-Hardness Barriers

**AuthorityEffect:** None.  
**Level:** Level 67 | **Epoch:** Epoch V | **Domain:** Computational Complexity  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Polynomial-time reduction certificates from NP-hard problems to sign-quenched partition sums`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_REDUCTION_MAP_DEFECT`  
**Evaluator Module:** `ComputationalComplexityModule` (`Fermion Sign Problem NP-Hardness Barrier Evaluator`)  
**Evaluator Contract:** `ComplexityReductionContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ComputationalComplexityModule` or contract `ComplexityReductionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 67 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 67: Fermion Sign Problem & NP-Hardness Barriers** within the Computational Complexity bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{67} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Polynomial-time reduction certificates from NP-hard problems to sign-quenched partition sums`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ComputationalComplexityModule` executing under `ComplexityReductionContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of polynomial-time Karp reductions showing that a general-purpose polynomial-time solution of the sign problem would solve NP-hard problems (Troyer and Wiese, 2005).

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (ComputationalComplexityModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: ComputationalComplexityModule           |
| Packet:               |              | Contract: ComplexityReductionContract       |
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

Proposals targeting Level 67 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_67_sign_problem_lower_bounds.json",
  "title": "sg_packet_level_67_sign_problem_lower_bounds",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "source_problem": "MAX_CUT",
    "target_problem": "FERMION_SIGN_VANISHING",
    "reduction_map": "karp_polynomial_gadget",
    "complexity_resource": "O(N^2)",
    "sign_vanishing_bound": "exp(-alpha * N)",
    "reduction_valid": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct ComplexityReductionPayload {
    pub move_type: MoveType,
    pub source_problem: String,
    pub target_problem: String,
    pub reduction_map: String,
    pub complexity_resource: String,
    pub sign_vanishing_bound: String,
    pub reduction_valid: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 67 binds the referee to `ComputationalComplexityModule` under `ComplexityReductionContract`:

Referees evaluate Level 67 candidates through computational complexity reductions (Troyer-Wiese):

1. **Source Problem Reduction:** Verifies that a known NP-hard source problem (such as Max-Cut or 3-SAT) is mapped via `reduction_map` into a certified fermionic or spin system.
2. **Polynomial Resource Bounds:** Verifies that the reduction gadget consumes polynomial complexity resources ($\mathcal{O}(N^2)$) in space and construction time.
3. **Sign Vanishing Witness:** Asserts that existence of a generic polynomial-time non-vanishing sign algorithm would imply $P = NP$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the polynomial-time reduction gadget preserves the optimization objective and certifies the hardness bound.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an obstinate sign barrier is certified intractable for general polynomial-time algorithms under the assumption P ≠ NP; NP-hardness gives a conditional obstruction, not an unconditional one.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 67? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `ComplexityReductionContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_REDUCTION_MAP_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 67, "carrier_match": true, "move": "ASSERT", "source_problem": "MAX_CUT", "reduction_map": "karp_polynomial_gadget", "complexity_resource": "O(N^2)", "reduction_valid": true}
REFEREE:  ACCEPT -> Status: ExactRepair (polynomial reduction map from Max-Cut to fermion sign problem verified)
```

**Reproducibility gap (2026-10-20):** the packet names a gadget (`karp_polynomial_gadget`) but gives no map, instance or size count, so neither the polynomial bound nor the preservation of the objective can be checked from it.

### Domain-Negative Test Vector (`ERR_REDUCTION_MAP_DEFECT`)
```text
PROPOSAL: {"level": 67, "carrier_match": true, "move": "ASSERT", "source_problem": "MAX_CUT", "reduction_map": "invalid_superpolynomial_map", "complexity_resource": "O(2^N)", "reduction_valid": false}
REFEREE:  REFUSED -> Refusal Code: ERR_REDUCTION_MAP_DEFECT, Status: Refused (reduction map requires exponential resources O(2^N), failing polynomial reduction requirement)
```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 67 under `ComplexityReductionContract`.
   - Specified detection of domain discrepancies emitting `ERR_REDUCTION_MAP_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Polynomial-time reductions from combinatorial NP-hard problems to sign-quenched partition sums`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `ComputationalComplexityModule` running `ComplexityReductionContract` is specified to distinguish valid `Computational Complexity` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
