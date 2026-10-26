---
name: lib-pedagogy-improvement
description: "Educational design and lesson structure improvements, micro-checks, worked examples, and faded scaffolding."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# lib-pedagogy-improvement

**✓ Check:** {1-sentence question}

## Micro-Check Patterns

### Inline Micro-Check Pattern *(NEW in v4)*

### Worked Example → Faded → Independent

## Improvement Patterns

## Exercise Quality Mini-Rubric

## Recommendations

## Style Guide Compliance

## Accessibility & Load Notes

## Prerequisite Violations

## Misconception Inventory *(NEW in v4)*

### Cog Sci

### Computation

### Philosophy

### Math/Physics

## Domain-Specific Audit

## Exercise Audit

**Proposed**: "{improved text}"
**Current**: "{quoted text}"
**Issue**: {description}
**Severity**: HIGH | MEDIUM | LOW

### [ISSUE-001] {Dimension}: {Section heading}

## Issues Found

## Sources / Further Reading *(NEW in v4 when physics/math/comp touched)*

## Representation/Transfer Notes

## Scores

## Inline Micro-Checks Summary *(NEW in v4)*

## Diagnostic Probe Results

### Alignment Map

### Objectives

## Learning Objectives & Alignment

## Status: PASS | NEEDS WORK | REJECT

### Step 5: Generate Report

### Step 4.6: Flow & Insight Pass

### Step 4.5: Accessibility & Cognitive Load

### Step 4: Style Guide Compliance

**Misconception inventory:** See [`misconception-inventory.md`](references/misconception-inventory.md).

## Review Workflow

### Thresholds

**Atomicity (10%)**
**Engagement (15%)**
**Prerequisites (20%)**
**Accuracy (25%)**
**Clarity (30%)**

### Scoring Guide

## 5-Dimension Evaluation Rubric

## Definition of Done (Hard Gates)

## When to Activate

**Reference material** (moved out of this file to keep it under the 300-line ceiling):

- Rubric and workflow detail — [`rubric-and-workflow.md`](references/rubric-and-workflow.md)
- Domain expert quality gate — [`domain-expert-gate.md`](references/domain-expert-gate.md)

## Calibration Appendix

To reduce reviewer drift, keep 1–2 "gold standard" scored examples.

### Template

- Example name: {e.g., Lesson 000.02 excerpt}
- Audience: ...
- Scores: ...
- Why those scores: 3–6 bullets citing specific sections
- Common disagreements: what reviewers tend to over/under-weight

## Improvement Log Template

After fixes are applied:

```markdown

# Improvement Log: {file_path}

**Reviewer**: pedagogy
**Date**: {date}
**Original Score**: X.XX
**Final Score**: X.XX

| Issue ID | Status | Change Made | Evidence |
|----------|--------|-------------|----------|
| ISSUE-001 | Fixed | Added eigenstate to lexicon | Lexicon section |
| ISSUE-002 | Fixed | Added (preview) marker | Void section |
| ISSUE-003 | Escalated | Sent to theoretical-physics | Awaiting |

```

## Thinker-to-Check Mapping Appendix

Use this appendix to translate "great thinkers" into **concrete review checks**. The goal is to keep reviews mechanical:
**If a thinker's insight matters, it should show up as a check, a probe, a representation requirement, or a feedback loop.**

## Quick Map (Thinker → Pedagogy Primitive → Skill Lever)

| Thinker / Lineage | Pedagogy primitive (what they explain) | Where it lives in this skill | What to add if missing |
|---|---|---|---|
| **Claude Shannon** | Channel capacity, noise, coding | Step 4.5 (Load), Step 0.5 (Probe) | Reduce "bandwidth": shorten sentences, chunk, add redundancy via multiple representations |
| **Miller / Baddeley** | Working memory limits, chunking | Step 4.5 (Load) | Chunk content; add intermediate "bridge" steps; avoid multi-operator leaps |
| **Broadbent / Treisman** | Attention filters; missed signals | Step 0.5 (Probe), Step 4.5 (Signposting), Step 0.6 (Micro-checks) | Insert micro-checks; add headings and "You'll learn…" markers |
| **Ausubel** | Prior knowledge is the main variable | Step 0.5 (Probe), Step 0 (LO alignment) | Add an "advance organizer": 3-sentence preface connecting to known schema |
| **Piaget** | Assimilation vs accommodation | Step 3.5 (Misconceptions), Step 4.6 (Insight) | Explicitly call out the "naive model" and show why it breaks |
| **Vygotsky** | ZPD, scaffolding, internalization | Step 0.5 (Probe → scaffold → re-probe) | Add scaffolds: definitions, worked example, simpler subproblem, then re-test |
| **Bruner** | Structure of a discipline; representation formats | Step 2.6 (Representation & Transfer) | Add words ↔ symbols ↔ diagrams ↔ examples; spiral back later |
| **Chi (ICAP)** | Activities that cause real learning | Step 4.6 (Feedback cadence) | Upgrade exercises from "active" to "constructive/interactive" (explain, generate, compare) |
| **Gestalt (Duncker/Köhler)** | Insight as re-representation | Step 4.6 (Aha triggers), Step 2.6 | Add a representation switch: diagram, limiting case, counterexample, symmetry |
| **Newell & Simon** | Problem spaces; operators and heuristics | Step 2.6 (Transfer), Improvement patterns | Add explicit "operators": moves, heuristics, invariants, search constraints |
| **Pólya** | Heuristics for unknown problems | Improvement patterns; Exercises | Add a "move list" + prompt: "What can you try next?" "What changes if…?" |
| **Lakatos** | Proofs evolve via refutation | Step 3.5 (Misconceptions), Step 4.6 (Counterexample) | Add a "refutation exercise": find counterexample → patch lemma → restate theorem |
| **Bjork(s)** | Retrieval, spacing, desirable difficulties | Exercises + audit; Step 4.6 | Add retrieval checks; spacing/interleaving; avoid massed re-reading |
| **Ericsson** | Deliberate practice + feedback | Exercise audit; Improvement patterns | Add "targeted loop": goal → attempt → feedback → repeat on weakest sub-skill |
| **Bloom** | Mastery learning gates | Step 0 alignment; Reporting | Add explicit pass criteria; "no advance until probe passes" |
| **Mayer** | Multimedia principles | Step 4.5 (Load), Representation | Remove seductive details; align words+diagrams; avoid redundant narration+text |
| **Csikszentmihalyi** | Flow: challenge/skill + fast feedback | Step 4.6 (Flow & Insight), Step 0.6 (Micro-checks) | Add bridge exercises, immediate checks, clear success criteria |
| **Grice / Clark** | Implicature + common ground | Step 1 (Audience), Step 4 (Style/Precision) | Add definitions, disambiguations, "precision notes," and assumption surfacing |
| **Pask** | Conversation as control system | Step 0.5 + re-probe; Step 0.6; Reporting | Add explicit "teach → check → adjust" loops; log wrong answers and fixes |
| **Wiener / Bateson / Maturana–Varela** | Feedback, control, structural coupling | Step 4.6 + Escalation | Treat teaching as regulation: measure error, adjust signal; don't "push harder," redesign coupling |

**Domain-specific translations:** See [`domain-translations.md`](references/domain-translations.md).

## Reviewer Cheatsheet (Minimal)

When you're short on time, do this:

1. Write 1–3 LOs.
2. Add a **Diagnostic Probe** (Step 0.5).
3. Add **1-2 inline micro-checks** per section (Step 0.6). *(v4)*
4. Ensure **2 representations + a transfer check** (Step 2.6).
5. Ensure **feedback every 2–5 minutes** via micro-checks (Step 4.6).
6. Add **claim tags** to physics claims + **sources footer**. *(v4)*
7. Fix **alignment map** to use section headings, not line numbers. *(v4)*
8. Ensure at least one **worked→faded→independent** loop (math/physics) OR **argument map + objection** (philosophy) OR **runnable + tests** (computation).

---

## Integration with Pedagogy Agent

This skill is invoked by the pedagogy agent as part of the review cycle:

1. `pedagogy` agent receives content for review
2. Agent invokes `lib-pedagogy-improvement` skill for evaluation
3. Skill generates critique report
4. Agent coordinates domain expert reviews if needed
5. Author addresses flagged issues
6. Skill validates improvements
7. Agent approves final version

**Section scaffolding template:** See [`section-scaffolding.md`](references/section-scaffolding.md).

## Claim Hygiene Quick Reference

Inline tags for epistemic labeling (append to claims):

| Tag Format | When to Use | Example |
|------------|-------------|---------|
| `*(Definition)*` | Agreed meaning | "We define closure as..." |
| `*(Empirical—[source, year])*` | Experimentally verified | "*(Empirical—Aharonov-Bohm effect, 1959)*" |
| `*(Derivation)*` | Follows from prior statements | Mathematical results |
| `*(Interpretation-dependent—[view])*` | Multiple schools disagree | "*(Interpretation-dependent—Copenhagen view)*" |
| `*(Speculative—[reason])*` | Hypothesis, not established | "*(Speculative—active research area)*" |
| `*(Metaphor)*` | Explicitly figurative | Analogies, not proof |

**Rule:** Physics-touching claims require at least one tag + Sources footer.

---

## Quick Commands

- **Full review**: Run complete 5-dimension evaluation + gates + domain audit
- **Prerequisite check only**: Just validate prerequisite chain
- **Style check only**: Just validate style guide compliance
- **Quick score**: Return scores without detailed issues
- **Exercise audit**: Return alignment map + exercise mini-rubric only
- **Misconception pass**: Return misconceptions + checks only
- **Domain audit**: Run domain-specific checklist only
- **v4 audit**: Check micro-checks, claim tags, sources, stable refs *(NEW)*
- **Cross-reference validation**: Generate structured report of all cross-references *(NEW)*

**Reference material** (moved out of this file to keep it under the 300-line ceiling):

- Cross-reference validation report — [`cross-reference-validation.md`](references/cross-reference-validation.md)
- Example session — [`example-session.md`](references/example-session.md)

## Related Skills

| Skill | Relationship |
|-------|--------------|
| lib-education-engine | Content import and validation |
| content-factory | Content rendering pipeline |

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: APPROVAL_REQUIRED, EVIDENCE_BASED

Summary:

- Content evaluation decisions require user review (APPROVAL_REQUIRED)
- All scores and recommendations must cite specific evidence (EVIDENCE_BASED)

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
