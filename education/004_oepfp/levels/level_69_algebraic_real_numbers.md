---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 69: Real Algebraic Field Q_alg & Sturm Chains"
kind: grammar-reference
level: 69
epoch: "Epoch VI"
domain: "Computer Algebra"
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
evaluator_contract: "AlgebraicRootContract"
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

# The Symbol Game Level 69: Real Algebraic Field Q_alg & Sturm Chains

**AuthorityEffect:** None.  
**Level:** Level 69 | **Epoch:** Epoch VI | **Domain:** Computer Algebra  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Square-free univariate polynomials in Q[x] with Sturm root isolation chains`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_ALGEBRAIC_ROOT_ISOLATION_DEFECT`  
**Evaluator Module:** `EnclosureAnalysisModule` (`Real Algebraic Number Q_alg & Sturm Chain Evaluator`)  
**Evaluator Contract:** `AlgebraicRootContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `EnclosureAnalysisModule` or contract `AlgebraicRootContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 69 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 69: Real Algebraic Field Q_alg & Sturm Chains** within the Computer Algebra bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{69} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Square-free univariate polynomials in Q[x] with Sturm root isolation chains`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `EnclosureAnalysisModule` executing under `AlgebraicRootContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact certification of real algebraic numbers via Sturm chains and isolating rational intervals.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (EnclosureAnalysisModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: EnclosureAnalysisModule           |
| Packet:               |              | Contract: AlgebraicRootContract       |
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

Proposals targeting Level 69 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `omega-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_69_algebraic_real_numbers.json",
  "title": "sg_packet_level_69_algebraic_real_numbers",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "polynomial_coefficients": ["-2", "0", "1"],
    "sturm_sequence": [
      ["-2", "0", "1"],
      ["0", "2"],
      ["2"]
    ],
    "isolation_interval": ["1", "2"],
    "exact_root_count": 1,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct AlgebraicRootPayload {
    pub move_type: MoveType,
    pub polynomial_coefficients: Vec<Rational>,
    pub sturm_sequence: Vec<Vec<Rational>>,
    pub isolation_interval: (Rational, Rational),
    pub exact_root_count: usize,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 69 binds the referee to `EnclosureAnalysisModule` under `AlgebraicRootContract`:

Referees evaluate Level 69 candidates through Sturm's theorem on real algebraic numbers:

1. **Sturm Chain Construction:** For square-free $P(x) \in \mathbb{Q}[x]$, computes the Sturm sequence $f_0 = P, f_1 = P', f_{i+1} = -\operatorname{rem}(f_{i-1}, f_i)$.
2. **Sign Variations:** Computes the number of sign variations $V(x)$ at interval boundaries $a$ and $b$.
3. **Exact Root Counting:** Asserts that the exact number of real roots in $(a, b]$ satisfies:
   $$N_{\mathrm{roots}} = V(a) - V(b) = \text{exact\_root\_count}$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the Sturm sequence is correctly constructed via Euclidean remaindering and $V(a) - V(b) = 1$ uniquely isolates the algebraic root.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff polynomial degree is high ($d \ge 8$) but root isolation is certified without numerical floating-point instability.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 69? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `AlgebraicRootContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_ALGEBRAIC_ROOT_ISOLATION_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 69, "carrier_match": true, "move": "ASSERT", "polynomial_coefficients": ["-2", "0", "1"], "sturm_sequence": [["-2", "0", "1"], ["0", "2"], ["2"]], "isolation_interval": ["1", "2"], "exact_root_count": 1}
REFEREE:  ACCEPT -> Status: ExactRepair (Sturm chain signs V(1) - V(2) = 1 - 0 = 1, unique real root of x^2 - 2 isolated in (1, 2])
```

**Worked check (2026-10-20):** the chain is f_0 = x² − 2, f_1 = 2x and f_2 = −rem(f_0, f_1) = 2. At x = 1 the values are (−1, 2, 2): one sign change, so V(1) = 1. At x = 2 they are (2, 4, 2): no change, so V(2) = 0. Hence V(1) − V(2) = 1. The line above previously read "2 − 1 = 1"; the count values were corrected on 2026-10-20.

### Domain-Negative Test Vector (`ERR_ALGEBRAIC_ROOT_ISOLATION_DEFECT`)
```text
PROPOSAL: {"level": 69, "carrier_match": true, "move": "ASSERT", "polynomial_coefficients": ["-2", "0", "1"], "sturm_sequence": [["-2", "0", "1"], ["0", "2"], ["2"]], "isolation_interval": ["-1", "1"], "exact_root_count": 1}
REFEREE:  REFUSED -> Refusal Code: ERR_ALGEBRAIC_ROOT_ISOLATION_DEFECT, Status: Refused (Sturm chain signs V(-1) - V(1) = 1 - 1 = 0; no roots of x^2 - 2 lie in (-1, 1], declared count 1 is false)
```

**Worked check (2026-10-20):** at x = −1 the values are (−1, −2, 2): one sign change, so V(−1) = 1, and V(1) = 1 as above. Hence V(−1) − V(1) = 0. The line above previously read "2 − 2 = 0".

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 69 under `AlgebraicRootContract`.
   - Specified detection of domain discrepancies emitting `ERR_ALGEBRAIC_ROOT_ISOLATION_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Square-free polynomials over Q with certified Sturm root isolation chains`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `EnclosureAnalysisModule` running `AlgebraicRootContract` is specified to distinguish valid `Computer Algebra` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
