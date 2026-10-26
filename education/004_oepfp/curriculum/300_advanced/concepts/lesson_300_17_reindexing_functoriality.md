# Lesson 300.17 — Reindexing Functoriality

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_17_reindexing_functoriality.ipynb](../notebooks/lesson_300_17_reindexing_functoriality.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Proving `(g circ f)* = f* circ g*` in Lean 4

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of reindexing functoriality.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of reindexing functoriality over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Does (g after f) pull back equal f pullback after g pullback on this set?

- **A:** Yes. Both preimage sets equal {0}.
- **B:** No. Pullback reverses functions only for invertible maps.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that proving `(g circ f)* = f* circ g*` in lean 4 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
def preimage(mapping, target):
    return {item for item, image in mapping.items() if image == target}

forward = {0: "x", 1: "y"}
assert preimage(forward, "y") == {1}
print("A different label has a different preimage")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Level22FibredDependentContexts.lean` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
