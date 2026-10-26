---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 40: Zero-Sum Minimax Certificates & Equilibrium Duality"
kind: grammar-reference
level: 40
epoch: "Epoch II"
domain: "Game Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "GameTheoryModule"
evaluator_contract: "ZeroSumMinimaxContract"
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

# The Symbol Game Level 40: Zero-Sum Minimax Certificates & Equilibrium Duality

**AuthorityEffect:** None.  
**Level:** Level 40 | **Epoch:** Epoch II | **Domain:** Game Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Finite two-player zero-sum matrix games A with rational minimax duality gap`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_BEST_RESPONSE_DEFECT`  
**Evaluator Module:** `GameTheoryModule` (`Two-Player Zero-Sum Minimax & Duality Gap Evaluator`)  
**Evaluator Contract:** `ZeroSumMinimaxContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `GameTheoryModule` or contract `ZeroSumMinimaxContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 40 establishes the Proposal Fidelity Protocol (PFP) arena for **Zero-Sum Minimax Certificates & Equilibrium Duality** within the Game Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{40} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Finite two-player zero-sum matrix games A with rational minimax duality gap`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `GameTheoryModule` (`ZeroSumMinimaxContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact rational duality certificates confirming minimax optimality in finite two-player zero-sum games.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 40         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `GameTheoryModule` metrics under `ZeroSumMinimaxContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_BEST_RESPONSE_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 40 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_40_equilibrium_evidence` family schema:

```json
{
  "schema_id": "sg_packet_level_40_equilibrium_evidence",
  "task_data": {
    "level": 40,
    "epoch": "Epoch II",
    "domain": "Game Theory",
    "carrier_digest": "blake3:b8d4e9..."
  },
  "protected_boundary": {
    "immutable_slots": ["carrier", "fuel_ceiling", "zero_relation_fences"],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "payoff_matrix_a": [
      ["1", "-1"],
      ["-1", "1"]
    ],
    "strategy_profile_p": ["1/2", "1/2"],
    "strategy_profile_q": ["1/2", "1/2"],
    "claimed_game_value": "0",
    "duality_gap": "0",
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
pub struct ZeroSumMinimaxPayload {
    pub move_type: MoveType,
    pub payoff_matrix_a: Vec<Vec<Rational>>,
    pub strategy_profile_p: Vec<Rational>,
    pub strategy_profile_q: Vec<Rational>,
    pub claimed_game_value: Rational,
    pub duality_gap: Rational,
    pub proposer_signature: String,
}

pub struct Level40Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: ZeroSumMinimaxPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: GameTheoryModule

### Contract: `ZeroSumMinimaxContract`

Referees evaluate Level 40 candidates through finite two-player zero-sum game minimax duality (von Neumann):

1. **Strategy Simplex Validation:** Asserts mixed strategies $p \in \Delta_m(\mathbb{Q}), q \in \Delta_n(\mathbb{Q})$ satisfy:
   $$\sum_{i=1}^m p_i = 1, \quad p_i \ge 0; \qquad \sum_{j=1}^n q_j = 1, \quad q_j \ge 0$$
2. **Minimax Duality Gap Calculation:** Computes the best-response payoff bounds against payoff matrix $A \in \mathbb{Q}^{m \times n}$:
   $$\underline{v}(p) = \min_{j} (p^T A)_j, \qquad \overline{v}(q) = \max_{i} (A q)_i$$
   The exact rational duality gap is:
   $$\Delta(p, q) = \overline{v}(q) - \underline{v}(p) \ge 0$$
3. **Equilibrium Certification:** By von Neumann's minimax theorem, $(p^*, q^*)$ is an optimal minimax equilibrium iff $\Delta(p^*, q^*) = 0$, certifying game value $v = \underline{v}(p^*) = \overline{v}(q^*)$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff strategy vectors lie on their respective rational simplices and the duality gap vanishes identically ($\Delta = 0$).
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an optimal mixed strategy support in a non-strictly determined matrix game (such as Matching Pennies with $v=0$) is certified stable under referee perturbations, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 40 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_BEST_RESPONSE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 40, "carrier_match": true, "move": "ASSERT", "payoff_matrix_a": [["1", "-1"], ["-1", "1"]], "strategy_profile_p": ["1/2", "1/2"], "strategy_profile_q": ["1/2", "1/2"], "duality_gap": "0"}
REFEREE:  ACCEPT -> Status: ExactRepair (zero-sum minimax strategy profile verified with zero duality gap)
  ```

  **Worked check (2026-10-20):** with $p = q = (1/2, 1/2)$, $p^T A = (0, 0)$ and $A q = (0, 0)$, so $\underline{v}(p) = 0$, $\overline{v}(q) = 0$ and $\Delta = 0$; the game value is $0$, matching `claimed_game_value`.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 40, "carrier_match": true, "move": "ASSERT", "payoff_matrix_a": [["1", "-1"], ["-1", "1"]], "strategy_profile_p": ["1", "0"], "strategy_profile_q": ["1/2", "1/2"], "duality_gap": "1"}
REFEREE:  REFUSED -> Refusal Code: ERR_BEST_RESPONSE_DEFECT, Status: Refused (strategy p=(1,0) yields duality gap 1 > 0 against matching pennies)
  ```

  **Worked check (2026-10-20):** $p^T A = (1, -1)$, so $\underline{v}(p) = -1$; $A q = (0, 0)$, so $\overline{v}(q) = 0$. Then $\Delta = 0 - (-1) = 1 > 0$, matching the packet's `duality_gap`.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 40, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 40: Zero-Sum Minimax Certificates & Equilibrium Duality within the Game Theory bounded context.
   - A proposed PFP packet envelope, `GameTheoryModule` (`ZeroSumMinimaxContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 40 specifies an exact, deterministic evaluation procedure for candidate proposals over `Finite two-player zero-sum matrix games A with rational minimax duality gap`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
