---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 80: Macaroon Caveat Chains & Scoped Delegation"
kind: grammar-reference
level: 80
epoch: "Epoch VIII"
domain: "Authorization"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "AuthorityModule"
evaluator_contract: "AuthorizationContract"
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

# The Symbol Game Level 80: Macaroon Caveat Chains & Scoped Delegation

**AuthorityEffect:** None.  
**Level:** Level 80 | **Epoch:** Epoch VIII | **Domain:** Authorization  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Cryptographic authorization tokens with append-only HMAC caveat chains`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `REFUSED_ACTION_NOT_PERMITTED`  
**Evaluator Module:** `AuthorityModule` (`AuthorizationContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `AuthorityModule` or contract `AuthorizationContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 80 establishes the Proposal Fidelity Protocol (PFP) arena for **Macaroon Caveat Chains & Scoped Delegation** within the Authorization bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{80} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Cryptographic authorization tokens with append-only HMAC caveat chains`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `AuthorityModule` via `AuthorizationContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Auditing delegation scope attenuation and refusing privilege escalation attacks.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 80        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `AuthorizationContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `REFUSED_ACTION_NOT_PERMITTED`) are emitted exclusively by `AuthorizationContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 80 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_80` schema:

```json
{
  "schema_id": "sg_packet_level_80_authorization",
  "task_data": {
    "level": 80,
    "epoch": "Epoch VIII",
    "domain": "Authorization",
    "carrier_digest": "blake3:carrier_level_80..."
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
    "token_id": "macaroon_tok_80_001",
    "root_identifier": "root_authority_id_80",
    "principal": "elder_theoria",
    "caveats": [
      {
        "caveat_id": "cav_01",
        "predicate": "action == read"
      },
      {
        "caveat_id": "cav_02",
        "predicate": "resource == /data/partition_1"
      },
      {
        "caveat_id": "cav_03",
        "predicate": "time <= 1700000000"
      }
    ],
    "signature_chain": [
      {
        "step": 0,
        "hmac": "hmac_sha256_root"
      },
      {
        "step": 1,
        "hmac": "hmac_sha256_cav_01"
      },
      {
        "step": 2,
        "hmac": "hmac_sha256_cav_02"
      },
      {
        "step": 3,
        "hmac": "hmac_sha256_cav_03"
      }
    ],
    "requested_action": "read",
    "requested_resource": "/data/partition_1",
    "verifier_context": {
      "caller_identity": "worker_agent_01",
      "current_time": 1699999000
    }
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_80"
  }
}
```

### AST Representation
```rust
pub struct ScopedAuthorizationPayload {
    pub token_id: String,
    pub root_identifier: String,
    pub principal: String,
    pub caveats: Vec<CaveatPredicate>,
    pub signature_chain: Vec<HmacStep>,
    pub requested_action: String,
    pub requested_resource: String,
    pub verifier_context: VerifierContext,
}
```

---

## 4. Evaluator Module & Objective Metrics: AuthorityModule

Referees evaluate candidates through `AuthorizationContract`:

Referees evaluate candidates through cryptographic HMAC verification and monotonic attenuation checks:
1. **Cryptographic Chaining:** Asserts that each caveat signature is derived as $H_i = \operatorname{HMAC}(H_{i-1}, C_i)$ from the declared root key.
2. **Scope Attenuation Invariant:** Verifies that delegated capabilities can only shrink: $\operatorname{scope}_{\text{delegated}} \subseteq \operatorname{scope}_{\text{principal}}$.
3. **Context Satisfaction:** Evaluates whether `requested_action` and `requested_resource` satisfy all caveats under `verifier_context`.
4. **Authority Firewall:** Asserts `AuthorityEffect: None`; successful verification mints zero ambient authority.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Valid HMAC caveat chain $H_i = \operatorname{HMAC}(H_{i-1}, C_i)$, attenuation verified (delegated scope does not exceed principal scope), and all caveats satisfied under the verifier context.
- **`StabilizedSurvivor` Admission Criterion:** Terminal non-escalated delegation capability recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 80 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `REFUSED_ACTION_NOT_PERMITTED`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 80, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no token, caveats, signature chain, request or verifier context, so none of the four checks in section 4 can be run on it; the `ExactRepair` line is a stated expectation only.

  **Worked check (2026-10-20):** The section 3 schema example is the checkable instance. `requested_action` `read` satisfies `action == read`; `requested_resource` `/data/partition_1` satisfies `resource == /data/partition_1`; `current_time` $1699999000 \le 1700000000$ satisfies the time caveat. All three caveats hold. The `hmac` values are placeholder labels, not computed HMACs, so the chain $H_i = \operatorname{HMAC}(H_{i-1}, C_i)$ cannot be checked from the packet. The domain negative vector requests `write` under `action == read`, so the caveat fails and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 80, "carrier_match": true, "requested_action": "write", "caveats": [{"predicate": "action == read"}]}
  REFEREE:  REFUSED -> Refusal Code: REFUSED_ACTION_NOT_PERMITTED, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 80, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Machine-verifiable Macaroon caveat attenuation and cryptographic scope confinement.
   - A proposed PFP packet envelope, `AuthorizationContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not grant operational authority or claim global trust for authenticated tokens.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Specifies an exact host referee for verifying that delegated Macaroon caveat chains do not expand scope (no such referee exists at the source pin).
4. **Next test needed:**
   - Implement the Rust Macaroon evaluation referee, then replay these vectors against it.
