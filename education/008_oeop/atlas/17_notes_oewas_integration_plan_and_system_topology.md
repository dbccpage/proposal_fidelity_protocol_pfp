> **HISTORICAL.** This note's location line, `use_cases/` layer, and 57-crate kernel picture are not the live tree. The live Woland entry and owner map are in [chapter 23](23_plan_oewas_consolidation_oeeis_and_demo_integration.md).

# OEWAS Master Integration Plan: Symbol Game, Swarms, OEOS & 57-Crate Kernel

**Status:** Architectural Analysis & Integration Plan (`mathematical_wip`)  
**Location:** this chapter. Its former source copy `_docs/05_notes_oewas_integration_plan_and_system_topology.md` in the retired OEWAS package has no successor under `omega_engine_operads`.  
**Governing Standard:** Clean Architecture, 5-Tier Coloured Operads, DDD Aggregates, Railway-Oriented Programming (ROP), RFC 8785 Canonical JSON  
**AuthorityEffect:** `None` (Zero-authority invariant)  
**Execution Posture:** Observation, Design & Integration Notes Only (Zero autonomous execution)  

---

## 1. Executive Vision & System Topology

The goal of the Omega Engine architecture is to unify mathematical proof systems, sparse manifold retraction, multi-agent cognitive debate, and operadic workflow compilation into a single, high-throughput, zero-authority execution estate.

```text
                           OMNI-ENGINE ESTATE TOPOLOGY
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ 1. USER & CONTROLLER INTERFACE                                                         │
 │   - Web UI / CLI Terminal / Interactive Slash Command Runners (/symbol-game, /oeags)   │
 │   - Thin Python API Controllers (Request validation, ROP Result[T, DomainError])      │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 2. OEOS (Omega Engine Operating System - Host Boundary)                                │
 │   - Process isolation, sandbox containment, CAS storage, quota & cancellation          │
 │   - 8-stage artifact waist integrity (Zero math/proof authority in host)               │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 3. OEWAS (Workflows, Agents & Skills - Colored Operad Compiler)                        │
 │   - Polarized Coloured Operad (O^+, O^-) & Planar Tree Workflow Compilation            │
 │   - Skills as generators, Anti-Skills as interrogative detectors, Agents as slices     │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 4. AGENTIC SWARMS & DIALECTIC BOUTS                                                    │
 │   - Generic Swarms (Base framework: scheduling, typed sinks, and telemetry)            │
 │   - Woland Swarm (7-Act Master & Margarita dialectic, 9-dot gauge break transformations)│
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 5. SYMBOL GAME (Prompt Engine & Sparse Manifold Retraction)                            │
 │   - 7 Discrete stages: Intake -> Extract -> Solve -> Classify -> Gate -> Ledger -> Seal│
 │   - Multi-Packet LLM dispatch (5-8 structured machine packets per turn)                │
 │   - Strict descent verification: (Φ_1, Γ_2, defect_count) monotonic reduction          │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 6. IMMUNE PHARMACY & RECURRENCE MINING                                                 │
 │   - Permanent antibody harvesting (count ≥ 3 recurrence trigger)                       │
 │   - Zero data-loss trace captures (_intelligence/symbol_game/)                         │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 7. MATHEMATICAL CORE & 57-CRATE RUST KERNEL (Low-level primitives)                     │
 │   - Category theory, higher topos theory, homology, sheaves, DDA, exact solvers        │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Clean Architecture Layer Isolation Rules

To prevent coupling and preserve zero-authority guarantees, the system enforces strict Clean Architecture boundaries:

* **Pure Domain Core (`domain/`)**:
  * Mathematical definitions, Value Objects, and Domain Entities.
  * Zero dependencies on operating systems, databases, networks, or LLM providers.
* **Use Cases (`use_cases/`)**:
  * Orchestrates business rules, workflow execution, and retraction steps.
  * Depends solely on Domain models and abstract Ports (`ports.py`).
* **Adapters & Infrastructure (`infrastructure/` & `adapters/`)**:
  * Implements ports: SQLite persistence, JSON-L logging, LLM client connections, and file system I/O.
* **Controllers & UI (`controllers/` & `frontend/`)**:
  * Thin entry points (CLI commands, FastAPI routers, slash command handlers).
* **OEOS Isolation**:
  * **The 8-Stage Artifact Waist**: Governs the progression of raw artifacts without absorbing mathematical proof logic.
  * **Authority Firewalls**: Host capabilities cannot grant `ActionLicense` values or alter mathematical evaluation statuses.

---

## 3. The Integration Pipeline: How the Pieces Connect

```text
                                  INTEGRATED RUNTIME FLOW
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ STEP 1: Planar Workflow Compilation (OEWAS)                                            │
 │   - User/CLI initiates task.                                                           │
 │   - OEWAS compiles the composite skill tree T into an Operad PlanarTree.               │
 │   - Agent capability slices are checked against permitted generator signatures.        │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ STEP 2: Host Allocation & Sandboxing (OEOS)                                            │
 │   - OEOS allocates sandbox, binds CAS storage paths, and sets execution quotas.        │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ STEP 3: Multi-Agent Dialectic Bout (Woland Swarm)                                      │
 │   - Swarm scheduler launches characters across the 7-Act dialectic.                     │
 │   - For every character inquiry, the character compiles a Symbol Game prompt packet.    │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ STEP 4: Sparse Manifold Retraction & Multi-Packet LLM Call (Symbol Game)               │
 │   - Prompt is wrapped with schema constraints, hieroglyphics & kill conditions.        │
 │   - LLM responds with canonical JSON machine block.                                    │
 │   - Symbol Game extracts 5–8 packets, evaluates (Φ_1, Γ_2), and verifies descent.       │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ STEP 5: Anti-Skill Evaluation & Antibody Mining (Immune Pharmacy)                       │
 │   - Operadic anti-skills (O^-) evaluate candidate packets against known failure modes. │
 │   - Trace sinks capture all candidate packets in _intelligence/.                       │
 │   - Recurrence miner flags patterns (count ≥ 3) to synthesize new Antibodies.          │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ STEP 6: Terminal Gatekeeping & Sealing (Woland / OEOS)                                  │
 │   - Woland applies terminal reality gate (PASS_TO_MASTER | REFUSE | OPEN_RESIDUAL).     │
 │   - OEOS seals the 4 canonical run files (receipt, novella, dda_actions, summary).     │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Skills, Anti-Skills & Operadic Retraction Integration

By grafting the **Polarized Coloured Operad** $(\mathcal{O}^+, \mathcal{O}^-)$ directly into the Symbol Game stages, the system achieves end-to-end type safety:

```text
                            POLARIZED OPERADIC RETRACTION
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 1. O^+ Generator (Forward Skill):                                          │
   │      f: State × Objective ──> CandidateArtifactV1 (Stage 2)                │
   ├────────────────────────────────────────────────────────────────────────────┤
   │ 2. O^- Generator (Interrogative Anti-Skill):                               │
   │      g: CandidateArtifactV1 × Context ──> ReviewedCandidate (Findings)     │
   ├────────────────────────────────────────────────────────────────────────────┤
   │ 3. O_repair Generator (Corrective Repair Skill):                           │
   │      r: CandidateArtifactV1 × Finding ──> RepairedCandidateArtifactV1     │
   ├────────────────────────────────────────────────────────────────────────────┤
   │ 4. Operadic Monadic Descent Gate:                                          │
   │      Evaluate: (Φ_1(t), Γ_2(t)) ≤ (Φ_1(t-1), Γ_2(t-1))                     │
   ├────────────────────────────────────────────────────────────────────────────┤
   │ 5. Sealing:                                                                │
   │      Seals EvaluationReceiptV1 & EliminationReceiptV1 (Stages 6 & 7)       │
   └────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Downstream Target: 57-Crate Rust Kernel Architecture

As the Python prototypes mature and stabilize, the entire mathematical and execution core will be compiled into the **57 Rust crates** (`anomalon/omega_engine/crates/`):

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ THIN FRONTEND / CONTROLLER (Python / Web UI / CLI)                                     │
 │   - REST / JSON-RPC / IPC Controller                                                   │
 │   - Request validation, ROP Result mapping, UI rendering                               │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ High-Speed FFI (PyO3 / C-ABI)
                                             v
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ COMPILED RUST CRATES KERNEL (57 Crates)                                                │
 │   ├─ omega_symbol_game        : Nanosecond sparse manifold retraction & descent checks │
 │   ├─ omega_category_theory    : Pure operadic multicategories & planar trees           │
 │   ├─ omega_solvers            : Exact rational L1 LP & Gauge-Higgs-SUSY solvers        │
 │   ├─ omega_discrete_deformation_algebra : DDA trajectory engine & coboundary operators│
 │   └─ omega_quantum_physics / omega_majorana / omega_homotopy_type_theory               │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

### Advantages of the Rust Kernel Target

1. **Zero-Overhead Memory & Speed**: Microsecond planar tree grafting and nanosecond coboundary evaluation.
2. **True Memory Safety & Concurrency**: Lock-free transactional outboxes and deterministic multi-agent scheduling.
3. **Exact Rational Arithmetic**: Eliminates IEEE 754 floating-point inaccuracies in duality gap certificates.
4. **Clean Decoupling**: A thin Python controller handles dynamic high-level scripting, while Rust guarantees mathematical purity and performance.

---

## 6. Verification & Step-by-Step Integration Plan

### Phase 1: Bounded Context Synchronization (Current Phase)

* [x] Standardize all documentation in `_docs/` to 2-digit numbered lowercase filenames.
* [x] Document Symbol Game sparse manifold retraction, multi-packet batches, and the 7 stages.
* [x] Document OEWAS Polarized Operad $(\mathcal{O}^+, \mathcal{O}^-)$ and the 10 Prime Laws of Anti-Skills.
* [x] Verify Operad Theory test suite 100% Green (225/225 tests passing/xfailed/xpassed).

### Phase 2: OEWAS ↔ Symbol Game Bridge Wiring

* [ ] Connect `OEASWorkflowOperad` tree compilation to `SymbolGameRunnerUseCase`.
* [ ] Implement `AntiSkill` interrogative adapter in `omega_engine_pfp/domain/`.
* [ ] Wire `Antibody` pharmacy fixtures into `SymbolGameEngine` kill conditions.

### Phase 3: Swarm Dialectic Integration (Woland Swarm & Generic Swarm)

* [ ] Wire Woland Swarm character bouts to dispatch turns through `SymbolGameBridgeSession`.
* [ ] Direct multi-packet return batches into `_intelligence/_woland/runs/<task_key>/`.
* [ ] Implement automatic trace mining for antibody synthesis when defect count $\ge 3$.

### Phase 4: OEOS Host Containment & Sandboxing

* [ ] Map OEOS CAS storage and process isolation to the Symbol Game and Woland runs.
* [ ] Verify 8-stage artifact waist compliance across all emitted receipts.

### Phase 5: Rust Kernel Lowering & Thin Controller Finalization

* [ ] Port OEWAS operad compiler logic to `omega_category_theory` and `omega_symbol_game` Rust crates.
* [ ] Deploy thin Python API controller and Web UI for interactive prompt dispatch.
