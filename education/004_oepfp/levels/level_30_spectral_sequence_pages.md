---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 30: Spectral Sequence Pages & Differential Transits"
kind: grammar-reference
level: 30
epoch: "Epoch I"
domain: "Homological Algebra"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SpectralSequenceModule"
evaluator_contract: "SpectralSequencePageContract"
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

# The Symbol Game Level 30: Spectral Sequence Pages & Differential Transits

**AuthorityEffect:** None.  
**Level:** Level 30 | **Epoch:** Epoch I | **Domain:** Homological Algebra  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Spectral sequence pages E_r^{p,q} with differentials d_r and homology transits`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_FILTRATION_DEFECT`  
**Evaluator Module:** `SpectralSequenceModule` (`Spectral Sequence Page & Differential Nilpotence Evaluator`)  
**Evaluator Contract:** `SpectralSequencePageContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SpectralSequenceModule` or contract `SpectralSequencePageContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 30 establishes the Proposal Fidelity Protocol (PFP) arena for **Spectral Sequence Pages & Differential Transits** within the Homological Algebra bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{30} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Spectral sequence pages E_r^{p,q} with differentials d_r and homology transits`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SpectralSequenceModule` (`SpectralSequencePageContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Differential bidegrees, nilpotence d_r ∘ d_r = 0, and successive page homology isomorphisms E_{r+1} ≅ H(E_r, d_r).

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 30         ┌──────────────────────────┐
│     Untrusted Neural     ├────────────────────────────────────────►│    Deterministic Host    │
│    Proposer (Player)     │◄────────────────────────────────────────┤      Checker (Rust)      │
└──────────────────────────┘          Typed Terminal Receipt         └────────────┬─────────────┘
                                                                                  │
                                             Emits Immutable Verification Receipt ▼
                                                                     ┌──────────────────────────┐
                                                                     │   Residual Loss Ledger   │
                                                                     │  (Zero Authority Mints)  │
                                                                     └──────────────────────────┘
```

1. **Untrusted Proposer Role:** Submits candidate move proposals formatted as typed wire envelopes. Proposer outputs carry zero ambient trust and cannot mutate board configuration directly.
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `SpectralSequenceModule` metrics under `SpectralSequencePageContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_FILTRATION_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 30 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_30_spectral_sequence_pages` family schema:

```json
{
  "schema_id": "sg_packet_level_30_spectral_sequence_pages",
  "task_data": {
    "level": 30,
    "epoch": "Epoch I",
    "domain": "Homological Algebra",
    "carrier_digest": "blake3:b8d4e9..."
  },
  "protected_boundary": {
    "immutable_slots": ["carrier", "fuel_ceiling", "zero_relation_fences"],
    "max_fuel": 10
  },
  "budget": {
    "turn_fuel_remaining": 10,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "page_index_r": 1,
    "bidegree_transit": {"dr_source": [0, 1], "dr_target": [1, 0]},
    "differential_matrix_dr": [[1, 0], [0, 0]],
    "nilpotence_check_dr_squared": [[0, 0], [0, 0]],
    "next_page_homology": {"E2_0_1_rank": 1, "E2_1_0_rank": 0},
    "proposer_signature": "untrusted_candidate_token" 
  },
  "witness_data": {
    "replay_trace": ["init", "step_1"],
    "proof_certificate": null
  }
}
```

### AST Representation
```rust
pub struct SpectralSequencePayload {
    pub move_type: MoveType,
    pub page_index_r: u32,
    pub bidegree_transit: BidegreeMap,
    pub differential_matrix_dr: Vec<Vec<Rational>>,
    pub nilpotence_check_dr_squared: Vec<Vec<Rational>>,
    pub next_page_homology: BTreeMap<String, u32>,
    pub proposer_signature: String,
}

pub struct Level30Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SpectralSequencePayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: SpectralSequenceModule

### Contract: `SpectralSequencePageContract`

Referees evaluate Level 30 candidates through spectral sequence page transit mechanics:

1. **Differential Bidegree & Nilpotence:** Verifies page $r$ differential $d_r\colon E_r^{p,q} \to E_r^{p+r, q-r+1}$ satisfies nilpotence:
   $$d_r^{p+r, q-r+1} \circ d_r^{p,q} = 0$$
2. **Page Homology Succession:** Evaluates candidate page modules $E_{r+1}^{p,q}$ verifying the canonical homology isomorphism:
   $$E_{r+1}^{p,q} \cong \frac{\ker(d_r^{p,q})}{\operatorname{im}(d_r^{p-r, q+r-1})}$$
3. **Filtered Chain Complexes Convergence:** Audits bounded filtration convergence ensuring finite sheet stabilization $E_r^{p,q} = E_\infty^{p,q}$ for $r > N$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff all page differentials satisfy $d_r^2 = 0$ identically and the successive page modules match the differential homology quotient.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant non-zero terminal term $E_\infty^{p,q} \ne 0$ corresponding to a persistent homology class in the abutment is certified stable, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 30 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_FILTRATION_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 30, "carrier_match": true, "move": "ASSERT", "page_index_r": 1, "differential_matrix_dr": [[0, 1], [0, 0]], "nilpotence_check_dr_squared": [[0, 0], [0, 0]], "next_page_homology": {"rank": 1}}
REFEREE:  ACCEPT -> Status: ExactRepair (page differential satisfies d_r^2 = 0 and page homology succession confirmed)
  ```

  **Worked check (2026-10-20):** the matrix $D = \begin{pmatrix} 0 & 1 \\ 0 & 0 \end{pmatrix}$ has $D^2 = 0$, as the packet states. Read as an endomorphism of one 2-dimensional group with $D^2 = 0$, its homology is $\ker D / \operatorname{im} D = \langle e_1 \rangle / \langle e_1 \rangle = 0$, so a next-page rank of 1 does not follow under that reading. Read instead as one map $E_1^{p,q} \to E_1^{p+1,q}$ between two different 2-dimensional groups with no other differentials, $\ker D$ has rank 1 at the source and $\operatorname{coker} D$ has rank 1 at the target, so the single value `"rank": 1` does not say which group it describes.

  **Correction (2026-10-20):** the schema example in Section 3 gives `dr_source` $(0,1)$ and `dr_target` $(1,0)$ on page $r = 1$. The stated bidegree rule $d_r\colon E_r^{p,q} \to E_r^{p+r,\,q-r+1}$ sends $(0,1)$ to $(1,1)$ when $r = 1$; a change of $(+1,-1)$ fits no value of $r$ under that rule. The same example lists `E2_1_0_rank: 0`, but the rank-1 map $\begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}$ into a 2-dimensional target leaves a cokernel of rank 1.

  **Reproducibility gap (2026-10-20):** a single differential between distinct bidegrees satisfies $d_r \circ d_r = 0$ only as a composite with the next differential; the packets give neither the group dimensions at each bidegree nor the neighbouring differentials, so "nilpotence" is checked here as a matrix square only.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 30, "carrier_match": true, "move": "ASSERT", "page_index_r": 1, "differential_matrix_dr": [[1, 0], [0, 1]], "nilpotence_check_dr_squared": [[1, 0], [0, 1]]}
REFEREE:  REFUSED -> Refusal Code: ERR_FILTRATION_DEFECT, Status: Refused (page differential fails nilpotence: d_r o d_r != 0)
  ```

  **Worked check (2026-10-20):** the identity matrix squares to itself, $I^2 = I \ne 0$, so as a matrix-square test the refusal follows from the data (subject to the reproducibility gap above).

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 30, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 30: Spectral Sequence Pages & Differential Transits within the Homological Algebra bounded context.
   - A proposed PFP packet envelope, `SpectralSequenceModule` (`SpectralSequencePageContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 30 specifies an exact, deterministic evaluation procedure for candidate proposals over `Spectral sequence pages E_r^{p,q} with differentials d_r and homology transits`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
