---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 84: LLM Tool Call Schemas & JSON-Schema Isolation"
kind: grammar-reference
level: 84
epoch: "Epoch VIII"
domain: "Agentic Systems"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "ToolExecutionContract"
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

# The Symbol Game Level 84: LLM Tool Call Schemas & JSON-Schema Isolation

**AuthorityEffect:** None.  
**Level:** Level 84 | **Epoch:** Epoch VIII | **Domain:** Agentic Systems  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Content-addressed JSON-Schema definitions, typed tool invocations, and execution receipts`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_TOOL_SCHEMA_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`ToolExecutionContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `ToolExecutionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 84 establishes the Proposal Fidelity Protocol (PFP) arena for **LLM Tool Call Schemas & JSON-Schema Isolation** within the Agentic Systems bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{84} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Content-addressed JSON-Schema definitions, typed tool invocations, and execution receipts`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `ToolExecutionContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Enforcing strict JSON-Schema boundary isolation, preventing command injection, and binding execution receipts.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 84        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `ToolExecutionContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_TOOL_SCHEMA_DEFECT`) are emitted exclusively by `ToolExecutionContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 84 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_84` schema:

```json
{
  "schema_id": "sg_packet_level_84_agentic_systems",
  "task_data": {
    "level": 84,
    "epoch": "Epoch VIII",
    "domain": "Agentic Systems",
    "carrier_digest": "blake3:carrier_level_84..."
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
    "tool_id": "run_simplicial_solve",
    "schema_digest": "sha256:schema_tool_solve_v1",
    "arguments": {
      "vertex_count": 4,
      "boundary_check": true
    },
    "argument_digest": "sha256:args_b9c8d7e6...",
    "execution_id": "exec_turn_84_001",
    "result_digest": "sha256:res_e4f5a6b7...",
    "exit_status": 0
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_84"
  }
}
```

### AST Representation
```rust
pub struct ToolExecutionPayload {
    pub tool_id: String,
    pub schema_digest: String,
    pub arguments: serde_json::Value,
    pub argument_digest: String,
    pub execution_id: String,
    pub result_digest: String,
    pub exit_status: i32,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `ToolExecutionContract`:

Referees validate tool call proposals against pinned JSON schemas and execution receipts:
1. **Schema Validation:** Validates arguments against pinned schema with `additionalProperties: false`.
2. **Boundary Enforcement:** Rejects unescaped command injection patterns, path traversal strings, and undeclared parameters.
3. **Digest Binding:** Binds proposal argument digest strictly to the executed tool receipt digest: $(\text{tool\_id}, \text{schema\_digest}, \text{argument\_digest}, \text{execution\_id}, \text{result\_digest}, \text{exit\_status})$.
4. **Exit Verification:** Asserts that tool execution terminated cleanly with exit status 0.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Arguments strictly conform to pinned JSON-Schema with no extra properties, parameter boundaries respected, argument digest matches receipt, and execution exit status is 0.
- **`StabilizedSurvivor` Admission Criterion:** Bound tool execution receipt recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 84 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_TOOL_SCHEMA_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 84, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no tool call, and the packet never prints the pinned argument schema behind `schema_digest`, so the schema validation in section 4 cannot be run; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** The section 3 schema example passes `vertex_count: 4` (an integer) and `boundary_check: true`. The domain negative vector passes `vertex_count: "4; rm -rf /"`, a string carrying a shell command separator; under any schema that types `vertex_count` as an integer it fails type validation before execution, so `Refused` follows. The receipt digests are placeholder labels.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 84, "carrier_match": true, "tool_id": "run_simplicial_solve", "arguments": {"vertex_count": "4; rm -rf /"}}
  REFEREE:  REFUSED -> Refusal Code: ERR_TOOL_SCHEMA_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 84, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Structural JSON-Schema validation and cryptographic binding of tool invocations to execution receipts.
   - A proposed PFP packet envelope, `ToolExecutionContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove that downstream external tools are free from internal implementation vulnerabilities.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Enforces schema conformance and binds proposed tool arguments to executed host receipts.
4. **Next test needed:**
   - Execute adversarial tool call injection suites against the host schema validator.
