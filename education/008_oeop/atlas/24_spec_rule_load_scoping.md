---
documentation_contract: symbol-game-documentation/v1
title: "Specification: rule load scoping and the always-loaded budget"
kind: architecture-reference
status: IMPLEMENTED
authority_effect: "None"
source_paths:
  - omega_engine_operads/skill_operad/yaml/rules_registry.yaml
  - omega_engine_operads/skill_operad/skill_compiler/rule_scope.py
  - omega_engine_operads/skill_operad/skill_compiler/rule_gate.py
  - omega_engine_operations/use_cases/cicd/pr_fast_gate.py
last_verified: 2026-10-07
---

# 24 Specification: rule load scoping and the always-loaded budget

**AuthorityEffect:** None.

First slice of the OEWAS refactor of host skills and rules (PR #582).

## Problem

A host rule file (`.agents/rules/**`, mirrored to `.claude/`, `.codex/`, `.grok/`)
without frontmatter loads into every IDE turn. On 2026-10-07 all 33 rules did:
213,568 bytes on every turn, whatever the turn touched.

## Design

The rule register is the one source of where a rule applies.

| Element | Where | Meaning |
|---|---|---|
| `load_paths` | each entry of `yaml/rules_registry.yaml` | Globs of the files the rule governs. Absent: the rule is always loaded. |
| `paths:` frontmatter | each rule file, all four hosts | Generated from `load_paths` by `rule_gate --write-scope`. Never hand-edited. Other frontmatter keys are kept as they are; the host ignores them. |
| `always_loaded_ceiling_bytes` | top of the register | Budget for the bodies of the always-loaded rules (17,000). |

The rule body is measured without its frontmatter, for R2 and for the budget
alike, because the host strips the frontmatter before loading a rule. The
12,000-byte file ceiling (R2) is unchanged by scoping.

The glob dialect is the host's: `**`, `*`, `?`, brace expansion `{a,b}` and
bracket expressions `[abc]`; an unreadable bracket matches nothing. `paths:`
may be a list or a comma-separated string.

## Checks (R9, `skill_compiler/rule_scope.py`)

| Finding | Fails when |
|---|---|
| `R9_FRONTMATTER` | A rule's frontmatter is not a mapping, or its `paths:` is not a list of strings. |
| `R9_SCOPE_DRIFT` | A rule's `paths:` differs from its register `load_paths`. |
| `R9_DEAD_GLOB` | A glob matches no tracked file (`git ls-files` of the root when the root is a repository's own top level; a pruned walk otherwise). |
| `R9_ALWAYS_LOADED_BUDGET` | The always-loaded bodies exceed the ceiling. |

Each finding has a test that triggers it
(`skill_compiler/tests/test_rule_gate.py`).

## Where the gate runs

- `py -3.12 -m omega_engine_operads.skill_operad.skill_compiler.rule_gate --repo-root .`
- Pre-commit hook `rule-gate`, on every commit (`always_run`): pre-commit never
  passes a deleted file, and a deleted rule or mirror is what R1 and R7 catch.
- The fast PR gate, check 5 `rule-gate`, when the branch changes or deletes a
  rule tree, `AGENTS.md`, `GEMINI.md`, a register external source
  (`.agents/registry/`), the register or the gate; `NOT_CHECKED` otherwise.
  The gate module is imported from the checkout that runs the fast gate, so
  the check means the same thing for any `--root`.
- Not a trigger: the `enforced_by` targets named in the register. A rename
  there surfaces at the next commit, which always runs the hook.

## Result

| | Rules | Bytes per turn |
|---|---|---|
| Before | 33 always loaded | 213,568 |
| After | 6 always loaded, 27 path-scoped | 15,861 |

The six always-loaded rules: model interaction, rules-as-code registry, GTLA
rubric, claim-disciplined compaction, review evidence, PR scope.

## Not covered

- Skill and agent descriptions still load every turn; they are the next budget.
- Rules are invariants in the register, not ops of the operad; see
  [12 Open issues](12_open_issues_nonclaims_and_roadmap.md) and [25 the setup review](25_review_agent_setup.md).
- A glob that matches a file is no evidence that the rule is relevant there.
