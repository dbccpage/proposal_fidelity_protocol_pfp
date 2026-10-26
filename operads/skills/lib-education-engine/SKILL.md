---
name: lib-education-engine
description: "Orchestrates pedagogical curriculum structure, section checks, and instructional engine workflows."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# lib-education-engine

**Part:** I — Foundations
**Duration:** ~15 minutes
**Section:** 6 of 84

## tldr: Triangles are rigid because SSS uniqueness - three fixed lengths form a unique shape

## Example Valid Section

### Valid Section File

## Examples

## Checklist

### 4. Content Bridge

**Lesson 003 (Quantum Bridge) & 004 (Quantum Field Theory) Example:**
**Error Handling:**
**Optional Content Types (skip domain expert gate):**
**Mandatory Content Types (must pass domain expert gate):**
**Implementation:**
**Integration Points:**
**The Lesson Factory Pipeline (updated):**
**NEW in Sprint 150:** All technical content (physics, mathematics, chemistry, computer science, linguistics) must pass **domain expert verification** before advancing to rendering.

### 3.5. Domain Expert Quality Gate (Mandatory for Technical Content)

### 3. Querying Content

### 2. Importing Lessons

**Optional fields:**
**Required frontmatter fields:**

### 1. Section File Format

## Instructions

## When to Activate

## description: Import, validate, and manage educational content for the physics curriculum. Use when importing lesson sections, validating section format, querying lessons/sections, or bridging to Content Factory

## Big Idea

Nature is lazy, but likes to be certain...

## Summary

Triangles are the only rigid polygon...

---

Next: 1.07 — The Square Cannot Hold

## Related Skills

| Skill | Relationship |
|-------|--------------|
| content-factory | Content rendering pipeline |
| alembic-migration | Database schema management |
| postgresql | Database patterns |
| lib-pedagogy-improvement | Content quality evaluation |

**Family:** education (see [family_registry.md](../_shared/family_registry.md))

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: APPROVAL_REQUIRED

Summary:

- Educational content imports require validation before commit (APPROVAL_REQUIRED)
- **Education Regression Suite**: All content must align with the `regression_template.md` governance. Probes must be high-quality (no keyword-only checks), include Status/Objective/Severity metadata, and adhere to monotonicity rules.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
