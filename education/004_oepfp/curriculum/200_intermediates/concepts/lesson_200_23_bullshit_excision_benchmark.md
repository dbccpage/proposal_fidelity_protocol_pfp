# Lesson 200.23 — Bullshit Excision Benchmark

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_23_bullshit_excision_benchmark.ipynb](../notebooks/lesson_200_23_bullshit_excision_benchmark.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea
- 2. Scope & Claim Boundary
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Student Exercise
- 5. Anchors

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 fixtures or papers.
> - **[Proved]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea

**Core Concept:** 50-task benchmark: L1 sparsity vs dense CoT token waste

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of bullshit excision benchmark.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of bullshit excision benchmark over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** How many of these five tokens are bracketed carrier tokens?

- **A:** 2. This list is the whole example.
- **B:** 5. Every token is on carrier.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that 50-task benchmark: l1 sparsity vs dense cot token waste continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
tokens = ("<a>", "<b>", "<c>")
kept = tuple(token for token in tokens if token.startswith("<") and token.endswith(">"))
assert len(kept) == 3
assert len(kept) != 2
print("A different list keeps", len(kept))
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `08_l1_sparsity` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
