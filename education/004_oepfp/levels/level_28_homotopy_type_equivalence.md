---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 28: Homotopy Type Equivalence Witnesses"
kind: grammar-reference
level: 28
epoch: "Epoch I"
domain: "Homotopy Type Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "HomotopyTypeModule"
evaluator_contract: "HomotopyEquivalenceContract"
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

# The Symbol Game Level 28: Homotopy Type Equivalence Witnesses

**AuthorityEffect:** None.  
**Level:** Level 28 | **Epoch:** Epoch I | **Domain:** Homotopy Type Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Homotopy type equivalence witnesses with quasi-inverses and half-adjoint homotopies`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_EQUIVALENCE_WITNESS_DEFECT`  
**Evaluator Module:** `HomotopyTypeModule` (`Homotopy Type Equivalence & Half-Adjoint Coherence Evaluator`)  
**Evaluator Contract:** `HomotopyEquivalenceContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `HomotopyTypeModule` or contract `HomotopyEquivalenceContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 28 establishes the Proposal Fidelity Protocol (PFP) arena for **Homotopy Type Equivalence Witnesses** within the Homotopy Type Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{28} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Homotopy type equivalence witnesses with quasi-inverses and half-adjoint homotopies`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `HomotopyTypeModule` (`HomotopyEquivalenceContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of map equivalence witnesses f: A ≃ B via quasi-inverses, homotopies, and half-adjoint coherence.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 28         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `HomotopyTypeModule` metrics under `HomotopyEquivalenceContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_EQUIVALENCE_WITNESS_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 28 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_28_homotopy_type_equivalence` family schema:

```json
{
  "schema_id": "sg_packet_level_28_homotopy_type_equivalence",
  "task_data": {
    "level": 28,
    "epoch": "Epoch I",
    "domain": "Homotopy Type Theory",
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
    "type_a": "TypeA",
    "type_b": "TypeB",
    "forward_map_f": "f: TypeA -> TypeB",
    "quasi_inverse_g": "g: TypeB -> TypeA",
    "left_homotopy_eta": "eta: g o f ~ id_A",
    "right_homotopy_epsilon": "epsilon: f o g ~ id_B",
    "half_adjoint_witness": "tau: f o eta ~ epsilon o f",
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
pub struct HomotopyEquivalencePayload {
    pub move_type: MoveType,
    pub type_a: String,
    pub type_b: String,
    pub forward_map_f: String,
    pub quasi_inverse_g: String,
    pub left_homotopy_eta: String,
    pub right_homotopy_epsilon: String,
    pub half_adjoint_witness: String,
    pub proposer_signature: String,
}

pub struct Level28Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: HomotopyEquivalencePayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: HomotopyTypeModule

### Contract: `HomotopyEquivalenceContract`

Referees evaluate Level 28 candidates through Voevodsky-style homotopy type equivalence definitions:

1. **Quasi-Inverse Verification:** Given map $f\colon A \to B$, evaluates candidate inverse $g\colon B \to A$.
2. **Homotopy Inversion Cells:** Audits homotopy proof terms establishing left and right inversion:
   $$\eta\colon g \circ f \sim \mathrm{id}_A, \quad \epsilon\colon f \circ g \sim \mathrm{id}_B$$
3. **Half-Adjoint Coherence Condition:** Audits the 2-homotopy witness ensuring the equivalence forms a lawful proposition $\mathrm{isequiv}(f)$:
   $$\tau(a)\colon \mathrm{ap}_f(\eta(a)) = \epsilon(f(a)) \quad \text{in the type } \big(f(g(f(a))) =_B f(a)\big)$$
   *(Corrected 2026-10-20: the earlier subscript $=_{f(g(f(a)))}$ named an element, not a type. Both sides are paths from $f(g(f(a)))$ to $f(a)$ in $B$; $\tau$ is a 2-path between them. Quasi-inverse data $(g, \eta, \epsilon)$ already determine an equivalence, since $\epsilon$ can be adjusted to satisfy this condition; the condition is required because the half-adjoint data type $\mathrm{ishae}(f)$ is a proposition, while the quasi-inverse data type is not one in general.)*
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the candidate equivalence witness satisfies quasi-inverse homotopies $\eta, \epsilon$ and half-adjoint identity $\tau$ identically.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a certified non-contractible homotopy equivalence class between distinct discrete carriers is recorded with zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 28 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_EQUIVALENCE_WITNESS_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 28, "carrier_match": true, "move": "ASSERT", "forward_map_f": "f", "quasi_inverse_g": "g", "left_homotopy_eta": "eta", "right_homotopy_epsilon": "epsilon", "half_adjoint_witness": "tau"}
REFEREE:  ACCEPT -> Status: ExactRepair (homotopy equivalence witness certified with quasi-inverse and half-adjoint coherence)
  ```

  **Reproducibility gap (2026-10-20):** `f`, `g`, `eta`, `epsilon` and `tau` are names only. The packet gives no types, no map definitions and no proof terms, so a referee cannot check $\eta$, $\epsilon$ or $\tau$; the same gap applies to the negative vector, whose refusal rests on the label `defective_homotopy_g_f_ne_id`.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 28, "carrier_match": true, "move": "ASSERT", "forward_map_f": "f", "quasi_inverse_g": "g", "left_homotopy_eta": "defective_homotopy_g_f_ne_id", "right_homotopy_epsilon": "epsilon"}
REFEREE:  REFUSED -> Refusal Code: ERR_EQUIVALENCE_WITNESS_DEFECT, Status: Refused (left homotopy fails to establish identity equivalence g o f ~ id_A)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 28, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 28: Homotopy Type Equivalence Witnesses within the Homotopy Type Theory bounded context.
   - A proposed PFP packet envelope, `HomotopyTypeModule` (`HomotopyEquivalenceContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 28 specifies an exact, deterministic evaluation procedure for candidate proposals over `Homotopy type equivalence witnesses with quasi-inverses and half-adjoint homotopies`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
