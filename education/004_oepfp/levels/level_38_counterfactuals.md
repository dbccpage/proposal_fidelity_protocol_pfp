---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 38: Counterfactual Structural Equations & Exogenous Twins"
kind: grammar-reference
level: 38
epoch: "Epoch II"
domain: "Causal Logic"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "CausalLogicModule"
evaluator_contract: "CounterfactualAbductionContract"
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

# The Symbol Game Level 38: Counterfactual Structural Equations & Exogenous Twins

**AuthorityEffect:** None.  
**Level:** Level 38 | **Epoch:** Epoch II | **Domain:** Causal Logic  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Structural causal model with exogenous variables U and counterfactual twin graph`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_EXOGENOUS_CONTEXT_DEFECT`  
**Evaluator Module:** `CausalLogicModule` (`Counterfactual Abduction-Action-Prediction Evaluator`)  
**Evaluator Contract:** `CounterfactualAbductionContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CausalLogicModule` or contract `CounterfactualAbductionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 38 establishes the Proposal Fidelity Protocol (PFP) arena for **Counterfactual Structural Equations & Exogenous Twins** within the Causal Logic bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{38} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Structural causal model with exogenous variables U and counterfactual twin graph`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CausalLogicModule` (`CounterfactualAbductionContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Pearl's 3-step counterfactual algorithm (Abduction, Action, Prediction) on structural equations and twin network evaluation.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 38         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `CausalLogicModule` metrics under `CounterfactualAbductionContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_EXOGENOUS_CONTEXT_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 38 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_38_counterfactuals` family schema:

```json
{
  "schema_id": "sg_packet_level_38_counterfactuals",
  "task_data": {
    "level": 38,
    "epoch": "Epoch II",
    "domain": "Causal Logic",
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
    "factual_evidence": {"X": "0", "Y": "0"},
    "exogenous_variables_u": ["U_X", "U_Y"],
    "abducted_posterior_u": {"U_X": "0", "U_Y": "0"},
    "counterfactual_action": {"variable": "X", "value": "1"},
    "predicted_counterfactual_y": "1",
    "twin_network_consistent": true,
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
pub struct CounterfactualAbductionPayload {
    pub move_type: MoveType,
    pub factual_evidence: BTreeMap<String, String>,
    pub exogenous_variables_u: Vec<String>,
    pub abducted_posterior_u: BTreeMap<String, String>,
    pub counterfactual_action: CausalAction,
    pub predicted_counterfactual_y: String,
    pub twin_network_consistent: bool,
    pub proposer_signature: String,
}

pub struct Level38Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: CounterfactualAbductionPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: CausalLogicModule

### Contract: `CounterfactualAbductionContract`

Referees evaluate Level 38 candidates through Pearl's 3-step structural counterfactual algorithm:

1. **Step 1 (Abduction):** Updates exogenous background probability distribution $P(U)$ conditioned on factual evidence $e$:
   $$P(U \mid e) = \frac{P(e \mid U) P(U)}{P(e)}$$
2. **Step 2 (Action):** Replaces structural equations for intervention targets with constant assignments $X := x'$ to form modified sub-model $M_{x'}$.
3. **Step 3 (Prediction):** Computes counterfactual outcome $Y_{x'}(u)$ using modified sub-model $M_{x'}$ under abducted exogenous distribution $P(U \mid e)$:
   $$P(Y_{x'} = y \mid e) = \sum_u P(Y_{x'}(u) = y) P(u \mid e)$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the 3-step abduction-action-prediction trace evaluates consistently and the twin network maintains exogenous identity.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant counterfactual probability bound (such as tight non-trivial intervals $[PN_{\min}, PN_{\max}]$ for Probability of Necessity) is certified invariant without point identification, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 38 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_EXOGENOUS_CONTEXT_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 38, "carrier_match": true, "move": "ASSERT", "factual_evidence": {"X": "0", "Y": "0"}, "abducted_posterior_u": {"U": "0"}, "counterfactual_action": {"variable": "X", "value": "1"}, "predicted_counterfactual_y": "1"}
REFEREE:  ACCEPT -> Status: ExactRepair (counterfactual abduction-action-prediction trace verified on structural causal model)
  ```

  **Reproducibility gap (2026-10-20):** no packet states the structural equations, so abduction and prediction cannot be recomputed. The valid vector also abducts a single variable `U`, while the schema example declares `U_X` and `U_Y`. For illustration only (an assumption, not the file's model): with $X := U_X$ and $Y := X \oplus U_Y$, the evidence $X = 0, Y = 0$ forces $U_X = 0$ and $U_Y = 0$; the action $X := 1$ then gives $Y_{X=1} = 1 \oplus 0 = 1$, matching `predicted_counterfactual_y`. Other models fit the same evidence and give a different prediction (for example $Y := X \wedge U_Y$ gives $U_Y$ undetermined by the evidence and $Y_{X=1} = U_Y$), so the model must be declared in the packet.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 38, "carrier_match": true, "move": "ASSERT", "factual_evidence": {"X": "0", "Y": "0"}, "abducted_posterior_u": {"U": "invalid_unnormalized_u"}, "counterfactual_action": {"variable": "X", "value": "1"}}
REFEREE:  REFUSED -> Refusal Code: ERR_EXOGENOUS_CONTEXT_DEFECT, Status: Refused (abducted exogenous posterior U fails normalization and consistency with factual evidence)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 38, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 38: Counterfactual Structural Equations & Exogenous Twins within the Causal Logic bounded context.
   - A proposed PFP packet envelope, `CausalLogicModule` (`CounterfactualAbductionContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 38 specifies an exact, deterministic evaluation procedure for candidate proposals over `Structural causal model with exogenous variables U and counterfactual twin graph`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
