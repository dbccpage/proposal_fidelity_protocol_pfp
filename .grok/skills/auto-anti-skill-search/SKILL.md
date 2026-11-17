---
name: auto-anti-skill-search
description: "Search for failure modes, test candidate skills against canary fixtures, and draft anti-skill specs."
invocation: discipline
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [meta, anti-skill, canary, thanatos, dianoia]
---

# Auto Anti-Skill Search

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Adversarial interrogator; constructs failure probes & canary receipts)
**Governance Council:** `L3_logos_thanatos` (Adversarial Truth & Truth Firewalls) / `L2_dianoia` (Dialectic)

---

## 1. Prime Directive

The **Auto Anti-Skill Search** acts as the interrogative dual operator ($\mathcal{O}^-$) of the Polarized Coloured Operad. It systematically analyzes episode traces, candidate skills, and boundary seams to discover unmet obligations, semantic smuggling, and latent failure modes, constructing formal Anti-Skill specifications and canary test fixtures.

---

## 2. Core Operational Invariants

### 1. Interrogative Anti-Skill Generation ($\mathcal{O}^-$)

- Formulates failure-mode probes and anti-skill specifications from session traces, uncontracted boundaries, and semantic overclaims.
- An anti-skill is not the inverse of a skill, but a typed interrogative detector mapping candidate artifacts and context to structural findings and unmet obligations.

### 2. Truth-Boundary Canary Fixture Evaluation

- Evaluates candidate skills against positive detection fixtures (known defects triggering findings) and negative control fixtures via Rust canary engine `engine/crates_rs/core_prompt_civilization` and StructureBench contract evaluation (`operads/structurebench/evaluator.py`).

### 3. Obstruction Certificate & Handoff to Dialectics

- If a candidate skill fails a canary test or contains uncontracted authority claims, emits an explicit `ObstructionCertificate`.
- Feeds discovered failure modes and fatal bottlenecks directly into `logos-dialectics-wizard` (Stage 3 of `auto-oe-autop`) to initiate the Nocebo-to-Placebo reframing cycle.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
