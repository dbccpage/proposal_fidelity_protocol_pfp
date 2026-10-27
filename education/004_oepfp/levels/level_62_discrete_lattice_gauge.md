---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 62: Wilson Plaquette Loops & Lattice Yang-Mills Action"
kind: grammar-reference
level: 62
epoch: "Epoch V"
domain: "Lattice Field Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "LatticeGaugeModule"
evaluator_contract: "LatticeGaugeContract"
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

# The Symbol Game Level 62: Wilson Plaquette Loops & Lattice Yang-Mills Action

**AuthorityEffect:** None.  
**Level:** Level 62 | **Epoch:** Epoch V | **Domain:** Lattice Field Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Hypercubic lattice gauge theories with unitary link variables and Wilson plaquette action`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_PLAQUETTE_HOLONOMY_DEFECT`  
**Evaluator Module:** `LatticeGaugeModule` (`Lattice Yang-Mills & Wilson Plaquette Action Evaluator`)  
**Evaluator Contract:** `LatticeGaugeContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `LatticeGaugeModule` or contract `LatticeGaugeContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 62 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 62: Wilson Plaquette Loops & Lattice Yang-Mills Action** within the Lattice Field Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{62} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Hypercubic lattice gauge theories with unitary link variables and Wilson plaquette action`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `LatticeGaugeModule` executing under `LatticeGaugeContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of unitary link variables, plaquette holonomies, and gauge-invariant Wilson lattice action.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (LatticeGaugeModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: LatticeGaugeModule           |
| Packet:               |              | Contract: LatticeGaugeContract       |
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

Proposals targeting Level 62 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_62_discrete_lattice_gauge.json",
  "title": "sg_packet_level_62_discrete_lattice_gauge",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "gauge_group": "SU(2)",
    "lattice_dimensions": [4, 4, 4, 4],
    "oriented_plaquettes": [
      {
        "plaquette_id": "p_01_xy",
        "base_vertex": [0, 0, 0, 0],
        "directions": [0, 1],
        "holonomy_trace": "2",
        "wilson_action_contribution": "0"
      }
    ],
    "total_wilson_action": "0",
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct LatticeGaugePayload {
    pub move_type: MoveType,
    pub gauge_group: String,
    pub lattice_dimensions: Vec<usize>,
    pub oriented_plaquettes: Vec<PlaquetteSpec>,
    pub total_wilson_action: Rational,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 62 binds the referee to `LatticeGaugeModule` under `LatticeGaugeContract`:

Referees evaluate Level 62 candidates through discrete lattice gauge theory:

1. **Link Variable Orientation:** Evaluates unitary link matrices $U_\mu(x) \in SU(N)$ satisfying $U_{-\mu}(x + \hat{\mu}) = U_\mu(x)^\dagger$.
2. **Plaquette Holonomy Computation:** For each elementary 2-cell (oriented plaquette $p = (x; \mu, \nu)$), computes the cyclic product:
   $$U_p = U_\mu(x) \cdot U_\nu(x + \hat{\mu}) \cdot U_\mu^\dagger(x + \hat{\nu}) \cdot U_\nu^\dagger(x)$$
3. **Wilson Action Calculation:** Verifies the gauge-invariant Wilson lattice action contribution:
   $$S_W = \sum_{p} \left( 1 - \frac{1}{N} \operatorname{Re}\operatorname{Tr}(U_p) \right)$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff link variables are unitary and `wilson_action_contribution` correctly matches the trace of the ordered plaquette product.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a non-trivial magnetic vortex (Plaquette with $\operatorname{Tr}(U_p) \ne N$) is certified topologically stable under local deformations.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 62? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `LatticeGaugeContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_PLAQUETTE_HOLONOMY_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 62, "carrier_match": true, "move": "ASSERT", "gauge_group": "SU(2)", "oriented_plaquettes": [{"plaquette_id": "p0", "holonomy_trace": "2", "wilson_action_contribution": "0"}], "total_wilson_action": "0"}
REFEREE:  ACCEPT -> Status: ExactRepair (oriented plaquettes satisfy cyclic link multiplication, Wilson action verified)
```

**Worked check (2026-10-20):** for SU(2), N = 2 and the contribution is 1 − Tr(U_p)/2 = 1 − 2/2 = 0.

**Reproducibility gap (2026-10-20):** no link variables are given, so the trace 2 cannot be recomputed from links; only the step from trace to action is checkable.

### Domain-Negative Test Vector (`ERR_PLAQUETTE_HOLONOMY_DEFECT`)
```text
PROPOSAL: {"level": 62, "carrier_match": true, "move": "ASSERT", "gauge_group": "SU(2)", "oriented_plaquettes": [{"plaquette_id": "p0", "holonomy_trace": "-2", "wilson_action_contribution": "0"}], "total_wilson_action": "0"}
REFEREE:  REFUSED -> Refusal Code: ERR_PLAQUETTE_HOLONOMY_DEFECT, Status: Refused (plaquette holonomy trace -2 does not match declared zero Wilson action contribution 1 - (-2)/2 = 2 != 0)
```

**Worked check (2026-10-20):** 1 − (−2)/2 = 2 ≠ 0. A trace of −2 in SU(2) means U_p = −I.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 62 under `LatticeGaugeContract`.
   - Specified detection of domain discrepancies emitting `ERR_PLAQUETTE_HOLONOMY_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Unitary lattice gauge theories on finite 4-dimensional hypercubic grids`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `LatticeGaugeModule` running `LatticeGaugeContract` is specified to distinguish valid `Lattice Field Theory` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
