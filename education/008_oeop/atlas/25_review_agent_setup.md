---
documentation_contract: symbol-game-documentation/v1
title: "Review: agent setup, load profile and operad reforms"
kind: architecture-reference
status: PROPOSED
authority_effect: "None"
source_paths:
  - .agents/skills
  - .agents/rules
  - .agents/agents
  - omega_engine_workflows_agents_skills/skill_operad
  - omega_engine_woland/use_cases/governance_dispatch.py
last_verified: 2026-10-07
---

# 25 Review: agent setup, load profile and operad reforms

AuthorityEffect: None. This is a review proposal; nothing here was applied to tracked files.

- Repository: `/home/claude/the_symbol_game`, branch `claude/skills-rules-operads-kv94nk`,
  HEAD `85a4a14cc`, upstream `origin/claude/skills-rules-operads-kv94nk`, working tree clean
  (`git status --porcelain | wc -l` = 0). Branch diff against `origin/main`
  (merge-base `c8d495790`): 123 files, +1478 / -56.
- Date of review: 2026-10-07. Python used for local runs: 3.13.16 (`python3`); `py -3.12` is not
  present in this Linux container.

## 1. Summary

1. **The largest always-loaded item is not in this repository.** The session environment sets
   `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`, so the CLAUDE.md files of the sibling checkouts
   `/home/claude/H3V7N5QF` (344,290 B) and `/home/claude/19L57G1` (37,525 B) are loaded into every
   thread. Together that is 381,815 B, about 95k tokens at ~4 B/token (inferred ratio), against
   about 77 KB that the_symbol_game itself contributes. They also carry instructions that conflict
   with this repo's ("no network", "no questions", "Python 3.14", "nothing is pushed").
2. **39 of 40 subagent definitions declare `tools: []`.** Per the Claude Code sub-agent
   documentation an empty tool list "usually refuses to launch the subagent ... `Agent would be
   spawned with zero tools`". The repo's own generator writes that value
   (`omega_engine_workflows_agents_skills/infrastructure/autopoiesis/agent_learning.py:124`), and the
   same line asks for `model: inherit` while all 40 files say `model: opus`.
3. **Hooks are not wired for Claude Code.** `.claude/hooks/hooks.json` holds the git-guard and BOM
   hooks, but Claude Code reads project hooks only from `.claude/settings.json` (none is tracked);
   `hooks/hooks.json` is the plugin layout. The commands also call `py -3.12`, which Linux hosts lack.
   So "never push to main" and "no whole-suite pytest" are prose, not gates, in Claude sessions.
4. **The skill listing overflows its budget.** 251 skills carry 55,669 B of descriptions. In this
   session only the first 74 (alphabetical, through `governance-pedagogy`) were listed with
   descriptions; 176 (70%) were listed by name only, including `woland`, `research`,
   `deep-research` and every `techne-*`. 19 `ext-*` skills spend listing budget on the placeholder
   description "Operad operation <name>".
5. **The operad is a registry of whole skills, not a composition engine.** 251 operations (one per
   SKILL.md), 10 colours, 231 of 251 with `residual_effect: unknown`, 41 typed `State -> State`.
   No caller selects skills through it: `/woland` hard-codes four governance skills by digest, its
   council maps seats to synthetic `skill_<seat>` IDs that match no package, `/research` binds
   capabilities as free text, the operad router skill is prose for the model to execute, and the
   Woland anti-skill port reports itself disconnected.
6. **The rule-scoping work on this branch holds up.** `rule_gate` passes (exit 0) with 15,861 B
   always-loaded; but path-scoped rules now cost 18.7–93.7 KB on first touch of a directory, mostly
   from groups of rules that share identical globs, and 81 of 102 registered invariants are still
   `CANDIDATE`.

Top reforms, ranked by context bytes recovered per unit of effort, are in section 6; a PR sequence
is in section 7.

## 2. Method, and what of /deep-research could not run here

`/deep-research` is `/research` with a larger budget (`.claude/skills/deep-research/SKILL.md:15-37`).
`/research` drives the Rust controller `omega_woland::research_loop` through
`py -3.12 -m omega_engine_woland.entrypoints.cli research ...` (`.claude/skills/research/SKILL.md:36`).

What failed in this container:

| Step | Command | Result |
|---|---|---|
| Pack check | `timeout 60 python3 -m omega_engine_woland.entrypoints.cli research check-pack` | `ModuleNotFoundError: No module named 'networkx'` (import chain through `omega_engine_woland/domain/cochain/metrics_evaluator.py:18`) |
| Controller | `NativeResearchLoopHost._invoke` (`omega_engine_woland/infrastructure/researcher/native_research_host.py:55-68`) | needs the `RustSymbolGameHost` native binary; not built here (a `-j 1` workspace build was judged out of budget) |
| Interpreter | `py -3.12` | absent (Linux); `python3` is 3.13.16 |
| Paid dispatch | — | deep profile keeps `max_cost_microusd: 0`; no grant was given |

So no mission was admitted, no run folder exists, and no host disposition was computed. The review
was done by hand with the loop's structure: questions (2.1), evidence (sections 3–4, each with a
command or file:line), findings (section 4), critique (section 5), and reforms (sections 6–7).
Read-only critics were not run in parallel. Outside practice came from the Claude Code docs
(skills, memory, sub-agents, hooks) and three operad / typed-composition sources. Disposition in
the loop's vocabulary: `NeedsExternalOracle` for the controller-verified version of this review;
the findings below are host-checked facts or marked *inferred*.

### 2.1 Questions

- Q1. What loads into every Claude Code turn for this repo, and how large is each part?
- Q2. How are the four host trees mirrored, and what does the mirroring cost?
- Q3. What does the operad model today, and is it used to pick skills at run time?
- Q4. How do `/woland`, `omega_engine_woland` and `/research` choose skills and anti-skills?
- Q5. Which content is duplicated, stale, contradictory, over budget, or already enforced in code?
- Q6. What would a runtime composition API through the operad need?

## 3. Measured load profile

Byte counts from `wc -c` / short Python scripts over `.claude/`. Token figures use ~4 B/token
(*inferred*; real tokenisation varies).

### 3.1 Loaded at session start (every turn)

| Rank | Item | Bytes | ~Tokens | Source of the measurement |
|---:|---|---:|---:|---|
| 1 | `/home/claude/H3V7N5QF/CLAUDE.md` (sibling repo, via `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`) | 344,290 | ~86k | `wc -c`; present in this session's opening context |
| 2 | Skill listing, repo part, before budget: 251 names + descriptions | 62,450 (6,781 + 55,669) | ~15.6k | frontmatter parse of `.claude/skills/*/SKILL.md` |
| 2a | — of which actually listed with descriptions (74 skills) | ~15,191 + ~4,600 names | ~5k | listing in this session stops describing after `governance-pedagogy` (index 74 of 251) |
| 3 | `/home/claude/19L57G1/CLAUDE.md` (sibling Genesis repo) | 37,525 | ~9.4k | `wc -c`; present in opening context |
| 4 | `.claude/AGENTS.md` (= `GEMINI.md`, byte-identical) | 34,658 | ~8.7k | `wc -c`; injected on the first Read under the repo in this session ("tool.call hook additional context") — *inferred* to load in every session that reads a repo file |
| 5 | Unscoped rules (6 files, no `paths:`) | 15,861 | ~4k | parse of `.claude/rules/**`; confirmed by `rule_gate` output `always-loaded rule bytes: 15861` |
| 6 | Agent descriptions (40 files) | 6,134 (+ names) | ~1.6k | frontmatter parse of `.claude/agents/*.md` |
| 7 | Plugin and built-in skills listed beside the repo's (~90 entries) | not measured | — | listing in this session; environment-level, not repo |
| 8 | Auto memory | 0 | 0 | `/root/.claude/projects/-home-claude/` has no `memory/` |

Repo-owned always-on load (rows 2a + 4 + 5 + 6): about 77 KB (~19k tokens). Sibling CLAUDE.md files:
381,815 B (~95k tokens), i.e. ~83% of the instruction bytes measured here. System prompt and MCP tool
schemas are not measurable from inside a subagent.

### 3.2 Loaded on first touch of a path (path-scoped rules)

Computed with a matcher over each rule's `paths:` frontmatter
(`scratchpad/rulematch.py`, `PurePosixPath.full_match`).

| First file touched | Rules loaded | Bytes |
|---|---:|---:|
| `omega_engine_pfp/domain/tower/ast.py` | 12 | 93,720 |
| `omega_engine_atlas/coda_atlas/x/papers/a.lean` | 9 | 78,761 |
| `omega_engine/crates_rs/omega_woland/src/lib.rs` | 7 | 58,955 |
| `omega_engine_woland/use_cases/base_swarm/specializations.py` | 6 | 37,239 |
| `omega_engine_workflows_agents_skills/skill_operad/skill_compiler/rule_gate.py` | 5 | 35,997 |
| `omega_engine_operations/use_cases/packaging/sync_cross_host_skills.py` | 4 | 32,018 |
| `.claude/skills/woland/SKILL.md` | 2 (+ `.claude/AGENTS.md` 34,658) | 18,742 |

Groups of rules with identical globs always load together:

| Group | Files | Bytes together |
|---|---:|---:|
| `papers/*` (same 4 globs) | 4 | 37,116 |
| `math/*` (same 8 globs) | 3 | 30,027 |
| `genesis/*` (same 5 globs) | 3 | 21,450 |
| `rl_python_engineering_standards` + `rl_python_runtime_and_environment_standards` (`**/*.py`) | 2 | 15,403 |

### 3.3 Repository weight of the host trees (not context, but search noise)

| Tree | Bytes | Files |
|---|---:|---:|
| `.agents/` | 31,563,821 | 2,721 |
| `.claude/` | 16,375,900 | 776 |
| `.codex/` | 16,375,900 | 776 |
| `.grok/` | 16,506,273 | 780 |

`.claude/documentation/sessions` alone is 13,121,945 B (63 files; the largest three are 2.2 MB
session summaries) and is byte-identical in all four hosts (sha1 comparison), so ~52 MB of the repo
is four copies of session logs. Skill scripts are 323,089 B per host, also ×4.

## 4. Findings with evidence

### F1. Sibling CLAUDE.md files dominate the always-loaded context (Q1)

- `echo $CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` → `1`. The memory docs: this variable "loads
  `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`, and `CLAUDE.local.md` from the additional
  directory".
- `wc -c /home/claude/*/CLAUDE.md` → 37,525 (19L57G1), 344,290 (H3V7N5QF).
- H3V7N5QF's file is the plan of 25 derivations; the_symbol_game sessions do not need it.
  It instructs "No network, no files outside it, no questions" and "Nothing is pushed"; 19L57G1's
  pins "Python 3.14"; the_symbol_game's rules pin `py -3.12`. Contradictory ambient instructions
  in one context (*inferred* risk: the docs note that with contradictions "Claude may pick one
  arbitrarily").
- The docs offer `claudeMdExcludes` (glob over absolute paths, any settings layer).

### F2. 39 of 40 agents cannot be spawned as written (Q1, Q5)

- `grep -c '^tools: \[\]' .claude/agents/*.md | grep -c ':1$'` → 39; the exception is
  `researcher.md` (`Read, Grep, Glob, Bash`).
- Sub-agents doc: "If `tools` is empty or resolves to nothing: Claude Code usually refuses to launch
  the subagent ... `Agent would be spawned with zero tools`." Unknown fields such as
  `licensed_skills`, `licensed_colours`, `authority_effect`, `standalone` "are ignored".
- So the "licensed skills" mapping is not enforced by the harness, and no agent preloads a skill
  (`skills:` field absent in all 40).
- `grep -h '^model:' .claude/agents/*.md | sort | uniq -c` → `40 model: opus`, while
  `agent_learning.py:124` says new agents use `model: inherit`. The always-loaded
  `rl_model_interaction_discipline.md` asks to inherit the active model unless justified.
- Six near-duplicate pairs: `code-testing`/`techne-code-testing`, `database`/`techne-database`,
  `devops-git`, `frontend-designer`, `python-dev`, `rust-dev` (difflib ratio 0.41–0.55).

> **Editor's note (2026-10-07, thread session that requested the review).** F2's launch failure was
> not observed. In the session that commissioned this review, the harness listed the 39 agents with
> `tools: []` as having "All tools", so this Claude Code build appears to read an empty list as no
> restriction. The `model: opus` versus `inherit` mismatch, the six duplicate pairs and the ignored
> `licensed_*` fields stand. Reform 2 keeps its value as manifest hygiene, at lower urgency.

### F3. Hooks and safety directives are prose in Claude sessions (Q5)

- `ls -a .claude` shows no `settings.json`. `.claude/hooks/hooks.json` defines `PreToolUse`
  (`py -3.12 .agents/hooks/scripts/pre_tool_git_guard.py`) and `PostToolUse` (BOM linter).
- Hooks doc: project hooks are read from `.claude/settings.json`; "Only plugins use
  `hooks/hooks.json`".
- AGENTS.md's own Primary Law says a gate "does not exist ... until it is implemented in ...
  executable code"; the push and whole-suite directives (`.claude/AGENTS.md:86-110`) have code
  (`pre_tool_git_guard.py`) that is not attached.

### F4. Skill descriptions are cut to names for 70% of skills (Q1, Q4)

- Skills doc: the listing budget "scales at 1% of the model's context window"; on overflow "Claude
  Code drops descriptions starting with the skills you invoke least"; fixes are
  `skillListingBudgetFraction`, `skillOverrides` set to `"name-only"`, `disable-model-invocation`,
  and trimming text. Per-entry cap 1,536 characters.
- Measured: descriptions total 55,669 B, median 204 B, max 631 B (`panep-math-and-physics-prof`).
  In this session the listing carried descriptions for 74 repo skills (~15.2 KB) and names only for
  176.
- `grep -l '^description: *"\?Operad operation' .claude/skills/*/SKILL.md | wc -l` → 19 (`ext-*`
  imports with no usable description).
- Prefix-duplicate skills (quick_ratio, bytes): `adversarial-receipt-audit` vs
  `thanatos-adversarial-receipt-audit` 1.0; `oeops-evidence-receipt-harness` vs
  `techne-oeops-evidence-receipt-harness` 1.0; `rgb-public-math-post-gate` vs
  `theoria-rgb-public-math-post-gate` 0.98; `silent-failure-hunter` vs `techne-silent-failure-hunter`
  0.75; `human-promotion-firewall` vs `thanatos-human-promotion-firewall` 0.70;
  `lib-pedagogy-improvement` vs `panep-pedagogy-improvement` 0.60.
- Six `goo-*` micro-skills remain although AGENTS.md's "Deep Module Skill Consolidation Invariant"
  asks that they be merged.

### F5. The operad registers whole skills; nothing composes through it at run time (Q3, Q4, Q6)

- `json/operad_signature.json`: 251 operations, 10 colours, 10 identities. Residual effect:
  `unknown` 231, `exact` 6, `diagnostic` 6, `contractive` 4, `preserving` 2, other 2. Arity: 2 → 146,
  1 → 97. 77 distinct typings; the most common is `(State) -> State` (41 ops), which constrains no
  composition.
- Operation descriptions duplicate the SKILL.md descriptions (55,181 B).
  `json/capability_catalog.v1.json` is 340,171 B.
- `skill_operad/yaml/decomposition_inventory.yaml` does not exist
  (`find . -name 'decomposition_inventory*'` → nothing).
- `techne-operad-swarm-router/SKILL.md:24-35`: path search over the coloured graph "minimizing
  cumulative residual cost" is a protocol for the model to carry out; the package has no script.
  With 92% of residuals unknown there is no cost to minimise.
- `skill_compiler/resolve.py` is a regex keyword router deciding "existing contract vs new skill"
  (`yaml/routes.yaml`); it does not type-check compositions. A route id is still
  `six_host_parity` and matches `\.gemini` (`routes.yaml:26-34`) although the roster has four hosts.
- The domain layer does have typed composition (`domain/planar.py`: `ColoredOp`, `ArityMismatch`,
  `ColorMismatch`, `formal_compose`), so the checking primitive exists.

### F6. How the swarms pick skills today (Q4)

- `/woland`: `omega_engine_woland/use_cases/governance_dispatch.py:86-136` hard-codes four skills
  (`governance-symbol-game`, `governance-ddc`, `governance-coda`, `governance-clean-arch`) and binds
  them by SHA-256 of `.agents/skills/<id>/SKILL.md`. When the file is missing it returns
  `"0" * 64` (`governance_dispatch.py:57`), which the always-loaded
  `rl_review_evidence_reproducibility.md` forbids ("Zero Hardcoded or Simulated Fallback Hashes").
- Woland council: `omega_engine/crates_rs/omega_woland/src/council.rs:195-214` classifies seats by
  substring of the role name (`"filter"`, `"scanner"` → `TESTER` with colours `Audit, State`) and
  sets `required_operations` to `id.replacen("seat_", "skill_", 1)` — IDs such as `skill_koroviev`
  that match no skill package (skill names forbid underscores).
- `.claude/skills/woland/SKILL.md` (19,441 B, 217 lines) names no other skill to invoke; selection
  is persona prose.
- Anti-skills: `omega_engine_woland/infrastructure/estates/oewas_anti_skill.py:1-9` — "Without one
  the gate holds every subject ... the probe reports the port disconnected ... no native host action
  exposes the Rust detector yet." `.agents/anti_skills/admitted/registry.json` has 4 specs.
- `/research`: mission `capability_bindings` are free-text strings (`examples/mission.yaml:21-25`:
  `source_search: unbound`, `formal_checker: unbound`); `verifier_routes` are prose. No operad ID.

### F7. Mirroring is byte-exact but copies code and logs four times (Q2)

- `diff -rq .agents/skills .claude/skills | wc -l` → 0. `host_root_parity.py` → exit 0.
- `sync_cross_host_skills.py:64-82`: roster of four skill roots; `DEFAULT_SKILLS` names
  `lib-coda-librarian`, `lib-encyclopedia-librarian`, `lib-lean4-librarian`, none of which exist.
- 62 skill scripts (56 skills) live inside host trees, ×4; AGENTS.md says gates belong in
  `omega_engine_operations` or Rust crates.
- Session logs mirrored (section 3.3).
- `RULE_OPERAD_DIR_LAYOUT_001` (`rl_operad_architecture_and_swarm_nomenclature.md`) prescribes
  `.agents/operad/yaml/` and `json/`; `ls -d .agents/operad` → missing. 20 Python files still name
  `.agents/operad`; `skill_operad/dispatch.py:6` usage string too.

### F8. Rules: duplication, prose already enforced, missing IDs (Q5)

- `rule_gate` (`python3 -m ...skill_compiler.rule_gate --repo-root .`, Python 3.13.16, exit 0,
  scope: 33 rules × 4 hosts): `CANDIDATE=81, ENFORCED=13, PARTIAL=8`.
- Fully enforced files that could become short stubs naming their tests:
  `swarms/rl_researcher_loop_discipline.md` (7 ENFORCED, 3,876 B),
  `swarms/rl_woland_base_swarm_specialization.md` (4 ENFORCED, 4,399 B).
- Files with no registered invariant ID at all (prose only): `authority/rl_gtla_rules_rubric.md`,
  both `claims/*`, `git/*`, `rl_clean_architecture_and_subsystem_governance.md`,
  `rl_intelligence_digestion_and_archiving_discipline.md`, all three `math/*` except
  `rl_relational_contract_*`, all three `genesis/*`, `rl_paper_harmonization_*`,
  `rl_atlas_consolidation.md`.
- `rl_rust_engineering_standards.md` body is 11,971 B against the 12,000 B ceiling.
- The always-loaded GTLA rubric (7,132 B) spends 3,044 B on section 8, a list of ten archive links,
  and line 12 uses a verb on the forbidden list of `rl_pr_scope_and_branch_diff_audit.md`.
- `.claude/AGENTS.md` (241 lines, 34,658 B; the memory docs advise under 200 lines): the register
  table is 13,915 B and restates `rules_registry.yaml` (topic, summary, skills); the "Four-Host"
  section (4,095 B) and the "Deep Module Skill Consolidation" protocol (3,205 B) are procedures,
  which its own "Rule vs. Skill Demarcation" section says belong in skills. Clause 1 of the
  consolidation invariant reads "Create single-rule or single-check micro-skill directories", the
  opposite of its heading. Its "Rules are passive, ambient invariants automatically injected ... into
  conversation turns" (line ~218) no longer matches the path-scoped design on this branch.
- Clean Architecture rule asks for "zero-facade direct canonical imports"; `skill_operad/colored_operad.py`
  describes itself as a "Thin facade" and sits beside `coloured_operad.py` (583 lines); also
  `hott.py`/`hott_lite.py`, `dda_trace_logger.py`/`ddc_trace_logger.py`.

### F9. Skills within the size budget, but near it (Q5)

- `budget_gate` (`python3 -m ...skill_compiler.budget_gate`, exit 0): all pass.
- Largest: `governance-symbol-game` 19,984 B, `woland` 19,441 B, `panep-math-and-physics-prof`
  18,288 B. Median SKILL.md 2,708 B; 14 above 10 KB. Total SKILL.md text 1,041,418 B; 132 reference
  files; total skill tree 2,665,557 B per host.

### F10. CI coverage of the agent setup (Q5)

- `pr_fast_gate.py:259-267` runs syntax, ruff, line endings, `rule_gate`, and targeted tests.
  `.pre-commit-config.yaml` adds `rule-gate` and three symbol-game checks, all via `py -3.12`.
- Not in either: `budget_gate`, `host_root_parity`, agent frontmatter validity, skill-listing size.

## 5. Critique (what the evidence does and does not support)

- Supports: the byte counts above; that 39 agent files contradict the documented `tools` contract;
  that `.claude/hooks/hooks.json` is not a documented Claude Code project hook location; that
  selection paths in `/woland` and `/research` do not consult the operad.
- Does not support: that agents fail in every Claude Code version (the doc says "usually"; a
  launch attempt was not possible from this subagent); the exact token cost (ratio inferred); that
  the listing cut-off order is alphabetical in general (the doc says least-invoked first; this
  session showed an alphabetical prefix, possibly because no usage data exists in a fresh container).
- Narrowest defensible claim: in this container session, about 460 KB of instruction text is loaded
  before work starts, ~83% of it from two sibling repositories, and the repo's own skill/agent
  metadata is partly unusable by the harness (names-only listing, zero-tool agents, unwired hooks).
- Next test (runnable): in an interactive Claude Code session at the repo root run `/context` and
  `/doctor`, then `claude --debug` and spawn `python-dev` via the Agent tool; record the Skills row,
  the listing warning, and whether the spawn returns `Agent would be spawned with zero tools`.
- Negative evidence retained: `/research check-pack` failed on `networkx`; the Rust host binary
  was not built; no `decomposition_inventory.yaml` exists; no auto memory is present.

## 6. Ranked reforms

Impact is in bytes of always-loaded or first-touch context unless stated. "Home" = where the
change belongs.

| # | Reform | Expected impact | Risk | Home |
|---:|---|---|---|---|
| 1 | Stop loading sibling CLAUDE.md files in the_symbol_game threads: unset `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` for these threads, or add user-level `claudeMdExcludes: ["/home/claude/H3V7N5QF/**", "/home/claude/19L57G1/**"]` in the environment setup; mount siblings only for derivation threads. No edit to 19L57G1 or H3V7N5QF. | −381,815 B (~95k tokens) per turn; removes contradictory instructions | Low; threads that do need Genesis context must opt in | Environment / setup script (not a repo file) |
| 2 | Repair agent manifests: drop `tools: []` (inherit) or list tools; `model: inherit`; add `skills:` preload where a licence is meant to load a skill; merge the six base/`techne-` pairs. Fix the generator `agent_learning.py:124` and its tests, regenerate four hosts. | 40 agents usable; −~6 KB files; −~1 KB listing | Low; tests in `tests/autopoiesis`, `test_capability_catalog_v1.py`, `test_agent_skill_manifest_audit.py` assert `tools: []` and must change with it | Operations code (generator) + CI check |
| 3 | Add a tracked `.claude/settings.json`: register the existing `pre_tool_git_guard.py` and BOM linter through a small portable launcher (`python3` on Linux, `py -3.12` on Windows), and set `skillOverrides` for low-priority skills. Classify it canon-for-Claude in `host_root_parity.py`. | Turns the push / whole-suite / BOM directives into gates; lets ~4 KB of AGENTS.md prose shrink to pointers | Medium: a wrong matcher blocks commands; test the hook scripts with fixtures first | Pre-tool hook (code) |
| 4 | Fit the skill listing: rewrite the 19 `ext-*` descriptions (or `disable-model-invocation: true`), delete or alias the 6 prefix duplicates and merge 6 `goo-*`, cap descriptions at ~160 B with the trigger first, add `paths:` to domain skills (papers, Lean, Genesis), and add a CI check that the summed listing stays under the 1% budget. | From 74 to ~200+ skills with descriptions (*inferred*); −~10–20 KB listing | Low–medium: renames ripple into `operad_signature.json`, catalogs, registry YAMLs | Skills + CI (`pr_fast_gate` when `.agents/skills/**` changes) |
| 5 | Make `.claude/AGENTS.md` small and generated: move the 13.9 KB register table to a generated, non-loaded file (rule_gate already owns the register), move the Four-Host and consolidation procedures into `governance-host-parity` references, fix the inverted micro-skill clause and the "rules are injected every turn" sentence, keep only estate-wide negative constraints. Generate all five register documents from `rules_registry.yaml`. | 34,658 → ~8,000 B (−~26 KB) on first touch | Low; `register_documents` and the parity tests change together | Rule text + operations code (generator) |
| 6 | Build the runtime composition API through the operad (detail in 6.1): typed small ops, an `oewas compose` resolver in `omega_engine_operations`, anti-skill gate wired in, callers (`/woland`, `/research`) bind op IDs instead of prose or digests. | Selection leaves the model's black box; dozens of skills can become name-only or `disable-model-invocation` | High effort; medium risk of a parallel registry if the old one is not retired | Operations code + Rust port; skills become thin |
| 7 | Consolidate path-scoped rules: merge each identical-glob group (papers 37.1 KB, math 30.0 KB, genesis 21.5 KB, python 15.4 KB) into one leaf per group under the 12 KB ceiling, give every invariant an ID, and replace the two fully ENFORCED swarm rules with stubs naming their Rust tests. | First-touch load for `symbol_game/domain/tower` 93.7 → ~45 KB; papers 37 → ≤12 KB (*inferred* from merge targets) | Medium: wording loss; keep negative examples | Rules + rule_gate; heavy semantic checks nightly |
| 8 | Repository hygiene: make `documentation/sessions` canon-only or move it to `_intelligence/` (−~39 MB of mirror copies); move skill scripts to `omega_engine_operations` and leave thin wrappers; remove stale `.agents/operad` references and rule clause, `DEFAULT_SKILLS` ghosts, the `six_host_parity` / `.gemini` route; replace the `"0" * 64` fallback with a typed refusal plus a negative test. | Smaller greps, fewer stale instructions; one rule violation closed | Low | Operations code + CI (host parity) |
| 9 | Shrink the always-loaded GTLA rubric: drop section 8 links to a pointer (−3,044 B), remove the forbidden verb at line 12, keep the seven fences. | 15,861 → ~12,500 B always-loaded | Low | Rule |
| 10 | Extend `pr_fast_gate` (path-triggered): `budget_gate`, `host_root_parity`, an agent-frontmatter validator (`tools` non-empty, known `model`), and the listing budget check; keep full catalog regeneration and cross-host hash sweeps nightly. | Catches F2/F4 regressions at PR time | Low | CI |

### 6.1 What a runtime composition API through the operad would need

Inferred design, grounded in what exists (`domain/planar.py` already raises `ColorMismatch` and
`ArityMismatch`) and in outside practice: Spivak's operad of wiring diagrams
([arXiv:1305.0297](https://arxiv.org/pdf/1305.0297)), temporal wiring diagrams
([arXiv:1307.6894](https://arxiv.org/pdf/1307.6894)), network operads for systems-of-systems design
([arXiv:2009.12647](https://www.arxiv.org/pdf/2009.12647)), and Waites and Baez's typed plumbing
language for agents, which checks channel types at every connection before any model call
([n-Category Café, 2026-03](https://golem.ph.utexas.edu/category/2026/03/a_typed_language_for_agent_coordination.html)).

1. **Finer colours and small ops.** Ten colours with 41 `State -> State` ops cannot steer a search.
   Add subcolours (for example `Receipt.ruff`, `Receipt.lean_axioms`, `Audit.claim_hygiene`,
   `Code.py`, `Code.rs`, `Proof.lean`) and decompose each coarse skill into ops that each do one
   check or one transform with a declared residual effect. Target: many ops of ≤ ~1 KB text each,
   most backed by a callable (`module::function` or a Rust host action), with the SKILL.md becoming
   an index of ops. This is where `decomposition_inventory.yaml` would live (absent today).
2. **Ops and anti-ops in one signature.** Register anti-skills as ops with target colour
   `Audit` (or a `Refusal` colour) and a polarity, using `yaml/polarity_pairs.yaml`; a composite is
   admissible only if every attached anti-op returns clear. Wire the Woland anti-skill port to that
   detector instead of `HOLD`.
3. **Resolver as code.** `omega_engine_operations` CLI/API:
   `compose --inputs Paper,Contract --goal Receipt [--exclude-residual unknown] [--max-depth k]`
   returns a planar term (JSON) or a typed refusal (`NO_ADMISSIBLE_PATH`, `TYPE_MISMATCH`), built on
   `formal_compose`. `run` executes the callables of a term and writes receipts. Replace the prose
   router skill with a one-line pointer to this CLI.
4. **Callers bind IDs, not prose.** `/research` `capability_bindings` and `verifier_routes` name op
   IDs; Woland seats name real op IDs rather than `skill_<seat>`; `governance_dispatch` resolves its
   bundle by query (colour + family) and refuses when a package is missing.
5. **Residuals measured, not declared.** Fill `residual_effect` from eval/receipt evidence
   (`evidence_trace.json`, `eval_runner.py`) and leave `unknown` out of automatic composition.
6. **Generated catalogs, one source.** Generate `operad_signature.json`, capability slices and the
   listing descriptions from op definitions; stop hand-maintaining 340 KB of catalog.
7. **Model-facing surface.** Expose `compose` to models as one small skill (or MCP tool) so the
   listing carries one entry instead of hundreds; mark op-level skills `disable-model-invocation`.

Allowed axioms: this design adds no Lean obligations; any Lean statement about the operad may use
`Classical.choice`; only Genesis-pinned material stays on `{propext, Quot.sound}`.

## 7. Proposed sequence of reviewable PR slices

Each slice targets `main` directly, small enough for one review.

1. **Environment (no repo diff).** Unset or exclude sibling CLAUDE.md for the_symbol_game threads;
   record before/after `/context` figures. (Reform 1)
2. **Agents.** Generator and tests to `model: inherit`, no empty `tools`; regenerate 40 files ×4;
   merge six duplicate pairs; add the frontmatter validator to `pr_fast_gate`. (Reforms 2, 10 part)
3. **Hooks.** Portable launcher + tracked `.claude/settings.json` + fixture tests for
   `pre_tool_git_guard.py`; host-parity classification. (Reform 3)
4. **Listing fit.** `ext-*` descriptions, duplicates, `goo-*` merge, description cap, listing
   budget check. Regenerate operad and catalogs in the same PR. (Reform 4)
5. **AGENTS.md generated and slim.** Generator from `rules_registry.yaml`; register table moved;
   procedures moved to `governance-host-parity/references/`; GTLA rubric trimmed. (Reforms 5, 9)
6. **Rule consolidation.** One PR per identical-glob group (papers, math, genesis, python); stubs
   for ENFORCED swarm rules; IDs for unregistered invariants. (Reform 7)
7. **Hygiene.** Session logs out of the mirror; stale `.agents/operad` references and rule clause;
   `DEFAULT_SKILLS`; routes; `"0" * 64` → typed refusal with a negative test. (Reform 8)
8. **Operad v2 schema.** Subcolours, op/anti-op schema, `decomposition_inventory.yaml` for 5 pilot
   skills (for example `glossa-claim-hygiene-linter`, `techne-silent-failure-hunter`,
   `governance-test-isolation`, `adversarial-receipt-audit`, `meta-no-comments`). (Reform 6.1–6.2)
9. **Resolver.** `compose`/`run` in `omega_engine_operations` with tests including a red mutation
   (a mistyped wiring must refuse). (Reform 6.3)
10. **Callers.** `/research` mission binds op IDs; Woland seats and `governance_dispatch` query the
    resolver; anti-skill port connected. Retire the prose router skill. (Reform 6.4–6.7)

## 8. Changeset shape at review time

- Branch `claude/skills-rules-operads-kv94nk`, upstream `origin/claude/skills-rules-operads-kv94nk`,
  HEAD `85a4a14cc`, no uncommitted files. The review itself changed no tracked file; its matcher script
  (`rulematch.py`) stayed in the session scratchpad and is not committed.

## 9. Sources

- Claude Code docs: [Skills](https://code.claude.com/docs/en/skills),
  [Memory](https://code.claude.com/docs/en/memory),
  [Sub-agents](https://code.claude.com/docs/en/sub-agents),
  [Hooks](https://code.claude.com/docs/en/hooks).
- D. Spivak, The operad of wiring diagrams, [arXiv:1305.0297](https://arxiv.org/pdf/1305.0297).
- D. Rupel, D. Spivak, The operad of temporal wiring diagrams,
  [arXiv:1307.6894](https://arxiv.org/pdf/1307.6894).
- Network operads for designing and tasking systems of systems (DARPA CASCADE work), [arXiv:2009.12647](https://www.arxiv.org/pdf/2009.12647).
- W. Waites, J. Baez, A typed language for agent coordination,
  [n-Category Café](https://golem.ph.utexas.edu/category/2026/03/a_typed_language_for_agent_coordination.html).
