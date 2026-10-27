---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 60: Gottesman Stabilizer Codes & Syndrome Decoders"
kind: grammar-reference
level: 60
epoch: "Epoch IV"
domain: "Quantum Computing"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "StabilizerCodeModule"
evaluator_contract: "StabilizerCodeContract"
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

# The Symbol Game Level 60: Gottesman Stabilizer Codes & Syndrome Decoders

**AuthorityEffect:** None.  
**Level:** Level 60 | **Epoch:** Epoch IV | **Domain:** Quantum Computing  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Abelian stabilizer subgroups S ⊂ P_n with syndrome measurement projectors`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_STABILIZER_GENERATORS_DEFECT`  
**Evaluator Module:** `StabilizerCodeModule` (`Gottesman Stabilizer Subgroup & Syndrome Decoder Evaluator`)  
**Evaluator Contract:** `StabilizerCodeContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `StabilizerCodeModule` or contract `StabilizerCodeContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 60 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 60: Gottesman Stabilizer Codes & Syndrome Decoders** within the Quantum Computing bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{60} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Abelian stabilizer subgroups S ⊂ P_n with syndrome measurement projectors`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `StabilizerCodeModule` executing under `StabilizerCodeContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of stabilizer code spaces C(S), mutually commuting Pauli generators, non-triviality -I ∉ S, and deterministic syndrome decoders.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (StabilizerCodeModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: StabilizerCodeModule           |
| Packet:               |              | Contract: StabilizerCodeContract       |
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

Proposals targeting Level 60 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_60_quantum_error_correction.json",
  "title": "sg_packet_level_60_quantum_error_correction",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "qubit_count": 5,
    "stabilizer_generators": [
      "X1Z2Z3X4I5",
      "I1X2Z3Z4X5",
      "X1I2X3Z4Z5",
      "Z1X2I3X4Z5"
    ],
    "minus_identity_excluded": true,
    "pairwise_commuting": true,
    "syndrome_lookup_table": {
      "0000": "IIIII",
      "1010": "ZIIII",
      "0101": "IZIII",
      "0010": "IIZII",
      "1001": "IIIZI"
    },
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct StabilizerCodePayload {
    pub move_type: MoveType,
    pub qubit_count: usize,
    pub stabilizer_generators: Vec<String>,
    pub minus_identity_excluded: bool,
    pub pairwise_commuting: bool,
    pub syndrome_lookup_table: HashMap<String, String>,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 60 binds the referee to `StabilizerCodeModule` under `StabilizerCodeContract`:

Referees evaluate Level 60 proposals under the Gottesman stabilizer formalism:

1. **Abelian Generator Commutation:** For independent generator set $\{g_1, \dots, g_{n-k}\} \subset \mathcal{P}_n$, verifies pairwise commutation:
   $$[g_i, g_j] = 0 \quad \forall i, j \in \{1, \dots, n-k\}$$
2. **Non-Triviality and Independence:** Asserts $-I \notin S$ and that the binary symplectic check matrix has full rank $n-k$ over $\mathbb{F}_2$.
3. **Syndrome Decoding Map:** Validates that `syndrome_lookup_table` associates distinct error operators $E \in \mathcal{E}$ with distinct syndrome vectors $s(E) \in \mathbb{F}_2^{n-k}$ where $s(E)_i = 0$ if $[E, g_i] = 0$ and $1$ if $\{E, g_i\} = 0$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff stabilizer generators are mutually commuting, linearly independent over $\mathbb{F}_2$, minus identity is excluded (`minus_identity_excluded == true`), and each syndrome uniquely resolves an error candidate.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an uncorrectable degenerate error coset is detected and structurally fenced within the code space without corrupting logical code states.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 60? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `StabilizerCodeContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `10 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_STABILIZER_GENERATORS_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `10 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 60, "carrier_match": true, "move": "ASSERT", "qubit_count": 5, "stabilizer_generators": ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"], "minus_identity_excluded": true, "pairwise_commuting": true, "syndrome_lookup_table": {"0000": "IIIII"}}
REFEREE:  ACCEPT -> Status: ExactRepair (stabilizer generators independent, commuting, minus identity excluded, code space verified)
```

**Worked check (2026-10-20):** each pair of the generators XZZXI, IXZZX, XIXZZ and ZXIXZ differs by non-identity Paulis in an even number of positions, so all pairs commute. Their binary symplectic rows have rank 4 over F_2, so k = 5 − 4 = 1. The syndrome bit s_i is 1 when the error anticommutes with g_i. Single-qubit errors give X1 → 0001, Z1 → 1010, X2 → 1000, Z2 → 0101, X3 → 1100, Z3 → 0010, X4 → 0110, Z4 → 1001, X5 → 0011 and Z5 → 0100: ten distinct nonzero syndromes. The section 3 lookup table previously mapped 0001, 0010, 0100 and 1000 to Z errors on qubits 1 to 4; those syndromes belong to X1, Z3, Z5 and X2, and the table was corrected above on 2026-10-20.

### Domain-Negative Test Vector (`ERR_STABILIZER_GENERATORS_DEFECT`)
```text
PROPOSAL: {"level": 60, "carrier_match": true, "move": "ASSERT", "qubit_count": 5, "stabilizer_generators": ["XZZXI", "ZXXXX", "XIXZZ", "ZXIXZ"], "minus_identity_excluded": true, "pairwise_commuting": false, "syndrome_lookup_table": {"0000": "IIIII"}}
REFEREE:  REFUSED -> Refusal Code: ERR_STABILIZER_GENERATORS_DEFECT, Status: Refused (generators XZZXI and ZXXXX anticommute, violating abelian stabilizer group requirement)
```

**Worked check (2026-10-20):** XZZXI and ZXXXX have different non-identity Paulis at positions 1, 2 and 3 and agree at position 4. Three is odd, so they anticommute.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 60 under `StabilizerCodeContract`.
   - Specified detection of domain discrepancies emitting `ERR_STABILIZER_GENERATORS_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Abelian stabilizer codes over finite qubit registers with symplectic parity checks`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `StabilizerCodeModule` running `StabilizerCodeContract` is specified to distinguish valid `Quantum Computing` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
