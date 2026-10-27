---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 68: Validated Interval Arithmetic & Box Enclosures"
kind: grammar-reference
level: 68
epoch: "Epoch VI"
domain: "Rigorous Numerics"
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
evaluator_contract: "IntervalArithmeticContract"
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

# The Symbol Game Level 68: Validated Interval Arithmetic & Box Enclosures

**AuthorityEffect:** None.  
**Level:** Level 68 | **Epoch:** Epoch VI | **Domain:** Rigorous Numerics  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Exact rational interval arithmetic with directed rounding and box enclosures`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_INTERVAL_CONTAINMENT_DEFECT`  
**Evaluator Module:** `EnclosureAnalysisModule` (`Validated Interval Arithmetic & Box Enclosure Evaluator`)  
**Evaluator Contract:** `IntervalArithmeticContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `EnclosureAnalysisModule` or contract `IntervalArithmeticContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 68 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 68: Validated Interval Arithmetic & Box Enclosures** within the Rigorous Numerics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{68} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Exact rational interval arithmetic with directed rounding and box enclosures`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `EnclosureAnalysisModule` executing under `IntervalArithmeticContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact rational interval enclosures, outward rounding, and certified root isolation algorithms.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (EnclosureAnalysisModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: EnclosureAnalysisModule           |
| Packet:               |              | Contract: IntervalArithmeticContract       |
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

Proposals targeting Level 68 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_68_interval_arithmetic.json",
  "title": "sg_packet_level_68_interval_arithmetic",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "root_isolation_algorithm": "bisection_interval_newton",
    "isolated_root_interval": ["7/5", "3/2"],
    "function_expression": "x^2 - 2",
    "endpoint_evaluations": {
      "f_low": "-1/25",
      "f_high": "1/4"
    },
    "containment_guaranteed": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct IntervalArithmeticPayload {
    pub move_type: MoveType,
    pub root_isolation_algorithm: String,
    pub isolated_root_interval: (Rational, Rational),
    pub function_expression: String,
    pub endpoint_evaluations: HashMap<String, Rational>,
    pub containment_guaranteed: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 68 binds the referee to `EnclosureAnalysisModule` under `IntervalArithmeticContract`:

Referees evaluate Level 68 candidates through rigorous interval analysis:

1. **Inclusion Monotonicity:** Verifies that for interval $[a, b] \subset \mathbb{Q}$, arithmetic operations satisfy the inclusion property $[x] \star [y] \supseteq \{x \star y \mid x \in [x], y \in [y]\}$.
2. **Root Isolation Verification:** Validates that `isolated_root_interval` $[a, b]$ satisfies $f(a) \cdot f(b) < 0$ and $f'(x) \ne 0$ on $[a, b]$ under `root_isolation_algorithm`, proving the existence of a unique real root.
3. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff interval endpoints are exact rationals with $a \le b$ and the enclosure property is machine-verified.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an interval width cannot be contracted below a finite precision threshold $\epsilon$ due to branch wrapping, but containment remains certified.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 68? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `IntervalArithmeticContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_INTERVAL_CONTAINMENT_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 68, "carrier_match": true, "move": "ASSERT", "root_isolation_algorithm": "bisection_interval_newton", "isolated_root_interval": ["7/5", "3/2"], "endpoint_evaluations": {"f_low": "-1/25", "f_high": "1/4"}}
REFEREE:  ACCEPT -> Status: ExactRepair (endpoints straddle zero with f(7/5) < 0 < f(3/2), root enclosure of sqrt(2) verified)
```

**Worked check (2026-10-20):** f(7/5) = 49/25 − 50/25 = −1/25 < 0 and f(3/2) = 9/4 − 2 = 1/4 > 0. On [7/5, 3/2], f'(x) = 2x ≥ 14/5 > 0, so f is increasing and exactly one root, √2 ≈ 1.4142, lies in the interval.

### Domain-Negative Test Vector (`ERR_INTERVAL_CONTAINMENT_DEFECT`)
```text
PROPOSAL: {"level": 68, "carrier_match": true, "move": "ASSERT", "root_isolation_algorithm": "bisection_interval_newton", "isolated_root_interval": ["3/2", "2"], "endpoint_evaluations": {"f_low": "1/4", "f_high": "2"}}
REFEREE:  REFUSED -> Refusal Code: ERR_INTERVAL_CONTAINMENT_DEFECT, Status: Refused (interval [3/2, 2] has f(3/2) = 1/4 > 0 and f(2) = 2 > 0; both endpoints positive, root not isolated)
```

**Worked check (2026-10-20):** f(3/2) = 1/4 and f(2) = 4 − 2 = 2 are both positive, and f is increasing on [3/2, 2], so the interval holds no root.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 68 under `IntervalArithmeticContract`.
   - Specified detection of domain discrepancies emitting `ERR_INTERVAL_CONTAINMENT_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Exact rational interval arithmetic and certified root box enclosures`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `EnclosureAnalysisModule` running `IntervalArithmeticContract` is specified to distinguish valid `Rigorous Numerics` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
