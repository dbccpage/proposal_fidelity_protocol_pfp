# Detailed definition: Python Runtime & Environment Standards (1)

**AuthorityEffect:** None.

Parent: [Python Runtime & Environment Standards](../../../../../rules/paths/rl_python_runtime_and_environment_standards.md). Load for the matching predicate, not every task.

# Rule: Python Runtime, Test & Environment Standards

**AuthorityEffect:** None.

This rule codifies Windows Python 3.12 runtime discipline, Windows pytest temporary directory pre-allocation, dynamic repository root resolution, worktree workspace boundary and sparse checkout hygiene, filesystem inspection and build tree pruning, Clean Architecture linter module tokenization, and Windows asyncio teardown and event loop policy hygiene across engine operations.

---

## Windows Python 3.12 Runtime Discipline (`RULE_WINDOWS_PYTHON_VERSION_DISCIPLINE_001`)

> **Explicit Python 3.12 Launcher Invocation on Windows:**
>
> 1. **Prohibition of Ambiguous `python` Invocation:** In Windows environments, autonomous agents and automated tooling must never invoke the unversioned command `python` or `python3` directly. On modern Windows workstations, `python` may resolve to pre-release/alpha builds (e.g. Python 3.14 alpha) lacking binary wheel compatibility or exhibiting namespace packaging defects (`AttributeError: module 'matplotlib' has no attribute '__path__'`).
> 2. **Mandatory `py -3.12` Standard:** All gate checks, test runners (`pytest`), linters, and script executions must explicitly use `py -3.12`:
>    ```powershell
>    py -3.12 -m pytest <path> -v
>    py -3.12 <script.py> [args]
>    ```
> 3. **Subprocess Interpreter Binding:** Python scripts that spawn child Python subprocesses must pass `sys.executable` (which resolves to the active Python 3.12 executable) rather than hardcoded `"python"`.

---

## Windows Pytest Temporary Directory Invariant (`RULE_WINDOWS_PYTEST_TMP_001`)

> **Windows Basetemp Pre-allocation:**
>
> 1. In Windows environments, invoking pytest with `--basetemp=<path>` requires that the parent directory (e.g., `scratch/pytest_tmp`) exists on disk prior to process launch.
> 2. Test runners and automated verification scripts must assert or pre-create `scratch/pytest_tmp` before running scoped pytest batches, preventing `FileNotFoundError: [WinError 3]` during fixture allocation.

## Dynamic Repository Root Resolution Invariant (`RULE_PYTHON_DYNAMIC_REPO_ROOT_001`)

> **Upward Traversal over Static Parent Indices & Subpackage Sentinel Anchors:**
>
> 1. Evaluators, contract parsers, schema loaders, test modules, and estate inspection tools must not rely on fragile static parent indices (`Path(__file__).resolve().parents[k]`) to locate the repository root or sibling assets.
> 2. Relocated packages under `omega_engine_pfp/`, `omega_engine_atlas/coda_atlas/F004_papers/`, `omega_engine_operations/`, and nested worktrees reside at differing directory depths. Code discovering repository roots and configuration assets must use dynamic upward search (e.g., walking upward until encountering `.git` or `pyproject.toml`):
>    ```python
>    def find_repo_root(curr: Path = Path(__file__).resolve()) -> Path:
>        for parent in curr.parents:
>            if (parent / ".git").exists() or (parent / "pyproject.toml").is_file():
>                return parent
>        return curr.parents[4]  # calibrated fallback only
>    ```
> 3. **Linked Git Worktree Compatibility:** In linked git worktrees, `.git` is a *file* (`gitdir: <path>`), not a directory. Dynamic upward traversals looking for `.git` must assert `(marker.is_file() or marker.is_dir())` or `marker.exists()`, rather than assuming `.git` is an exclusively directory-shaped anchor.
> 4. **Subpackage & Sibling Code Sentinel Discovery:** When script stubs, forwarding adapters, or data models must locate sibling source directories (e.g., `code/python`, `code/docs_integrity.py`, `pfp/infrastructure`), static `_HERE.parents[k]` indexing is strictly forbidden. Moving files between subtrees changes nesting depth and causes silent import failures in clean subprocesses. Code must use dynamic sentinel marker discovery:
>    ```python
>    _PKG_ROOT = next((p for p in _HERE.parents if (p / "code" / "python").exists()), _HERE.parents[fallback_idx])
>    ```
> 5. **Candidate Asset Priority for Relocated Bounded Context Assets:** Whenever schemas, templates, catalogs, or prompt definitions are relocated into a sovereign bounded context (e.g., `pfp/infrastructure/yaml_data/prompts/`), shared builders, validators, and test fixtures must search a candidate list prioritizing the canonical bounded context location first before falling back to legacy paths.
> 6. Static relative indexing (`parents[2]`, `parents[3]`) without dynamic traversal is strictly forbidden in production adapters, evaluators, and schema loaders. Fallback parent indexing is permitted only as a guarded secondary default after dynamic traversal fails.

## Worktree Workspace Boundary & Sparse Checkout Hygiene Invariant (`RULE_WINDOWS_TEMP_WORKTREE_HYGIENE_001`)

> **Workspace Locality, Ephemeral Worktree Teardown & Sparse Disk Hygiene:**
>
> 1. **Workspace Boundary:** Worktrees created for autonomous editing MUST reside inside the workspace root under `.worktrees/<name>`. External worktrees (e.g. in `~/.codex/worktrees/`) trigger platform tool permission refusals.
> 2. **Monorepo Sparse-Checkout Requirement:** Full checkouts of this 75,000+ file repository consume tens of gigabytes and exhaust workstation disk space. Scoped worktrees must initialize sparse checkout (`git sparse-checkout init --cone` and `git sparse-checkout set <packages>`), excluding massive documentation/kernel directories (`omega_engine_atlas`, `omega_engine_education`, `omega_engine_research_papers`, `lean4`, `_ooutwire`).
> 3. **Ephemeral Worktree Teardown:** Temporary worktrees in temp paths must be explicitly removed (`git worktree remove --force <path>`) upon completion to prevent disk exhaustion.

## Filesystem Inspection & Build Directory Pruning Invariant (`RULE_PYTHON_FILESYSTEM_AUDIT_PRUNING_001`)

> **Build Tree Pruning & File Size Ceiling:**
>
> 1. **Mandatory Build Directory Exclusion:** Any static analysis tool, claim scanner, AST auditor, or recursive file discoverer MUST explicitly skip tracking and build directories:
>    `{".git", ".venv", ".worktrees", "target", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}`.
> 2. **File Size Ceiling:** File inspection routines scanning text content for pattern matching must enforce a maximum file size threshold (e.g. $\le 1\text{ MB}$) to prevent reading oversized binary blobs, matrix dumps, or lake caches.

## Clean Architecture Linter Module-Path Tokenization Invariant (`RULE_PYTHON_CLEAN_ARCH_LINTER_TOKENIZATION_001`)

> **Module Segment Inspection over Raw Line Substrings:**
>
> 1. **Tokenized Module Segment Inspection:** Static analysis tools checking for outward dependency violations in `domain/` must parse and inspect module path segments (e.g. `mod.split(".")`), rather than executing substring searches on raw lines (`f"_{forbidden}" in line`).
> 2. **False Positive Prevention on Port Interfaces:** Inspection routines must evaluate only the imported module path itself, ensuring that legitimate domain port interfaces, variable names, or type aliases (such as `ui_frontend_port` or `controller_token`) are not falsely flagged as layer violations.

## Windows Asyncio Teardown & Event Loop Policy Hygiene (`RULE_PYTHON_ASYNC_SHUTDOWN_HYGIENE_001`)

> **Clean Async Teardown & Anti-Global Policy Mutation:**
>
> 1. **Threadpool Drain on Shutdown:** Asynchronous execution engines managing background threadpools or worker tasks must explicitly await task completion and drain threadpools before closing or stopping the active event loop. Stopping an event loop while C-extensions or background worker threads are active causes uncatchable Windows access violations (`STATUS_ACCESS_VIOLATION` / `0xc0000005`) during process exit.
> 2. **No Module-Level Event Loop Policy Mutation:** Test files and application modules must never alter the global asyncio event loop policy at module scope (e.g. `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` at top level). Custom loop policies, if necessary, must be scoped strictly to individual pytest fixtures with explicit teardown restoration, preventing cross-test pollution and runner exit crashes.
