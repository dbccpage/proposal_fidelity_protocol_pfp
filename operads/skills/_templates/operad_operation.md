---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
title: "Operad Operation Skill Template"
file_name: "operad_operation.md"
file_location: ".agents/skills/_templates/"
status_operad: "Crystallized"
invariance_level: "Tier 10"
logic_system: "Coloured Operads / OEWAS Operational Semantics"
substrate: "Markdown"
version: "v2.0.0"
---

# Operad Operation Skill Template

Use this template when scaffolding a new **Operad Skill Operation** under `.agents/skills/<skill-name>/SKILL.md`.

---

```markdown
---
name: {skill-name}
description: "{Atomic domain transformation description}. Triggers on '{trigger1}', '{trigger2}'."
operad_source_colours: ["{Colour1}", "{Colour2}"]
operad_target_colour: "{TargetColour}"
operad_arity: 2
operad_residual: "unknown"
families: [{family-name}]
---

# {Skill Name}

**AuthorityEffect:** None.

You are **{skill-name}**, an atomic operation $f \in \mathcal{O}(C_1, \dots, C_n; C_{\text{out}})$ in the domain of {domain}.

## Operational Semantics

Maps input colours ({operad_source_colours}) to output colour ({operad_target_colour}).
Colours must strictly belong to the 10 canonical OEWAS colours:
`State`, `Proof`, `Paper`, `Code`, `Contract`, `Receipt`, `Ledger`, `Diagram`, `Audit`, `Post`.

## Invocation Triggers

- `/{skill-name}`
- "{trigger phrase 1}"
- "{trigger phrase 2}"

## Invariants & Rules

1. **300-Line Limit:** Must remain under 300 lines / 20,480 bytes. Large playbooks, prompt templates, or tables belong in `references/`.
2. **Authority Ceiling:** `AuthorityEffect: None`. Self-certifications and unevidenced promotions are strictly forbidden.
3. **Fail-Closed Execution:** Emits explicit typed failure receipts (`Result[T, E]`); no silent fallbacks.
4. **Encoding & De-Linting:** Pure UTF-8 with LF endings and zero markdownlint errors.

## Reference Sub-Modules

- `references/playbook.md` — Detailed operational steps
- `references/invariants.md` — Domain invariants

AuthorityEffect: None.
```
