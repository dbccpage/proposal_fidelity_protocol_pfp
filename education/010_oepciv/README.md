---
documentation_contract: symbol-game-documentation/v1
title: "010_oepciv: Prompt Civilization & Lamarckian Evolution (OEPCIV)"
kind: grammar-reference
audience:
- researchers
- engineers
- coding-agents
status: active
maturity: draft
claim_status: verified
authority_effect: "None"
source_paths:
- product_planning_office/plans/epics/oegpciv/epic_pciv_v10rc.md
- product_planning_office/plans/epics/oegpciv/pfp_pciv_eis_second_pass_findings.md
- engine/crates_rs/core_prompt_civilization/src/lib.rs
prerequisites: []
aliases:
- oepciv
- pciv
- 040_prompt_civilization_and_lamarckian_evolution
related:
- ../README.md
- ../009_oeeis/README.md
- levels/README.md
- 01_v10rc_system_design_and_integration.md
- normal_forms/nf_01_prompt_society_and_civilization.md
- normal_forms/nf_02_lamarckian_pfp_adversary_loop.md
- normal_forms/nf_03_fugu_cemetery_and_antibody_gate.md
last_verified: 2026-10-10
---

# 010_oepciv: Prompt Civilization & Lamarckian Evolution (OEPCIV)

**AuthorityEffect:** None.

This directory establishes the architecture, population dynamics, and inheritance protocols for **Prompt Civilization and Lamarckian Evolution** within the Symbol Game Proposal Fidelity Protocol (PFP).

## Core Directives & Evolution Invariants

1. **Explicit Lineage & Ancestry Tracking:** Every mutated prompt candidate must retain cryptographic parent hashes, mutation operation tags, and delta records. No prompt is modified in place without recorded ancestry.
2. **Lamarckian Adaptation from Typed Failure Receipts:** Learned phenotypic modifications—specifically antibody rules extracted from counterexamples and cochain obstruction receipts ($\Phi_1 > 0$, $\Gamma_2 > 0$)—are integrated directly into child prompt genomes.
3. **Hermetic Population Separation:** Task prompts, mutation prompts, evaluation prompts, and meta-evolution orchestrators reside in strictly isolated populations. A prompt never evaluates or promotes itself.
4. **Anti-Hallucination & Canary Fences:** Each evolutionary generation is subjected to held-out test panels and canary prompts designed to detect self-promotional drift, sycophancy, and unmechanized claims.
5. **No Automatic Authority:** Evolutionary fitness scores license only candidate inspection; they do not constitute mathematical proofs, promotion authority, or model verification.

## Master System Specification & Normal Forms

- [**01. V1.0RC System Design & Integration**](01_v10rc_system_design_and_integration.md): Master architectural monograph defining the Four-Tier Civilizational Topology, Two-Graph Separation, Lamarckian Retro-Inheritance, and PFP/Adversary Integration.
- [**Normal Form 01: Prompt Societies & Civilizations**](normal_forms/nf_01_prompt_society_and_civilization.md): Normative RFC 8785 compatibility target (not encoder verification), mathematical state space, and Pareto conservation laws.
- [**Normal Form 02: Lamarckian PFP-Adversary Feedback Loop**](normal_forms/nf_02_lamarckian_pfp_adversary_loop.md): State machine algebra, sequence diagrams, and cryptographic mutation receipts.
- [**Normal Form 03: The Autophagous "Fugu" Cemetery & Pharmacy Gate**](normal_forms/nf_03_fugu_cemetery_and_antibody_gate.md): Closed-loop failure interment, pre-execution Act IV screening, and antibody regression prevention.

## Progressive Levels Curriculum & Interactive Tracks

The complete 11-level progressive technical curriculum and interactive track laboratories for Prompt Civilization are documented under [`curriculum/`](curriculum/README.md) and [`levels/`](levels/README.md):

- [**Curriculum Tracks Master Index**](curriculum/README.md): Interactive laboratories, concept lessons, notebooks, scripts, and video assets across 400-series tracks.
- [**Levels Catalog Overview**](levels/README.md): Architectural roadmap and progressive level matrix.
- [**Level 00: Substrate & Packaging**](levels/level_00_substrate_and_packaging.md): Governed Material vs Occurrence (`PromptGenomeV1`, `ExecutionOccurrenceV1`, canalization boundaries).
- [**Level 01: Lineage DAG & Causal Descent**](levels/level_01_lineage_dag_and_causal_descent.md): Two-Graph Separation (Inheritance DAG vs Reference Graph, ancestry trees).
- [**Level 02: Mutation Operators & Forge**](levels/level_02_mutation_operators_and_forge.md): Canalized Core vs Plastic Scaffold (`MutationOperatorCandidateV1`, epoch boundaries).
- [**Level 03: Lamarckian Retro-Inheritance**](levels/level_03_lamarckian_retro_inheritance.md): Hop-Bounded Retro-Inheritance ($d \le 10$, $(1/2)^d$ attenuation, no horizon reset).
- [**Level 04: Pareto Selection & Fitness**](levels/level_04_pareto_selection_and_fitness.md): Multi-Objective Exact Evaluation (Exact $\mathbb{Q}$, Pareto fronts, unmeasured exploration quotas).
- [**Level 05: Inverse Lineage PageRank**](levels/level_05_inverse_lineage_pagerank.md): Certified Ancestral Utility (`core.spectral.pagerank.v2` exact rational solver, transport parameter $q_c$).
- [**Level 06: Precedent Retrieval & Evaporation**](levels/level_06_precedent_retrieval_and_evaporation.md): Lexicographic Matching & Pheromone Evaporation (Half-life $H$ epoch-based decay).
- [**Level 07: Ecological Reserves & Population**](levels/level_07_ecological_reserves_and_population.md): Population Policy & Ecological Reserves (Largest-remainder allocation, disjoint reserves).
- [**Level 08: Lineage Taint & Custody Invalidation**](levels/level_08_lineage_taint_and_custody_invalidation.md): Lineage Taint vs Custody Invalidation (Forward causal taint fixpoint vs disarming).
- [**Level 09: Durable Event Log & Persistence**](levels/level_09_durable_event_log_and_persistence.md): Durable Event Log & Persistence (Producer-minted UUIDv5, separate `payload_sha256`, conflict detection).
- [**Level 10: Open Horizons & Multi-Island Ecology**](levels/level_10_open_horizons_and_multi_island_ecology.md): v0.2 Frontiers (Crossover homologous blocks, island migration, `FROZEN` anchors).
