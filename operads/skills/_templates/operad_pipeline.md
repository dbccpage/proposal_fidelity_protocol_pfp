---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
title: "Operadic Planar Pipeline Template"
file_name: "operad_pipeline.md"
file_location: ".agents/skills/_templates/"
status_operad: "Crystallized"
invariance_level: "Tier 10"
logic_system: "Coloured Operads / Planar Substitution Trees"
substrate: "Markdown"
version: "v2.0.0"
---

# Operadic Planar Pipeline Template

Use this template when scaffolding a new **Operadic Workflow Pipeline** under `.agents/workflows/<workflow_name>.md`.

---

```markdown
---
name: {workflow_name}
type: operadic_pipeline
description: "{Planar operadic tree composition of skill operations}"
controlling_council: {L3_logos_techne | L3_nous_oikonomia | L3_nous_panepistimion | L3_logos_thanatos}
tree_signature: "γ({root_skill}; {stage_1_skill}, {stage_2_skill})"
---

# {Workflow Name} — Planar Substitution Pipeline

**AuthorityEffect:** None.

Composes ordered operadic operations through planar tree substitution $\gamma(f; g_1, \dots, g_n)$ to achieve fail-closed pipeline convergence across declared colours.

## Sequential Stage Order

1. **Stage 1: {Stage 1 Name}** (`/{skill-1}`)
   - Source Colours: `[{ColourA}]`
   - Target Colour: `{ColourB}`
   - Role: Proposal / Generation
2. **Stage 2: {Stage 2 Name}** (`/{skill-2}`)
   - Source Colours: `[{ColourB}]`
   - Target Colour: `{ColourC}`
   - Role: Deterministic Verification
3. **Stage 3: {Stage 3 Name}** (`/{skill-3}`)
   - Source Colours: `[{ColourC}]`
   - Target Colour: `Receipt`
   - Role: Audit & Evidence Attestation

## Stage Transition Gates

- Stage $k+1$ executes if and only if Stage $k$ emits a valid receipt matching the target colour.
- Type mismatches or unverified attestations abort execution immediately with explicit diagnostic logs; no silent fallbacks.

AuthorityEffect: None.
```
