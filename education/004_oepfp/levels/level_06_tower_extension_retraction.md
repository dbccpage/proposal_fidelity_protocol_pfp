---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 06: Tower Extension, Retraction & Survivor Zeta"
kind: grammar-reference
level: 6
epoch: "Base Tower"
domain: "Analytic Combinatorics"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "SurvivorZetaModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
  - StabilizedSurvivor
  - LiftLicenseNeeded
source_paths:
  - omega_engine_education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 06: Tower Extension, Retraction & Survivor Zeta

**AuthorityEffect:** None.  
**Level:** Level 06 | **Epoch:** Base Tower | **Domain:** Analytic Combinatorics  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Retraction pairs (u_N: M_N-1 → M_N, d_N: M_N → M_N-1) with survivor spectrum s_n`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, RETRACT`  
**Primary Domain Error Code:** `ERR_RETRACTION_DEFECT`  
**Evaluator Module:** `SurvivorZetaModule` (`Retraction Dynamics & Survivor Zeta Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SurvivorZetaModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 06 establishes the Proposal Fidelity Protocol (PFP) arena for **Tower Extension, Retraction & Survivor Zeta** within the Analytic Combinatorics bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{06} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Retraction pairs (u_N: M_N-1 → M_N, d_N: M_N → M_N-1) with survivor spectrum s_n`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SurvivorZetaModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Formal presentation family with declared candidate retraction/lift structures generating the formal Dirichlet survivor series ζ_surv(s) = ∑ s_n n⁻ˢ.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 06         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, RETRACT`), calculates `SurvivorZetaModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_RETRACTION_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 06 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_06` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_06",
  "task_data": {
    "level": 6,
    "epoch": "Base Tower",
    "domain": "Analytic Combinatorics",
    "carrier_digest": "blake3:b8d4e906"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "retraction_pair": [
      "u_N: M_N-1 -> M_N",
      "d_N: M_N -> M_N-1"
    ],
    "survivor_term": 2,
    "dirichlet_series_bound": "zeta_surv(2) <= 3/2",
    "retraction_identity_holds": true,
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```

### AST Representation
```rust
pub struct Level06Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: RetractionPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: SurvivorZetaModule

Referees evaluate Level 06 candidates through presentation retraction pairs and formal Dirichlet survivor series:

1. **Retraction Closure:** Evaluates up-down map composition $d_N \circ u_N = \mathrm{id}_{M_{N-1}}$ on finite presentations $M_{N-1}, M_N$.
2. **Survivor Spectrum:** Evaluates the non-retracted survivor count $s_n = |M_N \setminus u_N(M_{N-1})|$.
3. **Formal Dirichlet Formulation:** Audits terms of the formal survivor zeta series $\zeta_{\mathrm{surv}}(s) = \sum s_n n^{-s}$ as a formal algebraic generating series without ungrounded continuum convergence claims.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff retraction identities hold on the active carrier presentation.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 06 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded when non-retracted survivor spectrum $s_n$ is verified; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | **Reachable.** Reachable upon certified same-level exhaustion when CEC preconditions qualify for inter-stage ascent. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_RETRACTION_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_06",
  "task_data": {
    "level": 6,
    "epoch": "Base Tower",
    "domain": "Analytic Combinatorics",
    "carrier_digest": "blake3:b8d4e906"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "source_elements": [
      "x",
      "y"
    ],
    "target_elements": [
      "xp",
      "yp",
      "z"
    ],
    "embedding_u": {
      "x": "xp",
      "y": "yp"
    },
    "retraction_r": {
      "xp": "x",
      "yp": "y",
      "z": "x"
    },
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved; r*u=id, complement={z})
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_06",
  "task_data": {
    "level": 6,
    "epoch": "Base Tower",
    "domain": "Analytic Combinatorics",
    "carrier_digest": "blake3:b8d4e906"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "source_elements": [
      "x",
      "y"
    ],
    "target_elements": [
      "xp",
      "yp",
      "z"
    ],
    "embedding_u": {
      "x": "xp",
      "y": "yp"
    },
    "retraction_r": {
      "xp": "x",
      "yp": "x",
      "z": "x"
    },
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: REFUSED -> Refusal Code: ERR_RETRACTION_DEFECT, Status: Refused (r*u(y) != y)
```

**Worked check (2026-10-20):**

1. Valid packet: `r(u(x)) = r(xp) = x` and `r(u(y)) = r(yp) = y`, so `r o u = id` on `{x, y}`. The image of `u` is `{xp, yp}`, so the survivor set is `{xp, yp, z} \ {xp, yp} = {z}` and the survivor count is `1`. Note that `u o r` is not the identity: `u(r(z)) = xp != z`. That is expected for a section/retraction pair.
2. Negative packet: `r(u(y)) = r(yp) = x != y`, so the retraction identity fails at `y`, as the refusal states.

**Scope note (2026-10-20):** This level writes the survivor series as a Dirichlet series `sum s_n n^(-s)`, while [math Chapter 07](../math/07_math_filtered_diagrams_persistence_and_survivors.md) defines the survivor generating function as the formal power series `prod (1 - z^deg(p))^(-1)`. The two objects differ. The Section 3 schema value `"zeta_surv(2) <= 3/2"` is an analytic bound with no supporting survivor counts in the packet, so it is not reproducible and conflicts with the formal-series stance of Section 4.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_06",
  "task_data": {
    "level": 6,
    "epoch": "Base Tower",
    "domain": "Analytic Combinatorics",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "move_type": "ASSERT",
    "injected_carrier_token": "\u03a9_UNPINNED",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "corrupted_init"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 06 (Tower Extension, Retraction & Survivor Zeta) within the Analytic Combinatorics bounded context.
   - A proposed PFP packet envelope, `SurvivorZetaModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 06 specifies an exact, deterministic evaluation procedure for candidate proposals over `Retraction pairs (u_N: M_N-1 → M_N, d_N: M_N → M_N-1) with survivor spectrum s_n`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
