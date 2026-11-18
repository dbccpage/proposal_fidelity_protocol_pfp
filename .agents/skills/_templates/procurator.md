---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Procurator Skill Template

Use this template when creating or updating **procurator-*** skills (council executives). Shared structure keeps family compliance and auto-symmetry-hunter audits consistent.

## Template Structure

```markdown
---
name: procurator-{code}
description: Procurator of {Council} Council - {one-line scope}. Peer reviews {X}. Triggers on "{triggers}"
---

## Procurator of {Council} Council ({Short Title})

{One paragraph: what this council and procurator do.}

---

## Position in Hierarchy

{Diagram: Curious Council → Upper/Logos → this council. Agent code, reports to.}

**Agent Code**: `procurator_{code}`
**Reports To**: Procurator-UC or Procurator-LC

---

## Prime Directive

### {Bold one-line identity}

1. {Principle 1}
2. {Principle 2}
3. {Principle 3}
4. {Principle 4}

---

## When to Activate

Use when:

- {trigger 1}
- {trigger 2}

Do NOT use when:

- {anti-trigger 1}

---

## Core Responsibilities

### 1. {Responsibility area}

| Item | Description | Output |
|------|-------------|--------|
| ... | ... | ... |

### 2. {Optional second area}

---

## Peer Review Protocol (if applicable)

{Which council this one reviews, and which reviews this one. Format: "Reviews: X. Is Reviewed By: Y."}

---

## Inputs (Minimum)

- {Required artifact 1}
- {Required artifact 2}

---

## Outputs (MANDATORY)

- {Output template or format}

---

## Anti-Patterns (Flag and Correct)

- {Anti-pattern 1}
- {Anti-pattern 2}

---

## Related Skills

| Skill | Relationship |
| ------- | -------------- |
| procurator-uc / procurator-lc | Reports to |
| {sibling council} | Peer review |
| blackrod | Enforcement |

**Family:** upper-council-domains / logos-council-domains / procurator-cc (see [family_registry.md](../_shared/family_registry.md))

---

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: EVIDENCE_FIRST, UNCERTAINTY_EXPLICIT, NO_OWNERSHIP_FOG, RESPECT_REQUIRED (or family-specific from family_registry).

---

## Self-Check (End of Session)

- Did I demand evidence for key claims?
- Did I assign ownership and review dates?
- Did I avoid status theater?

```

## Maintenance

When adding a new procurator skill:

1. Copy this template.
2. Fill in council-specific content; keep section order.
3. Add the skill to the appropriate family in [family_registry.md](../_shared/family_registry.md).
4. Run `/auto-symmetry-hunter --families-only` to verify compliance.

**Source:** auto-symmetry-hunter report Sprint 138; family_registry procurator families.
