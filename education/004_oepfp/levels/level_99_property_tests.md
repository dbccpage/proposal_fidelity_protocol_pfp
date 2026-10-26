---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 99: QuickCheck-Style Property Generators & Shrinking"
kind: grammar-reference
level: 99
epoch: "Epoch IX"
domain: "Automated Testing"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "VerificationToolchainModule"
evaluator_contract: "PropertyTestingContract"
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

# The Symbol Game Level 99: QuickCheck-Style Property Generators & Shrinking

**AuthorityEffect:** None.  
**Level:** Level 99 | **Epoch:** Epoch IX | **Domain:** Automated Testing  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Pseudo-random test generators, algebraic property predicates, counterexample shrinking traces`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_GENERATOR_SEED_DEFECT`  
**Evaluator Module:** `VerificationToolchainModule` (`PropertyTestingContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `VerificationToolchainModule` or contract `PropertyTestingContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 99 establishes the Proposal Fidelity Protocol (PFP) arena for **QuickCheck-Style Property Generators & Shrinking** within the Automated Testing bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{99} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Pseudo-random test generators, algebraic property predicates, counterexample shrinking traces`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `VerificationToolchainModule` via `PropertyTestingContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Auditing pseudo-random property-based testing runs and verifying minimal counterexample shrinking traces.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 99        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `PropertyTestingContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_GENERATOR_SEED_DEFECT`) are emitted exclusively by `PropertyTestingContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 99 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_99` schema:

```json
{
  "schema_id": "sg_packet_level_99_automated_testing",
  "task_data": {
    "level": 99,
    "epoch": "Epoch IX",
    "domain": "Automated Testing",
    "carrier_digest": "blake3:carrier_level_99..."
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
    "property_id": "prop_retraction_left_inverse",
    "predicate": "r_N(u_N(x)) == x",
    "generator_id": "gen_random_simplex_v2",
    "seed": 424242,
    "sample_count": 1000,
    "counterexample": null,
    "shrink_trace": []
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_99"
  }
}
```

### AST Representation
```rust
pub struct PropertyTestingPayload {
    pub property_id: String,
    pub predicate: String,
    pub generator_id: String,
    pub seed: u64,
    pub sample_count: u32,
    pub counterexample: Option<String>,
    pub shrink_trace: Vec<String>,
}
```

---

## 4. Evaluator Module & Objective Metrics: VerificationToolchainModule

Referees evaluate candidates through `PropertyTestingContract`:

Referees audit property-based generator suites against formal algebraic invariants:
1. **Generator Sampling:** Samples inputs from declared generator under pinned seed across declared sample count.
2. **Predicate Evaluation:** Evaluates algebraic invariant predicate for each sampled input vector.
3. **Shrinking Verification:** If a falsifying input occurs, verifies that the shrink trace monotonically minimizes input size.
4. **Epistemic Fence:** A passing property sample provides empirical evidence; does NOT constitute exhaustive mathematical proof.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Generator initialized with declared seed, 1,000 samples tested against predicate, all samples satisfy predicate, and zero counterexamples found.
- **`StabilizedSurvivor` Admission Criterion:** Sampled property certificate recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 99 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_GENERATOR_SEED_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 99, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no property, generator, seed or sample count, so the run in section 4 cannot be replayed from it; the `ExactRepair` line is a stated expectation only. The section 3 schema example is internally consistent (1000 samples, `counterexample: null`, empty shrink trace), but the generator `gen_random_simplex_v2` is not in source, so the run cannot be replayed. The domain negative vector reports a counterexample, so the property is falsified on a sampled input and `Refused` follows; the refusal code `ERR_GENERATOR_SEED_DEFECT` is this level's single primary error code, not a statement that the seed was wrong.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 99, "carrier_match": true, "counterexample": "falsifying_input_v4"}
  REFEREE:  REFUSED -> Refusal Code: ERR_GENERATOR_SEED_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 99, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of property-based test generation receipts, predicate satisfaction, and minimal counterexample traces.
   - A proposed PFP packet envelope, `PropertyTestingContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove general mathematical validity of the property across infinite or un-sampled finite states.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the tested property held across all sampled inputs generated under the declared seed.
4. **Next test needed:**
   - Execute Hypothesis-based property test sweeps on simplicial complex retractors.
