---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 39: Normal Form Game Strategies & Dominance Elimination"
kind: grammar-reference
level: 39
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
evaluator_contract: "NormalFormStrategyContract"
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

# The Symbol Game Level 39: Normal Form Game Strategies & Dominance Elimination

**AuthorityEffect:** None.  
**Level:** Level 39 | **Epoch:** Epoch II | **Domain:** Game Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Two-player bimatrix game (A, B) with rational mixed strategy profile (p, q)`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_STRATEGY_MAP_DEFECT`  
**Evaluator Module:** `GameTheoryModule` (`Normal Form Game & Iterated Dominance Strategy Evaluator`)  
**Evaluator Contract:** `NormalFormStrategyContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `GameTheoryModule` or contract `NormalFormStrategyContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 39 establishes the Proposal Fidelity Protocol (PFP) arena for **Normal Form Game Strategies & Dominance Elimination** within the Game Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{39} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Two-player bimatrix game (A, B) with rational mixed strategy profile (p, q)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `GameTheoryModule` (`NormalFormStrategyContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Two-player bimatrix game (A, B), iterated elimination of strictly dominated strategies, and rational Nash equilibrium certificates.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 39         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `GameTheoryModule` metrics under `NormalFormStrategyContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_STRATEGY_MAP_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 39 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_39_game_strategies` family schema:

```json
{
  "schema_id": "sg_packet_level_39_game_strategies",
  "task_data": {
    "level": 39,
    "epoch": "Epoch II",
    "domain": "Game Theory",
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
    "payoff_matrix_a": [
      ["3", "0"],
      ["5", "1"]
    ],
    "payoff_matrix_b": [
      ["3", "5"],
      ["0", "1"]
    ],
    "strategy_profile_p": ["0", "1"],
    "strategy_profile_q": ["0", "1"],
    "expected_payoffs": ["1", "1"],
    "best_response_defects": ["0", "0"],
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
pub struct NormalFormStrategyPayload {
    pub move_type: MoveType,
    pub payoff_matrix_a: Vec<Vec<Rational>>,
    pub payoff_matrix_b: Vec<Vec<Rational>>,
    pub strategy_profile_p: Vec<Rational>,
    pub strategy_profile_q: Vec<Rational>,
    pub expected_payoffs: (Rational, Rational),
    pub best_response_defects: (Rational, Rational),
    pub proposer_signature: String,
}

pub struct Level39Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: NormalFormStrategyPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: GameTheoryModule

### Contract: `NormalFormStrategyContract`

Referees evaluate Level 39 candidates through normal form game theory and dominance elimination:

1. **Strategy Simplex Admissibility:** Verifies mixed strategy vectors $p \in \Delta_m(\mathbb{Q}), q \in \Delta_n(\mathbb{Q})$ satisfy:
   $$\sum_{i=1}^m p_i = 1, \quad p_i \ge 0; \qquad \sum_{j=1}^n q_j = 1, \quad q_j \ge 0$$
2. **Iterated Strict Dominance Elimination:** Audits dominance steps where strategy $i$ is eliminated if there exists mixed strategy $\tilde{p}$ such that $(\tilde{p}^T A)_j > (A)_{ij}$ for all active $j$.
3. **Best-Response Defect Calculation:** Computes rational best-response defect distances:
   $$\operatorname{def}_1 = \max_{i} (A q)_i - p^T A q, \qquad \operatorname{def}_2 = \max_{j} (p^T B)_j - p^T B q$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff strategy vectors lie on their respective probability simplices and best-response defects vanish identically ($\operatorname{def}_1 = 0, \operatorname{def}_2 = 0$), certifying a rational Nash equilibrium.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an iterated dominance elimination trace yields a reduced non-trivial sub-game with surviving rationalizable strategy support, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 39 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_STRATEGY_MAP_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 39, "carrier_match": true, "move": "ASSERT", "payoff_matrix_a": [["3", "0"], ["5", "1"]], "payoff_matrix_b": [["3", "5"], ["0", "1"]], "strategy_profile_p": ["0", "1"], "strategy_profile_q": ["0", "1"], "best_response_defects": ["0", "0"]}
REFEREE:  ACCEPT -> Status: ExactRepair (strategy profile verified as rational Nash equilibrium with zero best-response defect)
  ```

  **Worked check (2026-10-20):** with $q = (0, 1)$, $A q = (0, 1)$ and $p^T A q = 1$, so $\operatorname{def}_1 = \max(0, 1) - 1 = 0$. With $p = (0, 1)$, $p^T B = (0, 1)$ and $p^T B q = 1$, so $\operatorname{def}_2 = 1 - 1 = 0$. The payoffs are $(1, 1)$, matching the schema's `expected_payoffs`. Dominance gives the same profile: row 2 strictly dominates row 1 for $A$ ($5 > 3$, $1 > 0$) and column 2 strictly dominates column 1 for $B$ ($5 > 3$, $1 > 0$), so iterated elimination leaves the single profile (row 2, column 2).

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 39, "carrier_match": true, "move": "ASSERT", "payoff_matrix_a": [["3", "0"], ["5", "1"]], "payoff_matrix_b": [["3", "5"], ["0", "1"]], "strategy_profile_p": ["1/2", "3/4"], "strategy_profile_q": ["0", "1"]}
REFEREE:  REFUSED -> Refusal Code: ERR_STRATEGY_MAP_DEFECT, Status: Refused (strategy vector p probability sum 1/2 + 3/4 = 5/4 != 1 violates simplex normalization)
  ```

  **Worked check (2026-10-20):** $1/2 + 3/4 = 5/4 \ne 1$, so $p \notin \Delta_2(\mathbb{Q})$ and the refusal follows.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 39, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 39: Normal Form Game Strategies & Dominance Elimination within the Game Theory bounded context.
   - A proposed PFP packet envelope, `GameTheoryModule` (`NormalFormStrategyContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 39 specifies an exact, deterministic evaluation procedure for candidate proposals over `Two-player bimatrix game (A, B) with rational mixed strategy profile (p, q)`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
