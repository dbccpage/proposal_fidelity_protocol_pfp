---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 23: Sheaf Gluing & Grothendieck Descent"
kind: grammar-reference
level: 23
epoch: "Epoch I"
domain: "Sheaf Theory"
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
evaluator_contract: "SheafDescentContract"
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

# The Symbol Game Level 23: Sheaf Gluing & Grothendieck Descent

**AuthorityEffect:** None.  
**Level:** Level 23 | **Epoch:** Epoch I | **Domain:** Sheaf Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Presheaf F on site (C, J) with sieve covering families and matching sections`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `REFUSED_OVERLAP_CONFLICT`  
**Evaluator Module:** `CategoryLimitsModule` (`Sheaf Gluing & Grothendieck Descent Evaluator`)  
**Evaluator Contract:** `SheafDescentContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CategoryLimitsModule` or contract `SheafDescentContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 23 establishes the Proposal Fidelity Protocol (PFP) arena for **Sheaf Gluing & Grothendieck Descent** within the Sheaf Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{23} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Presheaf F on site (C, J) with sieve covering families and matching sections`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CategoryLimitsModule` (`SheafDescentContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Equalizer verification for sieve covering families, local section overlap compatibility, and unique amalgamation.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 23         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `CategoryLimitsModule` metrics under `SheafDescentContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `REFUSED_OVERLAP_CONFLICT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 23 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_23_sheaf_and_descent` family schema:

```json
{
  "schema_id": "sg_packet_level_23_sheaf_and_descent",
  "task_data": {
    "level": 23,
    "epoch": "Epoch I",
    "domain": "Sheaf Theory",
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
    "covering_family": ["U_1", "U_2"],
    "local_sections": {"U_1": "s_1", "U_2": "s_2"},
    "overlap_restrictions": {
      "U_1_cap_U_2": {"from_s1": "s_12_alpha", "from_s2": "s_12_alpha"}
    },
    "candidate_amalgamation": "s_global",
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
pub struct SheafDescentPayload {
    pub move_type: MoveType,
    pub covering_family: Vec<String>,
    pub local_sections: BTreeMap<String, String>,
    pub overlap_restrictions: BTreeMap<String, OverlapPair>,
    pub candidate_amalgamation: String,
    pub proposer_signature: String,
}

pub struct Level23Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SheafDescentPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: CategoryLimitsModule

### Contract: `SheafDescentContract`

Referees evaluate Level 23 candidates through the canonical sheaf equalizer condition:

1. **Covering Sieve Matching:** Evaluates local section family $\{s_i \in \mathcal{F}(U_i)\}$ indexed over covering sieve $\{U_i \to U\}$.
2. **Pairwise Overlap Compatibility:** Evaluates restriction maps $\rho_{U_i \cap U_j}^{U_i}$, asserting identical restriction on overlaps:
   $$s_i|_{U_i \cap U_j} = s_j|_{U_i \cap U_j}$$
3. **Unique Amalgamation:** Verifies existence and uniqueness of global section $s \in \mathcal{F}(U)$ restricting to each local section:
   $$\rho_{U_i}^U(s) = s_i \quad \forall i$$
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff pairwise overlap restrictions match identically and candidate amalgamation $s$ restricts to local sections without defect.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff a non-zero Čech 1-cocycle $\{s_{ij}\}$ represents an unamalgamable obstruction certifying non-trivial Čech cohomology class $[\{s_{ij}\}] \ne 0 \in \check{H}^1(\mathcal{U}, \mathcal{F})$, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 23 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `REFUSED_OVERLAP_CONFLICT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 23, "carrier_match": true, "move": "ASSERT", "covering_family": ["U_1", "U_2"], "local_sections": {"U_1": "s_1", "U_2": "s_2"}, "overlap_restrictions": {"U_1_cap_U_2": {"from_s1": "v_match", "from_s2": "v_match"}}, "candidate_amalgamation": "s"}
REFEREE:  ACCEPT -> Status: ExactRepair (pairwise overlap sections match identically and unique amalgamation certified)
  ```

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 23, "carrier_match": true, "move": "ASSERT", "covering_family": ["U_1", "U_2"], "local_sections": {"U_1": "s_1", "U_2": "s_2"}, "overlap_restrictions": {"U_1_cap_U_2": {"from_s1": "v_val_A", "from_s2": "v_val_B"}}, "candidate_amalgamation": "s"}
REFEREE:  REFUSED -> Refusal Code: REFUSED_OVERLAP_CONFLICT, Status: Refused (overlap restrictions from s1 and s2 disagree on intersection U_1 cap U_2)
  ```

  **Reproducibility gap (2026-10-20):** Sections and restrictions are labels (`v_match`, `v_val_A`, `v_val_B`). The overlap comparison can be read off the labels, but existence and uniqueness of the amalgamation `s` cannot be checked without the presheaf values and restriction maps. A complete vector needs, for example, finite sets `F(U), F(U_1), F(U_2), F(U_1 cap U_2)` and the restriction functions.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 23, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 23: Sheaf Gluing & Grothendieck Descent within the Sheaf Theory bounded context.
   - A proposed PFP packet envelope, `CategoryLimitsModule` (`SheafDescentContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 23 specifies an exact, deterministic evaluation procedure for candidate proposals over `Presheaf F on site (C, J) with sieve covering families and matching sections`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
