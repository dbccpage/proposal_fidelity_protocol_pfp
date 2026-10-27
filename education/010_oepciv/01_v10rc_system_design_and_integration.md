---
documentation_contract: symbol-game-documentation/v1
title: "01_v10rc_system_design_and_integration: Prompt Civilization V1.0RC Architecture & PFP/Adversary Integration"
kind: architectural-specification
audience:
  - researchers
  - engineers
  - coding-agents
status: active
maturity: draft
claim_status: scoped-local-verification-and-design
authority_effect: "None"
source_paths:
  - product_planning_office/plans/epics/oepciv/epic_oe_oepciv_001_grammar_validity_and_distribution_plan.md
  - pciv/controllers/prompt_civ_controller.py
  - pciv/use_cases/custody.py
  - pciv/use_cases/fitness.py
  - pciv/scripts/run_evolutionary_stress_50gen.py
  - _ic/adversary/oev1rc_integration_closure_digestion.md
  - education/documentation/010_oepciv/00_index.md
prerequisites:
  - 00_index.md
  - README.md
related:
  - ../004_oepfp/README.md
  - ../009_oeeis/README.md
  - normal_forms/nf_01_prompt_society_and_civilization.md
  - normal_forms/nf_02_lamarckian_pfp_adversary_loop.md
last_verified: 2026-10-13
---

# 01_v10rc_system_design_and_integration: Prompt Civilization V1.0RC Architecture & PFP/Adversary Integration

**AuthorityEffect:** None.  
**Epistemic Posture:** Scoped local implementation evidence and integration design; mints no operational or mathematical authority. The source and test pins are in the historical verification receipt (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/adversary/oev1rc_integration_closure/oepciv_verification.json`). The diagram and biological mechanisms below describe intended architecture, not a claim that every mechanism is wired into the measured runner.

---

## 1. Executive Summary & Architectural Scope

The **Prompt Civilization (`OEPCIV`)** estate governs the evolutionary life cycle, causal ancestry, multi-objective fitness evaluation, and Lamarckian adaptation of immutable prompt programs within the engine.

The **Version 1.0RC design** distinguishes:
1. **The Four-Tier Civilizational Topology:**
   $$\text{Prompt Genome } (\mathcal{G}) \longrightarrow \text{Prompt Family } (\mathcal{F}) \longrightarrow \text{Prompt Society } (\mathcal{S}) \longrightarrow \text{Prompt Civilization } (\mathcal{C})$$
2. **Two-Graph Separation:** Strict demarcation between the **Hierarchical Containment Tree** (dataflow decomposition of an incoming prompt $P$ into a $P^\star$ node tree) and the **Causal Lineage DAG** (evolutionary ancestry, forks, and homologous crossovers across generations).
3. **Lamarckian Adaptation via Typed Failure Receipts:** Phenotypic mutations derived from external falsification witnesses and cochain obstruction residuals ($\Phi_1 > 0$, $\Gamma_2 > 0$, $\Xi > 0$) retro-inherited into plastic scaffold regions while preserving canalized core invariants.
4. **Estate Integration:** Existing PFP checkers, Adversary fixture bouts, protected-span mutation, and authenticated Python custody can be composed. Section 8 reports the measured finite path; live evolutionary efficacy and the OEPCIV001 grammar/distribution experiment remain research follow-up.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 OEPCIV V1.0RC TOPOLOGY WIREFRAME                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

        INCOMING TASK (P)
               │
               ▼
   ┌───────────────────────┐
   │ P* Family Compiler    │ ◄─── Decomposes P into ordered containment tree
   └───────────┬───────────┘      (Preserves exact UTF-8 bytes and source provenance)
               │
               ▼
   ┌───────────────────────┐
   │ Prompt Genome (G_0)   │ ◄─── Canalized Core (Immutable) + Plastic Scaffold (Modifiable)
   └───────────┬───────────┘
               │
               ├──────────────────────────────────────────────┐
               │ Dispatch to Dialectic Bout                   │ Direct PFP Measurement
               ▼                                              ▼
   ┌───────────────────────┐                      ┌───────────────────────┐
   │ ADVERSARY   │                      │          │
   │ - 7-Act Bout          │                      │  SYMBOL_GAME (PFP)    │
   │ - Panel Debate      │                      │ - Wire Envelope       │
   │ - Primal Dual Sandbox   │                      │ - Cochains Phi1/G2/Xi │
   │ - Genealogy Adapter   │                      │ - ExactPharmacyPort   │
   └───────────┬───────────┘                      └───────────┬───────────┘
               │                                              │
               └──────────────────────┬───────────────────────┘
                                      │ Failure Receipts & Defect Witnesses
                                      ▼
                          ┌───────────────────────┐
                          │ OEEIS Immune Repertoire│ ◄─── Thymus & Treg Negative Selection
                          │ - Candidate Antibodies│
                          └───────────┬───────────┘
                                      │
                                      ▼ Lamarckian Retro-Inheritance (Hop d <= 10)
                          ┌───────────────────────┐
                          │ Prompt Mutation Forge │
                          │ - Scaffold Revision   │
                          └───────────┬───────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │ Child Genome (G_{g+1})│ ◄─── Registered in Causal Genealogy DAG
                          └───────────────────────┘
```

---

## 2. Core Data Contracts: The Four-Tier Topology

### 2.1 Incoming Prompt ($P$) vs Compiled $P^\star$ Family
- **`IncomingPromptV1` ($P$):**
  - **Identity:** Cryptographic digest `sha256(raw_utf8_bytes)`.
  - **Properties:** Immutable raw text, caller provenance, ingress timestamp, assigned domain facet.
  - **Invariant:** Never modified in place; serves as the permanent root of task attribution.
- **`PStarFamilyRevisionV1` ($P^\star$):**
  - **Structure:** Ordered, directed acyclic containment tree decomposing $P$ into discrete execution nodes (e.g. thesis generator, counterexample hunter, verification oracle).
  - **Dataflow:** Explicit input/output port bindings validated through `OEWAS` operadic typing.
  - **Containment Rule:** Generation index in containment reflects decomposition depth ($k \in \{0, \dots, K\}$), **not** evolutionary mutation age ($g$).

### 2.2 Prompt Genome ($\mathcal{G}$) & Mutation Canalization
- **`PromptGenomeV1`:**
  $$\mathcal{G} = \langle \text{Core}_{\text{canalized}}, \text{Scaffold}_{\text{plastic}}, \text{Lineage}, \text{FacetTree} \rangle$$
  - **Canalized Core (`ProtectedSpanV1`):** Byte ranges containing inviolable semantic invariants, security boundaries, and non-negotiable formal obligations. Mutations targeting protected spans trigger immediate typed refusal (`MUTATION_TARGETS_CANALIZED_CORE`).
  - **Plastic Scaffold (`PlasticSpanV1`):** Byte ranges containing phrasing strategies, few-shot demonstration anchors, cognitive pacing cues, and antibody insertion sites.

### 2.3 Prompt Society ($\mathcal{S}$) & Prompt Civilization ($\mathcal{C}$)
- **`PromptSocietyV1`:**
  - An evaluated collaboration of prompt families bound to a coherent domain protocol $\mathcal{D}$ (e.g., `finite_quantum_mechanics`, `differential_cohomology`, `clean_architecture_techne`).
  - Maintains collective Pareto frontiers over exact rational evaluation tuples:
    $$\text{Fitness}(\mathcal{F}) = \langle \text{Accuracy}_{\mathbb{Q}}, \text{Cost}_{\mathbb{Q}}, \text{Robustness}_{\mathbb{Q}}, \text{Latency}_{\mathbb{Q}} \rangle \in \mathbb{Q}^4$$
- **`PromptCivilizationV1`:**
  - A federation of societies interoperating under shared global resource constraints, global epistemic antibody registries (`OEEIS`), and bounded governance.
  - Enforces cross-society migration policies, resource reservation caps, and anti-drift canary probes.

---

## 3. Lamarckian Retro-Inheritance & Biological Mechanisms

### 3.1 The Lamarckian Feedback Loop
When a candidate prompt produces an execution artifact that fails an external oracle or manifests a non-zero cochain residual ($\Phi_1 > 0$ or $\Gamma_2 > 0$):
1. **Defect Extraction:** PFP emits an evaluated failure receipt containing the exact counterexample or obstruction cycle.
2. **Antibody Packaging:** `OEEIS` packages the defect into an `AntibodyCandidateV1` defining a negative constraint or syntactic fence.
3. **Thymic Selection (`ThymusV1`):** The candidate antibody is tested against a clean invariant panel. If it induces false rejections on known-good controls, it is discarded.
4. **Retro-Inheritance Insertion:** Validated antibodies are inserted into the plastic scaffold of the parent genome's descendants.
5. **Attenuation Law:** Lamarckian influence attenuates exponentially with lineage distance:
   $$w(d) = \left(\frac{1}{2}\right)^d, \quad d \le 10$$
   Beyond $d = 10$, ancestral antibodies are either canalized into core invariants or pruned by pheromone evaporation.

---

## 4. Integration with `pfp` (PFP)

`pfp` supplies task-specific executable checks. The measured RC runner binds `SymbolGameCandidateChecker` to one finite C011 case and executes it on the actual candidate bytes. It does not measure generic prompt quality or cochain fitness. These additional integration contracts remain design context:
1. **PFP Wire Envelope (`PfpPacket`):**
   - Transports prompt instructions $P^\star$, runtime response $R_k$, and cryptographic turn proofs.
   - Sealed via RFC 8785 canonical JSON bytes and SHA-256 digests.
2. **Stealth Cochain Extraction:**
   - Evaluates triad residuals: $\Phi_1$ (functional defect), $\Gamma_2$ (obstruction residual), $\Xi$ (diagnostic parity).
   - A cochain report is diagnostic evidence for its declared task. The current feedback runner records `cochain_status=NOT_MEASURED` and never fabricates cochain scores.
3. **Exact Pharmacy Port (`ExactPharmacyPort`):**
   - Binds `engine/crates_rs/core_prompt_civilization/src/pharmacy.rs` to detect failure classes (`LogicalContradiction`, `AxiomViolation`, `FloatContamination`) at native Rust speeds.

---

## 5. Integration with `adversary`

`adversary` serves as the dialectical stress-testing apparatus:
1. **7-Act Dialectic Bout Integration:**
   - **Act I (Catalyst):** Prompt ingestion and synthetic diagnostic measurement.
   - **Act II (Panel Debate):** Candidate proposals stress-tested between Gauge Breaker and Defect Hunter.
   - **Act III (Epistemic Sieve):** Anti-skill fences applied from `OEWAS`.
   - **Act IV (Sandbox Execution):** Challenge checkers and external oracles run in isolated sandboxes.
   - **Act V (Master Formalization):** Candidate synthesis and proof extraction.
   - **Act VII (Verdict):** Terminal crystallization (`PASS_TO_MASTER`, `REFUSE`, `COMPOSTED`).
2. **Genealogy Estate Adapter (`PromptCivGenealogyAdapter`):**
   - Wires Adversary bout runs into the prompt civilization genealogy ledger (`adversary/infrastructure/estates/prompt_civ_genealogy.py`).
   - Every candidate artifact produced in Act II is bound to its producing prompt genome OID.
3. **Panel Character Persona Evolution:**
   - Prompt civilization evolutionary loops evaluate and refine the specialized system prompts for Adversary Panel seats (Gauge Breaker's adversarial sharpness, Defect Hunter's satirical precision, Scope Guard's ruthless execution) based on historical defect-detection yield.

---

## 6. Resolution of Critical Release Findings (F1–F6)

| Finding | Classification | Root Defect | V1.0RC Resolution |
| :---: | :--- | :--- | :--- |
| **F1** | P0 Security | Admission accepted recognized signature prefixes without verification. | The public Python controller requires a host-injected `PromptCustodyLedgerV1`, its configured external verifier, an authenticated ADMITTED review receipt, exact single-source prompt bytes, and admitted scope. Existing ledger transitions and replay checks apply. Native token-only admission explicitly refuses; Rust does not authenticate operator keys on this route. `AuthorityEffect` remains `None`. |
| **F2** | P0 Fitness | Nonempty fake receipt digests could earn fitness credit. | Python credit requires executing the host-bound `CandidateCheckerPort` on the candidate and binding receipt bytes to run/candidate/checker/verdict. The current runner uses this path. Legacy Python and Rust caller booleans/hash strings earn zero credit. A composition root must still choose a trusted checker. |
| **F3** | P0 Metrics | Early valid refusals masked task safety failures; completion rates inflated. | The tested outcome reducer preserves `TaskFail`/`NotMeasured` priority and completion rate $S / N_{\text{assigned}}$; zero assigned tasks returns no rate. These arithmetic controls do not authenticate a caller's claimed outcomes. |
| **F4** | P1 Parity | Domain origin and admitted read-scope had different meanings. | Canonical custody adapters retain their own scope/metadata rules. OEOS now reexports those canonical APIs; this pass does not claim complete Python/Rust scope-policy parity. |
| **F5** | P1 Projection | Mutable views and immutable payloads lacked normative field boundaries. | Canonical record/custody types retain identity and mutable projection separation. The controller checks the actual source bytes before projecting admission; arbitrary DTO hashes alone grant nothing. |
| **F6** | P1 Persistence | In-memory state alone cannot establish crash recovery or provider billing. | Existing SQLite custody ledger and content-addressed prompt storage are used. The fixture benchmark spends nothing. Durable live billing belongs to the existing PFP gateway; this document does not claim a new PCIV reservation system or power-loss proof. |

---

---

## 7. The Autophagous "Fugu" Cemetery & Pharmacy Antibody Gate

To eliminate circular evolutionary search where candidate mutations regress to previously falsified hypotheses, `OEPCIV` integrates directly with Adversary's Act IV pre-execution sandbox screening:

1. **Failure Interment:**
   - Adversary's existing cemetery adapter stores headstones below its selected canonical `_ic` custody root (default `_ic/darpa/adversary/cemetery/`). It does not automatically inter every experimental hint emitted by the feedback runner.
2. **Dynamic State Reloading:**
   - the city's `FileCemeteryAdapter` reloads all `*.headstone.json` records from disk dynamically (`load_headstones()`), ensuring subsequent bouts and generational iterations immediately recognize all buried casualties.
3. **Pre-Execution Act IV Screening:**
   - Candidates are screened prior to seat turns:
     - Matching a buried casualty triggers `REGRESSION_AGAINST_CEMETERY_REFUSED`.
     - Matching an active pharmacy antibody triggers `REGRESSION_AGAINST_ANTIBODY_REFUSED`.
4. **Controlled Ablation:**
   - `ablation_flags={"no_cemetery_defense": True}` allows disabling the screening gate to measure raw baseline regression frequencies.

---

## 8. Feedback Benchmark and Historical Evidence

The October 9 summary is preserved at [historical summary](../../../_ic/nara/historical/oewas007/evolutionary_stress_50gen/summary.json). It reports 50 generations, 150 bouts, and zero provider calls. Its diversity, entropy, and attenuation values came from a harness that did not feed its changing genomes into bouts and injected synthetic defects. Those values are historical diagnostics; they do not demonstrate observed failure-driven adaptation or live improvement. The retained historical artifact set does not justify claiming custody of 150 complete quad bundles.

The current [runner](../../../pciv/scripts/run_evolutionary_stress_50gen.py) uses a different measured contract:

1. Each bout objective contains the exact current genome text, its CAS digest, and a finite C011 task.
2. The host-bound independent checker executes on actual candidate bytes; its complete receipt bytes and candidate bytes are retained and independently replayed.
3. Only observed REJECTED checker reasons create experimental scaffold hints. Repeated reasons do not force new mutations.
4. Protected core bytes remain unchanged, and each child becomes that agent's next-generation parent.
5. Volatile bout identifiers are retained for exact receipt replay. A separate semantic replay digest covers stable task/genome/verdict/hint progression and agrees across repeated same-seed runs.

The targeted test completed 50 generations and 150 fixture bouts: 450 actual checker observations were REJECTED, none were ACCEPTED, and three initial learning updates added the distinct observed failure hints. Subsequent repetitions added no new hints. It checked persisted bout receipts and repeated two generations at the same seed for deterministic semantic replay. It also changed retained candidate bytes and required replay to fail. Commands, source pins, log hashes, actual observation counts, and the fresh native binary pin are recorded in the historical verification receipt (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/adversary/oev1rc_integration_closure/oepciv_verification.json`).

This is finite transport/checker/rewrite custody evidence. The deterministic fixture seats need not respond more successfully to added hints. The runner records `efficacy=NOT_MEASURED`, `cochain_status=NOT_MEASURED`, zero provider calls, and `AuthorityEffect=None`; it does not promote experimental hints to admitted antibodies.

The disconnected `run_evolutionary_stress_live.py` compatibility entry point now raises `LEGACY_LIVE_RUNNER_RETIRED` before credentials, filesystem writes, or dispatch. Its former raw seat transport is also retired. A live evolutionary trial must use the existing plan-consuming native/PFP teamwork boundary and its durable run-wide billing; the TeamworkAction executor cannot be passed off as a SeatTurnRequest executor. No such live evolution trial was run for this receipt.

---

## 9. Development RC Boundary and Follow-Up

The delivered development slice is authenticated host-ledger admission, refusal of token-shaped native admission, zero credit for untrusted fitness metadata, actual independent C011 checker credit in a production consumer, canonical OEOS adapter reuse, and a replayable finite feedback runner.

The diagrams, four-tier terminology, and biological analogy remain design descriptions where no named exercised consumer is shown. Low-level mutation helpers check byte-span and witness identifier syntax; a 64-hex witness string alone is not authenticated checker execution, immune admission, or proof of a task failure. The runner uses actual checker observations before creating experimental hints.

[OEPCIV001](../../../product_planning_office/plans/epics/oepciv/epic_oe_oepciv_001_grammar_validity_and_distribution_plan.md) remains `RESEARCH_HOLD`: the proposed grammar-validity and distribution experiment requires a real contributor population, recorded proposal draws, declared baselines, and measured held-out outcomes. Its empirical claims are not a prerequisite invented by this local repair, and they are not completed by fixture tests.

Remaining optional extensions are a live feedback trial through the supported accounted PFP boundary, held-out comparisons of rewrite/antibody benefit, and broader task-family/checker coverage. Any benefit claim needs measured independent outcomes and the original per-run cap; a fixture pass, admission receipt, or biological analogy cannot supply that result.
