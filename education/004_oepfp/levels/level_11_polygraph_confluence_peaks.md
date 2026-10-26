---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 11: Term Rewriting, ARS Confluence & 3-Polygraphs"
kind: grammar-reference
level: 11
epoch: "Base Tower"
domain: "Rewriting Theory"
game_edition: "v2 Packet Iteration / v3"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "RewriteModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
source_paths:
  - omega_engine_education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - omega_engine_education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 11: Term Rewriting, ARS Confluence & 3-Polygraphs

**AuthorityEffect:** None.  
**Level:** Level 11 | **Epoch:** Base Tower | **Domain:** Rewriting Theory  
**Game Edition:** `v2 Packet Iteration / v3`  
**Board Carrier:** `Abstract Rewriting Systems (ARS) over 2-cells and 3-polygraphs`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_CRITICAL_PEAK_NOT_JOINABLE`  
**Evaluator Module:** `RewriteModule` (`Abstract Rewriting & Critical Peak Joinability Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `RewriteModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 11 establishes the Proposal Fidelity Protocol (PFP) arena for **Term Rewriting, ARS Confluence & 3-Polygraphs** within the Rewriting Theory bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{11} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Abstract Rewriting Systems (ARS) over 2-cells and 3-polygraphs`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `RewriteModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `omega-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Local joinability of replayed declared critical peaks s ← u → t with joining witness w without asserting global confluence.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 11         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `RewriteModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_CRITICAL_PEAK_NOT_JOINABLE`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 11 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_11` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_11",
  "task_data": {
    "level": 11,
    "epoch": "Base Tower",
    "domain": "Rewriting Theory",
    "carrier_digest": "blake3:b8d4e90b"
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
    "critical_peak": [
      "u",
      "s",
      "t"
    ],
    "joining_witness": "w",
    "peak_locally_joinable": true,
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```

### AST Representation
```rust
pub struct Level11Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: RewritePeakPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: RewriteModule

Referees evaluate Level 11 candidates through Abstract Rewriting Systems (ARS) over 2-cells:

1. **Redex Matching:** Verifies source redex $u$ and reduction branches $s \leftarrow u \to t$.
2. **Local Peak Joinability:** Audits replayed declared critical peaks for existence of a joining term $w$ such that $s \to^* w \leftarrow^* t$.
3. **Scoped Boundary:** Local joinability of declared peaks is verified without asserting global confluence or Newman termination lemmas.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff all declared critical peaks in the proposal are joinable within the fuel limit.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 11 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_CRITICAL_PEAK_NOT_JOINABLE`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_11",
  "task_data": {
    "level": 11,
    "epoch": "Base Tower",
    "domain": "Rewriting Theory",
    "carrier_digest": "blake3:b8d4e90b"
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
    "critical_peak": [
      "u",
      "s",
      "t"
    ],
    "joining_term": "w",
    "left_reduction_path": [
      "s->w"
    ],
    "right_reduction_path": [
      "t->w"
    ],
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved; peak joins at w via s->w and t->w)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_11",
  "task_data": {
    "level": 11,
    "epoch": "Base Tower",
    "domain": "Rewriting Theory",
    "carrier_digest": "blake3:b8d4e90b"
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
    "critical_peak": [
      "u",
      "s",
      "t"
    ],
    "closed_finite_rules": {
      "us": [
        "u",
        "s"
      ],
      "ut": [
        "u",
        "t"
      ]
    },
    "reachable_from_s": [
      "s"
    ],
    "reachable_from_t": [
      "t"
    ],
    "move_type": "ASSERT",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: REFUSED -> Refusal Code: ERR_CRITICAL_PEAK_NOT_JOINABLE, Status: Refused ({s} cap {t} = empty)
```

**Worked check (2026-10-20):** A peak `s <- u -> t` is joinable when some term is reachable from both `s` and `t`. In the valid packet, `s -> w` and `t -> w`, so `w` is a common reduct. In the negative packet, the only rules are `u -> s` and `u -> t`; neither `s` nor `t` rewrites further, so `Reach(s) = {s}` and `Reach(t) = {t}`. Their intersection is empty, so the peak is not joinable. This shows non-confluence of this finite system only; joinability of one peak is local confluence, and global confluence needs termination as well (Newman's lemma).

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_11",
  "task_data": {
    "level": 11,
    "epoch": "Base Tower",
    "domain": "Rewriting Theory",
    "carrier_digest": "unpinned:raw_symbol_injection"
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
    "move_type": "ASSERT",
    "injected_carrier_token": "\u03a9_UNPINNED",
    "proposer_signature": "untrusted_candidate_token"
  },
  "witness_data": {
    "replay_trace": [
      "corrupted_init"
    ],
    "proof_certificate": null
  }
}
```
```text
REFEREE: INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 11 (Term Rewriting, ARS Confluence & 3-Polygraphs) within the Rewriting Theory bounded context.
   - A proposed PFP packet envelope, `RewriteModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 11 specifies an exact, deterministic evaluation procedure for candidate proposals over `Abstract Rewriting Systems (ARS) over 2-cells and 3-polygraphs`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
