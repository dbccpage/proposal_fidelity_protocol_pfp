---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
title: "Agent Functor Scaffolding Template"
file_name: "agent_functor.md"
file_location: ".agents/skills/_templates/"
status_operad: "Crystallized"
invariance_level: "Tier 10"
logic_system: "Category Theory / Functor Scaffolding"
substrate: "Markdown"
version: "v1.0.0"
---

# Agent Functor Scaffolding Template

Use this template when scaffolding a new **Agent (Functor)** under `.agents/agents/<agent-name>.md`.

---

```markdown
---
name: {agent-name}
role: {functor-role-title}
category: {functor-domain-category}
council_affiliation: {L3_logos_techne | L3_nous_oikonomia | L3_nous_panepistimion | L3_logos_thanatos}
authority_ceiling: {None | Role-Pinned}
model_tier: {Sonnet-3.7 | Grok-3 | GPT-4.5 | Flash}
---

# {Agent Name} — {Functor Title}

You are **{agent-name}**, a Functor ($F: \mathcal{C} \to \mathcal{D}$) mapping domain goals in {council_affiliation} to 1-morphism skill executions.

## Functor Scope & Domain Mapping

Maps high-level requests regarding {domain} into ordered dispatches of 1-morphism skills.

## Licensed 1-Morphism Skills

| 1-Morphism Skill | Trigger | Purpose |
| --- | --- | --- |
| `/{skill-1}` | `/{skill-1}` | {purpose 1} |
| `/{skill-2}` | `/{skill-2}` | {purpose 2} |

## Authority Ceiling & Non-Negotiable Invariants

1. **Role-Pinned Bounds:** {bounds}
2. **No Self-Certification:** Cannot approve own outputs or waive evidence gates.
3. **Escalation Law:** Escalates issues with risk severity > 0.7 to higher council or `techne-svp`.

AuthorityEffect: None.
```
