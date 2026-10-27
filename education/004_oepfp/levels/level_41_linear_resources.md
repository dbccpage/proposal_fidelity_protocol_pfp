---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 41: Girard Linear Logic & Resource Token Accounting"
kind: grammar-reference
level: 41
epoch: "Epoch III"
domain: "Proof Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "LinearLogicModule"
evaluator_contract: "LinearResourceAccountingContract"
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

# The Symbol Game Level 41: Girard Linear Logic & Resource Token Accounting

**AuthorityEffect:** None.  
**Level:** Level 41 | **Epoch:** Epoch III | **Domain:** Proof Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Linear logic propositions with resource operators ⊗, ⅋ and exact linear token consumption`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_RESOURCE_TOKEN_DEFECT`  
**Evaluator Module:** `LinearLogicModule` (`Girard Linear Logic Token Accounting Evaluator`)  
**Evaluator Contract:** `LinearResourceAccountingContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `LinearLogicModule` or contract `LinearResourceAccountingContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 41 establishes the Proposal Fidelity Protocol (PFP) arena for **Girard Linear Logic & Resource Token Accounting** within the Proof Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{41} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Linear logic propositions with resource operators ⊗, ⅋ and exact linear token consumption`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `LinearLogicModule` (`LinearResourceAccountingContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Strict no-cloning and no-erasure token accounting preventing duplicate spending of computational resources.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 41         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `LinearLogicModule` metrics under `LinearResourceAccountingContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_RESOURCE_TOKEN_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 41 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_41_linear_resources` family schema:

```json
{
  "schema_id": "sg_packet_level_41_linear_resources",
  "task_data": {
    "level": 41,
    "epoch": "Epoch III",
    "domain": "Proof Theory",
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
    "linear_context_gamma": ["token_A", "token_B"],
    "consumed_tokens_delta": ["token_A", "token_B"],
    "produced_tokens_sigma": ["token_C"],
    "consumption_balance_zero": true,
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
pub struct LinearResourcePayload {
    pub move_type: MoveType,
    pub linear_context_gamma: Vec<String>,
    pub consumed_tokens_delta: Vec<String>,
    pub produced_tokens_sigma: Vec<String>,
    pub consumption_balance_zero: bool,
    pub proposer_signature: String,
}

pub struct Level41Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: LinearResourcePayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: LinearLogicModule

### Contract: `LinearResourceAccountingContract`

Referees evaluate Level 41 candidates through Girard linear logic resource accounting:

1. **Strict Linear Resource Accounting:** Scoped strictly to ordinary linear resources; every non-exponential resource token must be consumed exactly once without duplication (no contraction) and without unconsumed discard (no weakening).
2. **Explicit Modality Governance:** Controlled structural rules are permitted only for propositions explicitly marked under modal exponentials ($!A$ for reusable supplies, $?B$ for consuming contexts); unmarked tokens are strictly affine-forbidden.
3. **Multiset Token Conservation:** Audits the multiset equation $\Gamma = \Delta$ where $\Delta$ is the exact multiset of tokens consumed by the inference step.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the multiset difference $\Gamma \setminus \Delta = \emptyset$ and every linear resource token is consumed without duplication or abandonment.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant reusable resource token certified under modal exponential $!A$ is admitted as an unbounded persistent capability, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 41 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_RESOURCE_TOKEN_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 41, "carrier_match": true, "move": "ASSERT", "linear_context_gamma": ["token_A", "token_B"], "consumed_tokens_delta": ["token_A", "token_B"], "produced_tokens_sigma": ["token_C"]}
REFEREE:  ACCEPT -> Status: ExactRepair (linear context consumed exactly once with zero balance deficit)
  ```

  **Worked check (2026-10-20):** as multisets, $\Gamma = \{\mathrm{token\_A}, \mathrm{token\_B}\}$ and $\Delta = \{\mathrm{token\_A}, \mathrm{token\_B}\}$, so $\Gamma \setminus \Delta = \emptyset$ and $\Delta \setminus \Gamma = \emptyset$: each token is used once. In the negative vector $\Delta = \{\mathrm{token\_A}^2\}$ exceeds $\Gamma = \{\mathrm{token\_A}\}$ by one copy, which is contraction on an unmarked token, so the refusal follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 41, "carrier_match": true, "move": "ASSERT", "linear_context_gamma": ["token_A"], "consumed_tokens_delta": ["token_A", "token_A"]}
REFEREE:  REFUSED -> Refusal Code: ERR_RESOURCE_TOKEN_DEFECT, Status: Refused (duplicate consumption of linear token_A violates no-cloning invariant)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 41, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 41: Girard Linear Logic & Resource Token Accounting within the Proof Theory bounded context.
   - A proposed PFP packet envelope, `LinearLogicModule` (`LinearResourceAccountingContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 41 specifies an exact, deterministic evaluation procedure for candidate proposals over `Linear logic propositions with resource operators ⊗, ⅋ and exact linear token consumption`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
