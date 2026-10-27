---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 77: ACID Transaction Envelopes & Two-Phase Commit"
kind: grammar-reference
level: 77
epoch: "Epoch VII"
domain: "Distributed Systems"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "TransactionModule"
evaluator_contract: "TransactionSerializabilityContract"
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

# The Symbol Game Level 77: ACID Transaction Envelopes & Two-Phase Commit

**AuthorityEffect:** None.  
**Level:** Level 77 | **Epoch:** Epoch VII | **Domain:** Distributed Systems  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Concurrent transaction schedules with conflict serialization graphs and 2PC logs`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SERIALIZABILITY_CYCLE_DEFECT`  
**Evaluator Module:** `TransactionModule` (`ACID Conflict Serializability & Two-Phase Commit Evaluator`)  
**Evaluator Contract:** `TransactionSerializabilityContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `TransactionModule` or contract `TransactionSerializabilityContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 77 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 77: ACID Transaction Envelopes & Two-Phase Commit** within the Distributed Systems bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{77} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Concurrent transaction schedules with conflict serialization graphs and 2PC logs`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `TransactionModule` executing under `TransactionSerializabilityContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of transaction conflict serialization graphs, WW/WR/RW conflict acyclicity, and atomic 2PC consensus logs.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (TransactionModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: TransactionModule           |
| Packet:               |              | Contract: TransactionSerializabilityContract       |
|  - MoveType           |              |                                      |
|  - Target Fields      |              | Discrepancy Checks:                  |
|  - Witness Artifact   | =====>>>>>   |  1. Syntax / Schema Gate             |
|                       |  (HTTP/Wire) |  2. Primary Domain Invariant Gate    |
| (Zero operational     |              |  3. Budget & Boundary Mask Audit     |
|  authority until      |              |                                      |
|  certified by         | <<<<<=====   | Emits: Immutable Evaluation Receipt  |
|  exact referee)       |   (Receipt)  |  - Disposition (8 Canonical Statuses)|
+-----------------------+              +--------------------------------------+
```

The game follows a strict non-conflation protocol: **proposals are untrusted hypotheses with zero authority until certified by the exact referee**.

---

## 3. Proposal Packet Schema

Proposals targeting Level 77 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_77_transactional_receipts.json",
  "title": "sg_packet_level_77_transactional_receipts",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "schedule_id": "sched_2pc_serializable",
    "transactions": ["T1", "T2"],
    "conflict_graph_edges": [
      {"from": "T1", "to": "T2", "type": "WRITE_READ", "item": "x"}
    ],
    "topological_sort_order": ["T1", "T2"],
    "two_phase_commit_log": {
      "coordinator": "C0",
      "participants": ["P1", "P2"],
      "votes": {"P1": "VOTE_COMMIT", "P2": "VOTE_COMMIT"},
      "global_verdict": "GLOBAL_COMMIT"
    },
    "conflict_serializable": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct TransactionSerializabilityPayload {
    pub move_type: MoveType,
    pub schedule_id: String,
    pub transactions: Vec<String>,
    pub conflict_graph_edges: Vec<ConflictEdge>,
    pub topological_sort_order: Vec<String>,
    pub two_phase_commit_log: TwoPhaseCommitLog,
    pub conflict_serializable: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 77 binds the referee to `TransactionModule` under `TransactionSerializabilityContract`:

Referees evaluate Level 77 candidates through transactional conflict serializability and 2PC consensus:

1. **Conflict Serializability Graph (CSG):** Recomputes all conflict edges (WW, WR, and RW anti-dependencies) from transaction read/write sets:
   $$T_i \longrightarrow T_j \iff \exists x : (o_i(x) \prec o_j(x)) \land (o_i \text{ or } o_j \text{ is write})$$
2. **Acyclicity Verification:** Asserts that the conflict graph contains no directed cycles, verifying conflict serializability via a valid `topological_sort_order`.
3. **2PC Consensus Integrity:** Verifies that `global_verdict` equals `GLOBAL_COMMIT` iff all participants voted `VOTE_COMMIT`; any abort vote forces `GLOBAL_ABORT`.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the conflict serialization graph is acyclic with verified topological sort, and the 2PC log satisfies atomic consensus.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an abort event is certified cleanly rolled back without dirty read cascade.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 77? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `TransactionSerializabilityContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_SERIALIZABILITY_CYCLE_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 77, "carrier_match": true, "move": "ASSERT", "transactions": ["T1", "T2"], "conflict_graph_edges": [{"from": "T1", "to": "T2", "type": "WR"}], "topological_sort_order": ["T1", "T2"], "two_phase_commit_log": {"votes": {"P1": "VOTE_COMMIT"}, "global_verdict": "GLOBAL_COMMIT"}, "conflict_serializable": true}
REFEREE:  ACCEPT -> Status: ExactRepair (conflict graph acyclic with topological order [T1, T2], 2PC atomic commit verified)
```

### Domain-Negative Test Vector (`ERR_SERIALIZABILITY_CYCLE_DEFECT`)
```text
PROPOSAL: {"level": 77, "carrier_match": true, "move": "ASSERT", "transactions": ["T1", "T2"], "conflict_graph_edges": [{"from": "T1", "to": "T2", "type": "WR"}, {"from": "T2", "to": "T1", "type": "RW"}], "topological_sort_order": ["T1", "T2"], "two_phase_commit_log": {"votes": {"P1": "VOTE_COMMIT"}, "global_verdict": "GLOBAL_COMMIT"}, "conflict_serializable": false}
REFEREE:  REFUSED -> Refusal Code: ERR_SERIALIZABILITY_CYCLE_DEFECT, Status: Refused (conflict graph contains directed cycle T1 -> T2 -> T1, violating conflict serializability)
```

**Worked check (2026-10-20):** Passing vector: the only conflict edge is `T1 -> T2`, so Kahn's algorithm removes `T1` (in-degree 0) and then `T2`; the order `[T1, T2]` is a valid topological sort and the graph is acyclic. Its 2PC log has one vote, `P1: VOTE_COMMIT`, so `GLOBAL_COMMIT` agrees with the all-commit rule for the participants listed in this vector (the schema example lists `P1` and `P2`; the vector lists only `P1`). Negative vector: edges `T1 -> T2` and `T2 -> T1` leave both in-degrees at 1, so no node can be removed first and the graph has the cycle `T1 -> T2 -> T1`. The supplied `topological_sort_order` `[T1, T2]` is therefore invalid, because `T2 -> T1` points backward in it. Neither vector lists read and write sets, so the conflict edges themselves cannot be recomputed from the packet as section 4 requires; they are taken as given.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 77 under `TransactionSerializabilityContract`.
   - Specified detection of domain discrepancies emitting `ERR_SERIALIZABILITY_CYCLE_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish general correctness outside `Concurrent transaction schedules with conflict serialization DAGs and 2PC logs`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `TransactionModule` running `TransactionSerializabilityContract` is specified to distinguish valid `Distributed Systems` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
