---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 83: End-to-End Data Lineage & Mutation DAGs"
kind: grammar-reference
level: 83
epoch: "Epoch VIII"
domain: "Data Governance"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "DataLineageContract"
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

# The Symbol Game Level 83: End-to-End Data Lineage & Mutation DAGs

**AuthorityEffect:** None.  
**Level:** Level 83 | **Epoch:** Epoch VIII | **Domain:** Data Governance  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Directed acyclic graphs of dataset transformations and column-level provenance mappings`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SOURCE_DIGEST_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`DataLineageContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `DataLineageContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 83 establishes the Proposal Fidelity Protocol (PFP) arena for **End-to-End Data Lineage & Mutation DAGs** within the Data Governance bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{83} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Directed acyclic graphs of dataset transformations and column-level provenance mappings`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `DataLineageContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying column-level transformation DAGs, acyclicity, and deterministic replay bindings.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 83        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `DataLineageContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SOURCE_DIGEST_DEFECT`) are emitted exclusively by `DataLineageContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 83 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_83` schema:

```json
{
  "schema_id": "sg_packet_level_83_data_governance",
  "task_data": {
    "level": 83,
    "epoch": "Epoch VIII",
    "domain": "Data Governance",
    "carrier_digest": "blake3:carrier_level_83..."
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
    "inputs": [
      {
        "node_id": "raw_telemetry",
        "digest": "sha256:input_telemetry_001"
      }
    ],
    "transform_id": "aggregate_hourly_v2",
    "code_digest": "blake3:code_transform_v2",
    "column_lineage": [
      {
        "target_col": "mean_residual",
        "source_cols": [
          "res_1",
          "res_2"
        ],
        "op": "mean"
      }
    ],
    "outputs": [
      {
        "node_id": "hourly_metrics",
        "digest": "sha256:output_hourly_001"
      }
    ],
    "edges": [
      [
        "raw_telemetry",
        "hourly_metrics"
      ]
    ],
    "acyclicity_witness": "topological_sort_valid"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_83"
  }
}
```

### AST Representation
```rust
pub struct DataLineagePayload {
    pub inputs: Vec<LineageNode>,
    pub transform_id: String,
    pub code_digest: String,
    pub column_lineage: Vec<ColumnMapping>,
    pub outputs: Vec<LineageNode>,
    pub edges: Vec<(String, String)>,
    pub acyclicity_witness: String,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `DataLineageContract`:

Referees audit transformation lineage DAGs for structural validity and reproducibility:
1. **DAG Acyclicity:** Asserts that the directed transformation graph contains zero cycles.
2. **Digest Binding:** Verifies that all input and output datasets match declared cryptographic digests.
3. **Column Mapping Totality:** Confirms that every target column has an explicit ancestor derivation rule.
4. **Replay Determinism:** Asserts that re-executing `code_digest` on inputs reproduces declared output digests.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Lineage graph is strictly acyclic, input/output node digests verified, column mapping operations declared and valid, and replay reproduces declared output digest.
- **`StabilizedSurvivor` Admission Criterion:** Certified lineage graph recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 83 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SOURCE_DIGEST_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 83, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no lineage graph, digests or column mapping, so the checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example the only edge is `raw_telemetry -> hourly_metrics`, so a topological sort exists and the graph is acyclic; the one target column `mean_residual` has a declared rule (`mean` of `res_1`, `res_2`). Digest and replay checks cannot be run because the digests are placeholder labels. The domain negative vector has edges `node_a -> node_b` and `node_b -> node_a`, a directed cycle, so the acyclicity check fails and `Refused` follows. The refusal code `ERR_SOURCE_DIGEST_DEFECT` is this level's single primary error code; the defect the vector shows is a cycle, not a digest mismatch.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 83, "carrier_match": true, "edges": [["node_a", "node_b"], ["node_b", "node_a"]]}
  REFEREE:  REFUSED -> Refusal Code: ERR_SOURCE_DIGEST_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 83, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Acyclicity verification and column-level provenance tracking across dataset transformation DAGs.
   - A proposed PFP packet envelope, `DataLineageContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove the external semantic correctness of the business logic within transformation functions.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that output datasets are topologically derivable from declared inputs without cyclic dependencies.
4. **Next test needed:**
   - Execute lineage graph replay across multi-stage aggregation pipelines.
