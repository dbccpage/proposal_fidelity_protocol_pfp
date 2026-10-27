---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 29: Derived Obstruction & Projective Resolutions"
kind: grammar-reference
level: 29
epoch: "Epoch I"
domain: "Homological Algebra"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "DerivedFunctorModule"
evaluator_contract: "ProjectiveResolutionContract"
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

# The Symbol Game Level 29: Derived Obstruction & Projective Resolutions

**AuthorityEffect:** None.  
**Level:** Level 29 | **Epoch:** Epoch I | **Domain:** Homological Algebra  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Projective resolutions P_• → M → 0 and derived functors Ext^n_R(M, N) over ring R = ℤ`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_RESOLUTION_COMPLEX_DEFECT`  
**Evaluator Module:** `DerivedFunctorModule` (`Projective Resolution & Derived Ext Evaluator (ℤ)`)  
**Evaluator Contract:** `ProjectiveResolutionContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `DerivedFunctorModule` or contract `ProjectiveResolutionContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 29 establishes the Proposal Fidelity Protocol (PFP) arena for **Derived Obstruction & Projective Resolutions** within the Homological Algebra bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{29} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Projective resolutions P_• → M → 0 and derived functors Ext^n_R(M, N) over ring R = ℤ`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `DerivedFunctorModule` (`ProjectiveResolutionContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exactness verification of projective resolutions P_• → M → 0 and derived extension functor Ext^n_ℤ(M, N) over ring ℤ.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 29         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `DerivedFunctorModule` metrics under `ProjectiveResolutionContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_RESOLUTION_COMPLEX_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 29 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_29_derived_obstruction` family schema:

```json
{
  "schema_id": "sg_packet_level_29_derived_obstruction",
  "task_data": {
    "level": 29,
    "epoch": "Epoch I",
    "domain": "Homological Algebra",
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
    "base_ring": "Z",
    "module_m": "Z_mod_n",
    "module_n": "Z",
    "projective_chain": ["P_1: Z", "P_0: Z"],
    "differential_matrices": {
      "d_1": [[2]],
      "augmentation_epsilon": [[1]]
    },
    "computed_ext_ranks": {"Ext_0": 0, "Ext_1": 1},
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
pub struct ProjectiveResolutionPayload {
    pub move_type: MoveType,
    pub base_ring: String,
    pub module_m: String,
    pub module_n: String,
    pub projective_chain: Vec<String>,
    pub differential_matrices: BTreeMap<String, Vec<Vec<i64>>>,
    pub computed_ext_ranks: BTreeMap<String, u32>,
    pub proposer_signature: String,
}

pub struct Level29Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: ProjectiveResolutionPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: DerivedFunctorModule

### Contract: `ProjectiveResolutionContract`

Referees evaluate Level 29 candidates through homological algebra over the integers $\mathbb{Z}$ (avoiding triviality over fields):

1. **Resolution Exactness Over $\mathbb{Z}$:** Verifies chain complex $\cdots \xrightarrow{d_2} P_1 \xrightarrow{d_1} P_0 \xrightarrow{\epsilon} M \to 0$ where each $P_i$ is a projective (free) $\mathbb{Z}$-module, evaluating exactness at each stage:
   $$\ker(\epsilon) = \operatorname{im}(d_1), \quad \ker(d_k) = \operatorname{im}(d_{k+1}) \quad (k \ge 1)$$
2. **Hom Functor Application:** Evaluates the dualized complex $0 \to \operatorname{Hom}_\mathbb{Z}(P_0, N) \xrightarrow{d_1^*} \operatorname{Hom}_\mathbb{Z}(P_1, N) \to \cdots$.
3. **Derived Extension Calculation:** Computes $\operatorname{Ext}^n_\mathbb{Z}(M, N) = H^n(\operatorname{Hom}_\mathbb{Z}(P_\bullet, N))$ over abelian group presentations.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the projective resolution is exact over $\mathbb{Z}$ and the candidate derived functor ranks match the cohomology of the dualized complex identically.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an extension class $[\xi] \in \operatorname{Ext}^1_\mathbb{Z}(\mathbb{Z}/n\mathbb{Z}, \mathbb{Z})$ is certified non-split (representing a non-trivial short exact sequence $0 \to \mathbb{Z} \to \mathbb{Z} \to \mathbb{Z}/n\mathbb{Z} \to 0$), recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 29 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_RESOLUTION_COMPLEX_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 29, "carrier_match": true, "move": "ASSERT", "base_ring": "Z", "differential_matrices": {"d_1": [[2]], "augmentation_epsilon": [[1]]}, "computed_ext_ranks": {"Ext_0": 0, "Ext_1": 1}}
REFEREE:  ACCEPT -> Status: ExactRepair (projective resolution over Z is exact; Ext^0 = 0 and Ext^1 = Z/2Z, one cyclic generator, Z-rank 0)
  ```

  **Worked check (2026-10-20):** $d_1 = [2]$ fixes $M = \mathbb{Z}/2\mathbb{Z}$ (the schema's `Z_mod_n` with $n = 2$). The resolution is $0 \to \mathbb{Z} \xrightarrow{\times 2} \mathbb{Z} \xrightarrow{\epsilon} \mathbb{Z}/2\mathbb{Z} \to 0$ with $\epsilon$ reduction mod 2. Exactness: $\ker \epsilon = 2\mathbb{Z} = \operatorname{im}(\times 2)$, and $\times 2$ is injective. Applying $\operatorname{Hom}_\mathbb{Z}(-, \mathbb{Z})$ gives $0 \to \mathbb{Z} \xrightarrow{\times 2} \mathbb{Z} \to 0$. Hence $\operatorname{Ext}^0 = \ker(\times 2) = 0$ and $\operatorname{Ext}^1 = \mathbb{Z}/2\mathbb{Z}$.

  **Correction (2026-10-20):** the payload value `"Ext_1": 1` is correct only if read as the number of cyclic generators. As a $\mathbb{Z}$-rank (dimension after tensoring with $\mathbb{Q}$), $\operatorname{Ext}^1_\mathbb{Z}(\mathbb{Z}/2\mathbb{Z}, \mathbb{Z})$ has rank 0, because it is torsion of order 2. The field name `computed_ext_ranks` is kept as a protocol identifier; the earlier referee text "Ext^1 rank verified" was replaced above.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 29, "carrier_match": true, "move": "ASSERT", "base_ring": "Z", "differential_matrices": {"d_1": [[0]], "augmentation_epsilon": [[1]]}, "computed_ext_ranks": {"Ext_0": 0, "Ext_1": 1}}
REFEREE:  REFUSED -> Refusal Code: ERR_RESOLUTION_COMPLEX_DEFECT, Status: Refused (resolution fails exactness condition: im(d_1) != ker(epsilon))
  ```

  **Worked check (2026-10-20):** with $d_1 = [0]$, $\operatorname{im}(d_1) = 0$ while $\ker \epsilon = 2\mathbb{Z} \ne 0$, so exactness at $P_0$ fails and the refusal follows from the data.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 29, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 29: Derived Obstruction & Projective Resolutions within the Homological Algebra bounded context.
   - A proposed PFP packet envelope, `DerivedFunctorModule` (`ProjectiveResolutionContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 29 specifies an exact, deterministic evaluation procedure for candidate proposals over `Projective resolutions P_• → M → 0 and derived functors Ext^n_R(M, N) over ring R = ℤ`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
