---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 01: Symbol Genesis & Rigid Binary Cuts"
kind: grammar-reference
level: 1
epoch: "Base Tower"
domain: "Combinatorial Rigidity"
game_edition: "v3 L1 Oracle Governor"
status: active
maturity: instructional
claim_status: specified
authority_effect: "None"
evaluator_module: "RigidityModule"
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

# The Symbol Game Level 01: Symbol Genesis & Rigid Binary Cuts

**AuthorityEffect:** None.  
**Level:** Level 01 | **Epoch:** Base Tower | **Domain:** Combinatorial Rigidity  
**Game Edition:** `v3 L1 Oracle Governor`  
**Board Carrier:** `Directed 2-vertex Cut D₂ = ({0, 1}, {(0, 1)})`  
**Fuel Budget:** `3 turns` | **Permitted Moves:** `ASSERT, CUT`  
**Primary Domain Error Code:** `ERR_BINARY_CUT_MALFORMED`  
**Evaluator Module:** `RigidityModule` (`Combinatorial Rigidity & Binary Cut Evaluator`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `RigidityModule`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 01 establishes the Proposal Fidelity Protocol (PFP) arena for **Symbol Genesis & Rigid Binary Cuts** within the Combinatorial Rigidity bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{01} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Directed 2-vertex Cut D₂ = ({0, 1}, {(0, 1)})`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `RigidityModule` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 3$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Rigid asymmetric directed cuts breaking permutation symmetry with Aut(D₂) = {id} and establishing binary naming expansion.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 01         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT`), calculates `RigidityModule` metrics, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **3 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_BINARY_CUT_MALFORMED`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 01 are specified as JSON envelopes for the proposed (not yet implemented) `canonical_paper043_packet_lvl_01` family schema:

```json
{
  "schema_id": "canonical_paper043_packet_lvl_01",
  "task_data": {
    "level": 1,
    "epoch": "Base Tower",
    "domain": "Combinatorial Rigidity",
    "carrier_digest": "blake3:b8d4e901"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 3
  },
  "budget": {
    "turn_fuel_remaining": 3,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "cut_edge": [
      0,
      1
    ],
    "orientation": "forward",
    "automorphism_order": 1,
    "symmetry_broken": true,
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
pub struct Level01Packet {
    pub schema_id: String,
    pub task_data: TaskData,
    pub protected_boundary: ProtectedBoundary,
    pub budget: BudgetAllocation,
    pub candidate_payload: BinaryCutPayload,
    pub witness_data: WitnessData,
}
```

---

## 4. Evaluator Module & Objective Metrics: RigidityModule

Referees evaluate Level 01 candidates through combinatorial asymmetry and rigid cut metrics:

1. **Asymmetry Check:** Verifies directed 2-vertex cut $D_2 = (\{0, 1\}, \{(0, 1)\})$ has trivial automorphism group $\operatorname{Aut}(D_2) = \{\mathrm{id}\}$.
2. **Cut Integrity:** Verifies orientation $0 \to 1$ is preserved under permutation actions.
3. **Naming Capacity:** Asserts binary uplift capacity over $\{0, 1\}$.
4. **Admission Criterion:** Candidate is admitted to `ExactRepair` iff the rigid cut is verified without symmetry degeneration.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 01 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | Dormant / Unreachable in this stage. No non-erasable survivor state defined on this carrier; all admissible outcomes resolve to `ExactRepair`. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; fuel budget exhausted without resolution. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Dormant / Unreachable in this stage. Local referee does not emit lift licenses; ascent requires external CEC certification. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_BINARY_CUT_MALFORMED`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_01",
  "task_data": {
    "level": 1,
    "epoch": "Base Tower",
    "domain": "Combinatorial Rigidity",
    "carrier_digest": "blake3:b8d4e901"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 3
  },
  "budget": {
    "turn_fuel_remaining": 3,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "vertices": [
      0,
      1
    ],
    "cut_edge": [
      0,
      1
    ],
    "automorphism_permutations": [
      [
        0,
        1
      ]
    ],
    "automorphism_order": 1,
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
  "schema_id": "canonical_paper043_packet_lvl_01",
  "task_data": {
    "level": 1,
    "epoch": "Base Tower",
    "domain": "Combinatorial Rigidity",
    "carrier_digest": "blake3:b8d4e901"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 3
  },
  "budget": {
    "turn_fuel_remaining": 3,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "vertices": [
      0,
      1
    ],
    "cut_edge": [
      1,
      0
    ],
    "automorphism_permutations": [
      [
        0,
        1
      ]
    ],
    "automorphism_order": 1,
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
REFEREE: REFUSED -> Refusal Code: ERR_ORIENTATION_MISMATCH, Status: Refused
```

**Worked check (2026-10-20):** The set `{0, 1}` has two bijections: the identity and the swap `0 <-> 1`. The swap sends the edge `(0, 1)` to `(1, 0)`, which is not in `E = {(0, 1)}`, so it is not an automorphism. Only the identity remains: `Aut(D2) = {id}`, of order 1, which matches `automorphism_permutations: [[0, 1]]` and `automorphism_order: 1`. The negative packet's edge `(1, 0)` would also give a rigid directed cut on its own; it is refused because it disagrees with the pinned carrier edge `(0, 1)`, not because it is symmetric.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
```json
{
  "schema_id": "canonical_paper043_packet_lvl_01",
  "task_data": {
    "level": 1,
    "epoch": "Base Tower",
    "domain": "Combinatorial Rigidity",
    "carrier_digest": "unpinned:raw_symbol_injection"
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 3
  },
  "budget": {
    "turn_fuel_remaining": 3,
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
   - Formal specification of The Symbol Game Level 01 (Symbol Genesis & Rigid Binary Cuts) within the Combinatorial Rigidity bounded context.
   - A proposed PFP packet envelope, `RigidityModule` evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 01 specifies an exact, deterministic evaluation procedure for candidate proposals over `Directed 2-vertex Cut D₂ = ({0, 1}, {(0, 1)})`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
