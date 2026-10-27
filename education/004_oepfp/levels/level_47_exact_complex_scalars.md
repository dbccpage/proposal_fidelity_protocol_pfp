---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 47: Gaussian Rational Field Q(i) & Exact Amplitudes"
kind: grammar-reference
level: 47
epoch: "Epoch IV"
domain: "Quantum Foundations"
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
evaluator_contract: "GaussianRationalScalarContract"
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

# The Symbol Game Level 47: Gaussian Rational Field Q(i) & Exact Amplitudes

**AuthorityEffect:** None.  
**Level:** Level 47 | **Epoch:** Epoch IV | **Domain:** Quantum Foundations  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Exact Gaussian-rational scalar field Q(i) with arithmetic operations and complex conjugation`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_RATIONAL_PAIR_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Gaussian Rational Field Q(i) Scalar Arithmetic Evaluator`)  
**Evaluator Contract:** `GaussianRationalScalarContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `GaussianRationalScalarContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 47 establishes the Proposal Fidelity Protocol (PFP) arena for **Gaussian Rational Field Q(i) & Exact Amplitudes** within the Quantum Foundations bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{47} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Exact Gaussian-rational scalar field Q(i) with arithmetic operations and complex conjugation`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`GaussianRationalScalarContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact rational arithmetic over Q(i) = {a + bi | a, b in Q}, conjugation involution, and exact rational modulus squared.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 47         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `GaussianRationalScalarContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_RATIONAL_PAIR_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 47 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_47_exact_complex_scalars` family schema:

```json
{
  "schema_id": "sg_packet_level_47_exact_complex_scalars",
  "task_data": {
    "level": 47,
    "epoch": "Epoch IV",
    "domain": "Quantum Foundations",
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
    "scalar_alpha": {"real": "3/5", "imag": "4/5"},
    "scalar_beta": {"real": "1/2", "imag": "-1/2"},
    "conjugate_alpha": {"real": "3/5", "imag": "-4/5"},
    "modulus_squared_alpha": "1",
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
pub struct GaussianRationalPayload {
    pub move_type: MoveType,
    pub scalar_alpha: ComplexRational,
    pub scalar_beta: ComplexRational,
    pub conjugate_alpha: ComplexRational,
    pub modulus_squared_alpha: Rational,
    pub proposer_signature: String,
}

pub struct Level47Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: GaussianRationalPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `GaussianRationalScalarContract`

Referees evaluate Level 47 candidates through exact field arithmetic over $\mathbb{Q}(i)$:

1. **Exact Gaussian Rational Field Representation:** Represents complex amplitudes as pairs $(a, b) \in \mathbb{Q} \times \mathbb{Q}$ corresponding to $\alpha = a + b i$.
2. **Field Operations & Inverses:** Computes multiplication and multiplicative inverses over $\mathbb{Q}$:
   $$(a + b i)(c + d i) = (ac - bd) + (ad + bc) i, \qquad (a + b i)^{-1} = \frac{a}{a^2 + b^2} - \frac{b}{a^2 + b^2} i$$
3. **Conjugation & Modulus Squared:** Evaluates conjugate $\alpha^* = a - bi$ and modulus squared $|\alpha|^2 = a^2 + b^2 \in \mathbb{Q}^+$. Scoped strictly as an exact Gaussian-rational fragment of quantum amplitudes (not continuous complex numbers).
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff field operations evaluate without remainder and conjugate involution satisfies $(\alpha^*)^* = \alpha$ identically over $\mathbb{Q}$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant discrete phase root ($i \in \mathbb{Q}(i)$ with $i^4 = 1$) is certified stable under scalar transits, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 47 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_RATIONAL_PAIR_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 47, "carrier_match": true, "move": "ASSERT", "scalar_alpha": {"real": "3/5", "imag": "4/5"}, "modulus_squared_alpha": "1", "conjugate_alpha": {"real": "3/5", "imag": "-4/5"}}
REFEREE:  ACCEPT -> Status: ExactRepair (Gaussian rational scalar operations and modulus squared verified over Q)
  ```

  **Worked check (2026-10-20):** for $\alpha = 3/5 + (4/5)i$: $|\alpha|^2 = 9/25 + 16/25 = 1$; $\alpha^* = 3/5 - (4/5)i$, and $(\alpha^*)^* = \alpha$. Since $|\alpha|^2 = 1$, the inverse formula gives $\alpha^{-1} = 3/5 - (4/5)i = \alpha^*$. The schema's $\beta = 1/2 - (1/2)i$ has $|\beta|^2 = 1/4 + 1/4 = 1/2$. In the negative vector the claimed $2/3$ differs from the computed $1$, so the refusal follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 47, "carrier_match": true, "move": "ASSERT", "scalar_alpha": {"real": "3/5", "imag": "4/5"}, "modulus_squared_alpha": "2/3"}
REFEREE:  REFUSED -> Refusal Code: ERR_RATIONAL_PAIR_DEFECT, Status: Refused (modulus squared calculation (3/5)^2 + (4/5)^2 = 1 != 2/3)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 47, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 47: Gaussian Rational Field Q(i) & Exact Amplitudes within the Quantum Foundations bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`GaussianRationalScalarContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 47 specifies an exact, deterministic evaluation procedure for candidate proposals over `Exact Gaussian-rational scalar field Q(i) with arithmetic operations and complex conjugation`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
