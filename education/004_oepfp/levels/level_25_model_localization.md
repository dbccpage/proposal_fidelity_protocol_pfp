---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 25: Model Localization & Weak Equivalences"
kind: grammar-reference
level: 25
epoch: "Epoch I"
domain: "Homotopical Algebra"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "LocalizationModule"
evaluator_contract: "ModelLocalizationContract"
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

# The Symbol Game Level 25: Model Localization & Weak Equivalences

**AuthorityEffect:** None.  
**Level:** Level 25 | **Epoch:** Epoch I | **Domain:** Homotopical Algebra  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Category C with declared weak equivalences W and calculus of fractions`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_WEAK_EQUIVALENCE_DEFECT`  
**Evaluator Module:** `LocalizationModule` (`Category Localization & Calculus of Fractions Evaluator`)  
**Evaluator Contract:** `ModelLocalizationContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `LocalizationModule` or contract `ModelLocalizationContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 25 establishes the Proposal Fidelity Protocol (PFP) arena for **Model Localization & Weak Equivalences** within the Homotopical Algebra bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{25} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Category C with declared weak equivalences W and calculus of fractions`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `LocalizationModule` (`ModelLocalizationContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Formal inversion of weak equivalences W, Ore condition verification, and roof composition in localized categories.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 25         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `LocalizationModule` metrics under `ModelLocalizationContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_WEAK_EQUIVALENCE_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 25 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_25_model_localization` family schema:

```json
{
  "schema_id": "sg_packet_level_25_model_localization",
  "task_data": {
    "level": 25,
    "epoch": "Epoch I",
    "domain": "Homotopical Algebra",
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
    "category_arrows": ["f: X -> Y", "w: Z -> X"],
    "weak_equivalences_w": ["w: Z -> X"],
    "roof_fraction": {"left_inverted_w": "w", "right_morphism_f": "f"},
    "ore_condition_witness": "roof_commutation_witness",
    "universal_localization_functor": "L: C -> C[W^-1]",
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
pub struct ModelLocalizationPayload {
    pub move_type: MoveType,
    pub category_arrows: Vec<String>,
    pub weak_equivalences_w: Vec<String>,
    pub roof_fraction: RoofFraction,
    pub ore_condition_witness: String,
    pub universal_localization_functor: String,
    pub proposer_signature: String,
}

pub struct Level25Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: ModelLocalizationPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: LocalizationModule

### Contract: `ModelLocalizationContract`

Referees evaluate Level 25 candidates through homotopical localization and fraction calculus (not limit cones):

1. **Weak Equivalence Closure:** Asserts class $W \subset \mathrm{Mor}(\mathcal{C})$ contains all identity morphisms and satisfies the 2-out-of-3 property.
2. **Calculus of Fractions (Ore Condition):** For any roof $X \xleftarrow{w} Z \xrightarrow{f} Y$ with $w \in W$, evaluates existence of a completing roof $X \xrightarrow{f'} Z' \xleftarrow{w'} Y$ with $w' \in W$ such that $w' \circ f = f' \circ w$ (both sides are maps $Z \to Z'$). *(Corrected 2026-10-20: the earlier equation $f \circ w' = w \circ f'$ does not type-check, because $w'\colon Y \to Z'$ cannot precede $f\colon Z \to Y$.)*
3. **Universal Localization Functor:** Verifies $L\colon \mathcal{C} \to \mathcal{C}[W^{-1}]$ maps all $w \in W$ to isomorphisms, and any functor $F\colon \mathcal{C} \to \mathcal{D}$ inverting $W$ factors uniquely through $L$.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff all inverted morphisms lie strictly in $W$ and the candidate roof satisfies the Ore composition condition and fraction equivalence.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an essential fraction $X \xleftarrow{w} Z \xrightarrow{f} Y$ represents a non-trivial localized morphism that cannot be represented by a direct arrow in $\mathcal{C}$ ($w$ not invertible in $\mathcal{C}$), recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 25 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_WEAK_EQUIVALENCE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 25, "carrier_match": true, "move": "ASSERT", "weak_equivalences_w": ["w: Z -> X"], "roof_fraction": {"left_inverted_w": "w", "right_morphism_f": "f: Z -> Y"}, "ore_condition_witness": "valid_ore"}
REFEREE:  ACCEPT -> Status: ExactRepair (roof fraction correctly composed with w in W under Ore conditions)
  ```

  **Worked check (2026-10-20):** The roof is $X \xleftarrow{w} Z \xrightarrow{f} Y$ with $w\colon Z \to X$ listed in $W$ and $f\colon Z \to Y$, so both legs start at the apex $Z$ and the inverted leg lies in $W$. In $\mathcal{C}[W^{-1}]$ the roof denotes the morphism $L(f) \circ L(w)^{-1}\colon X \to Y$. The schema example in Section 3 lists `"f: X -> Y"` instead; that arrow is not a leg out of $Z$. It gives a roof only as $(w, f \circ w)$, which denotes $L(f)$.

  **Reproducibility gap (2026-10-20):** `ore_condition_witness` is a label. The packet gives no completing span $(f', w', Z')$, so the referee cannot recompute the Ore square $w' \circ f = f' \circ w$ from the data.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 25, "carrier_match": true, "move": "ASSERT", "weak_equivalences_w": ["w: Z -> X"], "roof_fraction": {"left_inverted_w": "u_not_in_w", "right_morphism_f": "f: Z -> Y"}}
REFEREE:  REFUSED -> Refusal Code: ERR_WEAK_EQUIVALENCE_DEFECT, Status: Refused (inverted arrow u_not_in_w is not an admitted weak equivalence in W)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 25, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 25: Model Localization & Weak Equivalences within the Homotopical Algebra bounded context.
   - A proposed PFP packet envelope, `LocalizationModule` (`ModelLocalizationContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 25 specifies an exact, deterministic evaluation procedure for candidate proposals over `Category C with declared weak equivalences W and calculus of fractions`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
