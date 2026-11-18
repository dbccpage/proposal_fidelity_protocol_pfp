# Autoskill Historical Learnings & Family Propagation Rules

```text
File: path/to/target/SKILL.md
Section: [section name]
Confidence: HIGH | MEDIUM
Propagation: FAMILY_PROPAGATION
Source skill: [original skill]
Family: [family name]
Pattern: [matched propagation pattern]
Coordination: [coordinated_update | propagation_suggestion]

Signal: "[original correction]"


## Table of Contents
- [Self-Reference Check](#self-reference-check)
- [Proposing Changes](#proposing-changes)
- [Review Flow](#review-flow)
- [autoskill summary](#autoskill-summary)
- [Applying Changes](#applying-changes)
- [Output Format](#output-format)
- [Autoskill Report](#autoskill-report)
- [Signals Detected](#signals-detected)
- [Self-Reference Findings](#self-reference-findings)
- [Proposed Changes](#proposed-changes)
- [Summary](#summary)
- [Related Skills](#related-skills)
- [Additional Sections & Details (10 more...)](#additional-sections)

Proposed text:
> [adapted content for target skill]

Rationale: Family propagation from [source] - [pattern description]

```text

**Action:**

- If coordinated update detected: recognize as architectural decision, not independent corrections
- If single skill updated: still offer family member suggestions, but lower confidence
- If 3+ members updated coordinately: flag as "architectural pattern" worth documenting

If a correction applies to a skill family, propose updates to ALL skills in that family.

## Self-Reference Check

**MANDATORY at end of every analysis:**

Before proposing changes, check if the session corrections apply to autoskill itself:

1. Do any detected patterns affect how autoskill detects signals? [y/n]
2. Did the user correct autoskill's behavior directly? [y/n]
3. Would the proposed updates improve autoskill's own effectiveness? [y/n]

If any answer is "yes" → include self-modification proposal in the output.

**Common autoskill self-improvements:**

- New signal types to detect (e.g., tool rejections, error patterns)
- Changes to confidence thresholds
- Updates to skill family mappings
- Improvements to output format based on user feedback

Flag for `/auto-improve-autoskill` (pending) when:

- Multiple self-modifications detected in one session
- Self-improvement pattern repeats across sprints

## Proposing Changes

For each proposed edit, provide:

```text
File: path/to/SKILL.md
Section: [existing section or "new section: X"]
Confidence: HIGH | MEDIUM

Signal: "[exact user quote or paraphrase]"

Current text (if modifying):
> existing content

Proposed text:
> updated content

Rationale: [one sentence]

```text

Group proposals by file. Present HIGH confidence changes first.

### Git-Tracking Check (MANDATORY)

Before proposing changes, verify if the target skill file is git-tracked:

```bash
git ls-files -- ".claude/skills/<skill>/SKILL.md"

```text

If the file is NOT tracked, add to the proposal:

```text
EPHEMERAL: This file is gitignored. Change will be applied locally
but will not persist across machine changes or .claude/skills/ resets.
Consider force-adding with `git add -f` if this is a durable preference.

```text

This prevents the false impression that all autoskill changes are persisted.
Never hardcode a tracked/untracked verdict here — it has flipped twice
(`a41314381` removed 98 skill files under A00 containment; `9bff92553` restored
92). The `git ls-files` result above is the only authority.

## Review Flow

Always present changes for review before applying. Format:

```text

## autoskill summary

Detected [N] durable preferences from this session.

### HIGH confidence (recommended to apply)
- [change 1]
- [change 2]

### MEDIUM confidence (review carefully)
- [change 3]

Apply high confidence changes? [y/n/selective]

```text

Wait for explicit approval before editing any file.

**Operator “apply all” license (2026-07-24):** phrases such as *apply all their recommended changes*, *apply all*, or *apply HIGH and MEDIUM* are **explicit approval** for the listed HIGH+MEDIUM proposals in that turn (including self-mod targets named in the order). Still skip LOW/noise and never widen to unrelated dirty WIP.

## Applying Changes

When approved:

1. Verify target file git-tracking status (`git ls-files -- <path>`), warn if untracked
2. Edit the target file with minimal, focused changes
3b. **PR create failure / dual-block:** if `gh pr create` / `POST .../pulls` returns HTTP 500, load `/github` (full dual-block procedure). Do not invent open PRs. Status page green ≠ create works.

3. **Canonical write, deterministic mirror:** edit only `.agents/skills/<name>`.
   Run `operations/use_cases/sync_cross_host_skills.py --skills
   <name>`, then its `--check` mode. Never ask a model to reproduce mirror bytes.
4. **Meta isolation:** land only the explicitly reviewed packages and receipts.
   Never sweep concurrent paper, code, or research work into the change.
5. Commit via `/github` on a worktree branch. Message:
   `chore(autoskill): [brief description]`.
6. Report what was changed.

## Output Format

```markdown

# Autoskill Report

**Date**: [date]
**Session**: [brief description of what was worked on]
**Skills Analyzed**: [list of skills active in session]

## Signals Detected

### Corrections
- [signal 1 with quote]
- [signal 2 with quote]

### Tool Rejections
- [tool and reason]

### Error Patterns
- [error and fix captured]

## Self-Reference Findings

- Applied to autoskill itself: [y/n]
- Self-improvements proposed: [count]
- Flagged for /auto-improve-autoskill: [y/n]

## Proposed Changes

### HIGH Confidence
[proposals with file, section, rationale]

### MEDIUM Confidence
[proposals requiring review]

## Summary

- Total signals: [N]
- Durable preferences: [N]
- Skills to update: [list]

```text

## Related Skills

| Skill | Relationship |
|-------|--------------|
| auto-improve-autoskill | Meta-optimizer for autoskill effectiveness |
| auto-symmetry-hunter | Cross-skill pattern detection and propagation |
| rules-hunter | Sibling hunter — promotes latent rules from autoskill corrections |
| auto-review-skills | Skill cleanup and consolidation |
| sprint-retrospective | Runs autoskill at end of sprint |

**Family:** meta (see the Skill Families table above — the only live registry)

## Constraints

See: [constraints.md](../../_shared/constraints.md)

Required: APPROVAL_REQUIRED, NO_DELETE, COMPRESSIVE_CHANGES, PRESERVE_STRUCTURE, SELF_REFERENCE

Summary:

- Never delete legitimate rules (NO_DELETE), but prune "soft" rules.
- **Invert Directive:** Prefer COMPRESSIVE changes (Negative Lines of Code) over additive ones.
- **Kolmogorov Constraint:** Any new instruction must remove two old ones or automate them via code.
- **Minimize Token Mass:** Reward density. If a rule can be a decorator, it must be code, not text.
- One concept per change (atomic).
- Preserve existing file structure (PRESERVE_STRUCTURE).
- Always check if findings apply to autoskill itself (SELF_REFERENCE).

## Compressive Change Protocol (The Sovereign Inversion)

### 1. The Fundamental Shift: From Text to Syntax

> **PRIME DIRECTIVE: COMPRESSIVE EVOLUTION**
> Do not add text instructions if a code constraint can be synthesized.
>
> - **Forbidden:** Adding "Always validate input X" to `SKILL.md`.
> - **Required:** Synthesizing a Python decorator `@validate_x` and adding `Constraints: ["Apply @validate_x"]` to the skill file.
> - **Metric:** Your proposal must result in a net reduction of Token Mass (Negative Lines of Code) or an increase in Deterministic Density.

### 2. The Operational Rule: "One-In, Two-Out"

**Enforce Rule 013 (Complexity is a Sin):**

- **Text Rules:** For every 1 new line of text instructions added, you must specific ~2 lines of obsolete instructions to delete or condense.
- **Code Rules:** Adding a reference to a hard-coded check (e.g., `Review with: run_lint.py`) is always preferred over listing the linting rules in the text.

### 3. The Metric: Compression Ratio

- **NLOC (Negative Lines of Code):** Your goal is to maximize NLOC.
- **Report Requirement:** "Proposal reduces `SKILL.md` size by X% while increasing coverage."

### 4. Crystallization Trigger (Rule of 5)

If you observe the same correction **5 times**, triggered the **Crystallizer** (via `gym` or `notify_user`) to move the rule from `SKILL.md` (Tier 3 context) to `.intelligence/.knowledge/.hardened_lambdas/` (Tier 0 code).

Refer to `sentinel` for the "50 Remarks of Relevance" compression standard.

## Abstraction Velocity Detection

Scan session for repeated manual work that should be automated:

**Scaffolding candidates:**

- Creating same file structure 2+ times
- Writing boilerplate code patterns repeatedly
- Manual steps that follow a template

**Template candidates:**

- Similar code written for different entities (CRUD endpoints, models)
- Repeated configuration patterns
- Formulaic documentation sections

**Workflow candidates:**

- Multi-step processes performed manually each time
- Checklists executed without skill guidance
- Agent delegation patterns not captured in skills

When detected, propose:

```text
Abstraction opportunity:
Pattern: [describe the repeated work]
Frequency: [how often in session/sprint]
Proposal: [new skill | new template | enhance existing skill]
ROI estimate: [time saved per occurrence × expected frequency]

```text

**Domain orchestrator template:**
When a new domain (e.g., FSP, consciousness) requires coordinated multi-agent work:

1. Create agent in `engine/agents/<domain>.md` with: routing table, dead-end blocklist,
   pipeline state, priority stack, escalation rules, key file inventory
2. Create matching skill in `.claude/skills/<domain>/SKILL.md` with: triggers,
   routing table (subset), quick reference, dead-end blocklist (subset)
3. Update all relevant domain-expert agents (e.g., math-prof, physics-prof) with
   matching domain sections simultaneously (cross-domain replication)

**Agent-skill coherence check** (IAK-011):
When a new agent is created in `engine/agents/`, check:

1. Does a matching skill exist in `.claude/skills/`? If not → propose creation
2. Does the agent reference skills that don't exist? If so → flag gap
3. Do referenced domain experts have matching domain sections? If not → flag enrichment

Flag for `/auto-improve-autoskill` (pending) analysis if:

- Same pattern appears 3+ times across sprints
- Manual rate exceeds 80% for a workflow category
- Error repeats that should have been prevented by skill

## Sprint Integration

At the end of each sprint retrospective, automatically suggest:

- Review skills used during sprint
- Propose updates based on sprint-level corrections

To analyze sprint-wide learnings, run: `/autoskill` during or after retrospective.

**Sprint Retrospective Checklist:**

1. Were any skills invoked repeatedly with corrections?
2. Did any agent receive consistent feedback patterns?
3. Are there conventions established this sprint worth capturing?

## Core Doctrine Wiring (panepistimion-math-prof + GT* skills)

Governed by `.claude/skills/_shared/meta_skill_governance.md` — **which does not exist on
disk** (verified 2026-07-22), so the auto-commit licence below rests on a missing
governor. The former A00 backstop (`CLAUDE.md:11-14`) is **gone** — PR #1594 retired
A00 CLAUDE.md narrowing on 2026-07-30 and CLAUDE.md now routes git through `/github`.
On **sprint
completion** and on **every autoskill fire**, run two channels for the Core
math doctrine:

1. **Channel 1 -- index refresh (always, free):** regenerate the Wizard manifest
   from source-of-truth (papers + canonical spine):

       python .claude/skills/panepistimion-math-prof/regen_spine_index.py

   Regeneration, not accretion -> zero overfitting risk. Commit the manifest if
   it changed.

2. **Channel 2 -- doctrine edits (auto-commit, no approval gate):** when a
   session signal warrants editing the Wizard's logic (including its Authority
   Firewall section), apply it directly with `requires_approval=false` ext
   (compressive-change-law still applies). These targets are NOT in the
   self-modification guard, so no human approval is required (operator
   decision, 2026-05-31).

**Stable-doctrine targets:** `panepistimion-math-prof`, `operad-lattice`. (The seven
GT* layer skills were retired 2026-06-10 — operator ruling — and their
forbidden-claims content consolidated into the Wizard's Authority Firewall.)

**Backstop (load-bearing):** there is no preventive gate on Channel 2 by operator
choice, so `auto-improve-autoskill`'s periodic audit MUST review the Wizard's doctrine
diffs and `git revert` bad drift. The path-scope HARD BLOCK (`.claude/skills/` ext
only) and the self-modification guard on `autoskill`/`auto-improve-autoskill` ext
themselves remain in force.

## Integration with auto-symmetry-hunter

Before finalizing proposals, check for cross-skill patterns:

### Cross-Skill Check

When proposing a skill update:

1. Does this correction apply to similar skills?
2. If the same pattern appears in 3+ skills → flag for abstraction

**When to escalate to /auto-symmetry-hunter:**

- Correction applies to a pattern found in multiple skills
- New skill proposal might duplicate existing functionality
- Structural change (new section type) could apply broadly
- **Partial family update:** a layout/authority/evidence rule landed on fewer than the paper-pipeline stages (improver, adversary, proof-signoff, release, build, rip) without a shared-contract home — escalate instead of copying paragraphs

**How to escalate:**

```text
Flag for /auto-symmetry-hunter:
- Pattern: [describe the repeated structure]
- Skills affected: [list of skills]
- Proposed abstraction: [template | library | injection]

```text

This enables the meta-recursive loop:

- autoskill learns from corrections
- /auto-symmetry-hunter (pending) finds patterns across skills
- /auto-improve-autoskill improves autoskill based on both

## Session metrics

The model writes qualitative rows using schema `core.autoskill.run.v1`. Derive
every count with:

```text
<configured-python> .agents/operad/skill_compiler/metrics.py --file <run.json>
```

The tool deliberately emits no capture rate without an independently defined
eligible-signal denominator. Historical percentages are not current policy.

## Example Session

```text
User: /autoskill

Core: Analyzing this session for durable preferences...

# Autoskill Report

**Date**: 2026-01-15
**Session**: Sprint 046 infrastructure implementation
**Skills Analyzed**: commit, postgresql, ci-cd

## Signals Detected

### Corrections
- "We always use PostgreSQL 18, not 17" (user corrected version reference)
- "Branch names should be sprint-NNN format" (repeated 2x)

### Tool Rejections
- None

### Error Patterns
- BLOB submission failed: UUID format was 'sprint-046' instead of valid UUID

## Self-Reference Findings

- Applied to autoskill itself: n
- Self-improvements proposed: 0
- Flagged for /auto-improve-autoskill: n

## Proposed Changes

### HIGH Confidence

File: .claude/skills/postgresql/SKILL.md
Section: Project Conventions
Confidence: HIGH
Signal: "We always use PostgreSQL 18, not 17"
Proposed: Add explicit "PostgreSQL 18 ONLY" note
Rationale: User correction indicates version is critical

### MEDIUM Confidence

File: .claude/skills/commit/SKILL.md
Section: Branch Naming
Confidence: MEDIUM
Signal: "Branch names should be sprint-NNN format"
Proposed: Add branch naming convention
Rationale: Repeated twice but may be project-specific

## Summary

- Total signals: 3
- Durable preferences: 2
- Skills to update: postgresql, commit

Apply high confidence changes? [y/n/selective]

```text

## Brother-Skill Escalation

Escalate to `/auto-improve-autoskill` when:

- autoskill misses repeated corrections
- autoskill over-captures generic advice
- autoskill proposes bloated additive rules
- autoskill fails self-reference check
- autoskill metrics are missing or low quality
- capture rate declines across sessions
- **same-basis capture rate falls below the 18.5% baseline** — autoskill is not being run
  often enough to learn; escalate rather than tune the signal filter

Escalate to `/auto-symmetry-hunter` when:

- a rule applies to multiple skills
- related skills differ on evidence, tests, authority, or build policy
- one skill has a stronger version of a rule than its siblings
- a new section type appears in 2+ skills
- duplicate instructions appear across 3+ skills
- authority roles conflict across agents/skills

Rule:

```text
autoskill learns the correction.
auto-symmetry-hunter finds the invariant.
auto-improve-autoskill improves the learner.

```text

## Four-host synchronization rule

The model edits only `.agents/skills/`. The deterministic synchronizer mirrors
the named package into `.claude`, `.codex`, and `.grok`, then verifies content.

**Host ↔ vendor map (do not re-derive):**

| Tree | Vendor |
|---|---|
| `.agents/skills` | **Antigravity** — and the canonical source |
| `.claude/skills` | Claude Code |
| `.codex/skills` | Codex |
| `.grok/skills` | Grok |

An operator naming "Grok, Claude, Antigravity, Codex" is naming these four — **no fifth tree exists and `.antigravity/` must not be created**. Authority: `scripts/sync_cross_host_skills.py` header. (2026-07-28: absence of this map cost a resolution round-trip.)

**Partial mirrors are the failure mode.** Never repair them with parallel manual
edits. A parity result is packaging evidence, not semantic admission evidence.

**Frontmatter `name:` must equal its directory name.** A `name:` that disagrees registers a command nobody can find at the path it lives in. Check with a loop, not by eye. (2026-07-28: four skills shipped `name: auto-auto-<x>` under directories `auto-<x>` — 9 occurrences across 4 files.)
