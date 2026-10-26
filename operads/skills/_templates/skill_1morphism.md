---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
title: "1-Morphism Skill Scaffolding Template"
file_name: "skill_1morphism.md"
file_location: ".agents/skills/_templates/"
status_operad: "Crystallized"
invariance_level: "Tier 10"
logic_system: "Category Theory / 1-Morphism Scaffolding"
substrate: "Markdown"
version: "v1.0.0"
---

# 1-Morphism Skill Scaffolding Template

Use this template when scaffolding a new **1-Morphism Skill** under `.agents/skills/<skill-name>/SKILL.md`.

---

```markdown
---
name: {skill-name}
description: {Atomic domain transformation description}. Triggers on "{trigger1}", "{trigger2}".
category: {domain-category}
family: {family-group}
authority: {None}
status: canonical-candidate
---

# {Skill Name} — 1-Morphism ($f: A \to B$)

You are **{skill-name}**, an atomic 1-morphism operational transformation in the domain of {domain}.

## Operational Semantics

Maps input state $A$ ({input state description}) to output state $B$ ({output state description}).

## Invocation Triggers

- `/{skill-name}`
- "{trigger phrase 1}"
- "{trigger phrase 2}"

## Invariants & Rules

1. **300-Line Limit:** Must remain under 300 lines / 20 KB. Large playbooks or tables belong in `references/`.
2. **Authority Ceiling:** `AuthorityEffect: None`. Self-certifications and unevidenced promotions are forbidden.
3. **Fail-Closed Execution:** Emits explicit error log on failure; no silent fallbacks.

## Reference Sub-Modules

- `references/playbook.md` — Detailed operational steps
- `references/invariants.md` — Domain invariants

AuthorityEffect: None.
```
