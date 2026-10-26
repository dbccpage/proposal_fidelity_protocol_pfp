---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 24: Topos Subobject Classifiers & Truth Objects"
kind: grammar-reference
level: 24
epoch: "Epoch I"
domain: "Topos Theory"
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
evaluator_contract: "SubobjectClassifierContract"
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

# The Symbol Game Level 24: Topos Subobject Classifiers & Truth Objects

**AuthorityEffect:** None.  
**Level:** Level 24 | **Epoch:** Epoch I | **Domain:** Topos Theory  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Elementary topos E with subobject classifier Ω and truth arrow true: 1 → Ω`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SUBOBJECT_MONO_DEFECT`  
**Evaluator Module:** `CategoryLimitsModule` (`Topos Subobject Classifier & Characteristic Arrow Evaluator`)  
**Evaluator Contract:** `SubobjectClassifierContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `CategoryLimitsModule` or contract `SubobjectClassifierContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 24 establishes the Proposal Fidelity Protocol (PFP) arena for **Topos Subobject Classifiers & Truth Objects** within the Topos Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{24} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Elementary topos E with subobject classifier Ω and truth arrow true: 1 → Ω`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `CategoryLimitsModule` (`SubobjectClassifierContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Evaluation of characteristic arrows χ_m classifying monomorphisms m: A ↪ X via pullback along true: 1 → Ω.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 24         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `CategoryLimitsModule` metrics under `SubobjectClassifierContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SUBOBJECT_MONO_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 24 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_24_topos_and_subobject` family schema:

```json
{
  "schema_id": "sg_packet_level_24_topos_and_subobject",
  "task_data": {
    "level": 24,
    "epoch": "Epoch I",
    "domain": "Topos Theory",
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
    "subobject_mono_m": {"domain": "A", "codomain": "X", "is_monic": true},
    "ambient_object_x": "X",
    "truth_arrow": "true: 1 -> Omega",
    "classifier_arrow_chi": "chi_m: X -> Omega",
    "pullback_square_witness": "iso_A_pullback",
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
pub struct SubobjectClassifierPayload {
    pub move_type: MoveType,
    pub subobject_mono_m: MorphismDescriptor,
    pub ambient_object_x: String,
    pub truth_arrow: String,
    pub classifier_arrow_chi: String,
    pub pullback_square_witness: String,
    pub proposer_signature: String,
}

pub struct Level24Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: SubobjectClassifierPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: CategoryLimitsModule

### Contract: `SubobjectClassifierContract`

Referees evaluate Level 24 candidates through elementary topos universal subobject classification:

1. **Monomorphism Verification:** Verifies candidate arrow $m\colon A \to X$ is monic (left-cancellable):
   $$m \circ u = m \circ v \implies u = v$$
2. **Pullback Square Commutation:** Audits characteristic morphism $\chi_m\colon X \to \Omega$ such that the square commutes:
   $$\chi_m \circ m = \top_1 \circ !_A$$
3. **Pullback Universality & Uniqueness:** Verifies $A \cong X \times_\Omega 1$ and that $\chi_m$ is the unique arrow inducing this pullback.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff $m$ is certified monic and the pullback square along $\top\colon 1 \to \Omega$ commutes with unique characteristic map $\chi_m$.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an intuitionistic truth object structure with non-Boolean Heyting negation ($\neg \neg \ne \mathrm{id}_\Omega$) is certified invariant under declared subobject operations, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 24 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SUBOBJECT_MONO_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 24, "carrier_match": true, "move": "ASSERT", "subobject_mono_m": {"domain": "A", "codomain": "X", "is_monic": true}, "classifier_arrow_chi": "chi_m", "pullback_square_witness": "valid_pullback"}
REFEREE:  ACCEPT -> Status: ExactRepair (subobject monomorphism classified by unique characteristic arrow)
  ```

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 24, "carrier_match": true, "move": "ASSERT", "subobject_mono_m": {"domain": "A", "codomain": "X", "is_monic": false, "failure_witness": "m o u == m o v with u != v"}, "classifier_arrow_chi": "chi_m"}
REFEREE:  REFUSED -> Refusal Code: ERR_SUBOBJECT_MONO_DEFECT, Status: Refused (candidate arrow m is not a monomorphism)
  ```

  **Reproducibility gap (2026-10-20):** `is_monic`, the pullback witness and the failure witness are self-reported strings. No topos, objects or arrows are supplied, so neither monicity nor the pullback square can be recomputed. In the topos of finite sets, for example, a complete vector would give `m` as a function table, `Omega = {0, 1}`, `true` picking `1`, and `chi_m(x) = 1` exactly when `x` is in the image of `m`; monicity is then injectivity of the table.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 24, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 24: Topos Subobject Classifiers & Truth Objects within the Topos Theory bounded context.
   - A proposed PFP packet envelope, `CategoryLimitsModule` (`SubobjectClassifierContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 24 specifies an exact, deterministic evaluation procedure for candidate proposals over `Elementary topos E with subobject classifier Ω and truth arrow true: 1 → Ω`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
