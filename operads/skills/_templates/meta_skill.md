---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Meta-Skill Template

Use this template when creating skills that analyze or improve other skills,
agents, or system components. Meta-skills have unique requirements around
self-reference and integration.

## Template Structure

```markdown
---
name: {skill-name}
description: {one-line description}. Use when {trigger conditions}
---

## {Skill Name} - {Subtitle}

{One paragraph explaining what this meta-skill does and why it exists.}

## Core Principle

> **{Key insight in bold}**
> {Supporting statement}

## When to Activate

- {Explicit trigger phrase 1}
- {Explicit trigger phrase 2}
- {Context condition}

**Do NOT activate**:

- {Anti-trigger 1}
- {Anti-trigger 2}

## Analysis Workflow

### Step 1: {Verb} {Object}

{Description of what to gather/scan/collect}

### Step 2: {Verb} {Object}

{Description of extraction or processing}

### Step 3: {Verb} {Object}

{Description of analysis or computation}

### Step 4: Self-Reference Check

**MANDATORY at end of every analysis:**

```markdown

## Self-Reference Check

1. Do any proposed changes apply to my own prompt? [y/n]
2. Do any patterns I found exist in my own structure? [y/n]
3. Would my recommendations improve my own effectiveness? [y/n]

If any answer is "yes" → include self-modification proposal

```

## Output Format

```markdown

# {Skill Name} Report

**Date**: [date]
**Scope**: [what was analyzed]

## Findings

### {Category 1}
- {finding}

### {Category 2}
- {finding}

## Self-Reference Findings

- Compliance with own patterns: [%]
- Self-improvements proposed: [count]

## Recommended Actions

1. [action]
2. [action]

```

## Integration Points

### With {Related Skill 1}

{How this skill coordinates with or calls related skill}

### With {Related Skill 2}

{How this skill coordinates with or calls related skill}

## Constraints

See: [CONSTRAINTS.md](../_shared/constraints.md)

Required constraints for all meta-skills:

- SELF_REFERENCE: Always check if findings apply to self
- EVIDENCE_BASED: Proposals require 3+ specimens
- PRESERVE_VARIATION: Not all differences are accidents
- APPROVAL_REQUIRED: Wait for explicit approval before editing

## Example Session

```text
User: /{skill-name}

Omega: [Brief description of what will be analyzed]

# {Skill Name} Report

[Actual example output from a real session]

```

## Meta-Skill Checklist

Before publishing a new meta-skill, verify:

- [ ] Has self-reference check in workflow
- [ ] Output format includes "Self-Reference Findings"
- [ ] Integration points documented
- [ ] Constraints section present
- [ ] Example session from real usage
- [ ] Can improve itself (meta-recursive)

## Existing Meta-Skills

| Skill | Purpose | Self-Reference |
|-------|---------|----------------|
| autoskill | Learn from session corrections | Implicit (learns about learning) |
| auto-improve-autoskill | Improve autoskill performance | Yes (analyzes own effectiveness) |
| auto-symmetry-hunter | Find patterns across skills | Yes (checks own patterns) |

## Creating a New Meta-Skill

1. Copy this template
2. Fill in all `{placeholders}`
3. Implement self-reference check
4. Run the skill on itself as first test
5. Document the self-test as the example session
```
