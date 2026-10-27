---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 34: Fisher Information Metrics & Statistical Manifolds"
kind: grammar-reference
level: 34
epoch: "Epoch II"
domain: "Information Geometry"
game_edition: "Trans-Base Arena"
status: active
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
formal_status: none
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "InformationGeometryModule"
evaluator_contract: "StatisticalManifoldContract"
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

# The Symbol Game Level 34: Fisher Information Metrics & Statistical Manifolds

**AuthorityEffect:** None.  
**Level:** Level 34 | **Epoch:** Epoch II | **Domain:** Information Geometry  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `Parametric probability family M = {P_θ} with exact rational Fisher metric g_ij`  
**Fuel Budget:** `10 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_PARAMETRIC_FAMILY_DEFECT`  
**Evaluator Module:** `InformationGeometryModule` (`Fisher Information Metric & Certified KL Enclosure Evaluator`)  
**Evaluator Contract:** `StatisticalManifoldContract`  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `InformationGeometryModule` or contract `StatisticalManifoldContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 34 establishes the Proposal Fidelity Protocol (PFP) arena for **Fisher Information Metrics & Statistical Manifolds** within the Information Geometry bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{34} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `Parametric probability family M = {P_θ} with exact rational Fisher metric g_ij`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `InformationGeometryModule` (`StatisticalManifoldContract`) calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 10$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Exact rational Fisher information metric tensor g_ij(θ) and certified interval enclosures for relative entropy.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 34         ┌──────────────────────────┐
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
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), calculates `InformationGeometryModule` metrics under `StatisticalManifoldContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **10 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_PARAMETRIC_FAMILY_DEFECT`) are emitted exclusively by the domain evaluator.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 34 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_34_statistical_manifolds` family schema:

```json
{
  "schema_id": "sg_packet_level_34_statistical_manifolds",
  "task_data": {
    "level": 34,
    "epoch": "Epoch II",
    "domain": "Information Geometry",
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
    "parameter_theta": ["1/3", "1/3"],
    "fisher_metric_tensor": [
      ["6", "3"],
      ["3", "6"]
    ],
    "kl_certified_interval": ["1/10", "3/20"],
    "positive_semidefinite_witness": "min_eigenvalue_gt_zero",
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
pub struct StatisticalManifoldPayload {
    pub move_type: MoveType,
    pub parameter_theta: Vec<Rational>,
    pub fisher_metric_tensor: Vec<Vec<Rational>>,
    pub kl_certified_interval: (Rational, Rational),
    pub positive_semidefinite_witness: String,
    pub proposer_signature: String,
}

pub struct Level34Packet {
    pub schema_id: String,
    pub level_index: u32,
    pub carrier_state: CarrierState,
    pub candidate_move: MoveType,
    pub payload: StatisticalManifoldPayload,
    pub witness: Option<WitnessProof>,
}
```

---

## 4. Evaluator Module & Objective Metrics: InformationGeometryModule

### Contract: `StatisticalManifoldContract`

Referees evaluate Level 34 candidates through information geometry and Riemannian metric validation:

1. **Exact Rational Fisher Metric:** For rational parametric probability family $P_\theta$, computes the Fisher information metric tensor $g_{ij}(\theta)$ over $\mathbb{Q}$:
   $$g_{ij}(\theta) = \mathbb{E}_\theta\left[\frac{\partial \log P_\theta}{\partial \theta^i} \frac{\partial \log P_\theta}{\partial \theta^j}\right]$$
2. **Positive Definiteness:** Asserts $v^T g(\theta) v > 0$ for all $v \in \mathbb{Q}^d \setminus \{0\}$, verifying metric non-degeneracy on the statistical manifold. *(Corrected 2026-10-20: the earlier condition $\ge 0$ is positive semi-definiteness, which permits a degenerate metric; non-degeneracy, and the `ExactRepair` criterion below, need strict positivity.)*
3. **Certified Relative Entropy Enclosures:** Relative entropy $D_{\mathrm{KL}}(P \parallel Q)$ involves transcendental logarithms and is not generally closed in $\mathbb{Q}$; referees certify interval enclosures $[\underline{D}_{\mathrm{KL}}, \overline{D}_{\mathrm{KL}}] \subset \mathbb{Q}$ bounding the true divergence.
4. **Machine Criteria for Terminal Dispositions:**
   - **`ExactRepair` Admission Criterion:** Admitted iff the candidate parameter lies in the open probability simplex, $g_{ij}(\theta)$ is strictly positive definite over $\mathbb{Q}$, and KL interval enclosures are verified.
   - **`StabilizedSurvivor` Admission Criterion:** Admitted under license iff an invariant non-flat information Riemannian connection (e.g. Chentsov's alpha-connection) is certified non-vanishing on the statistical carrier, recording zero authority minted.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 34 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_PARAMETRIC_FAMILY_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 34, "carrier_match": true, "move": "ASSERT", "parameter_theta": ["1/3", "1/3"], "fisher_metric_tensor": [["6", "3"], ["3", "6"]], "positive_semidefinite_witness": "det_27_gt_0"}
REFEREE:  ACCEPT -> Status: ExactRepair (Fisher information metric tensor is exact rational and strictly positive definite)
  ```

  **Worked check (2026-10-20):** the file does not name the family. *Assumption:* $P_\theta$ is the categorical distribution on three outcomes with free parameters $(\theta_1, \theta_2)$ and $\theta_3 = 1 - \theta_1 - \theta_2$. Its Fisher metric is $g_{ij} = \delta_{ij}/\theta_i + 1/\theta_3$. At $\theta = (1/3, 1/3)$, $\theta_3 = 1/3$, so $g = \begin{pmatrix} 3+3 & 3 \\ 3 & 3+3 \end{pmatrix} = \begin{pmatrix} 6 & 3 \\ 3 & 6 \end{pmatrix}$, matching the packet. $\det g = 36 - 9 = 27 > 0$ and $\operatorname{tr} g = 12 > 0$, so $g$ is positive definite; its eigenvalues are $9$ and $3$, consistent with the schema label `min_eigenvalue_gt_zero`.

  **Reproducibility gap (2026-10-20):** the schema's `kl_certified_interval` $[1/10, 3/20]$ does not name the pair $(P, Q)$ whose divergence it encloses, so it cannot be checked.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 34, "carrier_match": true, "move": "ASSERT", "parameter_theta": ["3/2", "1/2"], "fisher_metric_tensor": [["6", "3"], ["3", "6"]]}
REFEREE:  REFUSED -> Refusal Code: ERR_PARAMETRIC_FAMILY_DEFECT, Status: Refused (parameter theta = 3/2 lies outside declared valid probability simplex)
  ```

  **Worked check (2026-10-20):** $\theta_1 = 3/2 > 1$ and $\theta_1 + \theta_2 = 2 > 1$ (so $\theta_3 = -1$), so $\theta$ is outside the open simplex and the refusal follows. The packet repeats the metric $\begin{pmatrix} 6 & 3 \\ 3 & 6 \end{pmatrix}$, which is not the Fisher metric at this $\theta$; the refusal does not depend on it.

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 34, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of The Symbol Game Level 34: Fisher Information Metrics & Statistical Manifolds within the Information Geometry bounded context.
   - A proposed PFP packet envelope, `InformationGeometryModule` (`StatisticalManifoldContract`) evaluation equations, and typed referee error dispatch.
2. **What this does not support:**
   - Does not assert unverified physical continuum emergence or continuous domain properties.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Level 34 specifies an exact, deterministic evaluation procedure for candidate proposals over `Parametric probability family M = {P_θ} with exact rational Fisher metric g_ij`.
4. **Next test needed:**
   - Implement the level referee, then replay these vectors against it; no referee for this level exists at the source pin.
