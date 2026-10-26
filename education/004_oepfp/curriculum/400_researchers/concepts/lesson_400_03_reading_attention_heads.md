# Lesson 400.03 — Reading Attention Heads

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_03_reading_attention_heads.ipynb](../notebooks/lesson_400_03_reading_attention_heads.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Distinguishing invariant carrier heads from unconstrained fluff heads

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of reading attention heads.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of reading attention heads over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Which head has the smaller support?

- **A:** The carrier head, support 2. Entropy is not computed.
- **B:** The fluff head, support 2.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that distinguishing invariant carrier heads from unconstrained fluff heads continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
carrier_head = ("<a>", "<b>", "<c>", "<d>")
fluff_head = ("the", "a")
assert len(set(carrier_head)) > len(set(fluff_head))
print("A wider carrier head is not the smaller support")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `09_attention_entropy` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
