---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 22: Fibred Dependent Contexts & Reindexing Functors"
kind: grammar-reference
level: 22
epoch: "Epoch I"
domain: "Fibration Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "CategoryLimitsModule"
evaluator_contract: "FibredContextContract"
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

# The Symbol Game Level 22: Fibred Dependent Contexts & Reindexing Functors

**AuthorityEffect:** None.  
**Level:** Level 22 | **Epoch:** Epoch I | **Domain:** Fibration Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Grothendieck fibration p: E → B with cartesian lifts and cleavage`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `REFUSED_FIBER_MISMATCH`  
**Evaluator Module:** `CategoryLimitsModule` (`Grothendieck Fibration & Cartesian Lift Evaluator`)  
**Evaluator Contract:** `FibredContextContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CategoryLimitsModule` or contract `FibredContextContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 22 establishes the Proposal Fidelity Protocol (PFP) arena for **Fibred Dependent Contexts & Reindexing Functors** within the Fibration Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{22} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Grothendieck fibration p: E → B with cartesian lifts and cleavage`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CategoryLimitsModule` (`FibredContextContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of cartesian lift arrows over base morphisms and cleavage functoriality across dependent contexts.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 22         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `CategoryLimitsModule` metrics under `FibredContextContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `REFUSED_FIBER_MISMATCH`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 22 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_22_fibred_dependent_contexts` family schema:

```json
{
  "schema_id": "sg_packet_level_22_fibred_dependent_contexts",
  "task_data": {
    "level": 22,
    "epoch": "Epoch I",
    "domain": "Fibration Theory",
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
    "base_morphism_f": {"source": "b_prime", "target": "b", "name": "f"},
    "target_object_e": {"fiber": "b", "name": "e"},
    "cartesian_lift_arrow": {"source": "e_prime", "target": "e", "projected_arrow": "f"},
    "lift_domain_fiber": "b_prime",
    "universal_factorization_witness": "unique_u",
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
pub struct FibredContextPayload {
    pub move_type: MoveType,
    pub base_morphism_f: MorphismId,
    pub target_object_e: ObjectId,
    pub cartesian_lift_arrow: LiftArrow,
    pub lift_domain_fiber: ObjectId,
    pub universal_factorization_witness: String,
    pub proposer_signature: String,
}

pub struct Level22Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: FibredContextPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: CategoryLimitsModule

### Contract: `FibredContextContract`

Referees evaluate Level 22 candidates through Grothendieck fibration axioms and cartesian arrow properties:

1. **Projection Fiber Matching:** Given base arrow $f\colon b' \to b$ and total object $e \in E_b$, verifies candidate cartesian arrow $\bar{f}\colon e' \to e$ projects strictly to $f$:
   $$p(\bar{f}) = f, \quad p(e') = b'$$
2. **Universal Cartesian Factorization:** For any arrow $g\colon e'' \to e$ in $E$ and base factorization $p(g) = f \circ h$, evaluates the existence and uniqueness of mediation $u\colon e'' \to e'$ over $h$:
   $$\bar{f} \circ u = g, \quad p(u) = h$$
3. **Cleavage Functoriality:** Audits horizontal reindexing $f^*\colon E_b \to E_{b'}$ verifying canonical isomorphism $(g \circ f)^* \cong f^* \circ g^*$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff $p(\bar{f}) = f$ identically and candidate universal arrow $u$ uniquely factorizes test arrows without fiber mismatch.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an authorized non-split fibration cleavage carries a certified non-trivial curvature/holonomy 2-cocycle in the base that cannot be strictly split, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 22 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `REFUSED_FIBER_MISMATCH`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 22, "carrier_match": true, "move": "ASSERT", "base_morphism_f": "f: b' -> b", "cartesian_lift_arrow": {"source": "e'", "target": "e", "projected_arrow": "f"}, "lift_domain_fiber": "b'"}
REFEREE:  ACCEPT -> Status: ExactRepair (cartesian lift arrow verified over base morphism)
  ```

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 22, "carrier_match": true, "move": "ASSERT", "base_morphism_f": "f: b' -> b", "cartesian_lift_arrow": {"source": "e'", "target": "e", "projected_arrow": "f_other"}, "lift_domain_fiber": "b_prime_mismatch"}
REFEREE:  REFUSED -> Refusal Code: REFUSED_FIBER_MISMATCH, Status: Refused (lift arrow projection does not match declared base morphism)
  ```

  **Reproducibility gap (2026-10-20):** The packets check only the labels `p(f_bar) = f` and `p(e') = b'`. No total category, test arrow `g` or base factorization `h` is supplied, so the cartesian (unique factorization) property in Section 4 item 2 is not exercised. A complete vector needs finite categories `E` and `B`, the functor `p` and at least one test arrow with its mediating map.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 22, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 22: Fibred Dependent Contexts & Reindexing Functors within the Fibration Theory bounded context.
   - A proposed PFP packet envelope, `CategoryLimitsModule` (`FibredContextContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 22 specifies an exact, deterministic evaluation procedure for candidate proposals over `Grothendieck fibration p: E → B with cartesian lifts and cleavage`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
