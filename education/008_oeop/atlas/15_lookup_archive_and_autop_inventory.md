# Omega Engine Archive, AutoP & Historical Artifact Inventory

**Date:** 2026-08-20  
**Status:** Canonical Reference Index (`mathematical_wip`)  
**AuthorityEffect:** None  
**Scope:** Comprehensive index of historical repositories, 57 active crates in `anomalon/omega_engine/crates`, prompt geometry engines, AutoP (`.atp`) specifications, Simplex Cosmos backlog (`smplx_000`–`smplx_009`), `_anomalon_archive` content-addressed corpora, trace archives, and curated Rust compiler modules across the Anomalon estate.

---

## 1. Overview

This document catalogs the primary and historical codebases, specifications, and telemetry traces that inform the **Polarized Operad**, **Prompt Civilization**, **AutoP**, **Simplex Cosmos Normal Forms**, and **Epistemic Immune System** architectures. It preserves exact file and URL paths so they can be referenced and integrated when appropriate.

---

## 2. Core Repository Locations

| Estate Component | Location / Path | Purpose |
| :--- | :--- | :--- |
| **Active Worktree (Python/Contracts)** | `c:\Users\a343o\source\repos\anomalonpy\` | Active Clean Architecture estate, 5-tier Operad Theory tower, OEWAS compiler, and Symbol Game. |
| **Active Crate Estate (57 Rust/Python Crates)** | `c:\Users\a343o\source\repos\anomalon\omega_engine\crates\` | Full active crate library: 57 domain crates spanning category theory, DDA, solvers, physics, topology, and agents. |
| **GitHub Remote (Anomalon Crates Root)** | `https://github.com/dbccpage/anomalon/tree/main/omega_engine/crates` | Upstream Git repository of the complete 57-crate Omega Engine crate library. |
| **Historical Archive (Rust/Python)** | `c:\Users\a343o\source\repos\omega_engine_archive\` | Historical implementations (v0.0.0 through v0.1.0), Courage pipeline, prompt geometry, and immune traces. |
| **Anomalon Archive (52MB Master / Content-Addressed)** | `c:\Users\a343o\source\repos\_anomalon_archive\` | Content-addressed archive (`old/`, `new/`, `atlas_tools/`) containing thousands of Rust, Lean 4, ATP, and LaTeX source artifacts, plus 52 MB `master_file.md`. |
| **Simplex Cosmos Backlog** | `c:\Users\a343o\source\repos\anomalonpy\_ooutwire\product_backlog\simplex_cosmos\` | 10-tier product backlog (`smplx_000` to `smplx_009`), AutoP grammar, Normal Forms, and `smplcache`. |
| **GitHub Remote Archive (Omega Engine)** | `https://github.com/dbccpage/omega_engine_archive/` | Upstream Git repository of historical Omega Engine versions. |
| **GitHub Remote Archive (Anomalon Old)** | `https://github.com/dbccpage/_anomalon_archive/tree/main/old` | Upstream Git repository of historical content-addressed artifacts. |

---

## 3. Active Crate Estate (57 Crates in `anomalon/omega_engine/crates/`)

* **Repository path:** [`anomalon_v0.2/omega_engine/crates/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/omega_engine/crates)
* **GitHub URL:** `https://github.com/dbccpage/anomalon/tree/main/omega_engine/crates`

The 57 crates form the core mathematical, physical, and computational substrate:

```text
                               57-CRATE ESTATE TOPOLOGY
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Mathematical Foundations:                                                              │
 │   omega_category_theory, omega_higher_category_theory, omega_topos_theory,             │
 │   omega_sheaf_theory, omega_homology, omega_homotopy_type_theory,                      │
 │   omega_linear_algebra, omega_topology_theory, omega_deformation_theory                │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Discrete Deformation & Obstruction Theory:                                             │
 │   omega_discrete_deformation_algebra (DDA), omega_obstruction_theory,                  │
 │   omega_residual_families, omega_certifiers, omega_corrigibility                       │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Physical & Quantum Substrates:                                                         │
 │   omega_quantum_physics, omega_general_relativity, omega_majorana,                     │
 │   omega_engine_majorana, omega_mub, omega_measurement                                  │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Applied Scientific Domains:                                                            │
 │   omega_biology, omega_chemistry, omega_economics, omega_machine_learning              │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Engine Control, Agents & Runtime:                                                      │
 │   omega_conductor, omega_engine_agents, omega_agent_registry, omega_llm_gateway,        │
 │   omega_solvers, omega_search, omega_symbol_game, omega_state, omega_trace,            │
 │   omega_terminalizers, omega_contracts, omega_contract_core, omega_governance          │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

### Complete Crate Roster (57 Crates)

1. `omega_category_theory` — Native Category Theory definitions and functors.
2. `omega_higher_category_theory` — $n$-categories, $(\infty, 1)$-categories, and higher morphisms.
3. `omega_topos_theory` — Topos classifications, subobject classifiers $\Omega$, Heyting algebras.
4. `omega_sheaf_theory` — Grothendieck topologies, sheaves, presheaves, and descent.
5. `omega_homology` — Chain/cochain complexes, homology, and boundary operators.
6. `omega_homotopy_type_theory` — Native HoTT and univalence primitives.
7. `omega_linear_algebra` — Exact rational and tensor linear algebra.
8. `omega_topology_theory` — Point-set and algebraic topology manifolds.
9. `omega_deformation_theory` — Formal deformation and deformation quantization.
10. `omega_discrete_deformation_algebra` — Discrete Deformation Algebra (DDA) trajectory engine.
11. `omega_obstruction_theory` — Obstruction classes and cochain boundary analysis.
12. `omega_residual_families` — Residual families and directional mass decay.
13. `omega_certifiers` — Exact rational duality-gap and witness certifiers.
14. `omega_corrigibility` — Epistemic corrigibility and alignment invariants.
15. `omega_quantum_physics` — Quantum mechanics and operator algebras.
16. `omega_general_relativity` — Differential geometry and spacetime curvature.
17. `omega_majorana` — Majorana fermion operator algebras.
18. `omega_engine_majorana` — Majorana engine integration.
19. `omega_mub` — Mutually Unbiased Bases.
20. `omega_measurement` — Quantum measurement and state collapse.
21. `omega_biology` — Computational biology and genomics models.
22. `omega_chemistry` — Molecular and reaction representations.
23. `omega_economics` — Game-theoretic and economic equilibrium models.
24. `omega_machine_learning` — Statistical learning and optimization.
25. `omega_solvers` — 112 unified exact solvers under `OmegaSolver<Input, Output, Cert>`.
26. `omega_search` — Exact combinatorial and heuristic search generators.
27. `omega_symbol_game` — Discrete Symbol Game manifold retraction engine.
28. `omega_conductor` — Multi-agent orchestration and workflow scheduling.
29. `omega_engine_agents` — Core engine agent roles and protocol adapters.
30. `omega_agent_registry` — Content-addressed agent registry and capability slices.
31. `omega_llm_gateway` — Provider-agnostic LLM inference gateway.
32. `omega_state` — Epistemic state models and CAS snapshots.
33. `omega_trace` — Unified telemetry trace logging and graph capture.
34. `omega_terminalizers` — Bounded termination and terminal reality gatekeepers.
35. `omega_contracts` — Formal contract manifests and schema validators.
36. `omega_contract_core` — Inward-facing contract types and verification protocols.
37. `omega_governance` — Council governance rules and Prime directives.
38. `omega_councils` — Council deliberation and session pipelines.
39. `omega_estate` — Monorepo estate discovery and layout validators.
40. `omega_factory_interfaces` — Factory interfaces and dependency injection ports.
41. `omega_functional` — Pure functional evaluation triad ($\Phi_1, \Gamma_2, \Xi$).
42. `omega_id_run` — Unique run ID generators and content hashes.
43. `omega_lander` — Landing zone and build artifact packaging.
44. `omega_lifts` — Functorial and monadic lift operators.
45. `omega_pipelines` — Execution pipeline runners.
46. `omega_q` — Quantum and topological circuit representations.
47. `omega_replay` — Deterministic execution replay and audit harness.
48. `omega_representation` — Geometric and algebraic representations.
49. `omega_representation_theory` — Group and algebra representation theory.
50. `omega_self_maintenance` — Autonomous self-repair and migration.
51. `omega_types` — Core value objects and domain types.
52. `omega_atlas_reconciliation` — Atlas reconciliation engine.
53. `omega_epk` — Epistemic Package Kernel.
54. `omega_engine_native_hott` — Native HoTT kernel.
55. `omega_engines` — Specialized engine composition roots.
56. `constants` — Mathematical and physical constants.
57. `__pycache__` — Python bytecode cache.

---

## 4. Simplex Cosmos Stack (`_ooutwire/product_backlog/simplex_cosmos/`)

* **Path:** [`_ooutwire/product_backlog/simplex_cosmos/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/_ooutwire/product_backlog/simplex_cosmos)

| Subsystem | Folder | Key Artifacts & Features |
| :--- | :--- | :--- |
| **`smplx_000`** | `smplx_000_simplex_cosmos/` | Cosmos-level architectural foundation and topology. |
| **`smplx_001`** | `smplx_001_simplex_operating_system/` | Simplex Operating System specification and kernel interfaces. |
| **`smplx_002`** | `smplx_002_simplex_virtualization/` | Virtualization and execution container boundary specifications. |
| **`smplx_003`** | `smplx_003_simplex_internet_protocol/` | Simplex Network & Transport Protocol definitions. |
| **`smplx_004`** | `smplx_004_simplex_networks/` | Network topology and routing invariants. |
| **`smplx_005`** | `smplx_005_simplex_code_repository/` | Content-addressed code repository and CAS stores. |
| **`smplx_006`** | `smplx_006_databases/` | Database engine specifications and schema normal forms. |
| **`smplx_007`** | [`smplx_007_simple_cache/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/_ooutwire/product_backlog/simplex_cosmos/smplx_007_simple_cache) | High-performance boundary cache (`smplcache.py`, `postgres_cdc.py`, SQLite integration, boundary intersection benchmarks, `sqlshape.py`). |
| **`smplx_008`** | `smplx_008_programming_languages/` | Language design specifications and compiler definitions. |
| **`smplx_009`** | [`smplx_009_simplex_atpu_.../`](https://github.com/dbccpage/anomalon_v0.2/tree/main/_ooutwire/product_backlog/simplex_cosmos/smplx_009_simplex_atpu_compiler_databases_normal_forms) | **AutoP Grammar** (`atp_grammar.ebnf`), **Normal Forms** (`simplex-normal-forms/`), `auto_p/`, `auto_p_db/`, and `tcp_omega/`. |

---

## 5. Curated Historical Rust Subsystems (Archive)

* [`compiler/l_infinity_operad.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/l_infinity_operad.rs): Multi-arity $L_\infty$-operadic conflict resolution via discrete Homotopy Transfer.
* [`compiler/string_diagram.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/string_diagram.rs): 97 KB topological string diagram compiler and graphical tensor calculus.
* [`compiler/boundary_check.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/boundary_check.rs): 113 KB boundary condition and invariant verification engine.
* [`compiler/egraph.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/egraph.rs): 51 KB equivalence saturation e-graph term rewrite engine.
* [`compiler/ptir.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/ptir.rs): 40 KB Presheaf Topological Intermediate Representation compiler.
* [`compiler/lifetime_check.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/lifetime_check.rs): 34 KB topological lifetime and linear resource borrow checker.
* [`compiler/tqc_atpu.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/compiler/tqc_atpu.rs): 44 KB Topological Quantum & Categorical ATPU compilation kernel.
* [`ascent/.../prompt_geometry.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/ascent/theory/metas/meta_04/prompt_geometry.rs): 7D metric prompt vector space $\mathbf{v}(P) \in \mathbb{R}^7$, `PromptClass`, `MorphismType`, and `is_crystal` / `is_noise` classifiers.
* [`oe_domain/epistemic_trace.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/omega_engine/oe_domain/epistemic_trace.rs): 74 KB domain engine for epistemic execution traces.
* [`oe_adapters/python_bridge/courage_bridge.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/omega_engine/oe_adapters/python_bridge/courage_bridge.rs): 63 KB Courage autonomous solver bridge.
* [`oe_adapters/lean4_bridge/compiler_bridge.rs`](https://github.com/dbccpage/omega_engine_archive/blob/main/omega_engine_v0.1.0/omega_core/src/omega_engine/oe_adapters/lean4_bridge/compiler_bridge.rs): 30 KB Lean 4 theorem prover compiler bridge.

---

## 6. AutoP (`.atp`) Specification Language

* **Primary Grammar Specification:**
  [`_ooutwire/.../atp_grammar.ebnf`](https://github.com/dbccpage/anomalon_v0.2/blob/main/_ooutwire/product_backlog/simplex_cosmos/smplx_009_simplex_atpu_compiler_databases_normal_forms/autop_specification_language/grammar/atp_grammar.ebnf)  
  *(1,304 lines of formal EBNF grammar declaring categorical, algebraic, sheaf-theoretic, and logic constructs)*.
* **Rust Implementation Modules in Archive:**
  * `omega_engine_v0.0.1/src/auto_p/`
  * `omega_engine_v0.0.1/src/auto_p_db/`

---

## 7. Active Python & Clean Architecture Estate

| Component | Path | Current Status |
| :--- | :--- | :--- |
| **5-Tier Operad Theory** | `omega_engine/crates/operad_theory/` (no longer present in `dbccpage/anomalon_v0.2`) | 100% Green (225/225 tests passing/xfailed/xpassed in `test_operad_theory.py` & `test_operad_theory_expanded.py`). |
| **OEWAS Workflow Operad** | [`omega_engine_workflows_agents_skills/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/omega_engine_workflows_agents_skills) | Clean Architecture implementation of Operad Compiler, domain models, and port typing. |
| **Swarm Immune Domain** | [`omega_engine_woland/domain/immune/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/omega_engine_woland/domain/immune) | `Antibody` Value Objects, `PharmacySeeder`, `PharmacyCatalogRepository`, default templates. |
| **Prompt Civilization** | [`omega_engine/crates/prompt_civilization/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/omega_engine/crates/prompt_civilization) | Typed prompt review operad (`models.py`, `registry.py`, `review.py`, `operad_operations.yaml`). |
| **Symbol Game Runtime** | [`omega_engine_pfp/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/omega_engine_pfp) | Discrete turn execution, manifold retraction, and packet envelope serialization. |
| **Governance Contracts** | [`omega_engine_governance/contracts/.../operad_theory/`](https://github.com/dbccpage/anomalon_v0.2/tree/main/omega_engine_governance/contracts/contracts_omega_engine_crates/mathematics/operad_theory) | 11 YAML contracts validated against schema `omega.contract.v1`. |

---

## 8. Documentation References in `_docs/`

* [`00_index.md`](https://github.com/dbccpage/anomalon_v0.2/blob/main/omega_engine_workflows_agents_skills/_docs/00_index.md): Master Table of Contents and documentation index.
* `01_spec_polarized_operad_and_anti_skills.md` (no longer present in `dbccpage/anomalon_v0.2`): Formal design specification of polarized operads $(\mathcal{O}^+, \mathcal{O}^-)$, claim hygiene, and the 10 Prime Laws of Anti-Skills.
* `02_review_applied_workflow_operad.md` (no longer present in `dbccpage/anomalon_v0.2`): Implementation review, architectural punchlist, and test resolutions.
* `04_guide_oewas_test_suite_execution.md` (no longer present in `dbccpage/anomalon_v0.2`): OEWAS test suite execution and verification guide.
