---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 94: Vertical Protocol Stacking & Clean Architecture Ports"
kind: grammar-reference
level: 94
epoch: "Epoch IX"
domain: "Software Architecture"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "VerificationToolchainModule"
evaluator_contract: "CleanArchitectureContract"
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

# The Symbol Game Level 94: Vertical Protocol Stacking & Clean Architecture Ports

**AuthorityEffect:** None.  
**Level:** Level 94 | **Epoch:** Epoch IX | **Domain:** Software Architecture  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Module dependency graphs, interface boundary contracts, and inward dependency matrices`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_INTERFACE_PORT_DEFECT`  
**Evaluator Module:** `VerificationToolchainModule` (`CleanArchitectureContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `VerificationToolchainModule` or contract `CleanArchitectureContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 94 establishes the Proposal Fidelity Protocol (PFP) arena for **Vertical Protocol Stacking & Clean Architecture Ports** within the Software Architecture bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{94} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Module dependency graphs, interface boundary contracts, and inward dependency matrices`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `VerificationToolchainModule` via `CleanArchitectureContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Enforcing Clean Architecture inward dependency rules and verifying zero cycle obstructions across architectural boundaries.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 94        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `CleanArchitectureContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_INTERFACE_PORT_DEFECT`) are emitted exclusively by `CleanArchitectureContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 94 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_94` schema:

```json
{
  "schema_id": "sg_packet_level_94_software_architecture",
  "task_data": {
    "level": 94,
    "epoch": "Epoch IX",
    "domain": "Software Architecture",
    "carrier_digest": "blake3:carrier_level_94..."
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
    "modules": [
      "domain",
      "use_cases",
      "infrastructure",
      "controllers"
    ],
    "ports": [
      {
        "name": "SolverPort",
        "owning_layer": "domain"
      }
    ],
    "edges": [
      [
        "use_cases",
        "domain"
      ],
      [
        "infrastructure",
        "domain"
      ],
      [
        "controllers",
        "use_cases"
      ]
    ],
    "allowed_inward_rules": [
      {
        "layer": "domain",
        "may_depend_on": []
      },
      {
        "layer": "use_cases",
        "may_depend_on": [
          "domain"
        ]
      },
      {
        "layer": "infrastructure",
        "may_depend_on": [
          "domain"
        ]
      },
      {
        "layer": "controllers",
        "may_depend_on": [
          "use_cases",
          "domain"
        ]
      }
    ],
    "violations": []
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_94"
  }
}
```

### AST Representation
```rust
pub struct CleanArchitecturePayload {
    pub modules: Vec<String>,
    pub ports: Vec<PortDeclaration>,
    pub edges: Vec<(String, String)>,
    pub allowed_inward_rules: Vec<InwardRule>,
    pub violations: Vec<String>,
}
```

---

## 4. Evaluator Module & Objective Metrics: VerificationToolchainModule

Referees evaluate candidates through `CleanArchitectureContract`:

Referees audit module dependency complexes for architectural boundary compliance:
1. **Strict Inward Dependency Rule:** Asserts that inner layers (`domain`) have zero dependencies on outer layers.
2. **Port Delegation:** Verifies that external infrastructure services are injected through domain ports.
3. **Cycle Obstruction Check:** Asserts that the directed module dependency graph has no directed cycle, checked by a topological sort. *(Correction, 2026-10-20: the earlier formula $\Gamma_2 = \|d_1 c\| = 0$ does not detect directed cycles. This level declares no 2-cells and no cochain $c$; with no 2-cells $d_1 = 0$, so the formula holds for every graph.)*
4. **Boundary Leakage:** Asserts that boundary cochain leakage is zero: $\Phi_1 = 0$. *(Open, 2026-10-20: no cochain or repair gauge is declared for this level, so $\Phi_1$ is undefined here; the check needs a declared cochain complex before it can be evaluated.)*

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** All dependency edges obey inward direction rules (domain has zero dependencies on outer layers) and zero cyclic obstructions exist on the module dependency complex.
- **`StabilizedSurvivor` Admission Criterion:** Clean Architecture boundary certification recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 94 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_INTERFACE_PORT_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 94, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no modules, edges or rules, so the checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example each edge points to an allowed layer: `use_cases -> domain` (allowed), `infrastructure -> domain` (allowed), `controllers -> use_cases` (allowed). `domain` has no outgoing edge, and a topological sort `controllers, use_cases, infrastructure, domain` exists, so the graph is acyclic. The domain negative vector adds `domain -> infrastructure`, but `domain` may depend on nothing, so the inward rule fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 94, "carrier_match": true, "edges": [["domain", "infrastructure"]]}
  REFEREE:  REFUSED -> Refusal Code: ERR_INTERFACE_PORT_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 94, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - AST-level enforcement of Clean Architecture inward dependencies and acyclic module structures.
   - A proposed PFP packet envelope, `CleanArchitectureContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove the absence of logical bugs within individual cleanly factored modules.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the analyzed module graph obeys declared inward dependency rules with zero architectural cycles.
4. **Next test needed:**
   - Execute Clean Architecture boundary checks across the omega_engine bounded contexts.
