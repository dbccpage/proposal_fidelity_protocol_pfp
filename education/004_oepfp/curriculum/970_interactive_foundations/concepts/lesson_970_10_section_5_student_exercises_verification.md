# Lesson 970.10 -- Section 5: Student Exercises & Verification

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_10_section_5_student_exercises_verification.ipynb](../notebooks/lesson_970_10_section_5_student_exercises_verification.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Section 5: Student Exercises & Verification

Complete these three exercises to verify your understanding:
1. **Exercise 1**: Write a Claude Code hook filter that detects ungrounded assertions of `Q.E.D.` in code comments.
2. **Exercise 2**: Formulate a compound epistemic test on an adversarial model output combining `PersonaAuthorityLeak` and `OptimalityHallucination`.
3. **Exercise 3**: Compute multi-pass collapse on a 4-cycle proposal space with target prefix $(1, 2, -1)$.

## Summary & Practitioner Takeaways

1. **Three-Layer Sovereignty is Mandatory**: Never let a generative model certify its own output. Keep model weights at Layer 1, decode sampling at Layer 2, and all verification at Layer 3.
2. **Fail-Closed Tooling**: Daily workflow hooks in Claude Code, Codex, and Antigravity swarms must refuse suspect or unverified state immediately.
3. **The 12 Epistemic Failure Classes**: Check for self-certifications, fake receipts, theorem name laundering, and complexity claims deterministically.
4. **Anti-Morphism Collapse**: Verification is an interior operator that shrinks proposal clouds to landed witnesses or honest empty refusals.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `00_agentic_symbol_game_quickstart`
- The code checks one finite example. It is not a general proof.
