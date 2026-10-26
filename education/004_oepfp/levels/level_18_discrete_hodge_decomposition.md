---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 18: Discrete Hodge Decomposition & Harmonic Cochains"
kind: grammar-reference
level: 18
epoch: "Base Tower"
domain: "Differential Topology"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "CochainResidualModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
  - StabilizedSurvivor
source_paths:
  - omega_engine_education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 18: Discrete Hodge Decomposition & Harmonic Cochains

**AuthorityEffect:** None.  
**Level:** Level 18 | **Epoch:** Base Tower | **Domain:** Differential Topology  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Combinatorial forms over Q with Hodge Laplacian Δ = dδ + δd`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_HODGE_RESIDUAL_NONZERO`  
**Evaluator Module:** `CochainResidualModule` (`Combinatorial Cohomology Evaluator (Q)`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CochainResidualModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 18 establishes the Proposal Fidelity Protocol (PFP) arena for **Discrete Hodge Decomposition & Harmonic Cochains** within the Differential Topology bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{18} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Combinatorial forms over Q with Hodge Laplacian Δ = dδ + δd`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CochainResidualModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Orthogonal splitting C¹ = im(d₀) ⊕ H¹ ⊕ im(δ₁) separating exact boundaries, harmonic survivors, and coexact flux.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 18         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `CochainResidualModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_HODGE_RESIDUAL_NONZERO`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 18 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_18` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_18",
  "task_data": {
    "level": 18,
    "epoch": "Base Tower",
    "domain": "Differential Topology",
    "carrier_digest": "blake3:b8d4e912"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 10
  },
  "budget": {
    "turn_fuel_remaining": 10,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "target_cochain": [
      1,
      0,
      -1
    ],
    "coboundary_witness": [
      0,
      0
    ],
    "cycle_defect": 0,
    "boundary_defect": 0,
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
pub struct Level18Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: ExactRationalCochain,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: CochainResidualModule

Referees evaluate Level 18 candidates through objective combinatorial cohomology over $\mathbb{Q}$:

1. **Boundary Defect ($\Phi_1$):** Measures quotient-norm distance from candidate cochain $c$ to the declared gauge $\operatorname{im}(d_0)$:
   $$\Phi_1 = \|[c]\|_{C^1 / \operatorname{im}(d_0)}$$
2. **Cycle Defect ($\Gamma_2$):** Measures the coboundary defect or holonomy deviation:
   $$\Gamma_2 = \|d_1 c\|_{C^2}$$
3. **Total Residual ($\Xi$):** The composite invariant:
   $$\Xi = \Phi_1 + \Gamma_2$$
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff $\Xi = 0$; admitted to `StabilizedSurvivor` if $\Phi_1 > 0$ is certified non-erasable with $\Gamma_2 = 0$.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 18 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded when $\Phi_1 > 0$ is certified non-erasable with $\Gamma_2 = 0$; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_HODGE_RESIDUAL_NONZERO`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_18",
  "task_data": {
    "level": 18,
    "epoch": "Base Tower",
    "domain": "Differential Topology",
    "carrier_digest": "blake3:b8d4e912"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 10
  },
  "budget": {
    "turn_fuel_remaining": 10,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "target_cochain": [
      1,
      0,
      -1
    ],
    "coboundary_witness": [
      0,
      0
    ],
    "cycle_defect": 0,
    "boundary_defect": 0,
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
  "schema_id": "canonical_paper043_packet_lvl_18",
  "task_data": {
    "level": 18,
    "epoch": "Base Tower",
    "domain": "Differential Topology",
    "carrier_digest": "blake3:b8d4e912"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 10
  },
  "budget": {
    "turn_fuel_remaining": 10,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "target_cochain": [
      1,
      1,
      1
    ],
    "coboundary_witness": [
      1,
      -1
    ],
    "cycle_defect": 2,
    "boundary_defect": 1,
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
REFEREE: REFUSED -> Refusal Code: ERR_HODGE_RESIDUAL_NONZERO, Status: Refused
```

**Worked check (2026-10-20):** The packets do not declare the complex. Assume the filled oriented triangle: edges `0->1`, `1->2`, `2->0` in that order, one face with `d1 = (1, 1, 1)`, and unit weights. This is an assumption, not packet data.

1. Valid packet, `c = (1, 0, -1)`: the cycle sum is `1 + 0 - 1 = 0`. The potential `alpha = (0, 1, 1)` gives `d0 alpha = (a1-a0, a2-a1, a0-a2) = (1, 0, -1) = c`, so `c` is exact, `Phi1 = 0` and `Gamma2 = |d1 c| = 0`. Its Hodge split is `(exact, harmonic, coexact) = (c, 0, 0)`. The packet's `coboundary_witness: [0, 0]` has two entries, while the potential needs one entry per vertex (three), so it is not the witness; `alpha = (0, 1, 1)` is.
2. Negative packet, `c = (1, 1, 1)`: the cycle sum is 3. The potential `alpha = (0, 1, 2)` gives `d0 alpha = (1, 1, -2)` and residual `(0, 0, 3)`, so `Phi1 <= 3`; the dual `y = (1, 1, 1)` balances at every vertex and pairs to 3, so `Phi1 >= 3`. Hence `Phi1 = 3`, and `Gamma2 = |d1 c| = 3`. On the filled triangle the harmonic space is zero and `c = d1^*(1)` is entirely coexact.
3. The packet reports `boundary_defect: 1` and `cycle_defect: 2`. Neither matches the recomputed values `3` and `3` under this assumption, so the refusal is consistent as a refusal of misreported defects. If the face were not declared, `Gamma2 = 0` and `Phi1 = 3 > 0` would meet the `StabilizedSurvivor` criterion of Section 4 instead.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_18",
  "task_data": {
    "level": 18,
    "epoch": "Base Tower",
    "domain": "Differential Topology",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 10
  },
  "budget": {
    "turn_fuel_remaining": 10,
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
   - Formal specification of The Symbol Game Level 18 (Discrete Hodge Decomposition & Harmonic Cochains) within the Differential Topology bounded context.
   - A proposed PFP packet envelope, `CochainResidualModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 18 specifies an exact, deterministic evaluation procedure for candidate proposals over `Combinatorial forms over Q with Hodge Laplacian Δ = dδ + δd`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
