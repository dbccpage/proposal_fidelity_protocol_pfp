---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 71: Cauchy Sequence Filtrations & Analytic Fences"
kind: grammar-reference
level: 71
epoch: "Epoch VI"
domain: "Constructive Analysis"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "EnclosureAnalysisModule"
evaluator_contract: "CauchyModulusContract"
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

# The Symbol Game Level 71: Cauchy Sequence Filtrations & Analytic Fences

**AuthorityEffect:** None.  
**Level:** Level 71 | **Epoch:** Epoch VI | **Domain:** Constructive Analysis  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Constructive rational Cauchy sequences with explicit moduli of convergence`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_CAUCHY_MODULUS_DEFECT`  
**Evaluator Module:** `EnclosureAnalysisModule` (`Constructive Cauchy Sequence Modulus & Analytic Fence Evaluator`)  
**Evaluator Contract:** `CauchyModulusContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `EnclosureAnalysisModule` or contract `CauchyModulusContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 71 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 71: Cauchy Sequence Filtrations & Analytic Fences** within the Constructive Analysis bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{71} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Constructive rational Cauchy sequences with explicit moduli of convergence`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `EnclosureAnalysisModule` executing under `CauchyModulusContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of constructive Cauchy sequences equipped with explicit rate of convergence moduli M(k).

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (EnclosureAnalysisModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: EnclosureAnalysisModule           |
| Packet:               |              | Contract: CauchyModulusContract       |
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

Proposals targeting Level 71 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `omega-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_71_analytic_limit_fences.json",
  "title": "sg_packet_level_71_analytic_limit_fences",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "sequence_definition": "x_n = sum_{j=0}^n (1 / j!)",
    "modulus_formula": "M(k) = k + 2",
    "target_limit_symbol": "e",
    "test_verifications": [
      {"k": 1, "n1": 3, "n2": 4, "difference": "1/24", "bound": "1/2"},
      {"k": 2, "n1": 4, "n2": 5, "difference": "1/120", "bound": "1/4"}
    ],
    "modulus_valid": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct CauchyModulusPayload {
    pub move_type: MoveType,
    pub sequence_definition: String,
    pub modulus_formula: String,
    pub target_limit_symbol: String,
    pub test_verifications: Vec<CauchyCheck>,
    pub modulus_valid: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 71 binds the referee to `EnclosureAnalysisModule` under `CauchyModulusContract`:

Referees evaluate Level 71 candidates through constructive Cauchy sequence analysis (Bishop):

1. **Cauchy Modulus of Convergence:** For rational sequence $\{x_n\} \subset \mathbb{Q}$, verifies the existence of an explicit modulus $M: \mathbb{N} \to \mathbb{N}$ such that:
   $$\forall k \in \mathbb{N}, \quad \forall m, n \ge M(k): \quad |x_m - x_n| \le 2^{-k}$$
2. **Finite Test Verification:** Computes rational sequence differences for sample indices $m, n \ge M(k)$ and verifies $|x_m - x_n| \le 2^{-k}$.
3. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the modulus formula $M(k)$ is constructive and verified on all declared test indices.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff sequence terms exhibit slow polynomial convergence ($M(k) \sim 2^k$) while the modulus remains constructively certified.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 71? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `CauchyModulusContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_CAUCHY_MODULUS_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 71, "carrier_match": true, "move": "ASSERT", "sequence_definition": "x_n = sum (1/j!)", "modulus_formula": "M(k) = k + 2", "test_verifications": [{"k": 1, "n1": 3, "n2": 4, "difference": "1/24", "bound": "1/2"}]}
REFEREE:  ACCEPT -> Status: ExactRepair (Cauchy modulus formula verified: difference 1/24 <= 1/2 bound)
```

**Worked check (2026-10-20):** x_4 − x_3 = 1/4! = 1/24 ≤ 1/2 and x_5 − x_4 = 1/5! = 1/120 ≤ 1/4 (the second row of section 3). For the modulus in general, the tail after index n is below 1/(n!·n); at n = M(k) = k + 2 this is at most 2^(−k), because (k + 2)!(k + 2) ≥ 2^k (checked exactly for k ≤ 30, and the left side grows faster).

### Domain-Negative Test Vector (`ERR_CAUCHY_MODULUS_DEFECT`)
```text
PROPOSAL: {"level": 71, "carrier_match": true, "move": "ASSERT", "sequence_definition": "x_n = sum (1/j!)", "modulus_formula": "M(k) = 1", "test_verifications": [{"k": 4, "n1": 1, "n2": 2, "difference": "1/2", "bound": "1/16"}]}
REFEREE:  REFUSED -> Refusal Code: ERR_CAUCHY_MODULUS_DEFECT, Status: Refused (modulus formula M(4)=1 fails: difference |x_1 - x_2| = 1/2 exceeds bound 2^-4 = 1/16)
```

**Worked check (2026-10-20):** x_2 − x_1 = 1/2! = 1/2, and 1/2 > 1/16 = 2^(−4).

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 71 under `CauchyModulusContract`.
   - Specified detection of domain discrepancies emitting `ERR_CAUCHY_MODULUS_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Constructive rational Cauchy sequences equipped with explicit convergence moduli`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `EnclosureAnalysisModule` running `CauchyModulusContract` is specified to distinguish valid `Constructive Analysis` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
