---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 16: Filtered Ind-Objects & Colimit Isolation"
kind: grammar-reference
level: 16
epoch: "Base Tower"
domain: "Category Theory"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "CategoryLimitsModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
  - LiftLicenseNeeded
source_paths:
  - omega_engine_education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 16: Filtered Ind-Objects & Colimit Isolation

**AuthorityEffect:** None.  
**Level:** Level 16 | **Epoch:** Base Tower | **Domain:** Category Theory  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Ind-completion Ind(C) over directed systems of finite presentations`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_COLIMIT_INCOHERENCE`  
**Evaluator Module:** `CategoryLimitsModule` (`Higher Category & Limit Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CategoryLimitsModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 16 establishes the Proposal Fidelity Protocol (PFP) arena for **Filtered Ind-Objects & Colimit Isolation** within the Category Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{16} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Ind-completion Ind(C) over directed systems of finite presentations`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CategoryLimitsModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Treating infinite systems strictly as filtered colimits of finite carrier presentations without continuum leaps.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 16         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `CategoryLimitsModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_COLIMIT_INCOHERENCE`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 16 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_16` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_16",
  "task_data": {
    "level": 16,
    "epoch": "Base Tower",
    "domain": "Category Theory",
    "carrier_digest": "blake3:b8d4e910"
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
    "diagram_morphism": "alpha",
    "cone_witness": "lim_F",
    "factorization_unique": true,
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
pub struct Level16Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: CategoryLimitPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: CategoryLimitsModule

Referees evaluate candidates through categorical limits, sheaves, and higher coherence structures:

1. **Diagram Commutativity:** Audits naturality and commutativity of declared diagram cells.
2. **Universal Property:** Verifies unique factorization through limiting or colimiting objects.
3. **Coherence Relations:** Verifies Stasheff associahedra, pentagon relations, or descent matching families.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff categorical coherence and factorization relations hold.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 16 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | **Reachable.** Reachable upon certified same-level exhaustion when CEC preconditions qualify for inter-stage ascent. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_COLIMIT_INCOHERENCE`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_16",
  "task_data": {
    "level": 16,
    "epoch": "Base Tower",
    "domain": "Category Theory",
    "carrier_digest": "blake3:b8d4e910"
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
    "diagram_morphism": "alpha",
    "cone_witness": "lim_F",
    "factorization_unique": true,
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
  "schema_id": "canonical_paper043_packet_lvl_16",
  "task_data": {
    "level": 16,
    "epoch": "Base Tower",
    "domain": "Category Theory",
    "carrier_digest": "blake3:b8d4e910"
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
    "diagram_morphism": "alpha",
    "cone_witness": null,
    "factorization_unique": false,
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
REFEREE: REFUSED -> Refusal Code: ERR_COLIMIT_INCOHERENCE, Status: Refused
```

**Reproducibility gap (2026-10-20):** The packets name a morphism `alpha` and a witness `lim_F` but give no diagram, objects or maps, so unique factorization cannot be checked. The carrier is an ind-completion, whose objects are filtered colimits; the witness for a colimit is a cocone under the diagram, not a cone over it, so the name `lim_F` (a limit) does not match the carrier. A complete vector needs a finite directed diagram, a cocone and a test cocone with its mediating map.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_16",
  "task_data": {
    "level": 16,
    "epoch": "Base Tower",
    "domain": "Category Theory",
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
   - Formal specification of The Symbol Game Level 16 (Filtered Ind-Objects & Colimit Isolation) within the Category Theory bounded context.
   - A proposed PFP packet envelope, `CategoryLimitsModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 16 specifies an exact, deterministic evaluation procedure for candidate proposals over `Ind-completion Ind(C) over directed systems of finite presentations`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
