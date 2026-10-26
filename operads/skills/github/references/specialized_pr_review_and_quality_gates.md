# Specialized PR Review & Quality Gates

**AuthorityEffect:** None

Operational specifications for specialized PR review and quality gates in the repository:

## 1. SHA-256 Content Hash Honesty Gate

- Refuse any PR containing 64-zero placeholder hashes in council meeting frontmatters, contracts, or planning manifests.
- Require cryptographically verified SHA-256 body digests for all immutable artifacts.

## 2. PR Relocation Bijection Guard

- For PRs performing package migrations or directory reorganizations:
  - Compare base-to-head inventories and assert exact bijection between source files and target locations.
  - Reject duplicate live authority roots and broken relative import paths.

## 3. Reserved Word & Valid Identifier Guard

- Inspect all added or renamed module files:
  - Refuse module stems failing `str.isidentifier()` or matching Python keywords (`keyword.iskeyword()`).
  - Prohibit dots, hyphens, or spaces in module filenames.

## 4. Tree-Diff Merge Isolation & Worktree Safety

- Perform three-way tree comparisons (`ONLY_PR` / `ONLY_MAIN` / `M_diff`) before merges.
- Isolate risky refactoring in temporary git worktrees to keep the primary working directory clean.

## 5. Local HTTP Containment & PR Trigger Coverage

- Compare Node and Python local-only forwarding rules by header presence, including empty values and mixed-case names. Use `tests/server_admission.test.mjs` to require refusals with zero provider dispatch on both handlers and successful direct-local controls.
- When changing the OEWAS router, wire DTOs, or API app, require each exact source path in the PR filter and the unconditional containment step; verify `omega_engine_pfp/tests/test_symbol_game_pr_workflow.py`, including path-removal controls.
- A failed CI job with no recorded steps supplies no test result. Report it separately from local replay; inaccessible failure annotations remain unknown, not a code diagnosis or passing check.
