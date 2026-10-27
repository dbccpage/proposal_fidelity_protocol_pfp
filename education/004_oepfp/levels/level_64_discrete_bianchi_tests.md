---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 64: Discrete Bianchi Identities & 3-Cell Commutation"
kind: grammar-reference
level: 64
epoch: "Epoch V"
domain: "Spacetime Geometry"
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
evaluator_contract: "DiscreteBianchiContract"
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

# The Symbol Game Level 64: Discrete Bianchi Identities & 3-Cell Commutation

**AuthorityEffect:** None.  
**Level:** Level 64 | **Epoch:** Epoch V | **Domain:** Spacetime Geometry  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `4D simplicial triangulations with hinge rotation matrices in SO(4)`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_BIANCHI_IDENTITY_DEFECT`  
**Evaluator Module:** `ReggeGeometryModule` (`Discrete Bianchi Identity & Noncommutative Path Evaluator`)  
**Evaluator Contract:** `DiscreteBianchiContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ReggeGeometryModule` or contract `DiscreteBianchiContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 64 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 64: Discrete Bianchi Identities & 3-Cell Commutation** within the Spacetime Geometry bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{64} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `4D simplicial triangulations with hinge rotation matrices in SO(4)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ReggeGeometryModule` executing under `DiscreteBianchiContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of the second discrete Bianchi identity along 2-sphere boundaries of 3-cells with path-ordered parallel transport.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (ReggeGeometryModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: ReggeGeometryModule           |
| Packet:               |              | Contract: DiscreteBianchiContract       |
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

Proposals targeting Level 64 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_64_discrete_bianchi_tests.json",
  "title": "sg_packet_level_64_discrete_bianchi_tests",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "cell_3d_id": "tetrahedron_tau_0",
    "boundary_hinges": ["h_012", "h_023", "h_031", "h_123"],
    "parallel_transports_to_base": {
      "h_012": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
      "h_023": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
      "h_031": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
      "h_123": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    },
    "hinge_rotations": {
      "h_012": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
      "h_023": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
      "h_031": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
      "h_123": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    },
    "ordered_product_identity": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct DiscreteBianchiPayload {
    pub move_type: MoveType,
    pub cell_3d_id: String,
    pub boundary_hinges: Vec<String>,
    pub parallel_transports_to_base: HashMap<String, Vec<Vec<Rational>>>,
    pub hinge_rotations: HashMap<String, Vec<Vec<Rational>>>,
    pub ordered_product_identity: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 64 binds the referee to `ReggeGeometryModule` under `DiscreteBianchiContract`:

Referees evaluate Level 64 candidates through the discrete second Bianchi identity:

1. **Noncommutative Path Product:** For a 3-simplex (tetrahedron $\tau$) with boundary 2-sphere $\partial \tau$, evaluates the path-ordered product of hinge rotation matrices $R_h \in SO(4)$ parallel-transported to a shared basepoint vertex $b$:
   $$U_{\partial \tau} = \vec{\prod}_{h \subset \partial \tau} \left( \mathcal{P}_{b \leftarrow v(h)} \cdot R_h \cdot \mathcal{P}_{b \leftarrow v(h)}^{-1} \right)$$
   Note: Hinge rotations are noncommutative; closure holds strictly under the topological orientation of $\partial \tau$.
2. **Bianchi Identity Verification:** Asserts that for a closed minimal triangulation:
   $$U_{\partial \tau} = I_{4 \times 4}$$
3. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff hinge rotations and parallel transport matrices lie in $SO(4)$ and their path-ordered product equals $I_{4 \times 4}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an open topological defect prevents identity closure but the commutator holonomy is certified bounded.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 64? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `DiscreteBianchiContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_BIANCHI_IDENTITY_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 64, "carrier_match": true, "move": "ASSERT", "cell_3d_id": "tau_0", "boundary_hinges": ["h_012", "h_023", "h_031", "h_123"], "parallel_transports_to_base": {"h_012": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_023": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_031": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_123": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}, "hinge_rotations": {"h_012": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_023": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_031": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_123": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}, "ordered_product_identity": true}
REFEREE:  ACCEPT -> Status: ExactRepair (path-ordered product of hinge rotations equals identity, discrete Bianchi identity satisfied)
```

**Worked check (2026-10-20):** a tetrahedron has four boundary triangles, and the carrier uses SO(4). Before 2026-10-20 both vectors listed two hinges with 2×2 matrices, which are not in SO(4), so the passing vector failed its own criterion. The vectors now use the four hinges and 4×4 matrices of the section 3 sketch. With every transport and rotation equal to I_4, each conjugated factor is I_4 and the ordered product is I_4.

### Domain-Negative Test Vector (`ERR_BIANCHI_IDENTITY_DEFECT`)
```text
PROPOSAL: {"level": 64, "carrier_match": true, "move": "ASSERT", "cell_3d_id": "tau_0", "boundary_hinges": ["h_012", "h_023", "h_031", "h_123"], "parallel_transports_to_base": {"h_012": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_023": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_031": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_123": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}, "hinge_rotations": {"h_012": [[0,1,0,0],[-1,0,0,0],[0,0,1,0],[0,0,0,1]], "h_023": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_031": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], "h_123": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}, "ordered_product_identity": false}
REFEREE:  REFUSED -> Refusal Code: ERR_BIANCHI_IDENTITY_DEFECT, Status: Refused (ordered hinge rotation product does not close to identity, discrete Bianchi identity violated)
```

**Worked check (2026-10-20):** R = [[0,1,0,0],[−1,0,0,0],[0,0,1,0],[0,0,0,1]] is orthogonal with determinant 1, so R ∈ SO(4). The ordered product is R · I_4 · I_4 · I_4 = R ≠ I_4. The earlier 2×2 version used [[0, 1], [−1, 0]] in place of this block matrix.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 64 under `DiscreteBianchiContract`.
   - Specified detection of domain discrepancies emitting `ERR_BIANCHI_IDENTITY_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `4D simplicial complexes with path-ordered SO(4) hinge holonomies`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `ReggeGeometryModule` running `DiscreteBianchiContract` is specified to distinguish valid `Spacetime Geometry` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
