---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 46: Total Self-Hosting & Kleene Fixed-Point Fences"
kind: grammar-reference
level: 46
epoch: "Epoch III"
domain: "Metamathematics"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "AutopoieticLoopModule"
evaluator_contract: "SelfHostingTerminationContract"
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

# The Symbol Game Level 46: Total Self-Hosting & Kleene Fixed-Point Fences

**AuthorityEffect:** None.  
**Level:** Level 46 | **Epoch:** Epoch III | **Domain:** Metamathematics  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Self-evaluating step functions with bounded well-founded ranking and Kleene fixed-point fences`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY, RETRACT`  
**Primary Domain Error Code:** `ERR_SELF_DESCRIPTION_DEFECT`  
**Evaluator Module:** `AutopoieticLoopModule` (`Self-Hosting Meta-Circular Interpreter & Termination Evaluator`)  
**Evaluator Contract:** `SelfHostingTerminationContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `AutopoieticLoopModule` or contract `SelfHostingTerminationContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 46 establishes the Proposal Fidelity Protocol (PFP) arena for **Total Self-Hosting & Kleene Fixed-Point Fences** within the Metamathematics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{46} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Self-evaluating step functions with bounded well-founded ranking and Kleene fixed-point fences`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `AutopoieticLoopModule` (`SelfHostingTerminationContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Evaluation of finite step-indexed structural descent in self-evaluating interpreters behind termination fences.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 46         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY, RETRACT`), calculates `AutopoieticLoopModule` metrics under `SelfHostingTerminationContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SELF_DESCRIPTION_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 46 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_46_self_host_and_termination` family schema:

```json
{
  "schema_id": "sg_packet_level_46_self_host_and_termination",
  "task_data": {
    "level": 46,
    "epoch": "Epoch III",
    "domain": "Metamathematics",
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
    "interpreter_state_digest": "blake3:4a5b6c...",
    "parent_state_digest": "blake3:1d2e3f...",
    "measure_before": 10,
    "measure_after": 9,
    "step_evaluation_witness": "meta_step_reduced",
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
pub struct SelfHostingTerminationPayload {
    pub move_type: MoveType,
    pub interpreter_state_digest: String,
    pub parent_state_digest: String,
    pub measure_before: u64,
    pub measure_after: u64,
    pub step_evaluation_witness: String,
    pub proposer_signature: String,
}

pub struct Level46Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SelfHostingTerminationPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: AutopoieticLoopModule

### Contract: `SelfHostingTerminationContract`

Referees evaluate Level 46 candidates through self-hosting interpreter step mechanics:

1. **Self-Evaluating Interpreter State Tracking:** Tracks meta-circular interpreter states via cryptographic digests (`parent_state_digest`, `interpreter_state_digest`).
2. **Well-Founded Size Descent:** Evaluates structural complexity measure $\mu(s)$, enforcing strict reduction on each recursive evaluation step:
   $$\mu(s_{i+1}) < \mu(s_i)$$
3. **Explicit Scope Discipline:** This stage verifies finite structural descent for bounded interpreters; it does not solve the general Turing halting problem or claim totality of Kleene fixed points in general.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the evaluation step demonstrates strict structural size descent $\mu(s_{i+1}) < \mu(s_i)$ with non-cyclic state digests.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant self-interpreter fixed-point configuration is certified stable under an explicit fuel fence, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 46 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SELF_DESCRIPTION_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 46, "carrier_match": true, "move": "ASSERT", "parent_state_digest": "blake3:1d2e...", "interpreter_state_digest": "blake3:4a5b...", "measure_before": 10, "measure_after": 9}
REFEREE:  ACCEPT -> Status: ExactRepair (meta-circular interpreter step exhibits strict structural ranking descent 10 -> 9)
  ```

  **Worked check (2026-10-20):** $\mu$ falls from 10 to 9, so $\mu(s_{i+1}) < \mu(s_i)$ holds for this step; the two digests differ, so no state repeat is visible. Because $\mu$ takes values in $\mathbb{N}$, at most 9 further strictly descending steps can follow from $\mu = 9$. In the negative vector $\mu$ stays at 10 and the digests are equal, so both checks fail.

  **Reproducibility gap (2026-10-20):** the digests are truncated placeholders (`blake3:1d2e...`) and the packet does not define $\mu$, so neither the state comparison nor the measure can be recomputed.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 46, "carrier_match": true, "move": "ASSERT", "parent_state_digest": "blake3:1d2e...", "interpreter_state_digest": "blake3:1d2e...", "measure_before": 10, "measure_after": 10}
REFEREE:  REFUSED -> Refusal Code: ERR_SELF_DESCRIPTION_DEFECT, Status: Refused (interpreter state digest cycle and failure of well-founded measure descent)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 46, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 46: Total Self-Hosting & Kleene Fixed-Point Fences within the Metamathematics bounded context.
   - A proposed PFP packet envelope, `AutopoieticLoopModule` (`SelfHostingTerminationContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 46 specifies an exact, deterministic evaluation procedure for candidate proposals over `Self-evaluating step functions with bounded well-founded ranking and Kleene fixed-point fences`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
