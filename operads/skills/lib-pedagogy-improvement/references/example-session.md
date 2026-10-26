# Example session

`AuthorityEffect: None.` Reference material for [`lib-pedagogy-improvement`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Example Session

``` ext
User: Review lesson 000.05 (Topological Knots) for pedagogy quality.

Omega: [Invokes /lib-pedagogy-improvement]

Step 0: Learning Objectives
- LO1: Define topological knot and distinguish from everyday knot.
- LO2: Explain what a knot invariant is and why it matters.
- LO3: Calculate the linking number for a simple example.

Step 0.5: Diagnostic Probe
- "Which of these is a knot in the topological sense? (A) a shoelace bow (B) a closed loop with a crossing (C) a straight rope"
- Common wrong answer: (A) -- everyday meaning vs. topological meaning.
- Scaffold added: definition of "closed curve in 3-space" before main content.

Step 1-2: Scores

| Dimension      | Score | Weight | Weighted |
|----------------|-------|--------|----------|
| Clarity        | 4     | 30%    | 1.20     |
| Accuracy       | 4     | 25%    | 1.00     |
| Prerequisites  | 3     | 20%    | 0.60     |
| Engagement     | 3     | 15%    | 0.45     |
| Atomicity      | 4     | 10%    | 0.40     |
| **Overall**    |       |        | **3.65** |

Status: PASS

Issues Found:
- [ISSUE-001] Prerequisites: "Jones polynomial" used in paragraph 3 before definition in paragraph 7.
  Severity: HIGH. Fix: Add (preview) marker with forward reference.
- [ISSUE-002] Engagement: No inline micro-check between sections 2 and 3.
  Severity: MEDIUM. Fix: Add "Check: Is the unknot a knot? Why or why not?"

Recommendations:
1. Add (preview) marker for Jones polynomial at first use.
2. Insert micro-check after knot invariant definition.
3. Add Sources footer (3-5 references for knot theory claims).

``` ext
