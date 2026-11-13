# Rubric and workflow detail

`AuthorityEffect: None.` Reference material for [`lib-pedagogy-improvement`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## description: Structured evaluation rubric and improvement workflow for educational content. Use when reviewing lessons, sections, or handouts for clarity, accuracy, prerequisite compliance, and learning effectiveness

``` ext

Or use callout format:

```markdown
> **Stop:** Translate the equation above into plain words before continuing.

``` ext

### Invariant First Pattern

Start with "what stays the same" before details.

- Physics: conserved quantity / symmetry
- Math: invariant under operation
- Computation: loop invariant / type invariant
- Philosophy: criterion of identity / persistence condition

### Argument Map Pattern

**Claim:** …
**Premise 1:** …
**Premise 2:** …
**Therefore:** …
**Objection:** …
**Reply:** …

### Prediction-First Microcheck

Before explaining, ask for a prediction. Then explain *in terms of the learner's error*.

### Claim Tagging Pattern *(NEW in v4)*

Add inline tags to non-trivial claims:

```markdown
The Casimir effect demonstrates that vacuum has measurable structure. *(Empirical)*

This suggests void is not absence but latent potential. *(Interpretation-dependent)*

We define potentiality as the capacity to become determinate. *(Definition)*

``` ext

### Sources Footer Pattern *(NEW in v4)*

At end of section, before Summary:

## ```markdown

## Sources / Further Reading

- Casimir, H. B. G. (1948). "On the attraction between two perfectly conducting plates." *KNAW Proceedings* 51: 793-795.
- Weinberg, S. (1995). *The Quantum Theory of Fields*, Vol. 1. Cambridge UP.
- Milonni, P. W. (1994). *The Quantum Vacuum*. Academic Press.

---
``` ext

### Objective-First Pattern

**Before:** Section introduces concepts, then adds exercises that feel loosely related.
**After:** State LO → teach minimal needed concepts → check → tighten based on wrong answers.

### Check-for-Understanding Pattern

Add a micro-check right after a dense paragraph:

- "In one sentence, what changed when X happened?"
- "Circle which statement is correct: (A) … (B) … (C) …"

### Wrong-Answer Feedback Pattern

For each exercise, add one plausible wrong answer and the fix:

- Wrong: "I think it's X because …"
- Feedback: "That reasoning assumes …; here's the missing constraint …"

### Jargon Fix Pattern

**Before:**
> The eigenstate collapses upon measurement.

**After:**
> The quantum state with definite value (eigenstate) changes upon measurement.
> *(Precision note: "collapse" is interpretation-dependent.)*

### Prerequisite Fix Pattern

**Option A - Introduce first:**
Add definition before first use.

**Option B - Mark as preview:**
> **superposition** *(preview)*: linear combination of states. Full treatment in Section 000.11.

### Abstract → Anchor Pattern

**Before:**
> Time emerges from discrete operations.

**After:**
> Time emerges from discrete operations. Just as a clock's second hand jumps between positions rather than flowing smoothly, spacetime in causal set theory consists of discrete events linked by causal order.
