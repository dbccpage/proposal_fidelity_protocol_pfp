---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 05: Regge Metric Simplices & Deficit Obstructions"
kind: grammar-reference
level: 5
epoch: "Base Tower"
domain: "Discrete Geometry"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "ReggeMetricModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
source_paths:
  - omega_engine_education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 05: Regge Metric Simplices & Deficit Obstructions

**AuthorityEffect:** None.  
**Level:** Level 05 | **Epoch:** Base Tower | **Domain:** Discrete Geometry  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Simplicial complexes with exact squared edge lengths ℓ² ∈ Q⁺`  
**Fuel Budget:** `6 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_CAYLEY_MENGER_METRIC_VIOLATION`  
**Evaluator Module:** `ReggeMetricModule` (`Regge Metric Simplices & Hinge Deficit Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ReggeMetricModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 05 establishes the Proposal Fidelity Protocol (PFP) arena for **Regge Metric Simplices & Deficit Obstructions** within the Discrete Geometry bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{05} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Simplicial complexes with exact squared edge lengths ℓ² ∈ Q⁺`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ReggeMetricModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 6$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Cayley-Menger determinant positivity checks and hinge deficit evaluations enforcing exact metric conservativity.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 05         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `ReggeMetricModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **6 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_CAYLEY_MENGER_METRIC_VIOLATION`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 05 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_05` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_05",
  "task_data": {
    "level": 5,
    "epoch": "Base Tower",
    "domain": "Discrete Geometry",
    "carrier_digest": "blake3:b8d4e905"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 6
  },
  "budget": {
    "turn_fuel_remaining": 6,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "simplex_dimension": 2,
    "squared_edge_lengths": {
      "e_01": 1,
      "e_12": 1,
      "e_02": 2
    },
    "cayley_menger_det": 4,
    "hinge_incidence": {
      "h_0": [
        "e_01",
        "e_12"
      ]
    },
    "hinge_deficits": {
      "h_0": 0
    },
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
pub struct Level05Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: ReggeMetricPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: ReggeMetricModule

Referees evaluate Level 05 candidates through exact rational Regge simplicial geometry:

1. **Simplex Dimension & Metric Positivity:** Verifies simplex dimension $n$ and strictly positive squared edge lengths $\ell_{ij}^2 \in \mathbb{Q}^+$.
2. **Cayley-Menger Determinant & Gram Positivity:** Evaluates the simplex volume via the sign-normalized Cayley-Menger determinant:
   $$V_n^2 = \frac{(-1)^{n+1}}{2^n (n!)^2} \det(CM(\ell^2)) > 0$$
   distinguishing raw $\det(CM)$ from the sign-normalized value $(-1)^{n+1}\det(CM)$. To verify Euclidean embedding, all leading principal minors of the metric Gram matrix must be strictly positive ($G \succ 0$, Sylvester's criterion). An indefinite Gram matrix or non-positive sign-normalized determinant triggers immediate metric failure (`ERR_CAYLEY_MENGER_METRIC_VIOLATION`).
3. **Hinge Deficits:** Evaluates complete hinge incidence stars and deficit angles $\varepsilon_h = 2\pi - \sum \theta_{h,\sigma}$ represented via exact rational trigonometric / algebraic enclosures.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff Gram positivity $G \succ 0$ and Cayley-Menger metric validity hold and deficit angles satisfy declared discrete conservativity bounds.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 05 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_CAYLEY_MENGER_METRIC_VIOLATION`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_05",
  "task_data": {
    "level": 5,
    "epoch": "Base Tower",
    "domain": "Discrete Geometry",
    "carrier_digest": "blake3:b8d4e905"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 6
  },
  "budget": {
    "turn_fuel_remaining": 6,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "simplex_dimension": 2,
    "squared_edge_lengths": {
      "e_01": "1/1",
      "e_12": "1/1",
      "e_02": "2/1"
    },
    "hinge_star": {
      "hinge_id": "h_0",
      "incident_simplices": [
        "sigma_0"
      ]
    },
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
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved; raw det(CM)=-4, sign-normalized=4, G succ 0)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_05",
  "task_data": {
    "level": 5,
    "epoch": "Base Tower",
    "domain": "Discrete Geometry",
    "carrier_digest": "blake3:b8d4e905"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 6
  },
  "budget": {
    "turn_fuel_remaining": 6,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "simplex_dimension": 2,
    "squared_edge_lengths": {
      "e_01": "1/1",
      "e_12": "1/1",
      "e_02": "9/1"
    },
    "hinge_star": {
      "hinge_id": "h_0",
      "incident_simplices": [
        "sigma_0"
      ]
    },
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
REFEREE: REFUSED -> Refusal Code: ERR_CAYLEY_MENGER_METRIC_VIOLATION, Status: Refused (raw det(CM)=45, sign-normalized=-45 < 0)
```

**Worked check (2026-10-20):** For a triangle (`n = 2`) with squared side lengths `a2, b2, c2`, the Cayley-Menger determinant satisfies `-det(CM) = 16 * Area^2 = 2(a2 b2 + b2 c2 + c2 a2) - (a2^2 + b2^2 + c2^2)`.

1. Valid packet, `(l01^2, l12^2, l02^2) = (1, 1, 2)`: `2(1 + 2 + 2) - (1 + 1 + 4) = 4`, so `det(CM) = -4`, the sign-normalized value is `4`, and `Area^2 = 4/16 = 1/4` (the right isosceles triangle with legs 1). The Gram matrix at vertex 0 is `G = [[1, 1], [1, 2]]` (`G_ij = (l0i^2 + l0j^2 - lij^2)/2`); its leading minors are `1` and `1`, so `G` is positive definite.
2. Negative packet, `(1, 1, 9)`: `2(1 + 9 + 9) - (1 + 1 + 81) = -45`, so `det(CM) = 45` and the sign-normalized value is `-45 < 0`. The side lengths `1, 1, 3` break the triangle inequality (`1 + 1 < 3`), and `det G = 9 - 81/4 = -45/4 < 0`.
3. The hinge `h_0` has one incident triangle in both packets, so no interior deficit angle is evaluated; the dispositions rest on the metric check alone.

**Note on the Section 3 schema example (2026-10-20):** `"cayley_menger_det": 4` is the sign-normalized value for the edge lengths `(1, 1, 2)`; the raw determinant is `-4`. The field name does not say which convention it uses.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_05",
  "task_data": {
    "level": 5,
    "epoch": "Base Tower",
    "domain": "Discrete Geometry",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 6
  },
  "budget": {
    "turn_fuel_remaining": 6,
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
   - Formal specification of The Symbol Game Level 05 (Regge Metric Simplices & Deficit Obstructions) within the Discrete Geometry bounded context.
   - A proposed PFP packet envelope, `ReggeMetricModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 05 specifies an exact, deterministic evaluation procedure for candidate proposals over `Simplicial complexes with exact squared edge lengths ℓ² ∈ Q⁺`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
