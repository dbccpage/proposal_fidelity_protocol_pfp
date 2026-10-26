# Lesson 970.05 -- 4. Student Exercises

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_05_4_student_exercises.ipynb](../notebooks/lesson_970_05_4_student_exercises.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 4. Student Exercises

To solidify your understanding, complete the following three exercises:

### Exercise 1: 4-Cycle Inspection
Given a 4-cycle of items $W \to X \to Y \to Z \to W$ with claimed edge differences:
- $W \to X = +2$
- $X \to Y = +3$
- $Y \to Z = -1$
- $Z \to W = -4$

Compute the cycle sum and defect $\Phi_1$. Is this system `CONSISTENT` or a `CONTRADICTION`?

### Exercise 2: Detecting Field Injection in a Sealed Packet
An untrusted model returns a payload that introduces an unauthorized field `"self_certified": true`.
Write a function `validate_packet_schema` that rejects any payload containing keys outside an approved schema allowlist `{"step", "vertex_from", "vertex_to", "value"}`.

### Exercise 3: Potential Gauge Reconstruction
If a cycle of 3 vertices is consistent with differences:
- $A \to B = 5$
- $B \to C = -2$
- $C \to A = -3$

Assuming gauge anchor $x_A = 0$, compute the exact scalar potentials $x_B$ and $x_C$.

## 5. Summary & Next Steps

### Key Beginner Takeaways
1. **The Naked Prompt Trap**: Language models predict likely tokens; they do not natively verify discrete global invariants. Persuasive prose can and will launder mathematical contradictions.
2. **Three-Layer Sovereignty**: Always isolate continuous generation (Layers 1 & 2) from discrete external verification (Layer 3).
3. **The Cycle Invariant ($\Phi_1$)**: Closed loops in directed difference networks must sum to zero. Any non-zero sum is an incontrovertible witness of defect ($\Phi_1 > 0$).
4. **Sealed Packets**: Never trust raw strings across system seams. Cryptographic envelope sealing prevents data tampering and prompt injection.

### Where to Go Next
- **Track 1 (Practitioners)**: Dive into `lesson_970_07_section_2_daily_workflow_integrations` and `lesson_970_08_epistemic_failure_classes` to learn how to build real Claude Code pre-tool hooks, Codex linters, Antigravity multi-agent swarms, and the 12 Epistemic Failure Classes.
- **Track 2 (Foundations)**: Explore `700_math/` for the full mathematical theory of simplicial cochain complexes, sheaf cohomology, discrete $L_1$ coboundary projection, and totally unimodular matrices.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `00_symbol_game_for_beginners`
- The code checks one finite example. It is not a general proof.
