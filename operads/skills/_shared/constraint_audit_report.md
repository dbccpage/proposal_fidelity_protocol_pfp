# Constraint Section Audit Report

**Date**: 2026-02-13
**Scope**: 34 skill files in `engine/.core_skills/` ext
**Auditor**: auto-symmetry-hunter (read-only audit)
**Audit Status**: READ_ONLY_FINDING
**Certification Status**: NOT CERTIFIED (Requires Blackrod/auto-review-skills approval)
**Branch**: sprint-153-p3-sovereign-ci

## Canonical Format

The canonical verbose format for `## Constraints` sections is:

```markdown

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: CONSTRAINT1, CONSTRAINT2, CONSTRAINT3

Summary:
- Brief description of constraint 1
- Brief description of constraint 2
- Brief description of constraint 3

``` ext

## Classification Criteria

| Classification | Criteria |
|----------------|----------|
| **COMPLIANT** | Has See link + Required list + Summary bullets |
| **PARTIAL** | Has some canonical elements but missing others |
| **COMPACT** | Uses only `Required: X, Y, Z` without See link or Summary |
| **MISSING** | No `## Constraints` section at all |

## Summary

| Classification | Count | Percentage |
|----------------|-------|------------|
| COMPLIANT | 33 | 97.1% |
| PARTIAL | 1 | 2.9% |
| COMPACT | 0 | 0.0% |
| MISSING | 0 | 0.0% |
| **Total** | **34** | **100%** |

## Detailed Classification

### COMPLIANT (33 files)

All three canonical elements present: `See:` link, `Required:` list, `Summary:` bullets.

| # | Skill | File | Required Constraints |
|---|-------|------|---------------------|
| 1 | alembic-migration | `SKILL.md` | APPROVAL_REQUIRED, NO_DELETE |
| 2 | patterns | `SKILL.md` | MAINTAIN_TESTS, PRESERVE_STRUCTURE, NO_HARDCODED_SECRETS |
| 3 | testing | `SKILL.md` | MAINTAIN_TESTS, EVIDENCE_BASED |
| 4 | async-patterns | `SKILL.md` | APPROVAL_REQUIRED |
| 5 | blackrod | `SKILL.md` | APPROVAL_REQUIRED |
| 6 | cartographer | `skill.md` | SELF_REFERENCE, EVIDENCE_BASED, APPROVAL_REQUIRED, ROI_FOCUSED, PRESERVE_VARIATION, MIN_SPECIMENS, READ_ONLY_DEFAULT |
| 7 | ci-cd | `SKILL.md` | APPROVAL_REQUIRED |
| 8 | code-review | `SKILL.md` | EVIDENCE_BASED, PRESERVE_VARIATION |
| 9 | database-config | `skill.md` | PG18_ONLY |
| 10 | debug | `SKILL.md` | MAINTAIN_TESTS, SECURITY_FIRST |
| 11 | lib-education-engine | `skill.md` | APPROVAL_REQUIRED |
| 12 | fastapi | `SKILL.md` | SECURITY_FIRST, NO_HARDCODED_SECRETS |
| 13 | github | `SKILL.md` | NO_FORCE_PUSH, DESCRIPTIVE_COMMITS, NO_AMEND_PUSHED, BRANCH_ISOLATION |
| 14 | auto-improve-autoskill | `SKILL.md` | SELF_REFERENCE, EVIDENCE_BASED, APPROVAL_REQUIRED, ROI_FOCUSED |
| 15 | lint | `SKILL.md` | APPROVAL_REQUIRED |
| 16 | lib-pedagogy-improvement | `SKILL.md` | APPROVAL_REQUIRED, EVIDENCE_BASED |
| 17 | postgresql | `SKILL.md` | APPROVAL_REQUIRED |
| 18 | procurators | `SKILL.md` | EVIDENCE_BASED, APPROVAL_REQUIRED |
| 19 | pydantic-models | `SKILL.md` | APPROVAL_REQUIRED |
| 20 | react | `SKILL.md` | APPROVAL_REQUIRED |
| 21 | redesign-golden-agent | `SKILL.md` | APPROVAL_REQUIRED, NO_DELETE |
| 22 | auto-review-agents | `SKILL.md` | APPROVAL_REQUIRED, EVIDENCE_BASED |
| 23 | auto-review-skills | `SKILL.md` | APPROVAL_REQUIRED, EVIDENCE_BASED |
| 24 | run-tests | `SKILL.md` | MAINTAIN_TESTS |
| 25 | sprint-execution | `SKILL.md` | APPROVAL_REQUIRED, QUALITY_GATES |
| 26 | sprint-planning | `SKILL.md` | APPROVAL_REQUIRED, EVIDENCE_BASED |
| 27 | sprint-retrospective | `SKILL.md` | EVIDENCE_BASED, SELF_REFERENCE |
| 28 | sprint-review | `SKILL.md` | APPROVAL_REQUIRED, EVIDENCE_BASED, EVIDENCE_PATH_REQUIRED |
| 29 | student-learning | `SKILL.md` | EVIDENCE_BASED |
| 30 | auto-symmetry-hunter | `SKILL.md` | SELF_REFERENCE, EVIDENCE_BASED, MIN_SPECIMENS, PRESERVE_VARIATION, APPROVAL_REQUIRED |
| 31 | systematic-debugging | `SKILL.md` | ROOT_CAUSE_FIRST, MAINTAIN_TESTS, EVIDENCE_BASED |
| 32 | lib-verification-loop | `SKILL.md` | MAINTAIN_TESTS, EVIDENCE_BASED |
| 33 | write-unit-tests | `SKILL.md` | MAINTAIN_TESTS, NO_WEAK_ASSERTIONS, DETERMINISTIC_TESTS |

### PARTIAL (1 file)

| # | Skill | File | Has See | Has Required | Has Summary | Notes |
|---|-------|------|---------|-------------|-------------|-------|
| 1 | commands-reference | `skill.md` | Yes | **No** | Yes | Deliberately omits `Required:` line. Summary states: "Reference documentation only - no constraints required." This is an intentional design choice, not an oversight. |

### COMPACT (0 files)

No files use the compact format.

### MISSING (0 files)

All 34 skill files have a `## Constraints` section.

## Constraint Usage Statistics

Frequency of each constraint ID across all 34 skill files:

| Constraint ID | Count | Skills Using It |
|---------------|-------|-----------------|
| APPROVAL_REQUIRED | 20 | alembic-migration, async-patterns, blackrod, cartographer, ci-cd, lib-education-engine, auto-improve-autoskill, lint, lib-pedagogy-improvement, postgresql, procurators, pydantic-models, react, redesign-golden-agent, auto-review-agents, auto-review-skills, sprint-execution, sprint-planning, sprint-review, auto-symmetry-hunter |
| EVIDENCE_BASED | 13 | testing, cartographer, code-review, auto-improve-autoskill, lib-pedagogy-improvement, procurators, auto-review-agents, auto-review-skills, sprint-planning, sprint-retrospective, sprint-review, student-learning, auto-symmetry-hunter, systematic-debugging, lib-verification-loop |
| MAINTAIN_TESTS | 6 | patterns, testing, debug, run-tests, systematic-debugging, lib-verification-loop, write-unit-tests |
| SELF_REFERENCE | 4 | cartographer, auto-improve-autoskill, sprint-retrospective, auto-symmetry-hunter |
| NO_DELETE | 2 | alembic-migration, redesign-golden-agent |
| PRESERVE_VARIATION | 3 | cartographer, code-review, auto-symmetry-hunter |
| SECURITY_FIRST | 2 | debug, fastapi |
| NO_HARDCODED_SECRETS | 2 | patterns, fastapi |
| ROI_FOCUSED | 2 | cartographer, auto-improve-autoskill |
| MIN_SPECIMENS | 2 | cartographer, auto-symmetry-hunter |
| PRESERVE_STRUCTURE | 1 | patterns |
| NO_FORCE_PUSH | 1 | github |
| DESCRIPTIVE_COMMITS | 1 | github |
| NO_AMEND_PUSHED | 1 | github |
| BRANCH_ISOLATION | 1 | github |
| QUALITY_GATES | 1 | sprint-execution |
| PG18_ONLY | 1 | database-config |
| READ_ONLY_DEFAULT | 1 | cartographer |
| ROOT_CAUSE_FIRST | 1 | systematic-debugging |
| NO_WEAK_ASSERTIONS | 1 | write-unit-tests |
| DETERMINISTIC_TESTS | 1 | write-unit-tests |
| EVIDENCE_PATH_REQUIRED | 1 | sprint-review |

## Observations

### 1. Near-Total Compliance

33 of 34 files (97.1%) are fully COMPLIANT with the canonical verbose format. The single PARTIAL file (`commands-reference/skill.md`) deliberately omits the `Required:` line because it is reference-only documentation with no actionable constraints.

### 2. APPROVAL_REQUIRED Dominance

`APPROVAL_REQUIRED` is the most-used constraint (20 of 34 files, 58.8%), reflecting the project's approval-first culture. `EVIDENCE_BASED` follows at 13 files (38.2%).

### 3. Constraint ID Consistency

All constraint IDs referenced in skill files are defined in `_shared/constraints.md`. No orphan or misspelled constraint IDs were found.

### 4. Summary Quality

All Summary sections provide meaningful descriptions of the constraints, not just restating the constraint name. Most include the constraint ID in parentheses for traceability (e.g., "All proposals must cite specific evidence from skills (EVIDENCE_BASED)").

### 5. Previous Session vs. Current State

The previous analysis session (before context compaction) classified multiple files as PARTIAL due to missing Summary sections. Concurrent agent edits during Sprint 153 appear to have standardized these files, bringing compliance from an estimated ~53% to 97.1%.

## Recommendations

### P1 - No Action Required

The `commands-reference/skill.md` PARTIAL classification is by design. No remediation needed.

### P2 - Optional Standardization

Consider adding a `Required: NONE` line to `commands-reference/skill.md` to make the absence of constraints explicit in the canonical format rather than implicit via omission. This would bring full 100% compliance.

### P3 - Monitoring

- Re-run this audit after each major sprint to catch drift
- Integrate constraint format validation into `/auto-symmetry-hunter` family compliance checks

---

**Source**: Sprint 153 auto-symmetry-hunter constraint audit (2026-02-13)
