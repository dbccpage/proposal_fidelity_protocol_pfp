---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 91: Verified Cross-Language AST Translation"
kind: grammar-reference
level: 91
epoch: "Epoch IX"
domain: "Compiler Verification"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "DialectAuditModule"
evaluator_contract: "LanguageTranslationContract"
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

# The Symbol Game Level 91: Verified Cross-Language AST Translation

**AuthorityEffect:** None.  
**Level:** Level 91 | **Epoch:** Epoch IX | **Domain:** Compiler Verification  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Multi-language Abstract Syntax Trees (Python, Rust, Lean 4) with formal simulation relations`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SOURCE_AST_DEFECT`  
**Evaluator Module:** `DialectAuditModule` (`LanguageTranslationContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `DialectAuditModule` or contract `LanguageTranslationContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 91 establishes the Proposal Fidelity Protocol (PFP) arena for **Verified Cross-Language AST Translation** within the Compiler Verification bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{91} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Multi-language Abstract Syntax Trees (Python, Rust, Lean 4) with formal simulation relations`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `DialectAuditModule` via `LanguageTranslationContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying cross-language AST translations and checking simulation relations for semantics preservation.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 91        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `LanguageTranslationContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SOURCE_AST_DEFECT`) are emitted exclusively by `LanguageTranslationContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 91 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_91` schema:

```json
{
  "schema_id": "sg_packet_level_91_compiler_verification",
  "task_data": {
    "level": 91,
    "epoch": "Epoch IX",
    "domain": "Compiler Verification",
    "carrier_digest": "blake3:carrier_level_91..."
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
    "source_lang": "Python",
    "source_ast_digest": "sha256:ast_py_001_source",
    "target_lang": "Rust",
    "target_ast_digest": "sha256:ast_rs_001_target",
    "symbol_map": {
      "calc_residual": "compute_phi1"
    },
    "simulation_witness": {
      "state_relation": "exact_rational_match",
      "step_correspondence": "one_to_one",
      "divergence_free": true
    }
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_91"
  }
}
```

### AST Representation
```rust
pub struct LanguageTranslationPayload {
    pub source_lang: String,
    pub source_ast_digest: String,
    pub target_lang: String,
    pub target_ast_digest: String,
    pub symbol_map: HashMap<String, String>,
    pub simulation_witness: SimulationWitness,
}
```

---

## 4. Evaluator Module & Objective Metrics: DialectAuditModule

Referees evaluate candidates through `LanguageTranslationContract`:

Referees evaluate cross-language source-to-target translations against operational semantics:
1. **Grammar Conformance:** Asserts that source and target ASTs are well-formed under their respective grammar rules.
2. **Interface Bounding:** Verifies that declared symbol mappings form a valid interface correspondence.
3. **Simulation Relation Audit:** Verifies that the simulation witness establishes step-by-step state preservation.
4. **Type Boundary Check:** Rejects translations that change exact rational types into lossy floating-point representations.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Source and target ASTs conform to declared grammar, symbol mapping is bijective across declared interface, and simulation witness demonstrates operational semantics preservation.
- **`StabilizedSurvivor` Admission Criterion:** Verified AST translation mapping recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 91 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SOURCE_AST_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 91, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no ASTs, symbol map or simulation witness, and the section 3 schema example gives only placeholder AST digests, so grammar conformance and the simulation relation cannot be checked from either; the `ExactRepair` line is a stated expectation only. The schema example's one-pair `symbol_map` (`calc_residual` to `compute_phi1`) is a bijection on its declared interface. The domain negative vector reports `divergence_free: false`, which contradicts the required simulation witness, so `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 91, "carrier_match": true, "simulation_witness": {"divergence_free": false}}
  REFEREE:  REFUSED -> Refusal Code: ERR_SOURCE_AST_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 91, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of cross-language AST translations and simulation witnesses for bounded operational subsets.
   - A proposed PFP packet envelope, `LanguageTranslationContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove whole-language semantic equivalence across unmodeled language runtime features.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the translated AST faithfully reproduces the declared source operations under the simulation relation.
4. **Next test needed:**
   - Execute translation verification on Python-to-Rust AST pairs in the engine test harness.
