---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 70: Transfer Matrix Spectra & Spectral Gap Enclosures"
kind: grammar-reference
level: 70
epoch: "Epoch VI"
domain: "Statistical Mechanics"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SpectralDiagnosticModule"
evaluator_contract: "TransferSpectraContract"
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

# The Symbol Game Level 70: Transfer Matrix Spectra & Spectral Gap Enclosures

**AuthorityEffect:** None.  
**Level:** Level 70 | **Epoch:** Epoch VI | **Domain:** Statistical Mechanics  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Positive transfer matrices in Q^{d x d} with Perron-Frobenius spectral gaps`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_TRANSFER_SPECTRAL_GAP_DEFECT`  
**Evaluator Module:** `SpectralDiagnosticModule` (`Transfer Matrix Spectral Gap & Correlation Length Evaluator`)  
**Evaluator Contract:** `TransferSpectraContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SpectralDiagnosticModule` or contract `TransferSpectraContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 70 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 70: Transfer Matrix Spectra & Spectral Gap Enclosures** within the Statistical Mechanics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{70} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Positive transfer matrices in Q^{d x d} with Perron-Frobenius spectral gaps`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SpectralDiagnosticModule` executing under `TransferSpectraContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact verification of Perron-Frobenius dominant eigenvalues, Gershgorin discs, and correlation length enclosures.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (SpectralDiagnosticModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: SpectralDiagnosticModule           |
| Packet:               |              | Contract: TransferSpectraContract       |
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

Proposals targeting Level 70 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `omega-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_70_finite_transfer_spectra.json",
  "title": "sg_packet_level_70_finite_transfer_spectra",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "transfer_matrix": [
      ["2", "1"],
      ["1", "2"]
    ],
    "dominant_eigenvalue": "3",
    "subleading_eigenvalue": "1",
    "spectral_gap": "2",
    "gershgorin_discs": [
      {"center": "2", "radius": "1"},
      {"center": "2", "radius": "1"}
    ],
    "correlation_length_enclosure": ["9/10", "11/10"],
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct TransferSpectraPayload {
    pub move_type: MoveType,
    pub transfer_matrix: Vec<Vec<Rational>>,
    pub dominant_eigenvalue: Rational,
    pub subleading_eigenvalue: Rational,
    pub spectral_gap: Rational,
    pub gershgorin_discs: Vec<GershgorinDisc>,
    pub correlation_length_enclosure: (Rational, Rational),
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 70 binds the referee to `SpectralDiagnosticModule` under `TransferSpectraContract`:

Referees evaluate Level 70 candidates through Perron-Frobenius transfer matrix spectral analysis:

1. **Perron-Frobenius Dominance:** For strictly positive transfer matrix $T \in \mathbb{Q}^{d \times d}$, asserts the existence of a unique maximal positive eigenvalue $\lambda_0 > |\lambda_1|$.
2. **Gershgorin Disc Enclosure:** Computes row radii $R_i = \sum_{j \ne i} |T_{ij}|$ and verifies that all eigenvalues lie within $\bigcup_i D(T_{ii}, R_i)$.
3. **Correlation Length Calculation:** Verifies that the physical correlation length enclosure satisfies:
   $$\xi = -\frac{1}{\ln(|\lambda_1| / \lambda_0)}$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff transfer matrix elements are rational, Gershgorin discs bound the spectrum, and the spectral gap $\Delta = \lambda_0 - |\lambda_1| > 0$ is certified.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff near-criticality ($\Delta \le \epsilon$) causes correlation length divergence while the spectral gap remains strictly positive.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 70? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `TransferSpectraContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_TRANSFER_SPECTRAL_GAP_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 70, "carrier_match": true, "move": "ASSERT", "transfer_matrix": [["2", "1"], ["1", "2"]], "dominant_eigenvalue": "3", "subleading_eigenvalue": "1", "spectral_gap": "2", "gershgorin_discs": [{"center": "2", "radius": "1"}, {"center": "2", "radius": "1"}], "correlation_length_enclosure": ["9/10", "11/10"]}
REFEREE:  ACCEPT -> Status: ExactRepair (Perron-Frobenius dominant eigenvalue 3, subleading 1, spectral gap 2 verified)
```

**Worked check (2026-10-20):** T = [[2, 1], [1, 2]] has eigenvalue 3 on (1, 1) and 1 on (1, −1). Both Gershgorin discs are centred at 2 with radius 1, covering [1, 3], which holds both eigenvalues. The gap is 3 − 1 = 2, and ξ = −1/ln(1/3) = 1/ln 3 ≈ 0.9102, inside [9/10, 11/10]. A rational certificate of that enclosure needs bounds on ln 3; 10/11 ≤ ln 3 ≤ 10/9 suffices, since ln 3 ≈ 1.0986.

### Domain-Negative Test Vector (`ERR_TRANSFER_SPECTRAL_GAP_DEFECT`)
```text
PROPOSAL: {"level": 70, "carrier_match": true, "move": "ASSERT", "transfer_matrix": [["2", "1"], ["1", "2"]], "dominant_eigenvalue": "3", "subleading_eigenvalue": "3", "spectral_gap": "0", "gershgorin_discs": [{"center": "2", "radius": "1"}], "correlation_length_enclosure": ["0", "0"]}
REFEREE:  REFUSED -> Refusal Code: ERR_TRANSFER_SPECTRAL_GAP_DEFECT, Status: Refused (declared spectral gap 0 violates Perron-Frobenius theorem for strictly positive matrix [[2,1],[1,2]])
```

**Worked check (2026-10-20):** the trace is 4 and the determinant is 3, so the eigenvalues are the roots of λ² − 4λ + 3 = 0, namely 3 and 1. A double eigenvalue 3 would need trace 6.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 70 under `TransferSpectraContract`.
   - Specified detection of domain discrepancies emitting `ERR_TRANSFER_SPECTRAL_GAP_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Positive rational transfer matrices with exact Perron-Frobenius spectral gaps`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `SpectralDiagnosticModule` running `TransferSpectraContract` is specified to distinguish valid `Statistical Mechanics` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
