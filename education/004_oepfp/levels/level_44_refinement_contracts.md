---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 44: Liquid Refinement Types & Hoare Predicates"
kind: grammar-reference
level: 44
epoch: "Epoch III"
domain: "Formal Methods"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "RefinementContractModule"
evaluator_contract: "LiquidRefinementTypeContract"
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

# The Symbol Game Level 44: Liquid Refinement Types & Hoare Predicates

**AuthorityEffect:** None.  
**Level:** Level 44 | **Epoch:** Epoch III | **Domain:** Formal Methods  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Refinement type judgments Γ ⊢ t : {v: T | Φ(v)} with decidable SMT verification conditions`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_PREDICATE_REFINEMENT_DEFECT`  
**Evaluator Module:** `RefinementContractModule` (`Liquid Refinement Type & Hoare Verification Condition Evaluator`)  
**Evaluator Contract:** `LiquidRefinementTypeContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `RefinementContractModule` or contract `LiquidRefinementTypeContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 44 establishes the Proposal Fidelity Protocol (PFP) arena for **Liquid Refinement Types & Hoare Predicates** within the Formal Methods bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{44} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Refinement type judgments Γ ⊢ t : {v: T | Φ(v)} with decidable SMT verification conditions`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `RefinementContractModule` (`LiquidRefinementTypeContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verification of refinement predicates {v: T | Φ(v)}, preconditions, postconditions, and decidable verification conditions.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 44         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `RefinementContractModule` metrics under `LiquidRefinementTypeContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_PREDICATE_REFINEMENT_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 44 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_44_refinement_contracts` family schema:

```json
{
  "schema_id": "sg_packet_level_44_refinement_contracts",
  "task_data": {
    "level": 44,
    "epoch": "Epoch III",
    "domain": "Formal Methods",
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
    "typed_term": "div(x, y)",
    "typing_environment": {"x": "Int", "y": "{v: Int | v != 0}"},
    "precondition_p": "y != 0",
    "postcondition_q": "{v: Int | v == x / y}",
    "verification_condition_proof": "valid_qflia_vc",
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
pub struct RefinementContractPayload {
    pub move_type: MoveType,
    pub typed_term: String,
    pub typing_environment: BTreeMap<String, String>,
    pub precondition_p: String,
    pub postcondition_q: String,
    pub verification_condition_proof: String,
    pub proposer_signature: String,
}

pub struct Level44Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: RefinementContractPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: RefinementContractModule

### Contract: `LiquidRefinementTypeContract`

Referees evaluate Level 44 candidates through decidable liquid refinement type checking:

1. **Typing Judgment & Refinement Invariants:** Evaluates judgment $\Gamma \vdash t\colon \{v\colon B \mid \Phi(v)\}$, verifying base type $B$ and refinement formula $\Phi(v)$.
2. **Verification Condition (VC) Validity:** Evaluates verification conditions in quantifier-free linear integer arithmetic (QFLIA):
   $$\Gamma \wedge P \implies Q$$
3. **Subtyping Refinement Implication:** Subtyping $t_1 <: t_2$ is verified by asserting logical implication between refinement predicates $\Phi_1(v) \implies \Phi_2(v)$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the term satisfies the base typing and the SMT verification condition discharges with zero residual defect.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an inductive loop invariant in a recursive function refinement is certified valid under SMT solver bounds, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 44 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_PREDICATE_REFINEMENT_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 44, "carrier_match": true, "move": "ASSERT", "typed_term": "abs(x)", "typing_environment": {"x": "Int"}, "postcondition_q": "{v: Int | v >= 0}", "verification_condition_proof": "valid_vc"}
REFEREE:  ACCEPT -> Status: ExactRepair (refinement typing judgment and Hoare postcondition verified)
  ```

  **Worked check (2026-10-20):** with $\mathrm{abs}(x) = \text{if } x \ge 0 \text{ then } x \text{ else } -x$, the VC is $(x \ge 0 \Rightarrow x \ge 0) \wedge (x < 0 \Rightarrow -x \ge 0)$, which is valid in QF-LIA. In the negative vector, $\mathrm{dec}(x) = x - 1$ under $x > 0$ gives the VC $x > 0 \Rightarrow x - 1 > 0$, falsified by $x = 1$ ($v = 0$), so the refusal follows.

  **Correction (2026-10-20):** the Section 3 schema example's postcondition `v == x / y` with a variable divisor `y` is outside quantifier-free linear integer arithmetic; division by a non-constant term is non-linear. That VC needs QF-NIA or an encoding of division as an uninterpreted function with axioms, not the QF-LIA fragment stated in Section 4.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 44, "carrier_match": true, "move": "ASSERT", "typed_term": "dec(x)", "typing_environment": {"x": "{v: Int | v > 0}"}, "postcondition_q": "{v: Int | v > 0}", "verification_condition_proof": "counterexample: x=1 => v=0"}
REFEREE:  REFUSED -> Refusal Code: ERR_PREDICATE_REFINEMENT_DEFECT, Status: Refused (term return value v=0 violates postcondition refinement v > 0)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 44, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 44: Liquid Refinement Types & Hoare Predicates within the Formal Methods bounded context.
   - A proposed PFP packet envelope, `RefinementContractModule` (`LiquidRefinementTypeContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 44 specifies an exact, deterministic evaluation procedure for candidate proposals over `Refinement type judgments Γ ⊢ t : {v: T | Φ(v)} with decidable SMT verification conditions`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
