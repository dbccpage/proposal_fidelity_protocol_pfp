---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 32: Kadanoff Block Coarse Graining & Projection"
kind: grammar-reference
level: 32
epoch: "Epoch II"
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
evaluator_module: "StatisticalPhysicsModule"
evaluator_contract: "CoarseGrainingContract"
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

# The Symbol Game Level 32: Kadanoff Block Coarse Graining & Projection

**AuthorityEffect:** None.  
**Level:** Level 32 | **Epoch:** Epoch II | **Domain:** Statistical Mechanics  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Lattice spin configuration S_L with block projection B: S_L → S_{L/b}`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_BLOCK_MAP_DEFECT`  
**Evaluator Module:** `StatisticalPhysicsModule` (`Kadanoff Block Spin & Microstate Projection Evaluator`)  
**Evaluator Contract:** `CoarseGrainingContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `StatisticalPhysicsModule` or contract `CoarseGrainingContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 32 establishes the Proposal Fidelity Protocol (PFP) arena for **Kadanoff Block Coarse Graining & Projection** within the Statistical Mechanics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{32} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Lattice spin configuration S_L with block projection B: S_L → S_{L/b}`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `StatisticalPhysicsModule` (`CoarseGrainingContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Block-spin projection B: S_L → S_{L/b}, majority/decimation rule aggregation, and exact microstate loss accounting.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 32         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `StatisticalPhysicsModule` metrics under `CoarseGrainingContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_BLOCK_MAP_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 32 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_32_coarse_graining` family schema:

```json
{
  "schema_id": "sg_packet_level_32_coarse_graining",
  "task_data": {
    "level": 32,
    "epoch": "Epoch II",
    "domain": "Statistical Mechanics",
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
    "fine_lattice_size": 4,
    "block_factor_b": 2,
    "fine_spin_configuration": [1, 1, -1, 1, 1, -1, -1, -1, 1, 1, 1, 1, -1, -1, -1, 1],
    "coarse_block_spins": [1, -1, 1, -1],
    "projection_rule": "majority_rule",
    "collapsed_fiber_sizes": [3, 3, 4, 3],
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
pub struct CoarseGrainingPayload {
    pub move_type: MoveType,
    pub fine_lattice_size: u32,
    pub block_factor_b: u32,
    pub fine_spin_configuration: Vec<i8>,
    pub coarse_block_spins: Vec<i8>,
    pub projection_rule: String,
    pub collapsed_fiber_sizes: Vec<u32>,
    pub proposer_signature: String,
}

pub struct Level32Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: CoarseGrainingPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: StatisticalPhysicsModule

### Contract: `CoarseGrainingContract`

Referees evaluate Level 32 candidates through Kadanoff block-spin coarse-graining projections:

1. **Lattice Partitioning & Geometry:** Partitions $L \times L$ fine lattice $S_L$ into non-overlapping $(L/b) \times (L/b)$ blocks of side $b$.
2. **Block Projection Map:** Evaluates candidate coarse configuration $s'_K \in \{-1, +1\}$ against the declared block majority rule:
   $$s'_K = \operatorname{sgn}\left(\sum_{i \in B_K} s_i\right)$$
3. **Loss Ledger & Microstate Fiber Accounting:** Verifies the loss ledger tracking microstates collapsed by projection, recording the exact conditional entropy / fiber volume $\log |B_K(s')|$ without asserting generic global monotonic entropy decay.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the coarse-grained block spins agree identically with the block majority rule applied to the fine lattice configuration.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a scale-invariant critical spin block pattern (where spatial correlation length $\xi \gg b$) is certified invariant under repeated block projections, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 32 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_BLOCK_MAP_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 32, "carrier_match": true, "move": "ASSERT", "fine_lattice_size": 4, "block_factor_b": 2, "fine_spin_configuration": [1,1,1,1, -1,-1,-1,-1, 1,1,-1,1, -1,-1,1,-1], "coarse_block_spins": [1, -1, 1, -1]}
REFEREE:  ACCEPT -> Status: ExactRepair (only under a row-block reading, in which each row of four spins is one block; under the 2 x 2 blocks of Section 4 every block sum is 0 and the majority rule gives no output)
  ```

  **Worked check (2026-10-20):** write the 16 spins row-major as a $4 \times 4$ lattice: rows $(1,1,1,1)$, $(-1,-1,-1,-1)$, $(1,1,-1,1)$, $(-1,-1,1,-1)$.

  - Section 4 geometry ($L = 4$, $b = 2$, four $2 \times 2$ blocks): the block sums are $0, 0, 0, 0$. Each block has two $+1$ and two $-1$ spins, so $\operatorname{sgn}(0) = 0 \notin \{-1, +1\}$ and the rule needs a declared tie-break before any disposition exists.
  - Row-block reading (each row of four spins is a block): the sums are $4, -4, 2, -2$, so the majority spins are $(1, -1, 1, -1)$, which match `coarse_block_spins`. The printed `ExactRepair` holds only under this reading, which contradicts the $b \times b$ blocking in Section 4.

  **Correction (2026-10-20):** in the Section 3 schema example, `collapsed_fiber_sizes` $= [3, 3, 4, 3]$ equals the number of spins in each row-block that agree with that block's majority, not a fiber size. For a block of four spins under strict majority, the fiber over $s'_K = +1$ (or $-1$) has $1 + 4 = 5$ configurations (sum 4 or sum 2), and 6 of the 16 block configurations tie. The loss ledger entry is therefore $\log 5$ per decided block, not $\log 3$ or $\log 4$.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 32, "carrier_match": true, "move": "ASSERT", "fine_lattice_size": 4, "block_factor_b": 2, "fine_spin_configuration": [1,1,1,1, -1,-1,-1,-1, 1,1,-1,1, -1,-1,1,-1], "coarse_block_spins": [-1, 1, 1, -1]}
REFEREE:  REFUSED -> Refusal Code: ERR_BLOCK_MAP_DEFECT, Status: Refused (coarse spin block 1 outputs -1 but fine spin sum is +4, violating majority rule)
  ```

  **Worked check (2026-10-20):** under the row-block reading the block sums are $4, -4, 2, -2$, so blocks 1 and 2 both disagree with the proposed $(-1, 1, 1, -1)$; the refusal follows. Under the $2 \times 2$ blocks of Section 4 every sum is 0 (see the worked check above), so the cited "sum +4" exists only under the row-block reading.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 32, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 32: Kadanoff Block Coarse Graining & Projection within the Statistical Mechanics bounded context.
   - A proposed PFP packet envelope, `StatisticalPhysicsModule` (`CoarseGrainingContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 32 specifies an exact, deterministic evaluation procedure for candidate proposals over `Lattice spin configuration S_L with block projection B: S_L → S_{L/b}`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
