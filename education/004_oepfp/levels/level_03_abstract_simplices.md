---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 03: Abstract Simplices & Exact LP Weak Duality"
kind: grammar-reference
level: 3
epoch: "Base Tower"
domain: "Convex Optimization"
game_edition: "v1 LP-Forcing / v3"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "ConvexOptimizationModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
source_paths:
  - education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 03: Abstract Simplices & Exact LP Weak Duality

**AuthorityEffect:** None.  
**Level:** Level 03 | **Epoch:** Base Tower | **Domain:** Convex Optimization  
**Game Edition:** `v1 LP-Forcing / v3`  
**Board Carrier:** `Oriented 2-simplices (triangles) with rational incidence matrices`  
**Fuel Budget:** `5 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_DUALITY_BOUND_VIOLATION`  
**Evaluator Module:** `ConvexOptimizationModule` (`Exact Rational LP Weak Duality Evaluator (Q)`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ConvexOptimizationModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 03 establishes the Proposal Fidelity Protocol (PFP) arena for **Abstract Simplices & Exact LP Weak Duality** within the Convex Optimization bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{03} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Oriented 2-simplices (triangles) with rational incidence matrices`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ConvexOptimizationModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 5$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact linear programming weak duality over ordered rational field Q bounding primal value cᵀx ≤ bᵀy for feasible solutions.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 03         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `ConvexOptimizationModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **5 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_DUALITY_BOUND_VIOLATION`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 03 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_03` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_03",
  "task_data": {
    "level": 3,
    "epoch": "Base Tower",
    "domain": "Convex Optimization",
    "carrier_digest": "blake3:b8d4e903"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 5
  },
  "budget": {
    "turn_fuel_remaining": 5,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "primal_vector": [
      1,
      2
    ],
    "dual_vector": [
      3,
      4
    ],
    "primal_objective": 5,
    "dual_objective": 5,
    "weak_duality_bound_satisfied": true,
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```

### AST Representation
```rust
pub struct Level03Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: LpDualityVectorPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: ConvexOptimizationModule

Referees evaluate Level 03 candidates through exact rational linear programming weak duality over $\mathbb{Q}$:

1. **Primal Feasibility:** Verifies $x \ge 0$ and $Ax \le b$ over $\mathbb{Q}$.
2. **Dual Feasibility:** Verifies $y \ge 0$ and $A^\top y \ge c$ over $\mathbb{Q}$.
3. **Weak Duality Bound:** Evaluates the fundamental inequality:
   $$c^\top x \le b^\top y$$
   Weak duality gives this bound for every feasible pair: $c^\top x \le (A^\top y)^\top x = y^\top A x \le y^\top b$, using $x \ge 0$, $y \ge 0$, $A^\top y \ge c$ and $Ax \le b$. (Zero duality gap requires separate strong duality feasibility).
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff primal and dual feasibility hold and the weak duality bound $c^\top x \le b^\top y$ is verified.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 03 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_DUALITY_BOUND_VIOLATION`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_03",
  "task_data": {
    "level": 3,
    "epoch": "Base Tower",
    "domain": "Convex Optimization",
    "carrier_digest": "blake3:b8d4e903"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 5
  },
  "budget": {
    "turn_fuel_remaining": 5,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "primal_vector_x": [
      "0/1",
      "2/1",
      "1/1"
    ],
    "dual_vector_y": [
      "1/1",
      "1/1"
    ],
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_03",
  "task_data": {
    "level": 3,
    "epoch": "Base Tower",
    "domain": "Convex Optimization",
    "carrier_digest": "blake3:b8d4e903"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 5
  },
  "budget": {
    "turn_fuel_remaining": 5,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "primal_vector_x": [
      "10/1",
      "20/1",
      "0/1"
    ],
    "dual_vector_y": [
      "1/1",
      "1/1"
    ],
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: REFUSED -> Refusal Code: ERR_PRIMAL_FEASIBILITY_VIOLATION, Status: Refused
```

**Reproducibility gap (2026-10-20):** Neither vector supplies the constraint matrix `A`, the bound vector `b` or the objective `c`. Feasibility (`x >= 0`, `Ax <= b`, `y >= 0`, `A^T y >= c`) and the bound `c^T x <= b^T y` cannot be recomputed from the packets, so neither `ACCEPT` nor `ERR_PRIMAL_FEASIBILITY_VIOLATION` can be reproduced. The shapes are also unstated: `x` has 3 entries and `y` has 2, which fits a 2-by-3 `A`, but the packet does not say so. The Section 3 schema example (`primal_objective = dual_objective = 5`) has the same gap. A complete vector needs `A`, `b` and `c` in the payload.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_03",
  "task_data": {
    "level": 3,
    "epoch": "Base Tower",
    "domain": "Convex Optimization",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 5
  },
  "budget": {
    "turn_fuel_remaining": 5,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "injected_carrier_token": "\u03a9_UNPINNED",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "corrupted_init"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 03 (Abstract Simplices & Exact LP Weak Duality) within the Convex Optimization bounded context.
   - A proposed PFP packet envelope, `ConvexOptimizationModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 03 specifies an exact, deterministic evaluation procedure for candidate proposals over `Oriented 2-simplices (triangles) with rational incidence matrices`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
