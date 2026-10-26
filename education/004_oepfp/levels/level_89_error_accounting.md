---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 89: Residual Error Accounting & Bounded Loss Budgets"
kind: grammar-reference
level: 89
epoch: "Epoch VIII"
domain: "Fault Tolerance"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "ErrorBudgetContract"
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

# The Symbol Game Level 89: Residual Error Accounting & Bounded Loss Budgets

**AuthorityEffect:** None.  
**Level:** Level 89 | **Epoch:** Epoch VIII | **Domain:** Fault Tolerance  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Bounded error distributions, loss accounting ledgers, and composite tolerance budgets over Q`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_ERROR_SOURCE_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`ErrorBudgetContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `ErrorBudgetContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 89 establishes the Proposal Fidelity Protocol (PFP) arena for **Residual Error Accounting & Bounded Loss Budgets** within the Fault Tolerance bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{89} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Bounded error distributions, loss accounting ledgers, and composite tolerance budgets over Q`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `ErrorBudgetContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Auditing multi-source numerical error accounting and verifying composite loss bounds over Q.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 89        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `ErrorBudgetContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_ERROR_SOURCE_DEFECT`) are emitted exclusively by `ErrorBudgetContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 89 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_89` schema:

```json
{
  "schema_id": "sg_packet_level_89_fault_tolerance",
  "task_data": {
    "level": 89,
    "epoch": "Epoch VIII",
    "domain": "Fault Tolerance",
    "carrier_digest": "blake3:carrier_level_89..."
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
    "error_sources": [
      {
        "source": "quantization",
        "bound": "1/1000"
      },
      {
        "source": "truncation",
        "bound": "3/1000"
      }
    ],
    "dependence": "worst_case_additive",
    "composition_law": "E_total = sum(E_i)",
    "composite_error_bound": "4/1000",
    "max_loss_budget": "5/1000"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_89"
  }
}
```

### AST Representation
```rust
pub struct ErrorBudgetPayload {
    pub error_sources: Vec<ErrorSourceBound>,
    pub dependence: String,
    pub composition_law: String,
    pub composite_error_bound: BigRational,
    pub max_loss_budget: BigRational,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `ErrorBudgetContract`:

Referees audit multi-source numerical error budgets using exact rational arithmetic:
1. **Rational Purity:** Confirms that all component error bounds are declared as exact rational numbers in $\mathbb{Q}$.
2. **Composition Law Verification:** Evaluates $E_{\text{total}} = F(E_1, \dots, E_n, D)$ under the declared dependence model.
3. **Loss Budget Containment:** Verifies that composite error satisfies $E_{\text{total}} \le L_{\text{budget}}$.
4. **Omission Check:** Confirms that all pipeline approximation steps have an associated entry in `error_sources`.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Error bounds are valid rationals, composition law calculation is mathematically exact, and composite error bound satisfies $E_{\text{total}} \le L_{\text{budget}}$.
- **`StabilizedSurvivor` Admission Criterion:** Bounded error accounting certificate recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 89 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_ERROR_SOURCE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 89, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no error sources or budget, so the checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example the worst-case additive law gives $E_{\text{total}} = 1/1000 + 3/1000 = 4/1000$, matching `composite_error_bound`, and $4/1000 \le 5/1000 = L_{\text{budget}}$, so the budget check passes. The domain negative vector states $6/1000 > 5/1000$, so containment fails and `Refused` follows; it omits `error_sources`, so its composite bound is taken as given rather than recomputed.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 89, "carrier_match": true, "composite_error_bound": "6/1000", "max_loss_budget": "5/1000"}
  REFEREE:  REFUSED -> Refusal Code: ERR_ERROR_SOURCE_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 89, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Exact rational verification of composite numerical error bounds and loss budget containment.
   - A proposed PFP packet envelope, `ErrorBudgetContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not ensure numerical precision beyond declared bounds for unmodeled noise sources.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that declared numerical errors compose under the specified law without exceeding the loss budget.
4. **Next test needed:**
   - Replay error budget arithmetic across multi-stage discrete solver pipelines.
