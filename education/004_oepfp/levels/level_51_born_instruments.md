---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 51: Born Rule Projective Measurement Instruments"
kind: grammar-reference
level: 51
epoch: "Epoch IV"
domain: "Measurement Theory"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "QuantumFoundationsModule"
evaluator_contract: "ProjectiveMeasurementContract"
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

# The Symbol Game Level 51: Born Rule Projective Measurement Instruments

**AuthorityEffect:** None.  
**Level:** Level 51 | **Epoch:** Epoch IV | **Domain:** Measurement Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Projective measurement instruments {P_k} over Q(i) with exact rational branch probabilities p_k`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_PROJECTOR_FAMILY_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Projective Measurement & Born Rule Probability Evaluator`)  
**Evaluator Contract:** `ProjectiveMeasurementContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `ProjectiveMeasurementContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 51 establishes the Proposal Fidelity Protocol (PFP) arena for **Born Rule Projective Measurement Instruments** within the Measurement Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{51} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Projective measurement instruments {P_k} over Q(i) with exact rational branch probabilities p_k`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`ProjectiveMeasurementContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Projector completeness sum P_k = I, unnormalized post-measurement branches, and exact rational Born probabilities p_k in Q.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 51         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `ProjectiveMeasurementContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_PROJECTOR_FAMILY_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 51 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_51_born_instruments` family schema:

```json
{
  "schema_id": "sg_packet_level_51_born_instruments",
  "task_data": {
    "level": 51,
    "epoch": "Epoch IV",
    "domain": "Measurement Theory",
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
    "projector_family": [
      [[{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}], [{"real": "0", "imag": "0"}, {"real": "0", "imag": "0"}]],
      [[{"real": "0", "imag": "0"}, {"real": "0", "imag": "0"}], [{"real": "0", "imag": "0"}, {"real": "1", "imag": "0"}]]
    ],
    "input_state": [{"real": "3/5", "imag": "0"}, {"real": "4/5", "imag": "0"}],
    "unnormalized_branches": [
      [{"real": "3/5", "imag": "0"}, {"real": "0", "imag": "0"}],
      [{"real": "0", "imag": "0"}, {"real": "4/5", "imag": "0"}]
    ],
    "branch_probabilities": ["9/25", "16/25"],
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
pub struct ProjectiveMeasurementPayload {
    pub move_type: MoveType,
    pub projector_family: Vec<[[ComplexRational; 2]; 2]>,
    pub input_state: Vec<ComplexRational>,
    pub unnormalized_branches: Vec<Vec<ComplexRational>>,
    pub branch_probabilities: Vec<Rational>,
    pub proposer_signature: String,
}

pub struct Level51Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: ProjectiveMeasurementPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `ProjectiveMeasurementContract`

Referees evaluate Level 51 candidates through projective measurement and exact Born probabilities:

1. **Orthogonal Projector Family:** Evaluates projectors $P_k = P_k^\dagger = P_k^2$ with mutual orthogonality $P_j P_k = \delta_{jk} P_k$ and completeness:
   $$\sum_k P_k = I$$
2. **Unnormalized Branches & Rational Weights:** For state $|\psi\rangle$, stores unnormalized post-measurement branches $|\phi_k\rangle = P_k |\psi\rangle$ and computes exact rational weights:
   $$p_k = \langle \psi | P_k | \psi \rangle = \|\phi_k\|^2 \in \mathbb{Q}$$
   This representation avoids out-of-field square roots ($1/\sqrt{p_k}$) while preserving exact state evolution.
3. **Total Probability Conservation:** Asserts $\sum_k p_k = 1$ over $\mathbb{Q}$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff projectors satisfy idempotence, Hermiticity, completeness, and branch probabilities match squared branch norms identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an uncollapsed projection onto a degenerate subspace ($\operatorname{Tr}(P_k) > 1$) is certified as an invariant subspace survivor, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 51 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_PROJECTOR_FAMILY_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 51, "carrier_match": true, "move": "ASSERT", "branch_probabilities": ["9/25", "16/25"], "unnormalized_branches": [[{"real": "3/5", "imag": "0"}, {"real": "0", "imag": "0"}], [{"real": "0", "imag": "0"}, {"real": "4/5", "imag": "0"}]]}
REFEREE:  ACCEPT -> Status: ExactRepair (projective measurement instrument satisfies completeness and exact rational Born probabilities)
  ```

  **Worked check (2026-10-20):** with the section 3 data P_1 = diag(1, 0), P_2 = diag(0, 1) and ψ = (3/5, 4/5), the branches are P_1 ψ = (3/5, 0) and P_2 ψ = (0, 4/5). Their squared norms are p_1 = 9/25 and p_2 = 16/25, and p_1 + p_2 = 25/25 = 1.

  **Reproducibility gap (2026-10-20):** this proposal omits `projector_family` and `input_state`, so the referee cannot recompute the branches from the packet alone.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 51, "carrier_match": true, "move": "ASSERT", "projector_family": [[[{"real": "1", "imag": "0"}, {"real": "0", "imag": "0"}], [{"real": "0", "imag": "0"}, {"real": "1", "imag": "0"}]]]}
REFEREE:  REFUSED -> Refusal Code: ERR_PROJECTOR_FAMILY_DEFECT, Status: Refused (specified refusal; the stated contract does not exclude the one-outcome family {I}, see the worked check below)
  ```

  **Worked check (2026-10-20):** the refusal does not follow from the contract in section 4. The one-element family {I} satisfies P = P† = P², completeness (the sum is I) and orthogonality (vacuous for one element); it is the trivial one-outcome measurement. A refusal needs a rule the contract does not state, such as "at least two outcomes". A family that does violate the stated contract is {diag(1, 0), I}: its sum is diag(2, 1) ≠ I, and diag(1, 0) · I = diag(1, 0) ≠ 0 breaks orthogonality.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 51, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 51: Born Rule Projective Measurement Instruments within the Measurement Theory bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`ProjectiveMeasurementContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 51 specifies an exact, deterministic evaluation procedure for candidate proposals over `Projective measurement instruments {P_k} over Q(i) with exact rational branch probabilities p_k`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
