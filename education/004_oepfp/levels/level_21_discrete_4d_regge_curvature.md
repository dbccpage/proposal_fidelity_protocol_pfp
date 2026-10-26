---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 21: Discrete 4D Regge Metric Deficits & Bianchi Holonomy"
kind: grammar-reference
level: 21
epoch: "Base Tower"
domain: "Discrete General Relativity"
game_edition: "v3 L1 Oracle Governor"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: partial
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "ReggeGeometryModule"
evaluator_contract: "ReggeBianchiContract"
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

# The Symbol Game Level 21: Discrete 4D Regge Metric Deficits & Bianchi Holonomy

**AuthorityEffect:** None.  
**Level:** Level 21 | **Epoch:** Base Tower | **Domain:** Discrete General Relativity  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `4-simplex spacetime complexes with 10 edge lengths and triangle hinge deficits`  
**Fuel Budget:** `12 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_BIANCHI_HOLONOMY_DEFECT`  
**Evaluator Module:** `ReggeGeometryModule` (`4D Simplicial Regge Curvature & Bianchi Holonomy Evaluator`)  
**Evaluator Contract:** `ReggeBianchiContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ReggeGeometryModule` or contract `ReggeBianchiContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 21 establishes the Proposal Fidelity Protocol (PFP) arena for **Discrete 4D Regge Metric Deficits & Bianchi Holonomy** within the Discrete General Relativity bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{21} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `4-simplex spacetime complexes with 10 edge lengths and triangle hinge deficits`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ReggeGeometryModule` (`ReggeBianchiContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 12$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Terminal geometric stage evaluating Cayley-Menger Gram determinants, certified deficit intervals, and discrete Bianchi rotation holonomy ∏ R_t = I.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 21         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `ReggeGeometryModule` metrics under `ReggeBianchiContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **12 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_BIANCHI_HOLONOMY_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 21 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_21` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_21",
  "task_data": {
    "level": 21,
    "epoch": "Base Tower",
    "domain": "Discrete General Relativity",
    "carrier_digest": "blake3:b8d4e9..."
  },
  "protected_boundary": {
    "immutable_slots": ["carrier", "fuel_ceiling", "zero_relation_fences"],
    "max_fuel": 12
  },
  "budget": {
    "turn_fuel_remaining": 12,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "edge_squared_lengths": ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1"],
    "gram_matrix_positive": true,
    "hinge_deficit_enclosures": [["1/10", "1/8"]],
    "ordered_loop_rotations": [
      [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    ],
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
pub struct ReggeBianchiPayload {
    pub move_type: MoveType,
    pub edge_squared_lengths: [Rational; 10],
    pub gram_matrix_positive: bool,
    pub hinge_deficit_enclosures: Vec<(Rational, Rational)>,
    pub ordered_loop_rotations: Vec<[[Rational; 4]; 4]>,
    pub proposer_signature: String,
}

pub struct Level21Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: ReggeBianchiPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: ReggeGeometryModule

### Contract: `ReggeBianchiContract`

Referees evaluate Level 21 candidates through simplicial metric validation and ordered noncommutative holonomy closure:

1. **Simplex Metric Validity:** Verifies all 10 squared edge lengths $\ell_{ij}^2 \in \mathbb{Q}^+$ and asserts Gram matrix positivity $G \succ 0$ via signed Cayley-Menger determinants:
   $$(-1)^5 \det(CM(\sigma^4)) > 0$$
2. **Triangle Hinge Deficits:** Computes dihedral angles around shared 2-simplex hinges $t$, bounding local deficit angles via certified rational interval enclosures:
   $$\delta_t = 2\pi - \sum_{\sigma \supset t} \theta_t(\sigma) \in [\underline{\delta_t}, \overline{\delta_t}]$$
3. **Ordered Noncommutative Bianchi Holonomy:** For every closed simplicial hinge circuit surrounding a 4-simplex cluster, common-frame rotation matrices $R_t \in \mathrm{SO}(4, \mathbb{Q})$ must satisfy the discrete Bianchi identity:
   $$\prod_{t=1}^k R_t = I_{4 \times 4}$$
   A non-zero deficit represents valid localized curvature; failure occurs when the holonomy product deviates from the identity matrix ($R_{\mathrm{loop}} \ne I$).
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff all simplices have strictly positive 4-volume and every closed hinge loop satisfies $\|\prod_{t=1}^k R_t - I\| = 0$ identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a valid 4D Regge simplicial complex contains certified non-zero local curvature ($\|\delta_t\| > 0$) while satisfying exact Bianchi loop closure $\prod R_t = I$ without global metric flattening, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 21 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_BIANCHI_HOLONOMY_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 21, "carrier_match": true, "move": "ASSERT", "edge_squared_lengths": ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1"], "ordered_loop_rotations": [[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]]}
REFEREE:  ACCEPT -> Status: ExactRepair (4-simplex Gram metric valid and Bianchi loop holonomy closed)
  ```

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 21, "carrier_match": true, "move": "ASSERT", "edge_squared_lengths": ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1"], "ordered_loop_rotations": [[[0,1,0,0],[-1,0,0,0],[0,0,1,0],[0,0,0,1]]]}
REFEREE:  REFUSED -> Refusal Code: ERR_BIANCHI_HOLONOMY_DEFECT, Status: Refused (ordered loop rotation product yields non-identity matrix)
  ```

  **Worked check (2026-10-20):** All ten squared edge lengths equal 1, so both packets describe the regular 4-simplex with unit edges.

  1. The 6-by-6 Cayley-Menger determinant is `det(CM) = -5`, so `(-1)^5 det(CM) = 5 > 0` and `V^2 = 5 / (2^4 (4!)^2) = 5/9216`.
  2. The Gram matrix at vertex 0 has 1 on the diagonal and `1/2` off it. Its leading principal minors are `1, 3/4, 1/2, 5/16`, all positive, so `G` is positive definite, and `det(G)/(4!)^2 = (5/16)/576 = 5/9216` agrees with item 1.
  3. Valid packet: the single loop rotation is the 4-by-4 identity, so the product is `I`.
  4. Negative packet: `R = [[0,1,0,0],[-1,0,0,0],[0,0,1,0],[0,0,0,1]]` satisfies `R R^T = I` and `det R = 1`, so it lies in `SO(4)`, and it is a quarter turn in the first coordinate plane, not `I`. The product therefore differs from `I`, as the refusal states.

  **Scope note (2026-10-20):** One 4-simplex has no interior triangle hinge, so no deficit angle is computed here, and the packets carry no `enclosing_boundary_witness` showing that the listed loop is a closed dual cycle around a vertex. The discrete Bianchi identity applies to such enclosing cycles; a single-hinge holonomy can differ from `I` on a curved complex without a defect. These vectors therefore test only the matrix product, not the Bianchi identity itself.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 21, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 21: Discrete 4D Regge Metric Deficits & Bianchi Holonomy within the Discrete General Relativity bounded context.
   - A proposed PFP packet envelope, `ReggeGeometryModule` (`ReggeBianchiContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 21 specifies an exact, deterministic evaluation procedure for candidate proposals over `4-simplex spacetime complexes with 10 edge lengths and triangle hinge deficits`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
