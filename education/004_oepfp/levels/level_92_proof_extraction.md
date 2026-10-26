---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 92: Automated Proof Witness Extraction & Replay"
kind: grammar-reference
level: 92
epoch: "Epoch IX"
domain: "Automated Reasoning"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "VerificationToolchainModule"
evaluator_contract: "ProofExtractionContract"
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

# The Symbol Game Level 92: Automated Proof Witness Extraction & Replay

**AuthorityEffect:** None.  
**Level:** Level 92 | **Epoch:** Epoch IX | **Domain:** Automated Reasoning  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Formal proof objects, solver traces (SMT/SAT/LP), and independent proof checker kernels`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SOLVER_TRACE_DEFECT`  
**Evaluator Module:** `VerificationToolchainModule` (`ProofExtractionContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `VerificationToolchainModule` or contract `ProofExtractionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 92 establishes the Proposal Fidelity Protocol (PFP) arena for **Automated Proof Witness Extraction & Replay** within the Automated Reasoning bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{92} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Formal proof objects, solver traces (SMT/SAT/LP), and independent proof checker kernels`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `VerificationToolchainModule` via `ProofExtractionContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Extracting proof certificates from untrusted solver traces and replaying them in independent trusted checker kernels.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 92        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `ProofExtractionContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SOLVER_TRACE_DEFECT`) are emitted exclusively by `ProofExtractionContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 92 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_92` schema:

```json
{
  "schema_id": "sg_packet_level_92_automated_reasoning",
  "task_data": {
    "level": 92,
    "epoch": "Epoch IX",
    "domain": "Automated Reasoning",
    "carrier_digest": "blake3:carrier_level_92..."
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
    "theorem_digest": "sha256:thm_simplex_nonempty_v1",
    "solver_id": "z3_4_12_2",
    "solver_result": "unsat",
    "trace_digest": "blake3:trace_z3_001_run",
    "proof_object": "(proof (step-1 (assert nonempty)) (conclusion (simplex_nonempty)))",
    "proof_format": "smt2_proof_v1",
    "trusted_checker_id": "carcara_v1_0",
    "replay_verdict": "valid"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_92"
  }
}
```

### AST Representation
```rust
pub struct ProofExtractionPayload {
    pub theorem_digest: String,
    pub solver_id: String,
    pub solver_result: String,
    pub trace_digest: String,
    pub proof_object: String,
    pub proof_format: String,
    pub trusted_checker_id: String,
    pub replay_verdict: String,
}
```

---

## 4. Evaluator Module & Objective Metrics: VerificationToolchainModule

Referees evaluate candidates through `ProofExtractionContract`:

Referees decouple untrusted solver generation from trusted proof kernel replay:
1. **Solver Independence:** Treats solver output as an untrusted hint; does not trust solver self-assertions.
2. **Proof Object Replay:** Submits `proof_object` directly to the independent trusted checker kernel (`carcara`).
3. **Step Validity Audit:** Verifies that every deduction step is justified by declared axioms and deduction rules.
4. **Conclusion Match:** Asserts that the proved conclusion matches `theorem_digest` identically.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Proof object parsed by trusted independent checker kernel, every deduction step verified valid, and proved conclusion matches theorem digest.
- **`StabilizedSurvivor` Admission Criterion:** Independent proof replay certificate recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 92 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SOLVER_TRACE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 92, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no proof object or theorem, so the replay in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** The section 3 schema example originally reported `solver_result: "sat"`. An SMT solver establishes a theorem by showing that its negation is unsatisfiable, and the named checker Carcara replays Alethe proofs of unsatisfiability; a `sat` answer yields a model, not a proof object. The example now reads `"unsat"`. Two inconsistencies remain and are not changed here: `proof_format` is `smt2_proof_v1` rather than Alethe, and the named solver `z3_4_12_2` does not emit Alethe proofs (cvc5 and veriT do). The printed `proof_object` is an illustrative string, not a checkable proof. The domain negative vector reports `replay_verdict: "invalid_deduction_step"`, so step validity fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 92, "carrier_match": true, "replay_verdict": "invalid_deduction_step"}
  REFEREE:  REFUSED -> Refusal Code: ERR_SOLVER_TRACE_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 92, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of solver traces via independent proof object extraction and trusted kernel replay.
   - A proposed PFP packet envelope, `ProofExtractionContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert that the underlying solver source code is formally verified.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the extracted proof object is verifiable by an independent trusted checker kernel.
4. **Next test needed:**
   - Replay SMT proof certificates using local Carcara/Alethe checker integrations.
