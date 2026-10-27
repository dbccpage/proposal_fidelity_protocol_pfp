---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 81: Differential Privacy & Bounded Query Sensitivity"
kind: grammar-reference
level: 81
epoch: "Epoch VIII"
domain: "Data Privacy"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "DifferentialPrivacyContract"
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

# The Symbol Game Level 81: Differential Privacy & Bounded Query Sensitivity

**AuthorityEffect:** None.  
**Level:** Level 81 | **Epoch:** Epoch VIII | **Domain:** Data Privacy  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Finite bounded datasets with discrete Hamming/neighbor metric and numerical queries`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_RELEASE_QUERY_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`DifferentialPrivacyContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `DifferentialPrivacyContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 81 establishes the Proposal Fidelity Protocol (PFP) arena for **Differential Privacy & Bounded Query Sensitivity** within the Data Privacy bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{81} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Finite bounded datasets with discrete Hamming/neighbor metric and numerical queries`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `DifferentialPrivacyContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying discrete differential privacy noise bounds, sensitivity witnesses, and cumulative privacy budget composition.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 81        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `DifferentialPrivacyContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_RELEASE_QUERY_DEFECT`) are emitted exclusively by `DifferentialPrivacyContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 81 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_81` schema:

```json
{
  "schema_id": "sg_packet_level_81_data_privacy",
  "task_data": {
    "level": 81,
    "epoch": "Epoch VIII",
    "domain": "Data Privacy",
    "carrier_digest": "blake3:carrier_level_81..."
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
    "query_id": "count_inhabited_cells",
    "dataset_d_digest": "sha256:d001_base_corpus",
    "dataset_d_prime_digest": "sha256:d002_neighbor_corpus",
    "adjacency_distance": 1,
    "sensitivity_bound_delta_f": "1",
    "epsilon": "1/2",
    "delta": "0",
    "mechanism": "discrete_laplace",
    "privacy_budget_total": "2",
    "privacy_budget_spent": "1/2",
    "query_result_raw": 42,
    "query_result_perturbed": 43,
    "noise_sample_witness": 1
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_81"
  }
}
```

### AST Representation
```rust
pub struct DifferentialPrivacyPayload {
    pub query_id: String,
    pub dataset_d_digest: String,
    pub dataset_d_prime_digest: String,
    pub adjacency_distance: u32,
    pub sensitivity_bound_delta_f: BigRational,
    pub epsilon: BigRational,
    pub delta: BigRational,
    pub mechanism: String,
    pub privacy_budget_total: BigRational,
    pub privacy_budget_spent: BigRational,
    pub query_result_raw: i64,
    pub query_result_perturbed: i64,
    pub noise_sample_witness: i64,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `DifferentialPrivacyContract`:

Referees evaluate candidate privacy mechanisms against discrete $(\epsilon, \delta)$-differential privacy bounds:
1. **Adjacency Assertion:** Confirms that datasets $D, D'$ differ by at most one record ($\|D \ominus D'\|_1 \le 1$).
2. **Sensitivity Bound:** Verifies that $|f(D) - f(D')| \le \Delta f$ across the declared adjacent pair.
3. **Noise Calibration:** Verifies that the noise scale matches declared $\epsilon, \delta$ under the declared mechanism.
4. **Budget Composition:** Verifies that cumulative privacy loss does not exceed total budget: $\epsilon_{\text{spent}} + \epsilon \le \epsilon_{\text{total}}$.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Dataset adjacency verified ($\|D \ominus D'\|_1 \le 1$), sensitivity verified $|f(D) - f(D')| \le \Delta f$, noise mechanism parameters match declared $(\epsilon, \delta)$, and $\epsilon_{\text{spent}} + \epsilon \le \epsilon_{\text{total}}$.
- **`StabilizedSurvivor` Admission Criterion:** Bounded privacy release certificate recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 81 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_RELEASE_QUERY_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 81, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no query, datasets, $\epsilon$, budget or noise sample, so the four checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** The section 3 schema example is the checkable instance. A counting query on datasets at adjacency distance 1 changes by at most 1, so $\Delta f = 1$ is a valid sensitivity bound. The release adds the noise sample to the raw count: $42 + 1 = 43$, as recorded. Budget composition: $\epsilon_{\text{spent}} + \epsilon = 1/2 + 1/2 = 1 \le 2 = \epsilon_{\text{total}}$, so the release fits. One noise sample cannot show that the discrete Laplace scale matches $\epsilon / \Delta f = 1/2$; that needs the mechanism's sampling code, not a single draw. The domain negative vector has $1/2 + 1/2 = 1 > 1/2 = \epsilon_{\text{total}}$, so the budget check fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 81, "carrier_match": true, "query_id": "count_inhabited_cells", "epsilon": "1/2", "privacy_budget_total": "1/2", "privacy_budget_spent": "1/2"}
  REFEREE:  REFUSED -> Refusal Code: ERR_RELEASE_QUERY_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 81, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Exact rational verification of query sensitivity bounds and $(\epsilon, \delta)$ budget composition.
   - A proposed PFP packet envelope, `DifferentialPrivacyContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove empirical zero reconstruction risk against arbitrary out-of-model correlated side-channels.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Verifies that declared discrete Laplace/Gaussian noise parameters satisfy $(\epsilon, \delta)$-DP budget bounds.
4. **Next test needed:**
   - Replay differential privacy mechanism tests against synthetic multi-query sequences.
