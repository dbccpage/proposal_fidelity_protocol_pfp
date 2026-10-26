---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 90: Natural Language Extraction & Semantic Loss Ledgers"
kind: grammar-reference
level: 90
epoch: "Epoch IX"
domain: "Language Grounding"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "SemanticLossContract"
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

# The Symbol Game Level 90: Natural Language Extraction & Semantic Loss Ledgers

**AuthorityEffect:** None.  
**Level:** Level 90 | **Epoch:** Epoch IX | **Domain:** Language Grounding  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Natural-language requirement corpora paired with formal ASTs and uncaptured clause ledgers`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SOURCE_SPAN_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`SemanticLossContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `SemanticLossContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 90 establishes the Proposal Fidelity Protocol (PFP) arena for **Natural Language Extraction & Semantic Loss Ledgers** within the Language Grounding bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{90} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Natural-language requirement corpora paired with formal ASTs and uncaptured clause ledgers`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `SemanticLossContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Auditing machine-verifiable structural coverage while registering unformalized natural language clauses in explicit semantic loss ledgers.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 90        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `SemanticLossContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SOURCE_SPAN_DEFECT`) are emitted exclusively by `SemanticLossContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 90 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_90` schema:

```json
{
  "schema_id": "sg_packet_level_90_language_grounding",
  "task_data": {
    "level": 90,
    "epoch": "Epoch IX",
    "domain": "Language Grounding",
    "carrier_digest": "blake3:carrier_level_90..."
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
    "source_spans": [
      {
        "span_id": "req_01",
        "text": "Must reject unverified keys",
        "digest": "sha256:span_01_text"
      }
    ],
    "formal_ast": {
      "type": "Assertion",
      "predicate": "KeyVerified(k)"
    },
    "structural_coverage": "1/1",
    "loss_ledger": [
      {
        "clause": "promptly",
        "status": "uncaptured_temporal_vagueness",
        "residual_type": "semantic_debt"
      }
    ]
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_90"
  }
}
```

### AST Representation
```rust
pub struct SemanticLossPayload {
    pub source_spans: Vec<SourceSpan>,
    pub formal_ast: serde_json::Value,
    pub structural_coverage: BigRational,
    pub loss_ledger: Vec<SemanticLossEntry>,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `SemanticLossContract`:

Referees decouple machine-checkable structural coverage from subjective semantic evaluation:
1. **Structural Coverage Audit:** Evaluates machine-checkable mappings from source requirement spans to AST elements.
2. **Explicit Loss Registration:** Verifies that every natural language nuance not formally captured is logged in `loss_ledger`.
3. **Epistemic Honesty Gate:** Refuses claims of complete natural-language formalization when uncaptured clauses remain.
4. **Authority Firewall:** Asserts `AuthorityEffect: None`; semantic extraction mints zero operational authority.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Machine-checkable structural coverage verified; every unformalized natural language clause is explicitly recorded in `loss_ledger` with typed residual category.
- **`StabilizedSurvivor` Admission Criterion:** Structured requirement mapping with explicit semantic debt certified under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 90 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SOURCE_SPAN_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 90, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no spans, AST or ledger, so the checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** The data as printed do not support the domain negative disposition. Its only span text is `Must reject unverified keys`, and the AST `KeyVerified(k)` with a rejection assertion covers that sentence; no clause in the text is left uncaptured, so an empty `loss_ledger` is consistent with the data. The section 3 schema example has the same mismatch in the other direction: its ledger records the clause `promptly`, which does not occur in its span text. The negative vector would support `Refused` if its span text contained an uncaptured clause, for example `Must promptly reject unverified keys` with the ledger left empty; that text is a suggested repair, not the recorded fixture.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 90, "carrier_match": true, "source_spans": [{"span_id": "req_01", "text": "Must reject unverified keys"}], "loss_ledger": []}
  REFEREE:  REFUSED -> Refusal Code: ERR_SOURCE_SPAN_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 90, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Machine-verifiable coverage tracking of requirement spans and explicit registration of semantic loss debt.
   - A proposed PFP packet envelope, `SemanticLossContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not claim general host decidability of human natural-language intent or philosophical meaning.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that parsed AST elements cover declared spans and unmodeled clauses are explicitly tracked as residuals.
4. **Next test needed:**
   - Replay extraction verification against normative specification corpora.
