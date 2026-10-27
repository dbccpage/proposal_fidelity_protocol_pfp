---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 13: Alternation Ladders & Bounded Non-Universal Execution"
kind: grammar-reference
level: 13
epoch: "Base Tower"
domain: "Computational Complexity"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "BoundedLadderModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
source_paths:
  - education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 13: Alternation Ladders & Bounded Non-Universal Execution

**AuthorityEffect:** None.  
**Level:** Level 13 | **Epoch:** Base Tower | **Domain:** Computational Complexity  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Stratified quantifier alternation ladders (Σ_k, Π_k) with expansion cycle detection`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_CYCLE_DETECTED`  
**Evaluator Module:** `BoundedLadderModule` (`Quantifier Alternation Ladder & Fuel Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `BoundedLadderModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 13 establishes the Proposal Fidelity Protocol (PFP) arena for **Alternation Ladders & Bounded Non-Universal Execution** within the Computational Complexity bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{13} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Stratified quantifier alternation ladders (Σ_k, Π_k) with expansion cycle detection`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `BoundedLadderModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Bounded non-universal execution model strictly bounded by a declared finite fuel budget with cycle detection; no claim of Turing completeness.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 13         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `BoundedLadderModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_CYCLE_DETECTED`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 13 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_13` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_13",
  "task_data": {
    "level": 13,
    "epoch": "Base Tower",
    "domain": "Computational Complexity",
    "carrier_digest": "blake3:b8d4e90d"
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
    "alternation_depth": 2,
    "expansion_path": [
      "sigma_1",
      "pi_1"
    ],
    "fuel_consumed": 4,
    "cycle_free": true,
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
pub struct Level13Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: AlternationLadderPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: BoundedLadderModule

Referees evaluate Level 13 candidates through quantifier alternation ladders and finite-fuel execution bounds:

1. **Hierarchy Depth:** Evaluates alternation depth across $(\Sigma_k, \Pi_k)$ strata.
2. **Cycle Interception:** Intercepts repeating state configurations on expansion trajectories.
3. **Fuel Boundedness:** Enforces a bounded non-universal execution model strictly halted by the declared fuel budget ($T \le 8$); no claim of Turing completeness is asserted.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff the expansion trajectory halts without cycle defects within the fuel quota.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 13 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_CYCLE_DETECTED`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_13",
  "task_data": {
    "level": 13,
    "epoch": "Base Tower",
    "domain": "Computational Complexity",
    "carrier_digest": "blake3:b8d4e90d"
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
    "alternation_depth": 2,
    "expansion_path": [
      "sigma_1",
      "pi_1"
    ],
    "fuel_consumed": 4,
    "cycle_free": true,
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
  "schema_id": "canonical_paper043_packet_lvl_13",
  "task_data": {
    "level": 13,
    "epoch": "Base Tower",
    "domain": "Computational Complexity",
    "carrier_digest": "blake3:b8d4e90d"
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
    "alternation_depth": 4,
    "expansion_path": [
      "sigma_1",
      "pi_1",
      "sigma_1",
      "pi_1",
      "sigma_1"
    ],
    "fuel_consumed": 9,
    "cycle_free": false,
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
REFEREE: REFUSED -> Refusal Code: ERR_CYCLE_DETECTED, Status: Refused
```

**Worked check (2026-10-20):** The fuel ceiling is `T <= 8`. The valid packet uses 4 units of fuel and the path `sigma_1, pi_1` repeats no label, so it halts within budget without a repeated configuration. The negative packet repeats the pair `sigma_1, pi_1` (the label `sigma_1` occurs at positions 1, 3 and 5), which is the repeated configuration that `ERR_CYCLE_DETECTED` names. It also reports `fuel_consumed: 9 > 8`, a second, independent violation, so this vector does not isolate the cycle check from the fuel check. The packets carry labels only; whether a repeated label means a repeated machine state is an assumption of this reading. The reported `alternation_depth: 4` for a five-entry path matches four alternations between adjacent strata.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_13",
  "task_data": {
    "level": 13,
    "epoch": "Base Tower",
    "domain": "Computational Complexity",
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
   - Formal specification of The Symbol Game Level 13 (Alternation Ladders & Bounded Non-Universal Execution) within the Computational Complexity bounded context.
   - A proposed PFP packet envelope, `BoundedLadderModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 13 specifies an exact, deterministic evaluation procedure for candidate proposals over `Stratified quantifier alternation ladders (Σ_k, Π_k) with expansion cycle detection`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
