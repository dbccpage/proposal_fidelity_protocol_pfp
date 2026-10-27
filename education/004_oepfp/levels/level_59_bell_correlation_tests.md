---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 59: Bell-CHSH Correlation Tests & Tsirelson Bounds"
kind: grammar-reference
level: 59
epoch: "Epoch IV"
domain: "Non-Locality"
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
evaluator_contract: "CHSHCorrelatorContract"
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

# The Symbol Game Level 59: Bell-CHSH Correlation Tests & Tsirelson Bounds

**AuthorityEffect:** None.  
**Level:** Level 59 | **Epoch:** Epoch IV | **Domain:** Non-Locality  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Bell-CHSH correlator configurations over Q(√2) with local bound S ≤ 2 and Tsirelson bound S ≤ 2√2`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_SETTING_PAIR_DEFECT`  
**Evaluator Module:** `QuantumFoundationsModule` (`Bell-CHSH Correlator & Tsirelson Bound Evaluator (Q(√2))`)  
**Evaluator Contract:** `CHSHCorrelatorContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `QuantumFoundationsModule` or contract `CHSHCorrelatorContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 59 establishes the Proposal Fidelity Protocol (PFP) arena for **Bell-CHSH Correlation Tests & Tsirelson Bounds** within the Non-Locality bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{59} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Bell-CHSH correlator configurations over Q(√2) with local bound S ≤ 2 and Tsirelson bound S ≤ 2√2`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `QuantumFoundationsModule` (`CHSHCorrelatorContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
CHSH correlators S = E(0,0)+E(0,1)+E(1,0)-E(1,1) in Q(√2), local bound violation S > 2, and Tsirelson bound respect S ≤ 2√2.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 59         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `QuantumFoundationsModule` metrics under `CHSHCorrelatorContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SETTING_PAIR_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 59 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_59_bell_correlation_tests` family schema:

```json
{
  "schema_id": "sg_packet_level_59_bell_correlation_tests",
  "task_data": {
    "level": 59,
    "epoch": "Epoch IV",
    "domain": "Non-Locality",
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
    "scalar_field": "Q(sqrt(2))",
    "correlators": {
      "E(0,0)": "1/sqrt(2)",
      "E(0,1)": "1/sqrt(2)",
      "E(1,0)": "1/sqrt(2)",
      "E(1,1)": "-1/sqrt(2)"
    },
    "chsh_parameter_s": "2*sqrt(2)",
    "violates_local_bound_two": true,
    "respects_tsirelson_bound": true,
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
pub struct CHSHCorrelatorPayload {
    pub move_type: MoveType,
    pub scalar_field: String,
    pub correlators: BTreeMap<String, String>,
    pub chsh_parameter_s: String,
    pub violates_local_bound_two: bool,
    pub respects_tsirelson_bound: bool,
    pub proposer_signature: String,
}

pub struct Level59Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: CHSHCorrelatorPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: QuantumFoundationsModule

### Contract: `CHSHCorrelatorContract`

Referees evaluate Level 59 candidates through CHSH correlation bounds over $\mathbb{Q}(\sqrt{2})$:

1. **Declared Field $\mathbb{Q}(\sqrt{2})$:** Evaluates settings $x, y \in \{0, 1\}$ and correlators $E(x, y) = \langle A_x B_y \rangle$ over algebraic field $\mathbb{Q}(\sqrt{2})$.
2. **CHSH Linear Combination:** Computes the Clauser-Horne-Shimony-Holt parameter:
   $$S = E(0, 0) + E(0, 1) + E(1, 0) - E(1, 1)$$
3. **Local Violation While Respecting Tsirelson Bound:** Audits that candidate quantum correlations violate the classical local hidden-variable bound ($S > 2$) while strictly respecting the Tsirelson (Cirel'son) quantum bound ($S \le 2\sqrt{2} \approx 2.828$). Correlator tables claiming $S > 2\sqrt{2}$ are rejected as unphysical super-quantum violations.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff correlators lie in $\mathbb{Q}(\sqrt{2})$, violate the local bound ($S > 2$), and strictly respect the Tsirelson bound ($S \le 2\sqrt{2}$).
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an extremal quantum correlator saturating Tsirelson's bound ($S = 2\sqrt{2}$) is certified invariant under licensed non-local fences, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 59 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SETTING_PAIR_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 59, "carrier_match": true, "move": "ASSERT", "scalar_field": "Q(sqrt(2))", "chsh_parameter_s": "2*sqrt(2)", "violates_local_bound_two": true, "respects_tsirelson_bound": true}
REFEREE:  ACCEPT -> Status: ExactRepair (CHSH correlator S = 2√2 violates local bound 2 while strictly respecting Tsirelson bound)
  ```

  **Worked check (2026-10-20):** with the section 3 correlators, S = 1/√2 + 1/√2 + 1/√2 − (−1/√2) = 4/√2 = 2√2. Since (2√2)² = 8 > 4, S > 2, and S ≤ 2√2 holds with equality. Equality saturates Tsirelson's bound, so this table meets both the `ExactRepair` criterion and the `StabilizedSurvivor` saturation clause; the contract needs a precedence rule.

  **Reproducibility gap (2026-10-20):** this proposal omits `correlators` and gives only S.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 59, "carrier_match": true, "move": "ASSERT", "scalar_field": "Q(sqrt(2))", "chsh_parameter_s": "3", "violates_local_bound_two": true, "respects_tsirelson_bound": false}
REFEREE:  REFUSED -> Refusal Code: ERR_SETTING_PAIR_DEFECT, Status: Refused (CHSH parameter S = 3 exceeds Tsirelson bound 2√2, representing an unphysical correlator)
  ```

  **Worked check (2026-10-20):** 3² = 9 > 8 = (2√2)², so S = 3 exceeds 2√2.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 59, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 59: Bell-CHSH Correlation Tests & Tsirelson Bounds within the Non-Locality bounded context.
   - A proposed PFP packet envelope, `QuantumFoundationsModule` (`CHSHCorrelatorContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 59 specifies an exact, deterministic evaluation procedure for candidate proposals over `Bell-CHSH correlator configurations over Q(√2) with local bound S ≤ 2 and Tsirelson bound S ≤ 2√2`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
