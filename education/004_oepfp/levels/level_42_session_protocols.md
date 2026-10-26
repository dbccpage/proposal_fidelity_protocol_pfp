---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 42: Multiparty Session Types & Duality Choreography"
kind: grammar-reference
level: 42
epoch: "Epoch III"
domain: "Concurrency Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SessionProtocolModule"
evaluator_contract: "SessionTypeChoreographyContract"
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

# The Symbol Game Level 42: Multiparty Session Types & Duality Choreography

**AuthorityEffect:** None.  
**Level:** Level 42 | **Epoch:** Epoch III | **Domain:** Concurrency Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Multiparty session type choreographies G with projected local endpoints and transition duals`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SEND_STATE_DEFECT`  
**Evaluator Module:** `SessionProtocolModule` (`Multiparty Session Type Projection & Transition Duality Evaluator`)  
**Evaluator Contract:** `SessionTypeChoreographyContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SessionProtocolModule` or contract `SessionTypeChoreographyContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 42 establishes the Proposal Fidelity Protocol (PFP) arena for **Multiparty Session Types & Duality Choreography** within the Concurrency Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{42} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Multiparty session type choreographies G with projected local endpoints and transition duals`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SessionProtocolModule` (`SessionTypeChoreographyContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Global choreography projection G ↾ p = S_p, endpoint communication transitions, and deadlock-free session duality.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 42         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `SessionProtocolModule` metrics under `SessionTypeChoreographyContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SEND_STATE_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 42 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_42_session_protocols` family schema:

```json
{
  "schema_id": "sg_packet_level_42_session_protocols",
  "task_data": {
    "level": 42,
    "epoch": "Epoch III",
    "domain": "Concurrency Theory",
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
    "global_choreography": "p -> q: msg_A; q -> r: msg_B; end",
    "participant_roles": ["p", "q", "r"],
    "projected_local_types": {
      "p": "q!msg_A; end",
      "q": "p?msg_A; r!msg_B; end",
      "r": "q?msg_B; end"
    },
    "transition_action": {"role": "p", "action": "send", "target": "q", "message": "msg_A"},
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
pub struct SessionChoreographyPayload {
    pub move_type: MoveType,
    pub global_choreography: String,
    pub participant_roles: Vec<String>,
    pub projected_local_types: BTreeMap<String, String>,
    pub transition_action: SessionAction,
    pub proposer_signature: String,
}

pub struct Level42Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SessionChoreographyPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: SessionProtocolModule

### Contract: `SessionTypeChoreographyContract`

Referees evaluate Level 42 candidates through multiparty session types and choreography projection:

1. **Choreography Projection Parity:** Audits global interaction choreography $G$ projected onto participant endpoints $S_p = G \upharpoonright p$, verifying message compatibility and role completeness.
2. **Communication Transition Order:** Asserts that each communication step matches the local session state (a role in a receive state cannot execute a send, and vice versa).
3. **Deadlock Freedom Verification:** Verifies progress across all participating roles through well-formed dualities and dependency acyclicity.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff local endpoint types strictly project from global choreography $G$ and the proposed transition satisfies local send/receive state order without deadlock.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant recursive session server loop ($\mu t. p?m; q!r; t$) is certified deadlock-free and terminating under licensed session fences, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 42 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SEND_STATE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 42, "carrier_match": true, "move": "ASSERT", "global_choreography": "p -> q: msg_A; end", "transition_action": {"role": "p", "action": "send", "target": "q", "message": "msg_A"}}
REFEREE:  ACCEPT -> Status: ExactRepair (endpoint transition matches projected session type sending state)
  ```

  **Worked check (2026-10-20):** projecting $G = p \to q{:}\ \mathrm{msg\_A};\ \mathrm{end}$ gives $G \upharpoonright p = q!\mathrm{msg\_A};\ \mathrm{end}$ and $G \upharpoonright q = p?\mathrm{msg\_A};\ \mathrm{end}$. The first action of $p$ is therefore a send to $q$ of `msg_A`, which matches the proposed transition. In the negative vector $p$ attempts a receive where its local type requires a send, so the refusal follows. The schema example's three-party projections ($p$: `q!msg_A; end`, $q$: `p?msg_A; r!msg_B; end`, $r$: `q?msg_B; end`) are also the correct projections of its choreography.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 42, "carrier_match": true, "move": "ASSERT", "global_choreography": "p -> q: msg_A; end", "transition_action": {"role": "p", "action": "recv", "from": "q", "message": "msg_A"}}
REFEREE:  REFUSED -> Refusal Code: ERR_SEND_STATE_DEFECT, Status: Refused (role p attempted receive action but local session state requires send)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 42, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 42: Multiparty Session Types & Duality Choreography within the Concurrency Theory bounded context.
   - A proposed PFP packet envelope, `SessionProtocolModule` (`SessionTypeChoreographyContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 42 specifies an exact, deterministic evaluation procedure for candidate proposals over `Multiparty session type choreographies G with projected local endpoints and transition duals`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
