---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 00: The Sub-Binary Ground & Void Wire Packet"
kind: grammar-reference
level: 0
epoch: "Base Tower"
domain: "Substrate Foundations"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "SubstrateModule"
reachable_terminal_statuses:
  - ExactRepair
  - OpenObstruction
  - Refused
  - Invalid
source_paths:
  - education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 00: The Sub-Binary Ground & Void Wire Packet

**AuthorityEffect:** None.  
**Level:** Level 00 | **Epoch:** Base Tower | **Domain:** Substrate Foundations  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Void Wire Carrier ⟨⟩, |C| < 2`  
**Fuel Budget:** `1 turns` | **Permitted Moves:** `ASSERT, RETRACT`  
**Primary Domain Error Code:** `ERR_EMPTY_CARRIER`  
**Evaluator Module:** `SubstrateModule` (`Void Wire Substrate Evaluator`)  

**Source status (rechecked 2026-10-22 at `305b9690f9`):** specification only. No evaluator named `SubstrateModule`, no schema id `canonical_paper043_packet_lvl_00` and no level referee occur in `engine`, `pfp` or `lean4` (`git grep`). The same absence was recorded on 2026-10-20 at `c419cc6beb`. The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values such as `blake3:b8d4e900` are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs), which still lists exactly eight variants.

---

## 1. Game Board & Conceptual Arena

Level 00 establishes the Proposal Fidelity Protocol (PFP) arena for **The Sub-Binary Ground & Void Wire Packet** within the Substrate Foundations bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{00} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Void Wire Carrier ⟨⟩, |C| < 2`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SubstrateModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 1$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Zero degrees of freedom sub-binary ground admitting strictly the atomic 2-byte token <> and enforcing Ground Inertia.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 00         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, RETRACT`), calculates `SubstrateModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **1 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_EMPTY_CARRIER`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 00 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_00` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_00",
  "task_data": {
    "level": 0,
    "epoch": "Base Tower",
    "domain": "Substrate Foundations",
    "carrier_digest": "blake3:b8d4e900"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 1
  },
  "budget": {
    "turn_fuel_remaining": 1,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "token_sequence": "<>",
    "bracket_depth": 1,
    "ground_inertia_verified": true,
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
pub struct Level00Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: SubstrateTokenPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: SubstrateModule

Referees evaluate Level 00 candidates through atomic substrate balance and ground inertia:

1. **Carrier Invariance:** Carrier $\mathcal{C} = \langle\rangle$ with zero degrees of freedom ($|\mathcal{C}| < 2$).
2. **Mark Parity:** Tokens must strictly match the atomic 2-byte bracket symbol `<>`.
3. **Ground Inertia:** Evaluates that the empty slate admits no ungrounded relational assertions without a prior cut.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` upon successful verification of Ground Inertia with zero syntax mutations.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 00 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_EMPTY_CARRIER`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_00",
  "task_data": {
    "level": 0,
    "epoch": "Base Tower",
    "domain": "Substrate Foundations",
    "carrier_digest": "blake3:b8d4e900"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 1
  },
  "budget": {
    "turn_fuel_remaining": 1,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "raw_bytes_hex": "3c3e",
    "token_sequence": "<>",
    "bracket_depth": 1,
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
REFEREE: ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
```

- **Domain Negative Counterexample (Domain Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_00",
  "task_data": {
    "level": 0,
    "epoch": "Base Tower",
    "domain": "Substrate Foundations",
    "carrier_digest": "blake3:b8d4e900"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 1
  },
  "budget": {
    "turn_fuel_remaining": 1,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "raw_bytes_hex": "3c3e3c3e",
    "token_sequence": "<><>",
    "bracket_depth": 1,
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
REFEREE: REFUSED -> Refusal Code: ERR_TRAILING_GROUND_DATA, Status: Refused
```

**Worked check (rechecked 2026-10-22):** In ASCII, `<` is byte `0x3c` and `>` is byte `0x3e`. The valid token `<>` is therefore the two bytes `3c3e`, matching `raw_bytes_hex`. The negative packet `<><>` is `3c3e3c3e`: the first two bytes are the ground token and the last two are trailing data, which is what `ERR_TRAILING_GROUND_DATA` names. Both packets report `bracket_depth: 1`; that field is the same in both, so the refusal rests on byte length, not depth.

## Listen, then watch

This block is a recording plan. Nothing here was spoken into a file on 2026-10-22.

**Plain opening.** Level 00 asks one question: is the proposal exactly the two-character mark left angle bracket, right angle bracket, and nothing after it? No program in the source runs that question. A line that begins `REFEREE:` is the specified answer, not a log.

**Terms at first use.** The carrier is the allowed mark. Ground inertia means the empty board admits only that one mark. `ExactRepair` would mean the mark matched. `Refused` means the bytes were readable and still wrong. `Invalid` means the packet could not be read as this specification.

**One number before the general rule.** The character `<` is byte 60, written `3c` in hexadecimal. The character `>` is byte 62, written `3e`. The mark `<>` is the two bytes `3c 3e`. The longer mark `<><>` is `3c 3e 3c 3e`, four bytes. Two bytes is the specified accept. Four bytes is the specified refusal. The general rule, in section 4, is that any extra byte after the mark fails ground inertia.

**A check you can fail.** Both packets print `bracket_depth` equal to 1. If you refuse the long mark because the depth changed, the check fails. The depth did not change. The length did.

**Spoken segment.** Duration: 35 seconds. One idea: the mark is two bytes, and a second copy is four.

> Left angle bracket, right angle bracket. That is two bytes. Say the hex digits: three c, then three e. Do not say them as a word. A second copy is four bytes: three c, three e, three c, three e. Four bytes is refused. The depth number is one on both packets, so depth is not the reason. No referee in the source printed this. It is the specification.

**Check with no screen.** How many bytes are in one left angle bracket followed by one right angle bracket? If you said four, you counted a second copy, or you counted letters in a word. The answer is two.

**Video beats.** Narration matches the prose above. On-screen words stay short. Do not color the outcome without the word.

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:08 | `<>` is two bytes | "The whole mark is a left angle bracket and a right angle bracket. Two bytes." |
| 0:08–0:18 | `3c 3e` | "Those bytes are three c, then three e. Say the hex digits." |
| 0:18–0:28 | `<><>` is four bytes | "A second copy is three c, three e, three c, three e. Four bytes is refused." |
| 0:28–0:40 | depth 1 on both | "Both packets say depth one. Depth is not the reason. Length is." |
| 0:40–0:50 | specification only | "No referee in the source ran this. The line is a specified outcome, not a log." |

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_00",
  "task_data": {
    "level": 0,
    "epoch": "Base Tower",
    "domain": "Substrate Foundations",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 1
  },
  "budget": {
    "turn_fuel_remaining": 1,
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
   - Formal specification of The Symbol Game Level 00 (The Sub-Binary Ground & Void Wire Packet) within the Substrate Foundations bounded context.
   - A proposed PFP packet envelope, `SubstrateModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 00 specifies an exact, deterministic evaluation procedure for candidate proposals over `Void Wire Carrier ⟨⟩, |C| < 2`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
