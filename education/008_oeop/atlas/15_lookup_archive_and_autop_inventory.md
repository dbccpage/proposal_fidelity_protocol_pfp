# Engine Archive, AutoP & Historical Artifact Inventory

**Date:** 2026-08-20  
**Status:** Canonical Reference Index (`mathematical_wip`)  
**AuthorityEffect:** None  
**Scope:** Comprehensive index of historical repositories, 57 active crates in `sentinel/engine/crates`, prompt geometry engines, AutoP (`.atp`) specifications, Simplex Cosmos backlog (`smplx_000`–`smplx_009`), `_sentinel_archive` content-addressed corpora, trace archives, and curated Rust compiler modules across the Sentinel estate.

---

## 1. Overview

This document catalogs the primary and historical codebases, specifications, and telemetry traces that inform the **Polarized Operad**, **Prompt Civilization**, **AutoP**, **Simplex Cosmos Normal Forms**, and **Epistemic Immune System** architectures. It preserves exact file and URL paths so they can be referenced and integrated when appropriate.

---

## 2. Core Repository Locations

| Estate Component | Location / Path | Purpose |
| :--- | :--- | :--- |
| **Active Worktree (Python/Contracts)** | `c:\Users\a343o\source\repos\sentinelpy\` | Active Clean Architecture estate, 5-tier Operad Theory tower, OEWAS compiler, and Symbol Game. |
| **Active Crate Estate (57 Rust/Python Crates)** | `c:\Users\a343o\source\repos\sentinel\engine\crates\` | Full active crate library: 57 domain crates spanning category theory, DDA, solvers, physics, topology, and agents. |
| **GitHub Remote (Sentinel Crates Root)** | `https://github.com/dbccpage/sentinel/tree/main/engine/crates` | Upstream Git repository of the complete 57-crate Engine crate library. |
| **Historical Archive (Rust/Python)** | `c:\Users\a343o\source\repos\archive\` | Historical implementations (v0.0.0 through v0.1.0), Courage pipeline, prompt geometry, and immune traces. |
| **Sentinel Archive (52MB Master / Content-Addressed)** | `c:\Users\a343o\source\repos\_sentinel_archive\` | Content-addressed archive (`old/`, `new/`, `atlas_tools/`) containing thousands of Rust, Lean 4, ATP, and LaTeX source artifacts, plus 52 MB `master_file.md`. |
| **Simplex Cosmos Backlog** | `c:\Users\a343o\source\repos\sentinelpy\_ooutwire\product_backlog\simplex_cosmos\` | 10-tier product backlog (`smplx_000` to `smplx_009`), AutoP grammar, Normal Forms, and `smplcache`. |
| **GitHub Remote Archive (Engine)** | `https://github.com/dbccpage/archive/` | Upstream Git repository of historical Engine versions. |
| **GitHub Remote Archive (Sentinel Old)** | `https://github.com/dbccpage/_sentinel_archive/tree/main/old` | Upstream Git repository of historical content-addressed artifacts. |

---

## 3. Active Crate Estate (57 Crates in `sentinel/engine/crates/`)

* **Repository path:** [`sentinel_v0.2/engine/crates/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/engine/crates)
* **GitHub URL:** `https://github.com/dbccpage/sentinel/tree/main/engine/crates`

The 57 crates form the core mathematical, physical, and computational substrate:

```text
                               57-CRATE ESTATE TOPOLOGY
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Mathematical Foundations:                                                              │
 │   core_category_theory, core_higher_category_theory, core_topos_theory,             │
 │   core_sheaf_theory, core_homology, core_homotopy_type_theory,                      │
 │   core_linear_algebra, core_topology_theory, core_deformation_theory                │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Discrete Deformation & Obstruction Theory:                                             │
 │   core_discrete_deformation_algebra (DDA), core_obstruction_theory,                  │
 │   core_residual_families, core_certifiers, core_corrigibility                       │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Physical & Quantum Substrates:                                                         │
 │   core_quantum_physics, core_general_relativity, core_majorana,                     │
 │   majorana, core_mub, core_measurement                                  │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Applied Scientific Domains:                                                            │
 │   core_biology, core_chemistry, core_economics, core_machine_learning              │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Engine Control, Agents & Runtime:                                                      │
 │   core_conductor, agents, core_agent_registry, core_llm_gateway,        │
 │   core_solvers, core_search, core_symbol_game, core_state, core_trace,            │
 │   core_terminalizers, core_contracts, core_contract_core, core_governance          │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

### Complete Crate Roster (57 Crates)

1. `core_category_theory` — Native Category Theory definitions and functors.
2. `core_higher_category_theory` — $n$-categories, $(\infty, 1)$-categories, and higher morphisms.
3. `core_topos_theory` — Topos classifications, subobject classifiers $\Omega$, Heyting algebras.
4. `core_sheaf_theory` — Grothendieck topologies, sheaves, presheaves, and descent.
5. `core_homology` — Chain/cochain complexes, homology, and boundary operators.
6. `core_homotopy_type_theory` — Native HoTT and univalence primitives.
7. `core_linear_algebra` — Exact rational and tensor linear algebra.
8. `core_topology_theory` — Point-set and algebraic topology manifolds.
9. `core_deformation_theory` — Formal deformation and deformation quantization.
10. `core_discrete_deformation_algebra` — Discrete Deformation Algebra (DDA) trajectory engine.
11. `core_obstruction_theory` — Obstruction classes and cochain boundary analysis.
12. `core_residual_families` — Residual families and directional mass decay.
13. `core_certifiers` — Exact rational duality-gap and witness certifiers.
14. `core_corrigibility` — Epistemic corrigibility and alignment invariants.
15. `core_quantum_physics` — Quantum mechanics and operator algebras.
16. `core_general_relativity` — Differential geometry and spacetime curvature.
17. `core_majorana` — Majorana fermion operator algebras.
18. `majorana` — Majorana engine integration.
19. `core_mub` — Mutually Unbiased Bases.
20. `core_measurement` — Quantum measurement and state collapse.
21. `core_biology` — Computational biology and genomics models.
22. `core_chemistry` — Molecular and reaction representations.
23. `core_economics` — Game-theoretic and economic equilibrium models.
24. `core_machine_learning` — Statistical learning and optimization.
25. `core_solvers` — 112 unified exact solvers under `CoreSolver<Input, Output, Cert>`.
26. `core_search` — Exact combinatorial and heuristic search generators.
27. `core_symbol_game` — Discrete Symbol Game manifold retraction engine.
28. `core_conductor` — Multi-agent orchestration and workflow scheduling.
29. `agents` — Core engine agent roles and protocol adapters.
30. `core_agent_registry` — Content-addressed agent registry and capability slices.
31. `core_llm_gateway` — Provider-agnostic LLM inference gateway.
32. `core_state` — Epistemic state models and CAS snapshots.
33. `core_trace` — Unified telemetry trace logging and graph capture.
34. `core_terminalizers` — Bounded termination and terminal reality gatekeepers.
35. `core_contracts` — Formal contract manifests and schema validators.
36. `core_contract_core` — Inward-facing contract types and verification protocols.
37. `core_governance` — Council governance rules and Prime directives.
38. `core_councils` — Council deliberation and session pipelines.
39. `core_estate` — Monorepo estate discovery and layout validators.
40. `core_factory_interfaces` — Factory interfaces and dependency injection ports.
41. `core_functional` — Pure functional evaluation triad ($\Phi_1, \Gamma_2, \Xi$).
42. `core_id_run` — Unique run ID generators and content hashes.
43. `core_lander` — Landing zone and build artifact packaging.
44. `core_lifts` — Functorial and monadic lift operators.
45. `core_pipelines` — Execution pipeline runners.
46. `core_q` — Quantum and topological circuit representations.
47. `core_replay` — Deterministic execution replay and audit harness.
48. `core_representation` — Geometric and algebraic representations.
49. `core_representation_theory` — Group and algebra representation theory.
50. `core_self_maintenance` — Autonomous self-repair and migration.
51. `core_types` — Core value objects and domain types.
52. `core_atlas_reconciliation` — Atlas reconciliation engine.
53. `core_epk` — Epistemic Package Kernel.
54. `native_hott` — Native HoTT kernel.
55. `engines` — Specialized engine composition roots.
56. `constants` — Mathematical and physical constants.
57. `__pycache__` — Python bytecode cache.

---

## 4. Simplex Cosmos Stack (`_ooutwire/product_backlog/simplex_cosmos/`)

* **Path:** [`_ooutwire/product_backlog/simplex_cosmos/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/_ooutwire/product_backlog/simplex_cosmos)

| Subsystem | Folder | Key Artifacts & Features |
| :--- | :--- | :--- |
| **`smplx_000`** | `smplx_000_simplex_cosmos/` | Cosmos-level architectural foundation and topology. |
| **`smplx_001`** | `smplx_001_simplex_operating_system/` | Simplex Operating System specification and kernel interfaces. |
| **`smplx_002`** | `smplx_002_simplex_virtualization/` | Virtualization and execution container boundary specifications. |
| **`smplx_003`** | `smplx_003_simplex_internet_protocol/` | Simplex Network & Transport Protocol definitions. |
| **`smplx_004`** | `smplx_004_simplex_networks/` | Network topology and routing invariants. |
| **`smplx_005`** | `smplx_005_simplex_code_repository/` | Content-addressed code repository and CAS stores. |
| **`smplx_006`** | `smplx_006_databases/` | Database engine specifications and schema normal forms. |
| **`smplx_007`** | [`smplx_007_simple_cache/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/_ooutwire/product_backlog/simplex_cosmos/smplx_007_simple_cache) | High-performance boundary cache (`smplcache.py`, `postgres_cdc.py`, SQLite integration, boundary intersection benchmarks, `sqlshape.py`). |
| **`smplx_008`** | `smplx_008_programming_languages/` | Language design specifications and compiler definitions. |
| **`smplx_009`** | [`smplx_009_simplex_atpu_.../`](https://github.com/dbccpage/sentinel_v0.2/tree/main/_ooutwire/product_backlog/simplex_cosmos/smplx_009_simplex_atpu_compiler_databases_normal_forms) | **AutoP Grammar** (`atp_grammar.ebnf`), **Normal Forms** (`simplex-normal-forms/`), `auto_p/`, `auto_p_db/`, and `tcp_core/`. |

---

## 5. Curated Historical Rust Subsystems (Archive)

* [`compiler/l_infinity_operad.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/l_infinity_operad.rs): Multi-arity $L_\infty$-operadic conflict resolution via discrete Homotopy Transfer.
* [`compiler/string_diagram.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/string_diagram.rs): 97 KB topological string diagram compiler and graphical tensor calculus.
* [`compiler/boundary_check.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/boundary_check.rs): 113 KB boundary condition and invariant verification engine.
* [`compiler/egraph.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/egraph.rs): 51 KB equivalence saturation e-graph term rewrite engine.
* [`compiler/ptir.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/ptir.rs): 40 KB Presheaf Topological Intermediate Representation compiler.
* [`compiler/lifetime_check.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/lifetime_check.rs): 34 KB topological lifetime and linear resource borrow checker.
* [`compiler/tqc_atpu.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/compiler/tqc_atpu.rs): 44 KB Topological Quantum & Categorical ATPU compilation kernel.
* [`ascent/.../prompt_geometry.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/ascent/theory/metas/meta_04/prompt_geometry.rs): 7D metric prompt vector space $\mathbf{v}(P) \in \mathbb{R}^7$, `PromptClass`, `MorphismType`, and `is_crystal` / `is_noise` classifiers.
* [`oe_domain/epistemic_trace.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/engine/oe_domain/epistemic_trace.rs): 74 KB domain engine for epistemic execution traces.
* [`oe_adapters/python_bridge/courage_bridge.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/engine/oe_adapters/python_bridge/courage_bridge.rs): 63 KB Courage autonomous solver bridge.
* [`oe_adapters/lean4_bridge/compiler_bridge.rs`](https://github.com/dbccpage/archive/blob/main/v0.1.0/core_core/src/engine/oe_adapters/lean4_bridge/compiler_bridge.rs): 30 KB Lean 4 theorem prover compiler bridge.

---

## 6. AutoP (`.atp`) Specification Language

* **Primary Grammar Specification:**
  [`_ooutwire/.../atp_grammar.ebnf`](https://github.com/dbccpage/sentinel_v0.2/blob/main/_ooutwire/product_backlog/simplex_cosmos/smplx_009_simplex_atpu_compiler_databases_normal_forms/autop_specification_language/grammar/atp_grammar.ebnf)  
  *(1,304 lines of formal EBNF grammar declaring categorical, algebraic, sheaf-theoretic, and logic constructs)*.
* **Rust Implementation Modules in Archive:**
  * `v0.0.1/src/auto_p/`
  * `v0.0.1/src/auto_p_db/`

---

## 7. Active Python & Clean Architecture Estate

| Component | Path | Current Status |
| :--- | :--- | :--- |
| **5-Tier Operad Theory** | `engine/crates/operad_theory/` (no longer present in `dbccpage/sentinel_v0.2`) | 100% Green (225/225 tests passing/xfailed/xpassed in `test_operad_theory.py` & `test_operad_theory_expanded.py`). |
| **OEWAS Workflow Operad** | [`workflows_agents_skills/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/workflows_agents_skills) | Clean Architecture implementation of Operad Compiler, domain models, and port typing. |
| **Swarm Immune Domain** | [`adversary/domain/immune/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/adversary/domain/immune) | `Antibody` Value Objects, `PharmacySeeder`, `PharmacyCatalogRepository`, default templates. |
| **Prompt Civilization** | [`engine/crates/prompt_civilization/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/engine/crates/prompt_civilization) | Typed prompt review operad (`models.py`, `registry.py`, `review.py`, `operad_operations.yaml`). |
| **Symbol Game Runtime** | [`pfp/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/pfp) | Discrete turn execution, manifold retraction, and packet envelope serialization. |
| **Governance Contracts** | [`governance/contracts/.../operad_theory/`](https://github.com/dbccpage/sentinel_v0.2/tree/main/governance/contracts/contracts_crates/mathematics/operad_theory) | 11 YAML contracts validated against schema `core.contract.v1`. |

---

## 8. Documentation References in `_docs/`

* [`00_index.md`](https://github.com/dbccpage/sentinel_v0.2/blob/main/workflows_agents_skills/_docs/00_index.md): Master Table of Contents and documentation index.
* `01_spec_polarized_operad_and_anti_skills.md` (no longer present in `dbccpage/sentinel_v0.2`): Formal design specification of polarized operads $(\mathcal{O}^+, \mathcal{O}^-)$, claim hygiene, and the 10 Prime Laws of Anti-Skills.
* `02_review_applied_workflow_operad.md` (no longer present in `dbccpage/sentinel_v0.2`): Implementation review, architectural punchlist, and test resolutions.
* `04_guide_oewas_test_suite_execution.md` (no longer present in `dbccpage/sentinel_v0.2`): OEWAS test suite execution and verification guide.
