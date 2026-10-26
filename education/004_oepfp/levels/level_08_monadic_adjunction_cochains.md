---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 08: Adjoint Monads & 16-Family Packet Catalog"
kind: grammar-reference
level: 8
epoch: "Base Tower"
domain: "Categorical Protocols"
game_edition: "v2 Packet Iteration"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "AdjunctionModule"
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

# The Symbol Game Level 08: Adjoint Monads & 16-Family Packet Catalog

**AuthorityEffect:** None.  
**Level:** Level 08 | **Epoch:** Base Tower | **Domain:** Categorical Protocols  
**Game Edition:** `v2 Packet Iteration`  
**Board Carrier:** `Categorical adjunction F ⊣ U with 16 frozen packet family schemas`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY, RETRACT`  
**Primary Domain Error Code:** `ERR_TRIANGLE_IDENTITY_VIOLATION`  
**Evaluator Module:** `AdjunctionModule` (`Categorical Adjunction & Packet Schema Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `AdjunctionModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 08 establishes the Proposal Fidelity Protocol (PFP) arena for **Adjoint Monads & 16-Family Packet Catalog** within the Categorical Protocols bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{08} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Categorical adjunction F ⊣ U with 16 frozen packet family schemas`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `AdjunctionModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Concentric zone-fenced packet envelopes with unit η: Id → UF and counit ε: FU → Id verifying triangle identities and packet family schemas.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 08         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY, RETRACT`), calculates `AdjunctionModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_TRIANGLE_IDENTITY_VIOLATION`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 08 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_08` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_08",
  "task_data": {
    "level": 8,
    "epoch": "Base Tower",
    "domain": "Categorical Protocols",
    "carrier_digest": "blake3:b8d4e908"
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
    "functor_pair": [
      "F_free",
      "U_forget"
    ],
    "unit_eta": "id_to_UF",
    "counit_epsilon": "FU_to_id",
    "naturality_witness": "eta_natural_and_epsilon_natural",
    "triangle_identities_hold": true,
    "packet_family_id": 8,
    "schema_conformance": "canonical_paper043_packet_lvl_08",
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
pub struct Level08Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: AdjunctionSchemaPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: AdjunctionModule

Referees evaluate Level 08 candidates through categorical adjunctions $F \dashv U$ and the 16-family packet catalog:

1. **Functor Pair & Units:** Evaluates candidate left adjoint $F: \mathcal{C} \to \mathcal{D}$ and right adjoint $U: \mathcal{D} \to \mathcal{C}$ with unit natural transformation $\eta: \mathrm{Id}_{\mathcal{C}} \to UF$ and counit $\varepsilon: FU \to \mathrm{Id}_{\mathcal{D}}$.
2. **Triangle Identities (Zig-zag Equations):** Evaluates the strict commutativity of the two triangle diagrams:
   $$U\varepsilon \circ \eta U = \mathrm{id}_U, \qquad \varepsilon F \circ F\eta = \mathrm{id}_F$$
   Failure of either identity triggers `ERR_TRIANGLE_IDENTITY_VIOLATION`.
3. **16-Family Schema Conformance:** Validates the proposal envelope against the declared concentric zone-fenced packet family schema.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff the adjunction triangle identities hold and the packet family schema is verified.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 08 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_TRIANGLE_IDENTITY_VIOLATION`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_08",
  "task_data": {
    "level": 8,
    "epoch": "Base Tower",
    "domain": "Categorical Protocols",
    "carrier_digest": "blake3:b8d4e908"
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
    "objects": [
      "*"
    ],
    "morphisms": [
      "e",
      "s"
    ],
    "functor_F": "id",
    "functor_U": "id",
    "unit_eta": {
      "*": "e"
    },
    "counit_epsilon": {
      "*": "e"
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
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved; eps*eta=e=id)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_08",
  "task_data": {
    "level": 8,
    "epoch": "Base Tower",
    "domain": "Categorical Protocols",
    "carrier_digest": "blake3:b8d4e908"
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
    "objects": [
      "*"
    ],
    "morphisms": [
      "e",
      "s"
    ],
    "functor_F": "id",
    "functor_U": "id",
    "unit_eta": {
      "*": "e"
    },
    "counit_epsilon": {
      "*": "s"
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
REFEREE: REFUSED -> Refusal Code: ERR_ADJUNCTION_TRIANGLE_VIOLATION, Status: Refused (eps*eta=s != id)
```

**Worked check (2026-10-20):** The category has one object `*` and two endomorphisms `e` (the identity) and `s`. With `F = U = id`, the triangle identities reduce to `epsilon_* o eta_* = id_*`.

1. Valid packet: `eta_* = e` and `epsilon_* = e`, so `e o e = e = id`. Both identities hold.
2. Negative packet: `epsilon_* = s`, so `s o e = s`, which is not `id` because `s != e`. The identity fails whatever the product `s o s` is, so the refusal does not depend on the omitted composition table. A component of a natural transformation `id => id` on a one-object category must commute with every morphism; `s` commutes with `e` and with itself, so `epsilon = s` is natural and the only failure is the triangle identity.

**Consistency gap (2026-10-20):** The header and Section 4 name the error `ERR_TRIANGLE_IDENTITY_VIOLATION`, but this vector emits `ERR_ADJUNCTION_TRIANGLE_VIOLATION`. One of the two labels needs to be chosen; this note does not rename either.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_08",
  "task_data": {
    "level": 8,
    "epoch": "Base Tower",
    "domain": "Categorical Protocols",
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
   - Formal specification of The Symbol Game Level 08 (Adjoint Monads & 16-Family Packet Catalog) within the Categorical Protocols bounded context.
   - A proposed PFP packet envelope, `AdjunctionModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 08 specifies an exact, deterministic evaluation procedure for candidate proposals over `Categorical adjunction F ⊣ U with 16 frozen packet family schemas`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
