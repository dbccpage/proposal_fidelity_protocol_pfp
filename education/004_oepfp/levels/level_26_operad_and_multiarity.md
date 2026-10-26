---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 26: Coloured Operads & Multiarity Tree Composition"
kind: grammar-reference
level: 26
epoch: "Epoch I"
domain: "Operad Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "OperadModule"
evaluator_contract: "OperadCompositionContract"
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

# The Symbol Game Level 26: Coloured Operads & Multiarity Tree Composition

**AuthorityEffect:** None.  
**Level:** Level 26 | **Epoch:** Epoch I | **Domain:** Operad Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Coloured operad P with multi-input single-output operations P(c₁,...,c_k; c)`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_OPERATION_ARITY_DEFECT`  
**Evaluator Module:** `OperadModule` (`Coloured Operad Tree Composition & Arity Evaluator`)  
**Evaluator Contract:** `OperadCompositionContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `OperadModule` or contract `OperadCompositionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 26 establishes the Proposal Fidelity Protocol (PFP) arena for **Coloured Operads & Multiarity Tree Composition** within the Operad Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{26} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Coloured operad P with multi-input single-output operations P(c₁,...,c_k; c)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `OperadModule` (`OperadCompositionContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Evaluation of multi-input operation profiles P(c₁,...,c_k; c), partial tree compositions ∘_i, and operadic associativity.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 26         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `OperadModule` metrics under `OperadCompositionContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_OPERATION_ARITY_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 26 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_26_operad_and_multiarity` family schema:

```json
{
  "schema_id": "sg_packet_level_26_operad_and_multiarity",
  "task_data": {
    "level": 26,
    "epoch": "Epoch I",
    "domain": "Operad Theory",
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
    "colors": ["Task", "Audit", "Receipt"],
    "operation_profile": {
      "inputs": ["Task", "Audit"],
      "output": "Receipt",
      "arity": 2,
      "operation_name": "theta"
    },
    "tree_substitution": {
      "parent_op": "theta",
      "target_slot": 1,
      "sub_op": "phi",
      "sub_op_profile": {"inputs": ["Code"], "output": "Task"}
    },
    "associativity_witness": "valid_tree_associativity",
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
pub struct OperadCompositionPayload {
    pub move_type: MoveType,
    pub colors: Vec<String>,
    pub operation_profile: OperationProfile,
    pub tree_substitution: TreeSubstitution,
    pub associativity_witness: String,
    pub proposer_signature: String,
}

pub struct Level26Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: OperadCompositionPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: OperadModule

### Contract: `OperadCompositionContract`

Referees evaluate Level 26 candidates through coloured operad tree composition axioms:

1. **Colour-Profile Matching:** Verifies operation $\theta \in \mathcal{P}(c_1, \ldots, c_k; c)$ and partial composition $\theta \circ_i \psi$ matching the $i$-th input colour of $\theta$ to the output colour of $\psi$:
   $$\mathrm{target}(\psi) = c_i$$
2. **Arity Bounds & Boundary Checks:** Asserts $1 \le i \le k$ for operation $\theta$ of arity $k$.
3. **Operadic Associativity Axioms:** Audits nested and parallel substitutions:
   $$(\theta \circ_i \psi) \circ_{i+j-1} \phi = \theta \circ_i (\psi \circ_j \phi)$$
   $$(\theta \circ_i \psi) \circ_{j+m-1} \phi = (\theta \circ_j \phi) \circ_i \psi \quad (i < j)$$
   Here $m$ is the arity of $\psi$ and, in the first law, $1 \le j \le m$. *(Clarified 2026-10-20: the file used $m$ without defining it.)*
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff all tree substitution nodes strictly match input/output colors, substitution slot indices are within arity bounds, and operadic associativity relations hold identically.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant coloured operad algebra profile (such as a 10-colour non-symmetric operad routing algebra) is certified non-contractible under tree substitutions, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 26 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_OPERATION_ARITY_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 26, "carrier_match": true, "move": "ASSERT", "operation_profile": {"inputs": ["Task", "Audit"], "output": "Receipt", "arity": 2}, "tree_substitution": {"target_slot": 1, "sub_op_output": "Task"}}
REFEREE:  ACCEPT -> Status: ExactRepair (tree substitution slot 1 matches input colour 'Task' and arity bounds)
  ```

  **Worked check (2026-10-20):** $\theta \in \mathcal{P}(\mathrm{Task}, \mathrm{Audit}; \mathrm{Receipt})$ has arity $k = 2$. Slot $i = 1$ satisfies $1 \le i \le 2$, and the input colour at slot 1 is `Task`, which equals the output colour of the substituted operation. With the schema example's $\varphi \in \mathcal{P}(\mathrm{Code}; \mathrm{Task})$, the composite is $\theta \circ_1 \varphi \in \mathcal{P}(\mathrm{Code}, \mathrm{Audit}; \mathrm{Receipt})$, of arity $2 + 1 - 1 = 2$. The schema example's `colors` list (`Task`, `Audit`, `Receipt`) omits `Code`, so a colour check against that list would reject the substitution; the list needs `Code` added.

  **Reproducibility gap (2026-10-20):** the valid vector gives only `sub_op_output`, not the input profile of the substituted operation, so the composite profile cannot be computed from that packet alone.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 26, "carrier_match": true, "move": "ASSERT", "operation_profile": {"inputs": ["Task", "Audit"], "output": "Receipt", "arity": 2}, "tree_substitution": {"target_slot": 3, "sub_op_output": "Task"}}
REFEREE:  REFUSED -> Refusal Code: ERR_OPERATION_ARITY_DEFECT, Status: Refused (tree substitution slot index 3 exceeds operation arity 2)
  ```

  **Worked check (2026-10-20):** the slot bound is $1 \le i \le k = 2$; $i = 3$ violates it, so the refusal follows from the data.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 26, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 26: Coloured Operads & Multiarity Tree Composition within the Operad Theory bounded context.
   - A proposed PFP packet envelope, `OperadModule` (`OperadCompositionContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 26 specifies an exact, deterministic evaluation procedure for candidate proposals over `Coloured operad P with multi-input single-output operations P(c₁,...,c_k; c)`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
