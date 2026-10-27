---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 43: Effect Rows & Scoped Capability Tokens"
kind: grammar-reference
level: 43
epoch: "Epoch III"
domain: "Type Systems"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "EffectSystemModule"
evaluator_contract: "ScopedCapabilityRowContract"
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

# The Symbol Game Level 43: Effect Rows & Scoped Capability Tokens

**AuthorityEffect:** None.  
**Level:** Level 43 | **Epoch:** Epoch III | **Domain:** Type Systems  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Typed computation terms with row-polymorphic effect rows and capability authorization tokens`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_EFFECT_ROW_DEFECT`  
**Evaluator Module:** `EffectSystemModule` (`Row-Polymorphic Effect & Capability Authorization Evaluator`)  
**Evaluator Contract:** `ScopedCapabilityRowContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `EffectSystemModule` or contract `ScopedCapabilityRowContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 43 establishes the Proposal Fidelity Protocol (PFP) arena for **Effect Rows & Scoped Capability Tokens** within the Type Systems bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{43} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Typed computation terms with row-polymorphic effect rows and capability authorization tokens`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `EffectSystemModule` (`ScopedCapabilityRowContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Row-polymorphic effect rows ⟨e₁,...,e_k | ρ⟩, capability token scoping, and handler authorization fences.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 43         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `EffectSystemModule` metrics under `ScopedCapabilityRowContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_EFFECT_ROW_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 43 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_43_effect_and_capability` family schema:

```json
{
  "schema_id": "sg_packet_level_43_effect_and_capability",
  "task_data": {
    "level": 43,
    "epoch": "Epoch III",
    "domain": "Type Systems",
    "carrier_digest": "blake3:b8d4e9..."
  },
  "protected_boundary": {
    "immutable_slots": ["carrier", "fuel_ceiling", "zero_relation_fences"],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "invoked_effect": "State.get",
    "ambient_effect_row": ["State.get", "State.put"],
    "granted_capability_tokens": ["cap_state_access"],
    "row_inclusion_witness": "effect_in_ambient_row",
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
pub struct ScopedCapabilityPayload {
    pub move_type: MoveType,
    pub invoked_effect: String,
    pub ambient_effect_row: Vec<String>,
    pub granted_capability_tokens: Vec<String>,
    pub row_inclusion_witness: String,
    pub proposer_signature: String,
}

pub struct Level43Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: ScopedCapabilityPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: EffectSystemModule

### Contract: `ScopedCapabilityRowContract`

Referees evaluate Level 43 candidates through row-polymorphic effect typing and capability authorization:

1. **Effect Row Inclusion:** For candidate term invoking effect $\epsilon$, evaluates inclusion within declared ambient row $\mathcal{E} = \langle \epsilon_1, \ldots, \epsilon_k \mid \rho \rangle$:
   $$\epsilon \in \mathcal{E}$$
2. **Capability Token Scoping:** Verifies that dangerous or external effects (such as IO, Network, or Mutation) are authorized by a matching active capability key $\kappa \in \mathcal{K}$.
3. **Handler Boundary Encapsulation:** Evaluates effect handling blocks, certifying that handled effects are removed from the outer computation effect row.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff every invoked effect is enclosed in the declared effect row and authorized by active capability tokens.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an unhandled ambient effect in an open capability context is certified safe behind an authorized runtime sandbox fence, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 43 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_EFFECT_ROW_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 43, "carrier_match": true, "move": "ASSERT", "invoked_effect": "State.get", "ambient_effect_row": ["State.get", "State.put"], "granted_capability_tokens": ["cap_state"]}
REFEREE:  ACCEPT -> Status: ExactRepair (invoked effect is enclosed in ambient effect row and authorized by capability token)
  ```

  **Worked check (2026-10-20):** `State.get` is a member of the ambient row `[State.get, State.put]`, so row inclusion holds. In the negative vector `IO.launch_missile` is not a member of that row, so the refusal follows from row inclusion alone.

  **Reproducibility gap (2026-10-20):** no packet declares which capability token each effect requires. The valid vector grants `cap_state` and the schema example grants `cap_state_access`; without an effect-to-token table the capability half of the `ExactRepair` criterion cannot be checked.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 43, "carrier_match": true, "move": "ASSERT", "invoked_effect": "IO.launch_missile", "ambient_effect_row": ["State.get", "State.put"], "granted_capability_tokens": ["cap_state"]}
REFEREE:  REFUSED -> Refusal Code: ERR_EFFECT_ROW_DEFECT, Status: Refused (invoked effect IO.launch_missile is absent from ambient effect row and ungranted by tokens)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 43, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 43: Effect Rows & Scoped Capability Tokens within the Type Systems bounded context.
   - A proposed PFP packet envelope, `EffectSystemModule` (`ScopedCapabilityRowContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 43 specifies an exact, deterministic evaluation procedure for candidate proposals over `Typed computation terms with row-polymorphic effect rows and capability authorization tokens`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
