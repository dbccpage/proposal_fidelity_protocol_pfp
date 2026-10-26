---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Regression Suite - {lesson_id}

Purpose: keep the lesson stable by preserving the **must-pass learning checks** discovered through tickets.

## Governance Rules

- Every closed ticket MUST add or update at least one probe.
- Diagnostics are not mastery evidence unless pass criteria are explicit.
- A probe may not be removed unless replaced by a stronger probe.
- Weak probes are invalid: no keyword-only checks, no vague "understands" criteria.
- Failed BLOCKER probes reopen the lesson ticket.
- Claim hygiene checks are mandatory for math, physics, computation, empirical, or philosophical claims.

## Probe Status

Each probe must be marked:

- ACTIVE -- currently required
- QUARANTINED -- suspected weak/ambiguous, not credit-bearing
- REPLACED -- superseded by stronger probe
- DEPRECATED -- removed with rationale and replacement

## Probe Quality Rules

A probe is invalid if it:

- can be passed by keyword matching alone
- only asks for recognition when production is required
- lacks pass criteria
- has no plausible wrong answer
- does not map to a lesson objective
- tests trivia instead of the target concept

## Probe Replacement Rule

A probe may be removed only if:

1. Replacement probe is named.
2. Replacement covers the same misconception/objective.
3. Replacement has stricter or clearer pass criteria.
4. Ticket trace records the replacement.

## Metadata

- Lesson: {lesson_id}
- Version: {n}
- Last updated: {YYYY-MM-DD}
- Target audience: {who}
- Core objectives (LO1-LO3): {short}

## Must-Pass Probes (Core)

### 1) Diagnostic Probe (Relevance Gate)

- **Status:** ACTIVE | QUARANTINED | REPLACED | DEPRECATED
- **Objective:** LO1 | LO2 | LO3
- **Severity if failed:** BLOCKER | MAJOR | MINOR
- **Kind:** discrimination | prediction | construct | explain
- **Prompt:**
- **Pass criteria:**
- **Common wrong answer(s):**
- **Scaffold if fail:** (definition | worked example | bridge exercise | prerequisite pointer)

### 2) Transfer Probe (Representation Switch)

Pick one conversion that matters most in this lesson.

- **Status:** ACTIVE | QUARANTINED | REPLACED | DEPRECATED
- **Objective:** LO1 | LO2 | LO3
- **Severity if failed:** BLOCKER | MAJOR | MINOR
- **Prompt:** (e.g., "Translate this equation into words." / "Write pseudocode for this concept.")
- **Pass criteria:** (what a correct transfer contains)
- **Common failure mode:**
- **Scaffold if fail:** (add representation block + micro-check)

### 3) Inline Micro-Check (Flow Cadence)

This should occur mid-lesson (anchor it to a heading).

- **Status:** ACTIVE | QUARANTINED | REPLACED | DEPRECATED
- **Objective:** LO1 | LO2 | LO3
- **Severity if failed:** BLOCKER | MAJOR | MINOR
- **Anchor (heading):**
- **Prompt:**
- **Pass criteria:**
- **If many fail:** insert scaffold immediately before anchor + re-test

### 4) Independent Attempt (Error-Correction)

- **Status:** ACTIVE | QUARANTINED | REPLACED | DEPRECATED
- **Objective:** LO1 | LO2 | LO3
- **Severity if failed:** BLOCKER | MAJOR | MINOR
- **Prompt:** (small exercise)
- **Pass criteria:** (result + check method)
- **Required check:** units/invariant/edge case/objection (choose one)
- **Wrong-but-plausible answer:** (and why wrong)

### 5) Retrieval Prompt (10-20 min)

- **Status:** ACTIVE | QUARANTINED | REPLACED | DEPRECATED
- **Objective:** LO1 | LO2 | LO3
- **Severity if failed:** BLOCKER | MAJOR | MINOR
- **Prompt:** "From memory: big idea + 3 key steps + one example."
- **Pass criteria:** (what must be recalled)
- **Hint (1 line):** (allowed if stuck)

## Domain Add-ons (Use When Relevant)

### Math / Physics Add-on

- **Units/dimensions check probe:**
- **Limiting case probe (x->0/infinity):**
- **Invariant/symmetry probe:**

### Philosophy Add-on

- **Argument map probe (P1... therefore C):**
- **Objection probe (best objection + reply):**
- **Hidden premise probe:**

### Computation Add-on

- **Runnable artifact probe:** (snippet/pseudocode required)
- **Tests probe:** (normal + edge case)
- **Debug probe:** (given failing test, locate likely bug class)

### Cog Sci Add-on

- **Mechanism vs description probe:**
- **Prediction probe (manipulate variable V -> expected outcome):**
- **Alternative explanation probe:**

## Claim Hygiene Checks (If physics/math/comp factual claims appear)

- **Claim tag exercise:** label as Definition/Empirical/Derivation/Interpretation-dependent/Metaphor/Speculative
- **Falsifiability question:** "What would change your mind about this claim?"
- **Sources footer required:** 3-5 items (textbook/survey/primary)

## Misconceptions Registry (Living List)

List predictable misconceptions and the probe that detects each.

1. **Misconception:**
   - Probe:
   - Corrective rule:
2. **Misconception:**
   - Probe:
   - Corrective rule:

## Ticket Trace (Optional)

Track which ticket introduced which probe.

- {ticket_id} -> Probe: {name} (anchor: {heading})

---

## How to Use This File (Ring Runner)

### Student Agent

- Run probes during BASELINE and VERIFY.
- If a must-pass probe fails, open or reopen a ticket.

### Pedagogy Agent

- When patching a ticket, add or update probes here.
- Never remove probes unless replaced by a stronger probe.
