---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 04: Simplex Graph Expansions & Presheaf Topoi"
kind: grammar-reference
level: 4
epoch: "Base Tower"
domain: "Category Theory"
game_edition: "v2 Packet Iteration / v3"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "PresheafModule"
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

# The Symbol Game Level 04: Simplex Graph Expansions & Presheaf Topoi

**AuthorityEffect:** None.  
**Level:** Level 04 | **Epoch:** Base Tower | **Domain:** Category Theory  
**Game Edition:** `v2 Packet Iteration / v3`  
**Board Carrier:** `Finite simplicial set presheaves Hom(Δ*, X) over context category C`  
**Fuel Budget:** `6 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_CONTEXT_INCONGRUENT`  
**Evaluator Module:** `PresheafModule` (`Presheaf Functoriality & Context Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `PresheafModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 04 establishes the Proposal Fidelity Protocol (PFP) arena for **Simplex Graph Expansions & Presheaf Topoi** within the Category Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{04} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Finite simplicial set presheaves Hom(Δ*, X) over context category C`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `PresheafModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 6$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Presheaf representation demonstrating that syntactic quotient congruence fails to preserve relational observation equivalence.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 04         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `PresheafModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **6 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_CONTEXT_INCONGRUENT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 04 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_04` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_04",
  "task_data": {
    "level": 4,
    "epoch": "Base Tower",
    "domain": "Category Theory",
    "carrier_digest": "blake3:b8d4e904"
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
    "context_morphism": "f_12",
    "presheaf_map": "Hom(Delta, X)",
    "congruence_preserved": true,
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
pub struct Level04Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: PresheafPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: PresheafModule

Referees evaluate Level 04 candidates through presheaf topoi and contextual observation metrics:

1. **Presheaf Functoriality:** Evaluates contravariant functor properties $X(g \circ f) = X(f) \circ X(g)$.
2. **Noncongruence Audit:** Verifies that syntactic quotient congruence does not collapse distinct semantic observations.
3. **Context Restriction:** Evaluates local section restrictions across context categories.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff presheaf mappings preserve declared functorial boundaries.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 04 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_CONTEXT_INCONGRUENT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_04",
  "task_data": {
    "level": 4,
    "epoch": "Base Tower",
    "domain": "Category Theory",
    "carrier_digest": "blake3:b8d4e904"
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
    "category_objects": [
      "A",
      "B",
      "C"
    ],
    "restriction_maps": {
      "f": [
        0,
        1
      ],
      "g": [
        1,
        0
      ],
      "h": [
        1,
        0
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
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_04",
  "task_data": {
    "level": 4,
    "epoch": "Base Tower",
    "domain": "Category Theory",
    "carrier_digest": "blake3:b8d4e904"
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
    "category_objects": [
      "A",
      "B",
      "C"
    ],
    "restriction_maps": {
      "f": [
        0,
        1
      ],
      "g": [
        1,
        0
      ],
      "h": [
        0,
        1
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
REFEREE: REFUSED -> Refusal Code: ERR_PRESHEAF_COMPOSITION_MISMATCH, Status: Refused
```

**Worked check (2026-10-20):** The packets do not state which morphism is a composite or what the source and target of `f`, `g` and `h` are. Assume, as the dispositions suggest, that each restriction map is a function table on a two-element set `{0, 1}` and that `h = g o f` in the context category. This is an assumption, not packet data.

1. `f = [0, 1]` is the identity and `g = [1, 0]` is the swap.
2. Contravariance requires `X(h) = X(g o f) = X(f) o X(g)`. With `f` the identity, `X(f) o X(g) = X(g) = [1, 0]`.
3. The valid packet has `h = [1, 0]`, which matches. The negative packet has `h = [0, 1]`, the identity, which differs from `[1, 0]` at both points, so `ERR_PRESHEAF_COMPOSITION_MISMATCH` is consistent.

**Reproducibility gap (2026-10-20):** A complete vector needs the morphisms with sources and targets, the composition law (here `h = g o f`) and the set assigned to each object.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_04",
  "task_data": {
    "level": 4,
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
   - Formal specification of The Symbol Game Level 04 (Simplex Graph Expansions & Presheaf Topoi) within the Category Theory bounded context.
   - A proposed PFP packet envelope, `PresheafModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 04 specifies an exact, deterministic evaluation procedure for candidate proposals over `Finite simplicial set presheaves Hom(Δ*, X) over context category C`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
