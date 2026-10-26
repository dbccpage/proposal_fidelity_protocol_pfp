---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 09: Dagger Monads & Reflection Duality"
kind: grammar-reference
level: 9
epoch: "Base Tower"
domain: "Involution Categories"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "InvolutionModule"
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

# The Symbol Game Level 09: Dagger Monads & Reflection Duality

**AuthorityEffect:** None.  
**Level:** Level 09 | **Epoch:** Base Tower | **Domain:** Involution Categories  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Involutive dagger category C† with profunctor reversal`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY, RETRACT`  
**Primary Domain Error Code:** `ERR_DAGGER_ASYMMETRY`  
**Evaluator Module:** `InvolutionModule` (`Dagger Category Involution Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `InvolutionModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 09 establishes the Proposal Fidelity Protocol (PFP) arena for **Dagger Monads & Reflection Duality** within the Involution Categories bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{09} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Involutive dagger category C† with profunctor reversal`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `InvolutionModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Adjoint involution f†† = f demonstrating the emergence of reflection symmetry on symmetric subcarriers.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 09         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY, RETRACT`), calculates `InvolutionModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_DAGGER_ASYMMETRY`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 09 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_09` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_09",
  "task_data": {
    "level": 9,
    "epoch": "Base Tower",
    "domain": "Involution Categories",
    "carrier_digest": "blake3:b8d4e909"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "morphism_id": "f_1",
    "dagger_morphism": "f_1_dagger",
    "involution_identity_holds": true,
    "contravariant_composition_holds": true,
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
pub struct Level09Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: DaggerInvolutionPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: InvolutionModule

Referees evaluate Level 09 candidates through involutive dagger functor mechanics:

1. **Involution Identity:** Verifies $f^{\dagger\dagger} = f$ for all candidate morphisms.
2. **Contravariant Composition:** Verifies $(g \circ f)^\dagger = f^\dagger \circ g^\dagger$.
3. **Reflection Symmetry:** Audits the emergence of reflection symmetry on symmetric subcarriers.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff dagger involution identities are satisfied.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 09 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_DAGGER_ASYMMETRY`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_09",
  "task_data": {
    "level": 9,
    "epoch": "Base Tower",
    "domain": "Involution Categories",
    "carrier_digest": "blake3:b8d4e909"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "category": "C3_one_object",
    "morphisms": [
      0,
      1,
      2
    ],
    "dagger_map": [
      0,
      2,
      1
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
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved; involution holds on all morphisms)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_09",
  "task_data": {
    "level": 9,
    "epoch": "Base Tower",
    "domain": "Involution Categories",
    "carrier_digest": "blake3:b8d4e909"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "category": "C3_one_object",
    "morphisms": [
      0,
      1,
      2
    ],
    "dagger_map": [
      0,
      2,
      2
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
REFEREE: REFUSED -> Refusal Code: ERR_DAGGER_INVOLUTION_FAILURE, Status: Refused ((1^dagger)^dagger = 2 != 1)
```

**Worked check (2026-10-20):** Read `C3_one_object` as the cyclic group `Z/3` with morphisms `0, 1, 2` and composition `a o b = a + b mod 3`. This reading is an assumption; the packet names the category but not its composition.

1. Valid packet: `dagger = [0, 2, 1]` sends `k` to `-k mod 3`. Then `dagger(dagger(k)) = k` for `k = 0, 1, 2`, and `(a + b)^dagger = -(a + b) = (-b) + (-a) = b^dagger o a^dagger` for all nine pairs, so the map is a contravariant involution. Here `f^dagger o f = 0`, the identity, so this dagger is the group inverse.
2. Negative packet: `dagger = [0, 2, 2]` gives `dagger(dagger(1)) = dagger(2) = 2 != 1`, as the refusal states.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_09",
  "task_data": {
    "level": 9,
    "epoch": "Base Tower",
    "domain": "Involution Categories",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
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
   - Formal specification of The Symbol Game Level 09 (Dagger Monads & Reflection Duality) within the Involution Categories bounded context.
   - A proposed PFP packet envelope, `InvolutionModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 09 specifies an exact, deterministic evaluation procedure for candidate proposals over `Involutive dagger category C† with profunctor reversal`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
