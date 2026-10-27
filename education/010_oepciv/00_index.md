# 040. Prompt Civilization & Lamarckian Evolution: Syllabus & Index

**AuthorityEffect:** None.

---

## 1. Master Architectural Specification & Integration

The definitive technical specification for Version 1.0RC and its integration with the Proposal Fidelity Protocol (PFP) and Adversary Swarm is established in:
- [**01. V1.0RC System Design & Integration**](01_v10rc_system_design_and_integration.md): The Four-Tier Civilizational Topology, Two-Graph Separation, Lamarckian Retro-Inheritance, and PFP/Adversary Seams.
- [**Normal Form 01: Prompt Societies & Civilizations**](normal_forms/nf_01_prompt_society_and_civilization.md): Normative schemas, Pareto domination criteria, and budget conservation laws.
- [**Normal Form 02: Lamarckian PFP-Adversary Feedback Loop**](normal_forms/nf_02_lamarckian_pfp_adversary_loop.md): Trace algebra, protected core invariance, and cryptographic mutation receipts.
- [**Normal Form 03: The Autophagous "Fugu" Cemetery & Pharmacy Gate**](normal_forms/nf_03_fugu_cemetery_and_antibody_gate.md): Closed-loop failure interment, pre-execution Act IV screening, and antibody regression prevention.

---

## 2. Progressive Curriculum: The 11 Levels

The complete technical curriculum for prompt genome evolution, causal inheritance DAGs, and Lamarckian adaptation is documented under [`levels/`](levels/README.md):

| Level | Document | Subject | Canonical Invariants |
| :---: | :--- | :--- | :--- |
| [**Level 00**](levels/level_00_substrate_and_packaging.md) | **Substrate & Packaging** | `PromptGenomeV1`, `ExecutionOccurrenceV1` | Canalization boundaries; immutable genome bytes |
| [**Level 01**](levels/level_01_lineage_dag_and_causal_descent.md) | **Lineage DAG & Causal Descent** | Two-graph separation (Inheritance DAG vs Reference Graph) | Cryptographic parent hash linking; cycle prevention |
| [**Level 02**](levels/level_02_mutation_operators_and_forge.md) | **Mutation Operators & Forge** | Canalized Core vs Plastic Scaffold | `MutationOperatorCandidateV1`; epoch boundary fences |
| [**Level 03**](levels/level_03_lamarckian_retro_inheritance.md) | **Lamarckian Retro-Inheritance** | Hop-bounded retro-inheritance from failure receipts | Hop limit $d \le 10$, $(1/2)^d$ attenuation |
| [**Level 04**](levels/level_04_pareto_selection_and_fitness.md) | **Pareto Selection & Fitness** | Multi-objective exact evaluation over $\mathbb{Q}$ | Exact rational Pareto fronts; zero float coercion |
| [**Level 05**](levels/level_05_inverse_lineage_pagerank.md) | **Inverse Lineage PageRank** | Certified ancestral utility | `core.spectral.pagerank.v2` exact solver |
| [**Level 06**](levels/level_06_precedent_retrieval_and_evaporation.md) | **Precedent Retrieval & Evaporation** | Lexicographic matching & pheromone evaporation | Half-life $H$ epoch-based decay |
| [**Level 07**](levels/level_07_ecological_reserves_and_population.md) | **Ecological Reserves & Population** | Population policy & ecological reserves | Largest-remainder allocation, disjoint reserves |
| [**Level 08**](levels/level_08_lineage_taint_and_custody_invalidation.md) | **Lineage Taint & Invalidation** | Causal taint fixpoints vs custody invalidation | Forward causal taint propagation |
| [**Level 09**](levels/level_09_durable_event_log_and_persistence.md) | **Durable Event Log & Persistence** | Append-only event logging & hash custody | Producer-minted UUIDv5, separate `payload_sha256` |
| [**Level 10**](levels/level_10_open_horizons_and_multi_island_ecology.md) | **Open Horizons & Multi-Island Ecology** | Crossover blocks, island migration, frozen anchors | Homologous crossover blocks, island isolation |

---

## 3. Clean Architecture Crosswalk & Integration Matrix

- **Sovereign Rust Crate:** [`engine/crates_rs/core_prompt_civilization/`](../../../engine/crates_rs/core_prompt_civilization/)
- **Python Domain Estate:** [`pciv/`](../../../pciv/)
- **Proposal Fidelity Protocol (PFP):** [`pfp/`](../../../pfp/)
- **Adversary Swarm Cognition Base:** [`adversary/`](../../../adversary/)
- **Verification Commands:**
  ```powershell
  # 1. Rust prompt civilization crate (unit + integration suites)
  cargo test --manifest-path engine/crates_rs/tests/Cargo.toml -p core_prompt_civilization

  # 2. Python prompt civilization unit tests (domain, models, fitness, F1-F4)
  py -3.12 -m pytest pciv/unit -v -p no:cacheprovider

  # 3. Autophagous Fugu cemetery and antibody blocking integration suite
  py -3.12 -m pytest pciv/tests/integration/test_fugu_cemetery_blocking_loop.py -v -p no:cacheprovider

  # 4. Lamarckian Adversary loop integration tests
  py -3.12 -m pytest pciv/tests/integration/test_lamarckian_adversary_loop.py -v -p no:cacheprovider

  # 5. Continuous 50-generation evolutionary stress benchmark
  py -3.12 -m pytest pciv/tests/integration/test_multi_agent_evolutionary_stress.py -v -p no:cacheprovider
  ```
