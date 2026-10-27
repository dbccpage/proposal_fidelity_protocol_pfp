---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 74: Codd Relational Algebra & Join Topology Graphs"
kind: grammar-reference
level: 74
epoch: "Epoch VII"
domain: "Database Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "RelationalDataModule"
evaluator_contract: "RelationalQueryContract"
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

# The Symbol Game Level 74: Codd Relational Algebra & Join Topology Graphs

**AuthorityEffect:** None.  
**Level:** Level 74 | **Epoch:** Epoch VII | **Domain:** Database Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Relational schema signatures over the SPJR algebra fragment with set semantics`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_QUERY_EQUIVALENCE_DEFECT`  
**Evaluator Module:** `RelationalDataModule` (`Codd Relational Algebra SPJR & Query Equivalence Evaluator`)  
**Evaluator Contract:** `RelationalQueryContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `RelationalDataModule` or contract `RelationalQueryContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 74 establishes the Proposal Fidelity Protocol (PFP) arena for **The Symbol Game Level 74: Codd Relational Algebra & Join Topology Graphs** within the Database Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{74} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Relational schema signatures over the SPJR algebra fragment with set semantics`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `RelationalDataModule` executing under `RelationalQueryContract`, calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8 turns$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact verification of relational query equivalence over the SPJR fragment (Select, Project, Join, Rename) with duplicate-free set semantics.

---

## 2. Proposer & Checker Protocol

```
 Proposer Candidate                     Referee Evaluator (RelationalDataModule)
+-----------------------+              +--------------------------------------+
| Untrusted LLM Proposal|              | Module: RelationalDataModule           |
| Packet:               |              | Contract: RelationalQueryContract       |
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

Proposals targeting Level 74 are specified by the following proposed JSON schema sketch (no schema file exists in source; the runtime sealer `core-canonical-v1` is not RFC 8785):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "sg_packet_level_74_relational_query_mapping.json",
  "title": "sg_packet_level_74_relational_query_mapping",
  "type": "object",
  "properties": {
    "move_type": "ASSERT",
    "query_fragment": "SPJR",
    "query_a": "pi_{A, B}(sigma_{C > 0}(R) bowtie S)",
    "query_b": "pi_{A, B}(sigma_{C > 0}(R bowtie S))",
    "rewrite_steps": [
      "pushdown_selection_through_join"
    ],
    "equivalence_witness": "identity_relational_homomorphism",
    "equivalent": true,
    "proposer_signature": "untrusted_candidate_token" 
  },
  "required": ["move_type", "proposer_signature"]
}
```

### Sovereign Rust Type Contract
```rust
pub struct RelationalQueryPayload {
    pub move_type: MoveType,
    pub query_fragment: String,
    pub query_a: String,
    pub query_b: String,
    pub rewrite_steps: Vec<String>,
    pub equivalence_witness: String,
    pub equivalent: bool,
    pub proposer_signature: String,
}
```

---

## 4. Evaluator Module Registration & Decision Mechanics

Level 74 binds the referee to `RelationalDataModule` under `RelationalQueryContract`:

Referees evaluate Level 74 candidates through Codd relational algebra:

1. **SPJR Fragment Discipline:** Restricts queries strictly to the SPJR fragment (Select $\sigma$, Project $\pi$, Natural Join $\bowtie$, Rename $\rho$) under duplicate-free set semantics and total NULL-free policy.
2. **Equivalence Witness Verification:** Validates that `rewrite_steps` preserve the evaluation homomorphism on all database instances:
   $$\mathcal{E}(Q_A, \mathcal{D}) = \mathcal{E}(Q_B, \mathcal{D}) \quad \forall \mathcal{D} \in \operatorname{Inst}(\Sigma)$$
3. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff queries are well-typed under schema $\Sigma$ and the rewrite steps constitute a valid algebraic equivalence proof.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff query equivalence is conditional on an explicit functional dependency key constraint.

### Canonical 8-Terminal Reachability Matrix

| Terminal Status | Reachable in Level 74? | Concrete Machine Condition for Disposition |
| :--- | :--- | :--- |
| **`CertifiedReceipt`** | **Yes** | All domain constraints of `RelationalQueryContract` satisfied with zero discrepancy. |
| **`ExactRepair`** | **Yes** | Proposal contains sub-threshold defect repairable within fuel quota without structural damage. |
| **`StabilizedSurvivor`**| **Yes** | Structural obstruction formally isolated and certified stable with invariant witness preserved. |
| **`OpenObstruction`** | **Yes** | Obstruction cannot be bounded or resolved within allocated fuel budget `8 turns`. |
| **`LiftLicenseNeeded`** | **Yes** | Certified same-level exhaustion reached; candidate proposal requires higher-order contract. |
| **`Refused`** | **Yes** | Proposal violates primary domain invariant, triggering `ERR_QUERY_EQUIVALENCE_DEFECT`. |
| **`Invalid`** | **Yes** | Payload fails schema validation, contains unknown fields, or violates syntactic format. |
| **`Halted`** | **Yes** | Turn budget `8 turns` exhausted before proposal admission. |

> **Correction (2026-10-20):** `CertifiedReceipt` and `Halted` are not members of the eight-status taxonomy. The source enum [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) has `ExactRepair`, `StabilizedSurvivor`, `OpenObstruction`, `OracleNeeded`, `LiftLicenseNeeded`, `Refused`, `Invalid` and `InfrastructureFailure`. Read the `CertifiedReceipt` row as part of `ExactRepair` and the `Halted` row as the fuel-exhaustion case of `OpenObstruction`; `OracleNeeded` and `InfrastructureFailure` are not reached in local evaluation.

---

## 5. Replayable Test Vectors

### Passing Test Vector (`ASSERT` / `ExactRepair`)
```text
PROPOSAL: {"level": 74, "carrier_match": true, "move": "ASSERT", "query_fragment": "SPJR", "query_a": "pi_{A}(sigma_{B=1}(R))", "query_b": "pi_{A}(sigma_{B=1}(pi_{A,B}(R)))", "rewrite_steps": ["selection_projection_commutation"], "equivalence_witness": "valid_spjr_rule", "equivalent": true}
REFEREE:  ACCEPT -> Status: ExactRepair (SPJR query equivalence verified through algebraic rewrite step)
```

**Worked check (2026-10-20):** before 2026-10-20 `query_b` read `sigma_{B=1}(pi_{A,B}(R))`, whose output schema is {A, B}, while `query_a` outputs {A}; the two queries were not equivalent. With the outer projection restored, σ_{B=1} commutes with π_{A,B} because the projection keeps B, and π_A ∘ π_{A,B} = π_A, so π_A(σ_{B=1}(π_{A,B}(R))) = π_A(σ_{B=1}(R)) on every instance.

### Domain-Negative Test Vector (`ERR_QUERY_EQUIVALENCE_DEFECT`)
```text
PROPOSAL: {"level": 74, "carrier_match": true, "move": "ASSERT", "query_fragment": "SPJR", "query_a": "pi_{A}(R bowtie S)", "query_b": "pi_{A}(R) bowtie pi_{A}(S)", "rewrite_steps": ["invalid_projection_distribution"], "equivalence_witness": "invalid_witness", "equivalent": false}
REFEREE:  REFUSED -> Refusal Code: ERR_QUERY_EQUIVALENCE_DEFECT, Status: Refused (projection does not distribute over natural join without key preservation, query equivalence defect)
```

**Reproducibility gap (2026-10-20):** the verdict depends on the schemas, which the vector does not declare. If R and S share an attribute besides A, say R(A, B) and S(A, B), then R = {(1, 1)} and S = {(1, 2)} give R ⋈ S = ∅, so π_A(R ⋈ S) = ∅ while π_A(R) ⋈ π_A(S) = {(1)}. If A is the only common attribute, both sides equal π_A(R) ∩ π_A(S) and the queries are equivalent.

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - A specification for referee verification of candidate proposals targeting Level 74 under `RelationalQueryContract`.
   - Specified detection of domain discrepancies emitting `ERR_QUERY_EQUIVALENCE_DEFECT`.
   - Specified receipt fields with `AuthorityEffect: None` (no receipt generator for this level exists at the source pin).
2. **What this does not support:**
   - Does not establish correctness outside `Codd relational algebra SPJR query rewrites with duplicate-free set semantics`.
   - Does not grant unconstrained operational authority or license unverified lifts.
3. **The narrowest defensible claim:**
   - Evaluator `RelationalDataModule` running `RelationalQueryContract` is specified to distinguish valid `Database Theory` proposal witnesses from invalid payloads on finite test fixtures.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
