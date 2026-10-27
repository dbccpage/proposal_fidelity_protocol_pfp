---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 36: Bayesian Likelihood Updates & Evidence Ratio"
kind: grammar-reference
level: 36
epoch: "Epoch II"
domain: "Bayesian Statistics"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "BayesianUpdateModule"
evaluator_contract: "BayesianLikelihoodContract"
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

# The Symbol Game Level 36: Bayesian Likelihood Updates & Evidence Ratio

**AuthorityEffect:** None.  
**Level:** Level 36 | **Epoch:** Epoch II | **Domain:** Bayesian Statistics  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Prior distribution P(H), likelihood matrix P(E|H), and posterior P(H|E)`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_LIKELIHOOD_DEFECT`  
**Evaluator Module:** `BayesianUpdateModule` (`Bayesian Likelihood Update & Marginal Evidence Evaluator`)  
**Evaluator Contract:** `BayesianLikelihoodContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `BayesianUpdateModule` or contract `BayesianLikelihoodContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 36 establishes the Proposal Fidelity Protocol (PFP) arena for **Bayesian Likelihood Updates & Evidence Ratio** within the Bayesian Statistics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{36} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Prior distribution P(H), likelihood matrix P(E|H), and posterior P(H|E)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `BayesianUpdateModule` (`BayesianLikelihoodContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact rational Bayes updates P(H_i|E) = P(E|H_i)P(H_i) / P(E) with typed refusal on zero evidence.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 36         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `BayesianUpdateModule` metrics under `BayesianLikelihoodContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_LIKELIHOOD_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 36 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_36_bayesian_updates` family schema:

```json
{
  "schema_id": "sg_packet_level_36_bayesian_updates",
  "task_data": {
    "level": 36,
    "epoch": "Epoch II",
    "domain": "Bayesian Statistics",
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
    "prior_distribution": ["1/3", "2/3"],
    "likelihood_matrix": [
      ["9/10", "1/10"],
      ["1/10", "9/10"]
    ],
    "observed_evidence_index": 0,
    "marginal_evidence": "11/30",
    "candidate_posterior": ["9/11", "2/11"],
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
pub struct BayesianLikelihoodPayload {
    pub move_type: MoveType,
    pub prior_distribution: Vec<Rational>,
    pub likelihood_matrix: Vec<Vec<Rational>>,
    pub observed_evidence_index: u32,
    pub marginal_evidence: Rational,
    pub candidate_posterior: Vec<Rational>,
    pub proposer_signature: String,
}

pub struct Level36Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: BayesianLikelihoodPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: BayesianUpdateModule

### Contract: `BayesianLikelihoodContract`

Referees evaluate Level 36 candidates through exact rational Bayesian inversion:

1. **Prior & Likelihood Admissibility:** Verifies prior $\sum P(H_i) = 1$ ($P(H_i) \ge 0$) and likelihood matrix entries $0 \le P(E_j | H_i) \le 1$ with $\sum_j P(E_j | H_i) = 1$ for all hypotheses $H_i$.
2. **Marginal Evidence Normalization:** Computes total evidence probability:
   $$P(E) = \sum_{i=1}^k P(E | H_i) P(H_i)$$
   If $P(E) = 0$, immediate typed refusal `REFUSED_ZERO_EVIDENCE` is triggered without division by zero.
3. **Posterior Rational Inversion:** Audits candidate posterior distribution against Bayes' theorem:
   $$P(H_i | E) = \frac{P(E | H_i) P(H_i)}{P(E)}$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff marginal evidence $P(E) > 0$ and the candidate posterior satisfies Bayes' formula identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant conjugate prior family or uninformative reference prior profile is certified stable under repeated updates, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 36 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_LIKELIHOOD_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 36, "carrier_match": true, "move": "ASSERT", "prior_distribution": ["1/3", "2/3"], "likelihood_matrix": [["9/10", "1/10"], ["1/10", "9/10"]], "observed_evidence_index": 0, "marginal_evidence": "11/30", "candidate_posterior": ["9/11", "2/11"]}
REFEREE:  ACCEPT -> Status: ExactRepair (Bayesian posterior update matches likelihood ratio and marginal evidence over Q)
  ```

  **Worked check (2026-10-20):** row $i$ of the likelihood matrix is $P(E_j \mid H_i)$, and each row sums to 1. For evidence index 0: $P(E) = \tfrac{9}{10} \cdot \tfrac13 + \tfrac{1}{10} \cdot \tfrac23 = \tfrac{9}{30} + \tfrac{2}{30} = \tfrac{11}{30}$. Posterior: $P(H_1 \mid E) = \tfrac{9/30}{11/30} = \tfrac{9}{11}$ and $P(H_2 \mid E) = \tfrac{2/30}{11/30} = \tfrac{2}{11}$, which sum to 1 and match the packet.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 36, "carrier_match": true, "move": "ASSERT", "prior_distribution": ["1/3", "2/3"], "likelihood_matrix": [["11/10", "1/10"], ["1/10", "9/10"]], "observed_evidence_index": 0}
REFEREE:  REFUSED -> Refusal Code: ERR_LIKELIHOOD_DEFECT, Status: Refused (likelihood matrix entry 11/10 exceeds probability bound 1)
  ```

  **Worked check (2026-10-20):** $11/10 > 1$, and row 0 also sums to $11/10 + 1/10 = 6/5 \ne 1$; either check refuses the packet.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 36, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 36: Bayesian Likelihood Updates & Evidence Ratio within the Bayesian Statistics bounded context.
   - A proposed PFP packet envelope, `BayesianUpdateModule` (`BayesianLikelihoodContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 36 specifies an exact, deterministic evaluation procedure for candidate proposals over `Prior distribution P(H), likelihood matrix P(E|H), and posterior P(H|E)`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
