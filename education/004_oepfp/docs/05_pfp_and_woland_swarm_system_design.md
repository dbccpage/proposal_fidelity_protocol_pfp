---
documentation_contract: symbol-game-documentation/v1
title: "Proposal Fidelity Protocol (PFP) & Woland Base Swarm System Design"
kind: design-document
audience:
  - engineers
  - coding-agents
  - researchers
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - omega_engine_woland
  - omega_engine_pfp
  - omega_engine_education/documentation/004_oepfp
last_verified: 2026-10-20
verification_scope: object names checked against tracked Python, Rust and YAML; design content not re-derived
---

# 05. Proposal Fidelity Protocol (PFP) & Woland Base Swarm System Design

**AuthorityEffect:** `None`  
**Domain Location:** `omega_engine_education/documentation/004_oepfp/docs/05_pfp_and_woland_swarm_system_design.md` (formerly under strand `030_...`)  
**Governing Rules:** [`.agents/rules/genesis/rl_genesis_and_sn_architecture_discipline.md`](../../../../.agents/rules/genesis/rl_genesis_and_sn_architecture_discipline.md), [`.agents/rules/architecture/rl_clean_architecture_and_subsystem_governance.md`](../../../../.agents/rules/architecture/rl_clean_architecture_and_subsystem_governance.md)  
**Architectural Specification:** [`06_prompt_packet_stage_synthesis.md`](06_prompt_packet_stage_synthesis.md)  
**Associated Epic Saga:** `SAGA-OE-WOLAND-PFP-DESIGN-001` (its file `saga_oe_woland_pfp_and_base_swarm_system_design.md` is not present at the 2026-10-20 pin; the current Woland planning file is [epic_oe_woland_consolidated_residual_plan.md](../../../../omega_engine_product_planning_office/plans/epics/oewoland/epic_oe_woland_consolidated_residual_plan.md))  

> **Current-source status (2026-10-20, pin `c419cc6beb`).** This is a design document. Most objects it specifies are proposed, not implemented. A word search of tracked `*.py`, `*.rs`, `*.yaml`, `*.json`, `*.toml` and `*.lean` files found:
>
> | Object in this page | Status at the pin |
> | --- | --- |
> | `PfpModeCluster` and the five clusters with their mode lists | Implemented: [modes.py](../../../../omega_engine_pfp/domain/types/modes.py) line 15 and [mode_catalog.yaml](../../../../omega_engine_pfp/infrastructure/yaml/modes/mode_catalog.yaml). Cluster II is named "Internal Steering" in code, not "Internal & Attention Steering". The mode record is `PfpModeCatalogEntry` with `PfpVerifierContract`; there is no class named `PfpMode`. |
> | `PfpPrompt` | A class of this name exists in [pfp_runtime.py](../../../../omega_engine_pfp/domain/contracts/pfp_runtime.py) line 33, with different fields (system/user text and response schema). The `prompt_id`/`generation_id`/`sub_prompts`/`prompt_type` record in section 3.2.1 is proposed. |
> | `PfpPromptType`, `PfpStage`, `PfpGate`, `PfpPacket`, `WolandBoutSession`, `WolandRetinueCast`, `IntelligenceDigestionPipeline`, `ThesisProposal`, `behemoth_interrogation_gate` | No definition found. Proposed. |
> | Five-stage `PfpStage` enum in section 3.2.4 | Not the runtime. The public runtime has 11 numbered stages ([controller.yaml](../../../../omega_engine_pfp/infrastructure/yaml/stages/controller.yaml)); the finite-QM research workflow has six (P0 to P5). |
> | Dashboard values (`Phi_1 [0.942]`, `Gamma_2 [0.018]`, `Xi [0.003]`, "124 ingested traces") | Illustrative mock-up values, not output of any run. PFP metrics are exact rationals ([10](10_functional_metric_ownership.md)), so decimal displays like these are not what the host emits. |
> | `stealth_cochain_tuple` as exact rationals `[Phi_1, Gamma_2, Xi]` | Proposed. In Rust, `Xi` is a diagnostic carrying an `f64` display value and a separate certified representation ([xi_diagnostic.rs](../../../../omega_engine/crates_rs/omega_types/src/xi_diagnostic.rs)); it is not a third exact cochain value. |

---

## 1. Conclave Principles & Inviolable Invariants

1. **Manuscripts Don't Burn («Рукописи не горят»):**
   - Formal mathematical truths, exact rational cochains, and verified kernels are conserved across all refactorings and migrations.
2. **Cowardice is the Most Terrible Vice («Трусость — самый страшный порок»):**
   - Silent skips, unverified assumptions, and sycophantic passes are strictly forbidden. A typed refusal is a first-class mathematical success over vanity.
3. **Freshness is Only One: The First, and It Is Also the Last («Свежесть бывает только одна»):**
   - Stale test passes and unverified mocks convey zero authority. Every candidate must pass fresh deterministic host checks.

---

## 2. Executive Summary & Architectural Scope

This design document establishes the joint object model, topology wireframes, and step-by-step execution protocol unifying:
1. **The Proposal Fidelity Protocol (PFP)**: The mathematical referee inside the Symbol Game (`omega_symbol_game` / `omega_engine_operations.domain.cicd`), responsible for turn validation, stealth cochain extraction ($\Phi_1, \Gamma_2, \Xi$), RFC 8785 canonical JSON envelope verification, and fail-closed gate arbitration.
2. **The Woland Base Swarm**: The dialectical cognitive architecture (`omega_engine_woland`), responsible for 7-Act dialectic bouts, persona retinue casting (Woland, Behemoth, Koroviev, Azazello, Hella, Abadonna, Master, Margarita), adaptive stability detection, and intelligence digestion.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                SYSTEM ARCHITECTURE TOPOLOGY WIREFRAME                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

        PROPOSAL FIDELITY PROTOCOL (PFP)                      WOLAND BASE SWARM ENGINE
    ┌──────────────────────────────────────┐            ┌─────────────────────────────────────────┐
    │  Object A: Proposal Envelope (RFC8785)│            │   Woland Dialectic Swarm Runtime        │
    │  ┌────────────────────────────────┐  │            │   ┌──────────────────────────────────┐  │
    │  │ Header: Candidate OID & Turn   │  │            │   │ 7-Act Bout Orchestrator          │  │
    │  │ Payload: State & Action Delta  │  │            │   │ - Act 1: Thesis / Proposal       │  │
    │  │ Cochains: Phi_1, Gamma_2, Xi   │  │            │   │ - Act 2: Interrogation (Behemoth)│  │
    │  └────────────────────────────────┘  │            │   │ - Act 3: Antithesis (Koroviev)   │  │
    └──────────────────┬───────────────────┘            │   │ - Act 4: Execution (Azazello)    │  │
                       │                                │   │ - Act 5: Falsification (Abadonna)│  │
                       ▼                                │   │ - Act 6: Synthesis (Master)      │  │
    ┌──────────────────────────────────────┐            │   │ - Act 7: Verdict (Woland)        │  │
    │  PFP Gate Referee Engine             │            │   └─────────────────┬────────────────┘  │
    │  ┌────────────────────────────────┐  │            └─────────────────────┼───────────────────┘
    │  │ Gate 1: UTF-8 & Schema Check   │  │                                  │
    │  │ Gate 2: Cochain Exactness      │  │◄─────────────────────────────────┘
    │  │ Gate 3: L1 Attention Bounds    │  │  PFP Proposal Input & Witness Validation
    │  │ Gate 4: Zero-BOM Cleanliness   │  │
    │  └────────────────┬───────────────┘  │
    └───────────────────┼──────────────────┘
                        │
                        ▼
    ┌──────────────────────────────────────┐
    │  Local CI Execution Receipt (v3)     │
    │  - Receipt SHA256 & Verdict          │
    │  - AuthorityEffect: None             │
    └──────────────────────────────────────┘
```

---

## 2. System Interface & UI/CLI Wireframe

### 2.1 Terminal & Web UI Wireframe Layout

```
+---------------------------------------------------------------------------------------------------+
| ANOMALON PFP & WOLAND SWARM OPERATIONAL DASHBOARD                                     [MODE: LIVE] |
+---------------------------------------------------------------------------------------------------+
| [PROPOSAL ENVELOPE]               | [WOLAND 7-ACT DIALECTIC BOUT ENGINE]                          |
| Candidate OID: sha256:e157...361c | Active Bout ID: bout_20261006_001                            |
| Turn Index   : 42                 | Stage          : Act 3 - Antithesis (Koroviev)                |
| Status       : PENDING_REFEREE    | Dialectic State: GAUGE_BREAK_DETECTED                         |
|                                   |                                                               |
| Stealth Cochains Extracted:       | Swarm Retinue Status:                                         |
|  - Phi_1 (Primitive) : [0.942]    |  - Woland    [LEAD]      : Evaluating Synthesis           |
|  - Gamma_2 (Boundary): [0.018]    |  - Behemoth  [AGITATOR]  : Gauge Break Falsified           |
|  - Xi      (L1 Attn) : [0.003]    |  - Koroviev  [SATIRIST]  : Injecting Counter-Examples      |
|                                   |  - Azazello  [EXECUTIONER]: Hardened Witness Verified         |
| Gate Referee Audit:               |  - Abadonna  [DESTROYER] : 0 Deadlocks Found              |
|  [PASS] Gate 1: Schema Integrity  |                                                               |
|  [PASS] Gate 2: Cochain Exactness | Intelligence Digestion Pipeline:                              |
|  [PASS] Gate 3: L1 Attention Bound|  - Ingested Traces : 124                                     |
|  [PASS] Gate 4: Zero-BOM Clean    |  - Digestion Rate  : 100% Deterministic                       |
+---------------------------------------------------------------------------------------------------+
| LOG TERMINAL RECEIPT OUTPUT                                                                       |
| > PFP_ENVELOPE_VERIFIED: sha256:a91f...                                                           |
| > WOLAND_BOUT_SYNTHESIS: Verdict = PASS_WITH_ADVISORY (AuthorityEffect: None)                    |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. PFP Top-Level Object Schemas & Formal Definitions

This section provides the rigorous, non-slop mathematical and structural specification of the Proposal Fidelity Protocol (PFP) objects and their transformation algebra.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             PFP FORMAL OBJECT TRANSFORMATION WIREFRAME                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

   Raw Input Packet P (Raw Text / ASCII)
              │
              ▼
   Template Mapping: P ──► P* (Root Prompt with Template & Generation ID)
              │
              ├──────► Sub-Prompt Tree Extraction: P* ──► { P*_{sub ij} } (Parent-Child Prompt Graph)
              │
              ▼
   Stage Traversal Loop: (P*, S_k, M) ──► Prompt Response R_k
              │
              ▼
   Swarm Character Gate Adapter: PfpGate(P*, R_k) ──► Swarm Persona Evaluation
              │
              ▼
   Canonical RFC 8785 Envelope: PfpPacket(P*, R_k, Receipts)
```

### 3.1 Formal Transformation Rules & Primitives

1. **Raw Input Packet $P$**:
   - **Definition**: The lowest-level input representation entering the system.
   - **Structure**: Unformatted raw text character sequence decoded from binary payload bytes via ASCII / UTF-8. Zero initial assumptions regarding syntax or JSON structure.

2. **Template Expansion $P \rightarrow P^\star$**:
   - **Definition**: The transformation mapping raw packet $P$ into root prompt $P^\star$.
   - **Formula**: $P^\star = \text{InjectTemplate}(P, \text{PromptTemplate}, \text{GenerationID})$.
   - **Properties**: Encloses raw input within the system prompt template, assigning a unique generation ID and lineage metadata.

3. **Sub-Prompt Graph Extraction $P^\star \rightarrow \{ P^\star_{\text{sub } ij} \}$**:
   - **Definition**: Decomposition of root prompt $P^\star$ into a tree or Directed Acyclic Graph (DAG) of child sub-prompts.
   - **Indexing**: Each sub-prompt $P^\star_{\text{sub } ij}$ carries parent reference $P^\star$, shared generation ID, depth index $i$, and sibling index $j$.
   - **Extraction Process**: Evaluates $P^\star$ via LLM or deterministic parser to extract explicit child sub-prompts $P^\star_{\text{sub } ij}$ with familiar parent-child relationships.

4. **Stage Sequence $S = (S_1, S_2, \dots, S_n)$ & Response Mapping $(P^\star, S_k) \rightarrow R_k$**:
   - **Definition**: An ordered tuple of execution stages through which prompt $P^\star$ (or sub-prompt $P^\star_{\text{sub } ij}$) is evaluated.
   - **Response $R_k$**: For each stage $S_k$, execution yields a typed response $R_k$ containing evaluation findings, cochain outputs, or proof attempts.

5. **Operational Mode $M$ (`PfpMode` / `PfpModeCluster`)**:
   - **Definition**: The operational modality governing evaluation rules, substrate binding, and verifier contracts across the Symbol Game.
   - **Structure**: Selected from the 20 Canonical Play Modes (`mode_01` to `mode_20`) organized into 5 Mode Clusters (`Cluster I: Carrier & Representation`, `Cluster II: Internal Steering`, `Cluster III: Group & Cochain Structure`, `Cluster IV: Dialectical & Adversarial`, `Cluster V: Foundational Mechanization`).
   - **Fields**: `mode_id` (1–20), `name`, `cluster`, `core_mechanism`, `substrate`, `paper_reference`, `verifier_contract` (`verifier_type`, `fail_closed`).

6. **Swarm Character Gate Adapter (`PfpGate`)**:
   - **Definition**: The character adapter interface bridging stage response $R_k$ and prompt $P^\star$ to specific Woland Swarm persona characters.
   - **Adapter Target**: Maps evaluation tasks to retinue character roles (Behemoth agitator, Azazello executioner, Koroviev satirist, Woland referee).

7. **Wire Envelope Packet (`PfpPacket`)**:
   - **Definition**: Canonical RFC 8785 JSON container packaging prompt $P^\star$, response $R_k$, stealth cochains ($\Phi_1, \Gamma_2, \Xi$), and cryptographic receipts.

---

### 3.2 Object Field Schemas

### Object 3.2.1: `PfpPrompt` ($P^\star$)
- **Fields**:
  - `prompt_id`: Unique UTF-8 identifier string (`sha256:...`).
  - `generation_id`: Lineage ID linking root prompt $P^\star$ to child sub-prompts $P^\star_{\text{sub } ij}$.
  - `prompt_text`: Template-expanded prompt text.
  - `parent_id`: `None` for root $P^\star$; parent `prompt_id` for child sub-prompt $P^\star_{\text{sub } ij}$.
  - `sub_prompts`: List of child `PfpPrompt` instances forming the prompt tree.
  - `prompt_type`: Reference to `PfpPromptType`.

### Object 3.2.2: `PfpPromptType` (Enum)
- **Variants**:
  - `THEORY_PROOF`: Formal proof step or Lean 4 cochain assertion.
  - `DEFORMATION_REWRITE`: Symbol rewrite or 2-step cochain transformation ($\Phi_1 \rightarrow \Gamma_2$).
  - `GATE_VERIFICATION`: Local CI gate rule audit request.
  - `SWARM_TACTIC`: High-level dialectic bout directive for the Woland swarm.

### Object 3.2.3: `PfpMode` & `PfpModeCluster`
- **Five Mode Clusters**:
  - `Cluster I: Carrier & Representation` (Modes 01, 02, 06, 15)
  - `Cluster II: Internal & Attention Steering` (Modes 03, 04, 05)
  - `Cluster III: Group & Cochain Structure` (Modes 07, 08, 12, 13)
  - `Cluster IV: Dialectical & Adversarial` (Modes 10, 11, 14, 16, 17, 20)
  - `Cluster V: Foundational Mechanization` (Modes 09, 18, 19)
- **`PfpMode` Record**: `mode_id` (1–20), `name`, `cluster`, `core_mechanism`, `substrate`, `paper_reference`, `rules`, `entry_preconditions`, `winning_condition`, `failure_condition`, `verifier_contract` (`verifier_type`, `fail_closed`).

### Object 3.2.4: `PfpStage` ($S_k$)
- **Variants**:
  - `1_RAW_PACKET_INGESTION`: Decoding raw ASCII packet $P$.
  - `2_TEMPLATE_AND_SUBPROMPT_TREE_BUILD`: Constructing $P^\star$ and sub-prompt tree $\{ P^\star_{\text{sub } ij} \}$.
  - `3_STAGE_TRAVERSAL_AND_RESPONSE`: Dispatching prompts through stage sequence $S$ to collect responses $R_k$.
  - `4_SWARM_GATE_ADAPTER_AUDIT`: Adapting $P^\star$ and $R_k$ through `PfpGate` character evaluators.
  - `5_CANONICAL_ENVELOPE_FINALIZATION`: Packaging into RFC 8785 `PfpPacket` with signed execution receipt.

### Object 3.2.5: `PfpGate` (Swarm Character Adapter)
- **Fields & Methods**:
  - `gate_id`: Adapter identifier (e.g., `behemoth_interrogation_gate`).
  - `disposition`: `REQUIRED` | `ADVISORY` | `QUARANTINED`.
  - `character_persona`: Assigned persona operator.
  - `evaluate_stage_response(prompt: PfpPrompt, response: PfpResponse) -> GateEvaluationV1`.

### Object 3.2.6: `PfpPacket` (Canonical Wire Envelope)
- **Fields**:
  - `packet_id`: SHA-256 digest of RFC 8785 canonical JSON bytes.
  - `root_prompt_id`: ID of root prompt $P^\star$.
  - `turn_index`: Discrete integer turn counter.
  - `stealth_cochain_tuple`: Exact rational array `[Phi_1, Gamma_2, Xi]`.
  - `responses`: List of stage responses $R_k$.
  - `signature_receipt`: Embedded execution receipt digest (`OMEGA_LOCAL_CI_RECEIPT_SHA256=...`).

---

---

## 4. Woland Swarm System Breakdown

### Object 4.1: `WolandBoutSession` (Dialectic Engine)
- **Role**: Manages the 7-Act dialectic workflow for hypothesis stress-testing.
- **Acts**:
  1. `ThesisProposal`: Initial proposal presentation (`PfpPrompt`).
  2. `Interrogation`: Behemoth stress tests boundary conditions.
  3. `Antithesis`: Koroviev constructs adversarial counter-examples.
  4. `Execution`: Azazello runs deterministic verifiers / Rust crates.
  5. `Falsification`: Abadonna audits for silent skips or fake proofs.
  6. `Synthesis`: Master synthesizes refined claim.
  7. `Verdict`: Woland issues final typed receipt.

### Object 4.2: `WolandRetinueCast` (Persona Operators)
- **Role**: Bounded context persona operators executing discrete audit roles.

### Object 4.3: `IntelligenceDigestionPipeline` (Trace Ingestion)
- **Role**: Collects execution receipts, runs obstruction hunters, and archives digested runs.

---

## 4. Claim Hygiene Summary

1. **What it supports:** Defines the architectural layout, object schemas, wireframe interfaces, and 7-Act dialectic pipeline unifying PFP and Woland Swarm.
2. **What it does not support:** Does not self-certify compliance through markdown prose alone; runtime execution requires verified Python/Rust test suites.
3. **Narrowest defensible claim:** This design document provides the canonical specification and object model for step-by-step implementation of PFP and Woland Swarm.
4. **Next test needed:** Object-by-object walkthrough and unit test coverage in `omega_engine_woland` and `omega_engine_operations`.
