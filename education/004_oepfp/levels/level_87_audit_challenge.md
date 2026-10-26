---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 87: Adversarial Challenge Injection & Red-Team Probes"
kind: grammar-reference
level: 87
epoch: "Epoch VIII"
domain: "Security Auditing"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "AdversarialFixtureContract"
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

# The Symbol Game Level 87: Adversarial Challenge Injection & Red-Team Probes

**AuthorityEffect:** None.  
**Level:** Level 87 | **Epoch:** Epoch VIII | **Domain:** Security Auditing  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Synthetically perturbed input fixtures, red-team challenge mutations, and referee reaction matrices`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_NEGATIVE_FIXTURE_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`AdversarialFixtureContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `AdversarialFixtureContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 87 establishes the Proposal Fidelity Protocol (PFP) arena for **Adversarial Challenge Injection & Red-Team Probes** within the Security Auditing bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{87} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Synthetically perturbed input fixtures, red-team challenge mutations, and referee reaction matrices`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `AdversarialFixtureContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying deterministic referee behavior against adversarial fixtures and red-team probe suites.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 87        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `AdversarialFixtureContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_NEGATIVE_FIXTURE_DEFECT`) are emitted exclusively by `AdversarialFixtureContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 87 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_87` schema:

```json
{
  "schema_id": "sg_packet_level_87_security_auditing",
  "task_data": {
    "level": 87,
    "epoch": "Epoch VIII",
    "domain": "Security Auditing",
    "carrier_digest": "blake3:carrier_level_87..."
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
    "fixture_id": "fix_boundary_overflow",
    "mutation_type": "arithmetic_overflow",
    "mutation_digest": "sha256:mut_overflow_001",
    "expected_disposition": "Refused",
    "actual_disposition": "Refused",
    "checker_version": "referee_rust_v2_1",
    "replay_receipt": "blake3:replay_overflow_001"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_87"
  }
}
```

### AST Representation
```rust
pub struct AdversarialFixturePayload {
    pub fixture_id: String,
    pub mutation_type: String,
    pub mutation_digest: String,
    pub expected_disposition: String,
    pub actual_disposition: String,
    pub checker_version: String,
    pub replay_receipt: String,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `AdversarialFixtureContract`:

Referees evaluate security-critical defenses against synthetic challenge suites:
1. **Adversarial Mutation Binding:** Injects controlled mutations (overflow, unescaped characters, negative capacities).
2. **Deterministic Response Matching:** Asserts actual referee disposition matches declared expected disposition (`Refused`, `ExactRepair`, `TypedChange`).
3. **No-Crash Invariant:** Asserts that invalid or malicious inputs never produce unhandled host panics or unformatted stack traces.
4. **Replay Receipt Verification:** Certifies that replaying the probe produces identical terminal dispositions.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Referee reaction on adversarial fixture matches declared expected disposition (`Refused`, `ExactRepair`, or `TypedChange`) deterministically without uncaught panic.
- **`StabilizedSurvivor` Admission Criterion:** Adversarial challenge response certified under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 87 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_NEGATIVE_FIXTURE_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 87, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no fixture or dispositions, so the comparison in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** In the section 3 schema example `expected_disposition` and `actual_disposition` are both `Refused`, so the response matches. The domain negative vector expects `Refused` but records `ExactRepair`; the mismatch fails the check and `Refused` follows. `TypedChange`, listed in section 4 as a possible expected disposition, is not one of the eight terminal statuses in section 5 or in `CodaTerminal`; it needs a mapping to one of them before it can be compared.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 87, "carrier_match": true, "expected_disposition": "Refused", "actual_disposition": "ExactRepair"}
  REFEREE:  REFUSED -> Refusal Code: ERR_NEGATIVE_FIXTURE_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 87, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of deterministic referee rejection or adaptation against checked-in adversarial challenge fixtures.
   - A proposed PFP packet envelope, `AdversarialFixtureContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove resilience against uncharacterized zero-day exploits outside the declared challenge suite.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that the host referee handles declared red-team mutation fixtures according to specification.
4. **Next test needed:**
   - Execute automated adversarial fuzzing suites against the PFP referee dispatch seam.
