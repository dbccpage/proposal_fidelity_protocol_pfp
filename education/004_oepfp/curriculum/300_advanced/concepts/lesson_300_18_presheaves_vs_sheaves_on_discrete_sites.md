# Lesson 300.18 — Presheaves vs Sheaves on Discrete Sites

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_18_presheaves_vs_sheaves_on_discrete_sites.ipynb](../notebooks/lesson_300_18_presheaves_vs_sheaves_on_discrete_sites.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Locality and gluing conditions for mathematical data

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of presheaves vs sheaves on discrete sites.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of presheaves vs sheaves on discrete sites over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Can local sections a and b glue when they disagree on the overlap?

- **A:** No.
- **B:** Yes. Sheaves glue every pair of local sections.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that locality and gluing conditions for mathematical data continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
local = {"U": {"p": 1, "q": 1}, "V": {"q": 1, "r": 2}}
overlap = set(local["U"]) & set(local["V"])
agree = all(local["U"][point] == local["V"][point] for point in overlap)
assert agree is True
print("Matching overlap values may glue")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Sheaf Theory` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
