# Detailed definition: Subsystem Relocation & Estate Purity (1)

**AuthorityEffect:** None.

Parent: [Subsystem Relocation & Estate Purity](../../../../../rules/architecture/rl_subsystem_relocation_and_estate_purity.md). Load for the matching predicate, not every task.

# Rule: Subsystem Relocation, Documentation Structure & Estate Purity

**AuthorityEffect:** None.

This rule codifies gate and registry relocation closure, docs conventions, storage encapsulation, shadow prototype retirement, and canonical ROP placement.

---

## Bounded Context Gate & Registry Relocation Closure Invariant (`RULE_GATE_REGISTRY_RELOCATION_001`)

> **Atomic Gate, Registry & Script Relocation:**
>
> Whenever moving, refactoring, or consolidating verification gates, evaluators, registries, or CLI diagnostic tools between bounded contexts:
>
> 1. **Embedded Registry Evidence Path Parity:** All JSON/YAML defense and capability registries (e.g. `cognitive_warfare_defense_registry.json`) containing repository-relative `evidence_path` keys must have their target paths updated synchronously with file relocation.
> 2. **Dual-Invocation `sys.path` Bootstrapping:** Any diagnostic script or report generator that can be executed directly as a standalone CLI tool (`py -3.12 path/to/script.py`) while importing from bounded context packages must include defensive repository root bootstrapping prior to project imports:
>    ```python
>    _REPO_ROOT = Path(__file__).resolve().parents[<depth>]
>    if __package__ in (None, "") and str(_REPO_ROOT) not in sys.path:
>        sys.path.insert(0, str(_REPO_ROOT))
>    ```
> 3. **Quadruple Local-CI Gate Route Synchronization:** When a CI verification gate entrypoint is relocated, four files must be updated atomically:
>    - `omega_engine_operations/infrastructure/cicd/local_ci_repository.py` (`_TRUSTED_EVALUATOR_PATH_PAIRS`)
>    - `omega_engine_operations/domain/cicd/catalog.py` (`GATE_CATALOG_V3`)
>    - `omega_engine_operations/domain/cicd/gate_catalog_v3.yaml`
> 4. **Documentation `source_paths` Alignment:** Documentation files adhering to `symbol-game-documentation/v1` frontmatter must be verified and updated so their `source_paths` list matches the new file locations.
> 5. **Canonical Context Priority with Explicit Fallbacks:** Whenever tools, gates, or evaluators resolve workspace paths dynamically from `REPO_ROOT` (e.g. `TESTS_DIR`, `DEFENSE_REGISTRY_PATH`), the path resolution MUST prioritize the active canonical bounded context (e.g. `omega_engine_cognitive_operations/tests/...`), followed by documented legacy fallbacks if historical backwards compatibility is required. Immediately audit every `Path(__file__).resolve().parents[N]` call to ensure it accurately resolves to the workspace root at its new directory depth.
> 6. **Dynamic Ascending Parent Resolution for Sibling Assets:** When discovering sibling planning, catalog, or documentation assets outside the active bounded context (e.g., `plans/*.md`), tools and checkers MUST avoid hardcoded parent index offsets (e.g. `ROOT.parents[2]`). Instead, use dynamic upward generator discovery across `(ROOT, *ROOT.parents)` with explicit fallback.
> 7. **Atomic Relocation of Mixed Tracked & Gitignored Estates:** When moving a subsystem directory containing local execution runs, caches, or gitignored artifacts (such as `_ic/nara/legacy/runs/`), agents must move the directory at the filesystem level and run `git add -A` on both old and new paths to ensure no stranded directory structures remain in the former path.
> 8. **Transitional Forwarding Entrypoint & Staged Retention Parity:** When relocating an active execution suite, test harness, or subsystem root between bounded contexts, if backward-compatible invocations (e.g. standalone CLI runners or verification scripts like `run_fifty_demos.py`) are expected at the former path:
>    - *Lightweight Delegation:* Provide a thin delegating entrypoint at the legacy location that adds both `_REPO_ROOT` and the canonical `_PYTHON_DIR` to `sys.path` before delegating to the canonical Clean Architecture controller.
>    - *Git Index Synchronization:* If the legacy tree was staged as deleted (`git rm`), explicitly ensure the parent directory is created and run `git add` on the forwarding script immediately so git index and working directory remain synchronized without phantom missing-file regressions.
>    - *Dual Path Parity:* Verify that both the canonical entrypoint and the legacy forwarding entrypoint execute identically and pass all linter and formatting checks.
> 9. **Dynamic Discovery Adapter Seam Parity:** Whenever relocating contract catalogs, modes, grammars, or schemas out of scratch/prototype trees into canonical educational or operational contexts:
>    - *Candidate List Priority:* All infrastructure discovery adapters (e.g. `mode_discovery.py`, `check_grammars.py`) MUST update their search candidate lists to prioritize canonical paths (e.g. `004_oepfp/modes/`) prior to legacy fallbacks.
>    - *Dynamic Ascending Marker Search:* Scripts and test runners MUST dynamically resolve workspace and submodule roots via marker directories (e.g. `next(p for p in HERE.parents if (p / "omega_engine_pfp").is_dir() or (p / ".git").exists())`) rather than static `HERE.parents[N]` indexing.
> 10. **Pre-Move Git Index Sanitization (`git mv` Safety):** Prior to executing `git mv` on a directory, inspect `git status --porcelain <path>` and synchronize the index. Unstaged deletions or unlinked files in the subtree must be reconciled via `git add -u <path>` before moving, preventing `fatal: bad source` and working tree corruption.
> 11. **Nested Sub-Application & Test Suite Relocation Closure:** When factoring a bounded context into nested sub-apps (e.g. `omega_engine_education/education_app/`) and relocating its test suite:
>     - *Multi-Candidate Manifest Discovery:* Storage ports resolving shared manifests (e.g. `curriculum_manifest.yaml`) must search candidate paths across active sub-app and parent package roots (`[self.root / "manifest.yaml", self.root.parent / "manifest.yaml"]`).
>     - *Test Suite App-Root Re-Anchoring:* When tests move to `<sub_app>/tests/`, test fixtures and AST auditors must anchor `self.app_dir = Path(__file__).resolve().parents[1]` directly to the sub-app root, ensuring `self.domain_dir = self.app_dir / "domain"`.

## Shadow Prototype Retirement & Estate Purity (`RULE_SHADOW_PROTOTYPE_RETIREMENT_001`)

> **Atomic Retirement of Shadowed Prototypes:**
>
> 1. **No Lingering Subsystem Prototypes:** Once a prototype or demonstration migrates to its canonical bounded context (e.g., MSS-N demonstrations belong strictly to `omega_engine_pfp`, never `omega_engine_woland`), the obsolete subtree must be deleted atomically across `domain/`, `use_cases/`, and `tests/`.
> 2. **Four-Point Retirement Audit:** Audit callers and repoint to canonical imports, prune obsolete test discovery entries in `pytest.ini`, execute `git rm -r` on the obsolete subtree, and verify targeted tests with `py -3.12`.
> 3. **Orphaned Cache & Empty Directory Eradication:** Whenever a prototype, demo, or use-case directory is retired or relocated, all intermediate `__pycache__` artifacts, `.pyc` files, and empty parent directories must be completely deleted from the filesystem (`Remove-Item -Recurse -Force`). A directory containing only cached bytecode is an orphaned estate defect and must never be committed or left lingering in the workspace.
> 4. **Sibling Test Import Scrubbing:** When a legacy research subtree or prototype is absorbed or retired, immediately run ripgrep for the retired package prefix across all test directories. Lingering imports in surviving test modules must be repointed to canonical packages or retired alongside the prototype to prevent test collection failure (`ModuleNotFoundError`).
> 5. **Consumer Bytecode Invalidation:** Following any subtree deletion or import repointing, execute a recursive `__pycache__` purge across both the target package and its consumers to prevent stale `.pyc` bytecode from loading vanished paths in parallel test executors.


## Documentation Estate & Submodule Layout Cross-Reference

For bounded context docs layout (`RULE_BOUNDED_CONTEXT_DOCS_001`), curriculum storage (`RULE_CURRICULUM_STORAGE_DOCS_001`), doc indices (`RULE_DOCS_INDEX_DISCIPLINE_001`), education submodules (`RULE_EDUCATION_DOCS_SUBMODULE_LAYOUT_001`), and link relativity (`RULE_INTERNAL_MARKDOWN_LINK_RELATIVITY_001`), see [`.agents/rules/docs/rl_documentation_estate_and_submodule_layout.md`](../../../../../rules/docs/rl_documentation_estate_and_submodule_layout.md).
