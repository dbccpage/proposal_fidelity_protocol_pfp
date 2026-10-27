---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 82: Software Supply Chain Provenance (SLSA v1.0)"
kind: grammar-reference
level: 82
epoch: "Epoch VIII"
domain: "Supply Chain Security"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "SupplyChainProvenanceContract"
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

# The Symbol Game Level 82: Software Supply Chain Provenance (SLSA v1.0)

**AuthorityEffect:** None.  
**Level:** Level 82 | **Epoch:** Epoch VIII | **Domain:** Supply Chain Security  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Cryptographic build receipts, content-addressed materials, and signed in-toto/SLSA v1.0 statements`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_SIGNED_MANIFEST_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`SupplyChainProvenanceContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `SupplyChainProvenanceContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 82 establishes the Proposal Fidelity Protocol (PFP) arena for **Software Supply Chain Provenance (SLSA v1.0)** within the Supply Chain Security bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{82} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Cryptographic build receipts, content-addressed materials, and signed in-toto/SLSA v1.0 statements`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `SupplyChainProvenanceContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying SLSA v1.0 verifiable build provenance receipts, material digests, and builder attestations.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 82        ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `SupplyChainProvenanceContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_SIGNED_MANIFEST_DEFECT`) are emitted exclusively by `SupplyChainProvenanceContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 82 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_82` schema:

```json
{
  "schema_id": "sg_packet_level_82_supply_chain_security",
  "task_data": {
    "level": 82,
    "epoch": "Epoch VIII",
    "domain": "Supply Chain Security",
    "carrier_digest": "blake3:carrier_level_82..."
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
    "subject_name": "referee",
    "subject_digest": "sha256:a1b2c3d4e5f67890...",
    "builder_id": "https://trusted-builder.local/v1",
    "build_type": "https://slsa.dev/provenance/v1",
    "materials": [
      {
        "uri": "git+https://github.com/the_symbol_game/repo",
        "digest": {
          "sha1": "3100c4e1a2b3c4d5"
        }
      }
    ],
    "predicate_type": "https://slsa.dev/provenance/v1",
    "signatures": [
      {
        "key_id": "key_ed25519_builder_01",
        "sig": "ed25519_sig_bytes_verified"
      }
    ],
    "trust_policy_digest": "sha256:policy_core_v1"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_82"
  }
}
```

### AST Representation
```rust
pub struct SupplyChainProvenancePayload {
    pub subject_name: String,
    pub subject_digest: String,
    pub builder_id: String,
    pub build_type: String,
    pub materials: Vec<ArtifactMaterial>,
    pub predicate_type: String,
    pub signatures: Vec<SignatureBlock>,
    pub trust_policy_digest: String,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `SupplyChainProvenanceContract`:

Referees audit build provenance statements against declared cryptographic trust policies:
1. **Subject Digest Binding:** Verifies that the built artifact digest matches declared `subject_digest`.
2. **Materials Purity:** Verifies that source materials match pinned repository commit digests.
3. **Builder Attestation:** Confirms that `builder_id` is authorized in `trust_policy_digest`.
4. **Signature Verification:** Validates builder digital signature against pinned public keys.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Valid SLSA v1.0 statement schema, builder ID authorized in policy, materials match pinned git commit, subject digest verified, and signature cryptographically verified.
- **`StabilizedSurvivor` Admission Criterion:** Sealed build provenance receipt recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 82 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_SIGNED_MANIFEST_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 82, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no subject, materials, builder or signature, so none of the four checks in section 4 can be run on it; the `ExactRepair` line is a stated expectation only. The domain negative vector names a tampered material digest but gives no pinned commit digest to compare it with.

  **Worked check (2026-10-20):** The section 3 schema example cannot be checked as printed. Its digests and signature are placeholder labels; the `sha1` value `3100c4e1a2b3c4d5` has 16 hexadecimal characters, while a SHA-1 digest has 40. Two field choices also differ from SLSA v1.0: `materials` is the v0.2 field (v1.0 records inputs under `buildDefinition.resolvedDependencies`), and `build_type` repeats the predicate type URI `https://slsa.dev/provenance/v1`, whereas in v1.0 `buildType` names the builder's own build template. The field names are kept here because they are the proposed schema's identifiers.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 82, "carrier_match": true, "materials": [{"uri": "git+repo", "digest": {"sha1": "tampered_commit_hash"}}]}
  REFEREE:  REFUSED -> Refusal Code: ERR_SIGNED_MANIFEST_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 82, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of SLSA v1.0 provenance receipts, materials digests, and cryptographic builder signatures.
   - A proposed PFP packet envelope, `SupplyChainProvenanceContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove that source code contains zero security vulnerabilities or functional defects.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that a given binary matches the recipe and cryptographic attestation emitted by an authorized builder.
4. **Next test needed:**
   - Execute end-to-end SLSA provenance verification against checked-in binary receipts.
