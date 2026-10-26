---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 85: Task Routing DAGs & Capability Gating"
kind: grammar-reference
level: 85
epoch: "Epoch VIII"
domain: "Multi-Agent Systems"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "CapabilityRoutingContract"
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

# The Symbol Game Level 85: Task Routing DAGs & Capability Gating

**AuthorityEffect:** None.  
**Level:** Level 85 | **Epoch:** Epoch VIII | **Domain:** Multi-Agent Systems  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Multi-agent task dependency DAGs with typed capability manifests and principal authority scopes`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_TASK_SCOPE_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`CapabilityRoutingContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `CapabilityRoutingContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 85 establishes the Proposal Fidelity Protocol (PFP) arena for **Task Routing DAGs & Capability Gating** within the Multi-Agent Systems bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{85} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Multi-agent task dependency DAGs with typed capability manifests and principal authority scopes`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `CapabilityRoutingContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying multi-agent task routing, capability containment, and delegated scope attenuation.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 85        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `CapabilityRoutingContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_TASK_SCOPE_DEFECT`) are emitted exclusively by `CapabilityRoutingContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 85 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_85` schema:

```json
{
  "schema_id": "sg_packet_level_85_multi-agent_systems",
  "task_data": {
    "level": 85,
    "epoch": "Epoch VIII",
    "domain": "Multi-Agent Systems",
    "carrier_digest": "blake3:carrier_level_85..."
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
    "task_id": "subtask_homology_sweep",
    "required_capabilities": [
      "rust_solver_execution",
      "exact_rational_eval"
    ],
    "agent_id": "agent_techne_solver",
    "agent_capabilities": [
      "rust_solver_execution",
      "exact_rational_eval",
      "python_test"
    ],
    "principal_scope": [
      "read_fixtures",
      "execute_solver"
    ],
    "delegated_scope": [
      "execute_solver"
    ]
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_85"
  }
}
```

### AST Representation
```rust
pub struct CapabilityRoutingPayload {
    pub task_id: String,
    pub required_capabilities: Vec<String>,
    pub agent_id: String,
    pub agent_capabilities: Vec<String>,
    pub principal_scope: Vec<String>,
    pub delegated_scope: Vec<String>,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `CapabilityRoutingContract`:

Referees audit task assignments for capability satisfaction and scope attenuation:
1. **Capability Containment:** Explicitly asserts $\operatorname{required}(task) \subseteq \operatorname{capabilities}(agent)$.
2. **Scope Attenuation:** Explicitly asserts $\operatorname{scope}_{\text{delegated}} \subseteq \operatorname{scope}_{\text{principal}}$.
3. **No-Escalation Gate:** Rejects any task delegation where the assigned agent receives authority unheld by the delegator.
4. **Authority Firewall:** Asserts `AuthorityEffect: None`; valid task routing mints zero autonomous authority.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Task required capabilities are fully contained in agent capabilities ($\operatorname{required}(task) \subseteq \operatorname{capabilities}(agent)$) and delegated scope is attenuated ($\operatorname{scope}_{\text{delegated}} \subseteq \operatorname{scope}_{\text{principal}}$).
- **`StabilizedSurvivor` Admission Criterion:** Gated task routing record certified under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 85 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_TASK_SCOPE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 85, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no capability or scope sets, so the containment checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example, required = {`rust_solver_execution`, `exact_rational_eval`} is a subset of the agent's {`rust_solver_execution`, `exact_rational_eval`, `python_test`}, and delegated = {`execute_solver`} is a subset of principal = {`read_fixtures`, `execute_solver`}; both checks pass. The domain negative vector requires {`rust_solver_execution`} from an agent holding only {`python_test`}; the subset test fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 85, "carrier_match": true, "required_capabilities": ["rust_solver_execution"], "agent_capabilities": ["python_test"]}
  REFEREE:  REFUSED -> Refusal Code: ERR_TASK_SCOPE_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 85, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of capability containment and authority attenuation across multi-agent task delegations.
   - A proposed PFP packet envelope, `CapabilityRoutingContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not ensure that the assigned agent will complete the task without errors.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that an agent possesses declared prerequisites and does not exceed principal authorization.
4. **Next test needed:**
   - Execute capability routing checks across multi-tier delegation graphs.
