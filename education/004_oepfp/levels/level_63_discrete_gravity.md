---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 63: Discrete Regge Spacetime & Simplicial Action"
kind: grammar-reference
level: 63
epoch: "Epoch V"
domain: "Quantum Gravity"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "ReggeGeometryModule"
evaluator_contract: "ReggeGravityContract"
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

# The Symbol Game Level 63: Discrete Regge Spacetime & Simplicial Action

**AuthorityEffect:** None.  
**Level:** Level 63 | **Epoch:** Epoch V | **Domain:** Quantum Gravity  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Discrete 4D simplicial manifolds with exact rational squared edge lengths`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_REGGE_METRIC_DEFECT`  
**Evaluator Module:** `ReggeGeometryModule` (`Discrete Regge Spacetime & Gravitational Action Evaluator`)  
**Evaluator Contract:** `ReggeGravityContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ReggeGeometryModule` or contract `ReggeGravityContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 63 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 63: Discrete Regge Spacetime & Simplicial Action** within the Quantum Gravity bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{63} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Discrete 4D simplicial manifolds with exact rational squared edge lengths`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ReggeGeometryModule` executing under `ReggeGravityContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact verification of simplicial metric embedding, triangle hinge areas, deficit angle enclosures, and Regge gravitational action.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (ReggeGeometryModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: ReggeGeometryModule           |
| Packet:               |              | Contract: ReggeGravityContract       |
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

Proposals targeting Level 63 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `omega-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_63_discrete_gravity.json",
  "title": "sg_packet_level_63_discrete_gravity",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "simplicial_complex_id": "regge_4_simplex_cluster",
    "squared_edge_lengths": {
      "(0,1)": "1", "(0,2)": "1", "(0,3)": "1", "(0,4)": "1",
      "(1,2)": "1", "(1,3)": "1", "(1,4)": "1",
      "(2,3)": "1", "(2,4)": "1", "(3,4)": "1"
    },
    "cayley_menger_positive": true,
    "deficit_angle_enclosure": {
      "hinge_012": ["0", "0"]
    },
    "total_regge_action_enclosure": ["0", "0"],
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct ReggeGravityPayload {
    pub move_type: MoveType,
    pub simplicial_complex_id: String,
    pub squared_edge_lengths: HashMap<String, Rational>,
    pub cayley_menger_positive: bool,
    pub deficit_angle_enclosure: HashMap<String, (Rational, Rational)>,
    pub total_regge_action_enclosure: (Rational, Rational),
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 63 binds the referee to `ReggeGeometryModule` under `ReggeGravityContract`:

Referees evaluate Level 63 candidates through discrete Regge calculus:

1. **Cayley-Menger Metric Validity:** For each $k$-simplex $\sigma^k$, verifies the metric embeddability condition on squared edge lengths $s_e = \ell_e^2 \in \mathbb{Q}_{>0}$:
   $$(-1)^{k+1} \det(CM(\sigma^k)) > 0$$
2. **Hinge Areas & Dihedral Angles:** Computes triangle hinge areas $A_h = \frac{1}{4}\sqrt{-\det(CM(\sigma^2))}$ and certifies interval enclosures of dihedral angles $\theta_h(\sigma^4)$ over rational bounds.
3. **Deficit Angle Enclosure & Regge Action:** For each hinge $h$, computes the deficit angle enclosure:
   $$\epsilon_h = 2\pi - \sum_{\sigma^4 \supset h} \theta_h(\sigma^4)$$
   and the total Regge action enclosure:
   $$S_{\mathrm{Regge}} = \sum_h A_h \epsilon_h$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff Cayley-Menger determinants are strictly positive and the candidate's `deficit_angle_enclosure` tightly contains the true geometric deficit.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an obstinate non-flat deficit angle is certified to reside within a stable bounded enclosure without metric collapse.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 63? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `ReggeGravityContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_REGGE_METRIC_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Specified Passing Test Vector (`ASSERT`; does not pass as printed, see the worked check)
```text
PROPOSAL: {"level": 63, "carrier_match": true, "move": "ASSERT", "squared_edge_lengths": {"(0,1)": "1", "(0,2)": "1", "(1,2)": "1"}, "cayley_menger_positive": true, "deficit_angle_enclosure": {"hinge_012": ["0", "0"]}, "total_regge_action_enclosure": ["0", "0"]}
REFEREE:  REFUSED -> Refusal Code: ERR_REGGE_METRIC_DEFECT, Status: Refused (corrected 2026-10-20: the Cayley-Menger test passes, but the enclosure [0, 0] does not contain the deficit of hinge 012)
```

**Worked check (2026-10-20):** for the unit triangle, det CM = −3, so (−1)³ det CM = 3 > 0 and the area is √3/4. A lone triangle lies in no 4-simplex, so ε = 2π − (empty sum) = 2π and [0, 0] does not contain it. With the section 3 sketch (a regular 4-simplex with unit squared edges, (−1)⁵ det CM = 5 > 0) each dihedral angle is arccos(1/4) ≈ 1.3181, so the interior formula gives ε ≈ 4.9651 and the boundary convention π − θ gives ε ≈ 1.8235; neither is 0. Zero deficits need dihedral angles around each hinge that sum to 2π, and 2π / arccos(1/4) ≈ 4.77 is not an integer, so no cluster of regular unit 4-simplices is flat. The original line read `ACCEPT -> Status: ExactRepair`; it was corrected because the section 4 criterion requires the enclosure to contain the true deficit.

### Domain-Negative Test Vector (`ERR_REGGE_METRIC_DEFECT`)
```text
PROPOSAL: {"level": 63, "carrier_match": true, "move": "ASSERT", "squared_edge_lengths": {"(0,1)": "1", "(0,2)": "4", "(1,2)": "1"}, "cayley_menger_positive": false, "deficit_angle_enclosure": {"hinge_012": ["0", "0"]}, "total_regge_action_enclosure": ["0", "0"]}
REFEREE:  REFUSED -> Refusal Code: ERR_REGGE_METRIC_DEFECT, Status: Refused (triangle inequality violated: edge lengths 1, 1, 2 yield degenerate zero Cayley-Menger determinant)
```

**Worked check (2026-10-20):** squared lengths 1, 4, 1 give 16A² = 2(1·4 + 4·1 + 1·1) − (1 + 16 + 1) = 18 − 18 = 0, so det CM = 0 and the triangle is degenerate.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 63 under `ReggeGravityContract`.
   - Specified detection of domain discrepancies emitting `ERR_REGGE_METRIC_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Simplicial 4-geometries with rational squared edge lengths and interval deficit enclosures`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `ReggeGeometryModule` running `ReggeGravityContract` is specified to distinguish valid `Quantum Gravity` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
