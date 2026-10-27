# Detailed definition: Subsystem Retirement & Adapter Isolation (1)

**AuthorityEffect:** None.

Parent: [Subsystem Retirement & Adapter Isolation](../../../../../rules/engineering/rl_subsystem_retirement_and_adapter_invariants.md). Load for the matching predicate, not every task.

# Rule: Subsystem Retirement, Adapter Isolation & Specialist Consolidation

**AuthorityEffect:** None.

This rule codifies canonical model provider adapter locations, anti-shim legacy subsystem absorption, zero data-loss asset relocation, and single-manager specialist triad consolidation. Cross-reference native Rust engineering standards: [`rl_rust_engineering_standards.md`](../../../../../rules/engineering/rl_rust_engineering_standards.md).

---

## Canonical Model Provider Adapters Invariant (`RULE_PROVIDER_ADAPTERS_CANONICAL_001`)

> **Canonical Provider Adapters Location:**
>
> 1. All model and LLM provider adapters (e.g., Mock LLM, Ollama Local, Gemini Live, Local ONNX) must reside strictly within `adversary/infrastructure/providers/adapters/`.
> 2. The legacy `engine/adapters/` and `providers/` locations are permanently deleted and must never be reintroduced or imported.
> 3. Consumers and test suites across the repository must import from `adversary.infrastructure.providers.adapters` (and domain types from `adversary.domain.providers`), with `pytest.ini` configured to run `adversary/tests/providers`.

---

## Legacy Subsystem Absorption & Retirement Invariant

> **Anti-Shim Subsystem Consolidation Protocol:**
>
> 1. **Canonical Package Authority Audit**: When resolving duplicate, overlapping, or legacy code trees (e.g. `engine/` vs `pfp/`), verify canonical package declarations in `pyproject.toml` or `Cargo.toml`.
> 2. **Set-Theoretic Divergence Check**: Determine whether the candidate legacy tree is a strict subset or divergent branch of the canonical package.
> 3. **Anti-Shim Rejection of Mutual Merging**: If the legacy tree relies on deprecated compatibility shims, re-export facades, or obsolete imports, never execute a mutual two-way merge. The canonical modern package must absorb any verified unique assets, and the legacy tree must be cleanly deleted via `git rm -r`.
> 4. **Configuration & Harness Purge**: Upon legacy tree removal, immediately update test runners (`pytest.ini` exclusions/ignores), benchmarks, notebook scenes, and documentation to remove references to the retired path.
> 5. **Cross-Subsystem Re-routing Closure**: When retiring a shared library or adapter package (such as `providers/`), all importing modules across client estates (`pfp`, `education`, `pciv`, etc.) must be re-routed to the successor package before removing the legacy folder, ensuring zero runtime `ModuleNotFoundError` regressions and confirming that fresh-process imports of the retired root fail-closed (`RETIRED_ROOT_REFUSED`).

---

## Legacy Prototype Retirement & Zero Data-Loss Relocation Invariant (`RULE_RETIREMENT_ZERO_DATA_LOSS_001`)

> **Zero Data-Loss Asset Relocation:**
>
> 1. When retiring, deprecating, or deleting legacy code directories (such as `engine/_legacy/symbol_game_recovery/python/`), non-executable assets (monographs, game rules, product contracts, obstruction packets, master architecture plans, and reviews) must never be discarded silently.
> 2. Prior to deleting any legacy directory, all non-code documentation and contracts must be audited, mapped, and absorbed into their canonical research or governance home (`research/mssn_sn_tower/` subdirectories: `monograph/`, `how_to_play/`, `packets/`, `reviews/`, `contracts/`).
> 3. Verify SHA-256 byte-level identity upon relocation so Git detects clean 100% rename operations (`R100`) before purging the deprecated container.

---

## Subsystem Specialist Triad Absorption Invariant (`RULE_AGENT_SPECIALIST_TRIAD_ABSORPTION_001`)

> **Single-Manager Orchestration & Specialist Absorption:**
>
> 1. **Triad Consolidation Mandate:**
>    Specialized domain sub-contexts must not maintain fragmented separate agent persona manifests for Developer, Reviewer, and Tester (e.g. `techne-<subsystem>-developer.md`, `techne-<subsystem>-reviewer.md`, `techne-<subsystem>-tester.md`).
>    They must be consolidated into a single master orchestrator/manager agent manifest: `techne-<subsystem>-manager.md`.
> 2. **Orchestrator Persona Structure:**
>    - **Mandate Absorption:** Explicitly delineate the three absorbed roles (Developer, Reviewer, Tester) in Section 1.
>    - **Underlying Skill Licensing:** License the granular parent skills (`techne-code-<subsystem>-developer`, `techne-code-<subsystem>-reviewer`, `techne-code-<subsystem>-tester`) in YAML frontmatter `licensed_skills`.
>    - **Full Color Closure:** Enclose the complete sub-operad colors (`licensed_colours: [Audit, Code, Contract, Receipt, State]`).
>    - **Unified Cognitive Defense:** Synthesize the red-cell immune profiles (Clean Architecture inward dependencies, exact rational arithmetic, lossy projection rejection, and test falsification).
> 3. **Atomic Four-Host Propagation & Retirement:**
>    - When creating or updating a manager agent, the three absorbed specialist agent files must be atomically removed via `git rm` across all four host roots (`.agents/agents/`, `.claude/agents/`, `.codex/agents/`, `.grok/agents/`).
>    - The unified manager agent manifest must be installed with byte-level parity across all four host roots.

---

## Dual-Language Adapter & Test Isolation Parity Invariant (`RULE_DUAL_LANGUAGE_ADAPTER_AND_TEST_ISOLATION_001`)

> **Dual-Language Adapter & Test Isolation Directive:**
>
> 1. **Lockstep Python & Rust Default Redirection:** When default persistence roots or telemetry custody paths are redirected (e.g. defaulting to `_ic/nara/permanent_records/`), the redirection must be implemented in both Python adapters (`JsonlBoutJournal.for_repository`, `FileGenealogyAdapter.for_repository`, `DurableIntelligenceCollector.for_repository`) and compiled Rust kernel crates (`core_symbol_game::adversary_custody` namespace mapping and `adversary_host` journal discovery) in lockstep.
> 2. **Strict Test Isolation Preservation:** Default path redirection must only take effect when caller-supplied `output_dir` is `None`. Test harnesses passing explicit temporary paths (`tmp_path`) must take absolute precedence to ensure hermetic test execution without side effects in repository permanent records.
