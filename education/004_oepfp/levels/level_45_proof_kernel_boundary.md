---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 45: LCF Proof Kernel & Trusted Computing Base"
kind: grammar-reference
level: 45
epoch: "Epoch III"
domain: "Proof Engines"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "ProofKernelModule"
evaluator_contract: "LCFProofKernelContract"
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

# The Symbol Game Level 45: LCF Proof Kernel & Trusted Computing Base

**AuthorityEffect:** None.  
**Level:** Level 45 | **Epoch:** Epoch III | **Domain:** Proof Engines  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Abstract theorem type thm constructible only through primitive LCF inference rules`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, VERIFY`  
**Primary Domain Error Code:** `ERR_PROOF_TERM_DEFECT`  
**Evaluator Module:** `ProofKernelModule` (`LCF Proof Kernel & Trusted Inference Replay Evaluator`)  
**Evaluator Contract:** `LCFProofKernelContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `ProofKernelModule` or contract `LCFProofKernelContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 45 establishes the Proposal Fidelity Protocol (PFP) arena for **LCF Proof Kernel & Trusted Computing Base** within the Proof Engines bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{45} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Abstract theorem type thm constructible only through primitive LCF inference rules`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `ProofKernelModule` (`LCFProofKernelContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Abstract theorem type thm, trusted inference rule-set digest, and primitive rule derivation replay.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 45         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, VERIFY`), calculates `ProofKernelModule` metrics under `LCFProofKernelContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_PROOF_TERM_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 45 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_45_proof_kernel_boundary` family schema:

```json
{
  "schema_id": "sg_packet_level_45_proof_kernel_boundary",
  "task_data": {
    "level": 45,
    "epoch": "Epoch III",
    "domain": "Proof Engines",
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
    "trusted_rule_digest": "sha256:7f8e9d...",
    "theorem_sequent": {"hypotheses": ["A", "A -> B"], "conclusion": "B"},
    "primitive_rule_applied": "ModusPonens",
    "derivation_steps": ["axiom_1", "hyp_1", "step_mp"],
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
pub struct LCFProofKernelPayload {
    pub move_type: MoveType,
    pub trusted_rule_digest: String,
    pub theorem_sequent: TheoremSequent,
    pub primitive_rule_applied: String,
    pub derivation_steps: Vec<String>,
    pub proposer_signature: String,
}

pub struct Level45Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: LCFProofKernelPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: ProofKernelModule

### Contract: `LCFProofKernelContract`

Referees evaluate Level 45 candidates through LCF-style trusted computing base verification:

1. **Abstract Theorem Encapsulation:** Values of type $\mathrm{thm}$ cannot be constructed via string injection or ad-hoc data literals; they must be constructed strictly via declared primitive inference rules.
2. **Primitive Rule Derivation Replay:** Evaluates candidate inference step $R(\phi_1, \ldots, \phi_k) \vdash \psi$, verifying that premises $\phi_i$ are valid previously certified theorems and $R$ is an admitted rule in the trusted kernel.
3. **Hypothesis Context Tracking:** Asserts hypothesis discharge correctness (e.g. implication introduction discharges antecedent).
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the proposed theorem sequent is derived strictly through the replay of primitive LCF inference rules without kernel breach.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an unproved primitive axiom declared in the trusted computing base is admitted with zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 45 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_PROOF_TERM_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 45, "carrier_match": true, "move": "ASSERT", "theorem_sequent": {"hypotheses": ["A", "A -> B"], "conclusion": "B"}, "primitive_rule_applied": "ModusPonens"}
REFEREE:  ACCEPT -> Status: ExactRepair (theorem sequent successfully derived via primitive ModusPonens rule in LCF kernel)
  ```

  **Worked check (2026-10-20):** modus ponens takes premises $A$ and $A \to B$ to conclusion $B$, which is the stated sequent $A, A \to B \vdash B$. In the negative vector the sequent $A \vdash B$ is not derivable from $A$ alone by any sound rule (take $A$ true and $B$ false), and its rule name is not in the admitted set, so the refusal follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 45, "carrier_match": true, "move": "ASSERT", "theorem_sequent": {"hypotheses": ["A"], "conclusion": "B"}, "primitive_rule_applied": "ForgedRuleWithoutPremise"}
REFEREE:  REFUSED -> Refusal Code: ERR_PROOF_TERM_DEFECT, Status: Refused (forged theorem derivation: rule is unadmitted in LCF trusted computing base)
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 45, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 45: LCF Proof Kernel & Trusted Computing Base within the Proof Engines bounded context.
   - A proposed PFP packet envelope, `ProofKernelModule` (`LCFProofKernelContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 45 specifies an exact, deterministic evaluation procedure for candidate proposals over `Abstract theorem type thm constructible only through primitive LCF inference rules`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
