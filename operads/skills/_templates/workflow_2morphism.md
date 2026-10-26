---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
title: "Workflow 2-Morphism Scaffolding Template"
file_name: "workflow_2morphism.md"
file_location: ".agents/skills/_templates/"
status_operad: "Crystallized"
invariance_level: "Tier 10"
logic_system: "Category Theory / Natural Transformation Scaffolding"
substrate: "Markdown"
version: "v1.0.0"
---

# Workflow 2-Morphism Scaffolding Template

Use this template when scaffolding a new **Workflow (2-Morphism / Natural Transformation)** under `.agents/workflows/<workflow_name>.md`.

---

```markdown
---
name: {workflow_name}
type: 2-morphism
description: {Natural transformation composition of 1-morphism stages}
controlling_council: {L3_logos_techne | L3_nous_oikonomia | L3_nous_panepistimion | L3_logos_thanatos}
---

# {Workflow Name} — Natural Transformation Pipeline ($\eta: f \Rightarrow g$)

Composes ordered 1-morphism stages to achieve fail-closed pipeline convergence.

## Sequential Stage Order

1. **Stage 1: {Stage 1 Name}** — `/{1morphism-skill-1}`
2. **Stage 2: {Stage 2 Name}** — `/{1morphism-skill-2}`
3. **Stage 3: {Stage 3 Name}** — `/{1morphism-skill-3}`

## Stage Transition Gates

- Stage $k+1$ executes if and only if Stage $k$ emits a valid execution receipt satisfying ZeroRel.
- Failures abort execution with explicit diagnostic logs; no silent fallback.

AuthorityEffect: None.
```
