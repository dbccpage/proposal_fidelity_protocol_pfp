---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 66: Signed Sum Characters & Non-Positive Measures"
kind: grammar-reference
level: 66
epoch: "Epoch V"
domain: "Computational Physics"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SignedStatisticalPhysicsModule"
evaluator_contract: "SignedPartitionSumContract"
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

# The Symbol Game Level 66: Signed Sum Characters & Non-Positive Measures

**AuthorityEffect:** None.  
**Level:** Level 66 | **Epoch:** Epoch V | **Domain:** Computational Physics  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Finite configuration spaces with rational signed weights and non-positive measure characters`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SIGN_COLLAPSE_DEFECT`  
**Evaluator Module:** `SignedStatisticalPhysicsModule` (`Signed Partition Sum & Non-Positive Measure Evaluator`)  
**Evaluator Contract:** `SignedPartitionSumContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SignedStatisticalPhysicsModule` or contract `SignedPartitionSumContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 66 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 66: Signed Sum Characters & Non-Positive Measures** within the Computational Physics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{66} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Finite configuration spaces with rational signed weights and non-positive measure characters`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SignedStatisticalPhysicsModule` executing under `SignedPartitionSumContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact verification of signed partition functions, absolute reference weights, and average sign observables.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (SignedStatisticalPhysicsModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: SignedStatisticalPhysicsModule           |
| Packet:               |              | Contract: SignedPartitionSumContract       |
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

Proposals targeting Level 66 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_66_signed_sum_models.json",
  "title": "sg_packet_level_66_signed_sum_models",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "state_space_size": 4,
    "signed_weights": ["1", "-1/2", "1/4", "-1/8"],
    "signed_partition_sum": "5/8",
    "absolute_partition_sum": "15/8",
    "average_sign": "1/3",
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct SignedPartitionSumPayload {
    pub move_type: MoveType,
    pub state_space_size: usize,
    pub signed_weights: Vec<Rational>,
    pub signed_partition_sum: Rational,
    pub absolute_partition_sum: Rational,
    pub average_sign: Rational,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 66 binds the referee to `SignedStatisticalPhysicsModule` under `SignedPartitionSumContract`:

Referees evaluate Level 66 candidates through signed statistical sums:

1. **Signed Partition Sum:** For configuration space $\Omega$ with signed weights $w_c \in \mathbb{Q}$, computes:
   $$Z_{\mathrm{signed}} = \sum_{c \in \Omega} w_c$$
2. **Absolute Partition Sum & Average Sign:** Computes the positive reference sum $Z_{\mathrm{abs}} = \sum_{c \in \Omega} |w_c|$ and the exact average sign:
   $$\langle \sigma \rangle = \frac{Z_{\mathrm{signed}}}{Z_{\mathrm{abs}}} \in [-1, 1]$$
3. **Sign Collapse Fences:** Detects catastrophic cancellations where $\langle \sigma \rangle \approx 0$, demonstrating numerical exponential variance in Monte Carlo sampling.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff signed weights are exact rationals, $Z_{\mathrm{signed}}$ and $Z_{\mathrm{abs}}$ are correctly evaluated, and average sign matches $\langle \sigma \rangle = Z_{\mathrm{signed}} / Z_{\mathrm{abs}}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an obstinate sign cancellation ($|\langle \sigma \rangle| \le 10^{-3}$) is certified structurally isolated by a parity-preserving cluster decomposition.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 66? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `SignedPartitionSumContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_SIGN_COLLAPSE_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 66, "carrier_match": true, "move": "ASSERT", "signed_weights": ["1", "-1/2", "1/4", "-1/8"], "average_sign": "1/3"}
REFEREE:  ACCEPT -> Status: ExactRepair (signed weights, partition sums, and average sign 1/3 verified exactly)
```

**Worked check (2026-10-20):** Z_signed = 1 − 1/2 + 1/4 − 1/8 = 5/8, Z_abs = 1 + 1/2 + 1/4 + 1/8 = 15/8, and ⟨σ⟩ = (5/8)/(15/8) = 1/3.

### Domain-Negative Test Vector (`ERR_SIGN_COLLAPSE_DEFECT`)
```text
PROPOSAL: {"level": 66, "carrier_match": true, "move": "ASSERT", "signed_weights": ["1", "-1/2", "1/4", "-1/8"], "average_sign": "1/2"}
REFEREE:  REFUSED -> Refusal Code: ERR_SIGN_COLLAPSE_DEFECT, Status: Refused (declared average sign 1/2 does not match exact ratio (5/8)/(15/8) = 1/3)
```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 66 under `SignedPartitionSumContract`.
   - Specified detection of domain discrepancies emitting `ERR_SIGN_COLLAPSE_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Finite statistical systems with signed rational weights and exact average sign ratios`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `SignedStatisticalPhysicsModule` running `SignedPartitionSumContract` is specified to distinguish valid `Computational Physics` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
