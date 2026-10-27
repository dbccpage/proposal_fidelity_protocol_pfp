---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 37: Pearl Causal Graphs & Do-Calculus Interventions"
kind: grammar-reference
level: 37
epoch: "Epoch II"
domain: "Causal Inference"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "CausalInferenceModule"
evaluator_contract: "CausalInterventionContract"
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

# The Symbol Game Level 37: Pearl Causal Graphs & Do-Calculus Interventions

**AuthorityEffect:** None.  
**Level:** Level 37 | **Epoch:** Epoch II | **Domain:** Causal Inference  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Causal DAG G = (V, E) with structural equations and mutilated graph G_{X=x}`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_STRUCTURAL_EQUATION_DEFECT`  
**Evaluator Module:** `CausalInferenceModule` (`Pearl Causal DAG & Do-Calculus Graph Surgery Evaluator`)  
**Evaluator Contract:** `CausalInterventionContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CausalInferenceModule` or contract `CausalInterventionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 37 establishes the Proposal Fidelity Protocol (PFP) arena for **Pearl Causal Graphs & Do-Calculus Interventions** within the Causal Inference bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{37} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Causal DAG G = (V, E) with structural equations and mutilated graph G_{X=x}`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CausalInferenceModule` (`CausalInterventionContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Causal DAG acyclicity, structural equation intervention do(X=x), mutilated graph G_{X=x}, and backdoor adjustment formula.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 37         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `CausalInferenceModule` metrics under `CausalInterventionContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_STRUCTURAL_EQUATION_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 37 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_37_causal_intervention` family schema:

```json
{
  "schema_id": "sg_packet_level_37_causal_intervention",
  "task_data": {
    "level": 37,
    "epoch": "Epoch II",
    "domain": "Causal Inference",
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
    "dag_nodes": ["Z", "X", "Y"],
    "dag_edges": [["Z", "X"], ["Z", "Y"], ["X", "Y"]],
    "intervention_target": "X",
    "intervention_value": "1",
    "mutilated_edges": [["Z", "Y"], ["X", "Y"]],
    "backdoor_adjustment_formula": "P(Y|do(X=x)) = sum_z P(Y|X=x, Z=z) P(Z=z)",
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
pub struct CausalInterventionPayload {
    pub move_type: MoveType,
    pub dag_nodes: Vec<String>,
    pub dag_edges: Vec<(String, String)>,
    pub intervention_target: String,
    pub intervention_value: String,
    pub mutilated_edges: Vec<(String, String)>,
    pub backdoor_adjustment_formula: String,
    pub proposer_signature: String,
}

pub struct Level37Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: CausalInterventionPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: CausalInferenceModule

### Contract: `CausalInterventionContract`

Referees evaluate Level 37 candidates through Pearl causal graph surgery and do-calculus:

1. **DAG Acyclicity & Topological Sort:** Verifies directed graph $\mathcal{G} = (V, E)$ is strictly acyclic without directed cycles.
2. **Graph Surgery (Mutilated Graph):** Evaluates $do(X=x)$ intervention, verifying that the mutilated graph $\mathcal{G}_{\overline{X}}$ eliminates all incoming edges into $X$:
   $$\operatorname{pa}_{\mathcal{G}_{\overline{X}}}(X) = \emptyset, \quad \mathcal{G}_{\overline{X}} = (V, E \setminus \{W \to X \mid W \in \operatorname{pa}_\mathcal{G}(X)\})$$
3. **Backdoor Criterion & Adjustment:** Verifies adjustment set $Z$ blocks all backdoor paths between $X$ and $Y$ without containing descendants of $X$, confirming the interventional distribution:
   $$P(Y \mid do(X=x)) = \sum_z P(Y \mid X=x, Z=z) P(Z=z)$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the causal DAG is acyclic, the mutilated graph correctly cuts all arrows incoming to the intervention target, and the backdoor adjustment formula is valid.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an unidentifiable causal effect (where latent confounding precludes unconfounded estimation under Tian-Pearl completeness) is certified non-identifiable, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 37 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_STRUCTURAL_EQUATION_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 37, "carrier_match": true, "move": "ASSERT", "dag_edges": [["Z", "X"], ["Z", "Y"], ["X", "Y"]], "intervention_target": "X", "mutilated_edges": [["Z", "Y"], ["X", "Y"]]}
REFEREE:  ACCEPT -> Status: ExactRepair (mutilated DAG correctly cuts incoming arrow Z -> X for do(X=x))
  ```

  **Worked check (2026-10-20):** the graph $Z \to X$, $Z \to Y$, $X \to Y$ is acyclic (topological order $Z, X, Y$). $\operatorname{pa}(X) = \{Z\}$, so $\mathcal{G}_{\overline{X}}$ removes exactly $Z \to X$ and keeps $\{Z \to Y, X \to Y\}$, matching `mutilated_edges`. The only backdoor path is $X \leftarrow Z \to Y$; conditioning on $Z$ blocks it, and $Z$ is not a descendant of $X$, so the adjustment formula in the schema example applies.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 37, "carrier_match": true, "move": "ASSERT", "dag_edges": [["Z", "X"], ["Z", "Y"], ["X", "Y"]], "intervention_target": "X", "mutilated_edges": [["Z", "X"], ["Z", "Y"], ["X", "Y"]]}
REFEREE:  REFUSED -> Refusal Code: ERR_STRUCTURAL_EQUATION_DEFECT, Status: Refused (mutilated graph retains incoming edge Z -> X to intervention target X)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 37, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 37: Pearl Causal Graphs & Do-Calculus Interventions within the Causal Inference bounded context.
   - A proposed PFP packet envelope, `CausalInferenceModule` (`CausalInterventionContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 37 specifies an exact, deterministic evaluation procedure for candidate proposals over `Causal DAG G = (V, E) with structural equations and mutilated graph G_{X=x}`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
