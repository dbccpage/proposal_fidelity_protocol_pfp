---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 65: Commuting Triangle Bridges & Spin Foam Vertices"
kind: grammar-reference
level: 65
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
evaluator_module: "SpinFoamModule"
evaluator_contract: "SpinFoamContract"
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

# The Symbol Game Level 65: Commuting Triangle Bridges & Spin Foam Vertices

**AuthorityEffect:** None.  
**Level:** Level 65 | **Epoch:** Epoch V | **Domain:** Quantum Gravity  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Spin-foam 2-complexes with SU(2) representations and 15j vertex amplitudes`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_INTERTWINER_INVARIANCE_DEFECT`  
**Evaluator Module:** `SpinFoamModule` (`Spin Foam Quantum Gravity Vertex & Intertwiner Evaluator`)  
**Evaluator Contract:** `SpinFoamContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SpinFoamModule` or contract `SpinFoamContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 65 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 65: Commuting Triangle Bridges & Spin Foam Vertices** within the Quantum Gravity bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{65} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Spin-foam 2-complexes with SU(2) representations and 15j vertex amplitudes`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SpinFoamModule` executing under `SpinFoamContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of SU(2) spin-label triangular closures, intertwiner gauge invariance, and 15j-symbol vertex recoupling amplitudes.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (SpinFoamModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: SpinFoamModule           |
| Packet:               |              | Contract: SpinFoamContract       |
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

Proposals targeting Level 65 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `omega-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_65_quantum_gravity_interface.json",
  "title": "sg_packet_level_65_quantum_gravity_interface",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "vertex_id": "v_spin_foam_0",
    "face_spins": {
      "f_01": "1/2", "f_02": "1/2", "f_03": "1/2", "f_04": "1/2",
      "f_12": "1/2", "f_13": "1/2", "f_14": "1/2",
      "f_23": "1/2", "f_24": "1/2", "f_34": "1/2"
    },
    "spin_labels": ["1/2", "1/2", "1/2", "1/2"],
    "intertwiners": {
      "e_0": "0", "e_1": "0", "e_2": "0", "e_3": "0", "e_4": "0"
    },
    "amplitude_15j_symbol": "1/8",
    "intertwiner_invariant": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct SpinFoamPayload {
    pub move_type: MoveType,
    pub vertex_id: String,
    pub face_spins: HashMap<String, Rational>,
    pub spin_labels: Vec<Rational>,
    pub intertwiners: HashMap<String, Rational>,
    pub amplitude_15j_symbol: Rational,
    pub intertwiner_invariant: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 65 binds the referee to `SpinFoamModule` under `SpinFoamContract`:

Referees evaluate Level 65 candidates through spin foam state sum models:

1. **SU(2) Triangular Closure:** For each edge with incident face spins $\{j_1, j_2, j_3, j_4\}$, verifies triangular admissibility conditions and that invariant intertwiners satisfy:
   $$\vec{J}_{\mathrm{total}} \cdot \iota_e = \Big( \sum_{i=1}^4 \vec{J}_i \Big) \iota_e = 0$$
2. **15j Vertex Amplitude:** Verifies that the vertex amplitude $A_v(j_f, \iota_e)$ corresponds to the contracted 15j-recoupling symbol of the 4-simplex vertex graph.
3. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff face spins lie in $\frac{1}{2}\mathbb{N}$, intertwiners are $SU(2)$-invariant, and the $15j$-symbol amplitude matches exact combinatorial recoupling.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an off-shell spin foam amplitude exhibits bounded quantum fluctuations under boundary state constraints.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 65? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `SpinFoamContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_INTERTWINER_INVARIANCE_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 65, "carrier_match": true, "move": "ASSERT", "spin_labels": ["1/2", "1/2", "1/2", "1/2"], "intertwiners": {"e0": "0"}, "amplitude_15j_symbol": "1/8", "intertwiner_invariant": true}
REFEREE:  ACCEPT -> Status: ExactRepair (spin labels admissible, SU(2) intertwiner invariance certified, 15j vertex amplitude verified)
```

**Reproducibility gap (2026-10-20):** the value 1/8 cannot be recomputed because the file does not fix the 15j convention (normalization of the intertwiners, pairing of faces at each edge, sign and phase choices). Spin admissibility does check: two spin-1/2 faces couple to a virtual spin 0 or 1, so intertwiner label 0 is allowed.

### Domain-Negative Test Vector (`ERR_INTERTWINER_INVARIANCE_DEFECT`)
```text
PROPOSAL: {"level": 65, "carrier_match": true, "move": "ASSERT", "spin_labels": ["1/2", "1/2", "1/2", "1/2"], "intertwiners": {"e0": "1/2"}, "amplitude_15j_symbol": "1/8", "intertwiner_invariant": false}
REFEREE:  REFUSED -> Refusal Code: ERR_INTERTWINER_INVARIANCE_DEFECT, Status: Refused (intertwiner spin 1/2 does not couple four spin-1/2 representations to a singlet, SU(2) invariance defect)
```

**Worked check (2026-10-20):** coupling two spin-1/2 representations gives virtual spin 0 or 1 only, so the label 1/2 is not admissible. The invariant subspace of four spin-1/2 representations has dimension 2 (virtual spins 0 and 1).

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 65 under `SpinFoamContract`.
   - Specified detection of domain discrepancies emitting `ERR_INTERTWINER_INVARIANCE_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Spin foam 2-complexes with exact SU(2) recoupling theory and 15j vertex amplitudes`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `SpinFoamModule` running `SpinFoamContract` is specified to distinguish valid `Quantum Gravity` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
