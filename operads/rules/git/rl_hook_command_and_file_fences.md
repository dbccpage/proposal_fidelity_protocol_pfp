---
paths:
  - "operads/hooks/**"
---

# Rule: Hook-Enforced Command and File Fences

**AuthorityEffect:** None.

**Guard:** the shell commands and file writes that a host hook refuses at run time, each refusal naming the invariant below.

**Compose:** [shared boundary vocabulary](../../skills/techne-documentation-manager/references/rules_index.md#shared-boundary-vocabulary). Read the relevant definition before acting; retain its conditions, exceptions, witnesses and refusal.

These invariants are ENFORCED by the hook scripts that `operads/hooks/hooks.json` registers. That file is generated from the `hooks` section of the rule register by `python -m operads.skill_operad.skill_compiler.hook_compiler --write`, and the rule gate fails when the two differ.

## Invariants

- `RULE_GIT_NO_FORCE_OR_MAIN_PUSH_001`: no force push, no `--all` or `--mirror` push, no bare `git push`, and no push whose destination is `main` or `master`. Changes reach `main` through a pull request.
- `RULE_GIT_EXPLICIT_STAGING_001`: stage named paths. `git add -A`, `--all`, `.`, `*` and `:/` are refused.
- `RULE_GIT_NO_COMMIT_ALL_001`: `git commit -a` and `--all` are refused, so a commit holds only what was staged by name.
- `RULE_PYTEST_TARGETED_RUNS_001`: pytest runs name one to three targets. A run with no target, or with the repository root as target, is refused.
- `RULE_SHELL_QUOTED_STASH_REF_001`: a stash reference such as `stash@{0}` is quoted, because PowerShell evaluates the braces.
- `RULE_FILE_STRICT_UTF8_001`: a file written through an edit tool is strict UTF-8; a leading BOM is stripped.

`RULE_PYTHON_LINTER_CLEANLINESS_001` is PARTIAL through the same post-write hook: Ruff runs on each Python file an edit tool writes, not on the whole tree.
