---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Skill Family Template

Template for defining and documenting skill families - groups of related skills that share structure, constraints, and workflow patterns.

## What is a Skill Family?

A skill family is a collection of skills that:

- Share similar structure and sections
- Work together in a workflow or domain
- Have overlapping constraints
- Can reference each other via Related Skills

## Identified Skill Families

| Family | Skills | Shared Pattern |
| -------- | -------- | ---------------- |
| **Sprint Workflow** | sprint-planning, sprint-review, sprint-execution, sprint-retrospective | Sequential workflow with BLOB tracking |
| **Code Quality** | lint, code-review, run-tests, security-scan | Pre-commit/CI validation |
| **Code Generation** | fastapi, react, sqlalchemy-orm, pydantic-models | Pattern libraries with examples |
| **Database** | postgresql, sqlalchemy-orm, alembic-migration | Schema and migration patterns |
| **Meta** | autoskill, auto-improve-autoskill, auto-symmetry-hunter, auto-review-skills | Self-reference, analysis workflows |

---

## Family Definition Template

### Metadata

### Governance Constraints

Required constraints:

- RULE_PRIME_0_0
- NO_SELF_CERTIFICATION
- EVIDENCE_PATH_REQUIRED
- NO_GREEN_THEATER
- APPROVAL_REQUIRED where mutation/credit/promotion occurs

Family-specific constraints:

- {list}

Forbidden claims:

- Skill output is DONE without evidence
- Skill review certifies itself
- Mock-only validation counts as external validation
- Diagnostics count as proof

### Evidence Levels

| Level | Meaning |
| ------ | --------- |
| F0 | Structure exists; not externally validated |
| F1 | Unit/integration tests pass |
| F2 | Cross-skill consistency checked |
| F3 | External oracle/council approval |
| F4 | Production/runtime evidence |

### Family Mutation Rules

Changes to this family require:

1. A proposed diff
2. A reason/migration note
3. Impact list of member skills
4. Symmetry-hunter propagation check
5. Review-skills approval
6. Blackrod approval for constraint changes

Forbidden:

- Removing required constraints without approval
- Weakening evidence requirements
- Adding a member skill without Related Skills updates
- Letting a skill self-certify compliance

---

## Anomalon Governance Skill Family

## Family Identifier

**ID**: anomalon-governance
**Purpose**: Enforce evidence, non-self-certification, promotion gates, and audit discipline across skills, agents, and sprint artifacts.

## Member Skills

| Skill | Role in Family | Position |
| --- | --- | --- |
| blackrod | Final gatekeeper / credit decision | Last |
| woland | Adversarial contradiction finder | Any |
| techne-code-soviet-inspector | Test-quality veto | Before credit |
| vp-engineering-sprint-audit | Sprint evidence auditor | Before Blackrod |
| svp-sadc-council-review | Architecture council authority | Council-only |
| auto-review-skills | Skill ecosystem auditor | Periodic / triggered |
| auto-review-agents | Agent ecosystem auditor | Periodic / triggered |
| auto-symmetry-hunter | Cross-skill drift detector | Before propagation |

Required constraints:

```text
RULE_PRIME_0_0
NO_SELF_CERTIFICATION
EVIDENCE_PATH_REQUIRED
NO_GREEN_THEATER
NO_WEAK_ASSERTIONS
NO_MOCK_ONLY_SAFETY
APPROVAL_REQUIRED

``` ext

---

```markdown

# {Family Name} Skill Family

## Family Identifier

**ID**: {family-id}
**Purpose**: {one-line description of family purpose}

## Member Skills

| Skill | Role in Family | Position |
|-------|----------------|----------|
| {skill-1} | {role description} | {first/middle/last/any} |
| {skill-2} | {role description} | {position} |

## Shared Constraints

All skills in this family MUST include these constraints:

See: [constraints.md](../_shared/constraints.md)

Required: {CONSTRAINT_1}, {CONSTRAINT_2}

## Shared Sections

Every skill in this family MUST have:

1. **{Section 1}** - {description}
2. **{Section 2}** - {description}
3. **Related Skills** - Cross-references to other family members

## Workflow Position (if applicable)

``` ext

{skill-1} -> {skill-2} -> {skill-3} -> {skill-4}
     |                                      |
     +<------------------------------------+

``` ext

## Handoff Patterns

| From | To | Trigger | Artifact |
|------|----|---------|----------|
| {skill-1} | {skill-2} | {when to handoff} | {what is passed} |

## Family-Specific Checklist

- [ ] All member skills have Required constraints
- [ ] All member skills have Related Skills section
- [ ] Handoff messages reference next skill in family
- [ ] Shared sections are structurally consistent

``` ext

---

## Sprint Workflow Family

### Family Identifier

**ID**: sprint-workflow
**Purpose**: Orchestrate sprint lifecycle from planning through retrospective

### Member Skills

| Skill | Role in Family | Position |
|-------|----------------|----------|
| sprint-planning | Plan sprint backlog | First |
| sprint-review | PO/Blackrod approval | Second |
| sprint-execution | Execute stories | Third |
| sprint-retrospective | Capture learnings | Last (loops to first) |

### Shared Constraints

Required: APPROVAL_REQUIRED, EVIDENCE_BASED

### Shared Sections

1. **Usage** - Command invocation patterns
2. **Prerequisites** - What must exist before activation
3. **Workflow Overview** - Step/event table
4. **Instructions** - work, handoff
5. **Next Workflow** - Navigation to next skill

### Workflow Position

``` ext
/sprint-planning -> /sprint-review -> /sprint-execution -> /sprint-retrospective
       |                                                            |
       +<-----------------------------------------------------------+

``` ext

---

## Code Quality Family

### Family Identifier

**ID**: code-quality
**Purpose**: Validate code quality before commit and in CI

### Member Skills

| Skill | Role in Family | Position |
|-------|----------------|----------|
| lint | Format and style checking | Any (parallel) |
| run-tests | Test execution and coverage | Any (parallel) |
| security-scan | Vulnerability detection | Any (parallel) |
| code-review | Human/AI review patterns | After others |

### Shared Constraints

Required: NO_HARDCODED_SECRETS, MAINTAIN_TESTS

### Shared Sections

1. **Quick Commands** - Copy-paste ready commands
2. **When to Activate** - Trigger phrases
3. **Best Practices** - Domain-specific guidance

---

## Meta Family

### Family Identifier

**ID**: meta
**Purpose**: Analyze and improve the skill/agent ecosystem

### Member Skills

| Skill | Role in Family | Position |
|-------|----------------|----------|
| autoskill | Learn from corrections | Primary (runs frequently) |
| auto-improve-autoskill | Improve autoskill | Meta-improver |
| auto-symmetry-hunter | Find cross-skill patterns | Analyzer |
| auto-review-skills | Audit skill relevance | Auditor |
| auto-review-agents | Audit agent relevance | Auditor |

### Shared Constraints

Required: SELF_REFERENCE, EVIDENCE_BASED, APPROVAL_REQUIRED

### Shared Sections

1. **When to Activate** - Explicit triggers
2. **Analysis Workflow** - Step-by-step process
3. **Self-Reference Check** - MANDATORY
4. **Output Format** - Report structure
5. **Related Skills** - Cross-references

---

## Creating a New Skill Family

1. Identify 3+ skills with shared patterns
2. Document the family using this template
3. Update each member skill's Related Skills section
4. Ensure shared constraints are present in all members
5. Add family to the "Identified Skill Families" table above

## Family Compliance Audit

Run this checklist when auditing family compliance:

```markdown

## {Family Name} Compliance Audit

### Member Skills
- [ ] {skill-1}: Has all shared sections
- [ ] {skill-2}: Has all shared sections
- [ ] {skill-n}: Has all shared sections

### Constraints
- [ ] All members have required constraints

### Cross-References
- [ ] All members have Related Skills section
- [ ] Cross-references are accurate and bidirectional

### Structural Consistency
- [ ] Section headers match across members
- [ ] Handoff patterns documented

``` ext
