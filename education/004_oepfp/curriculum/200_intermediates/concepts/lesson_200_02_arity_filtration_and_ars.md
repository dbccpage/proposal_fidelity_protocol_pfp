# Lesson 200.02 — Arity Filtration and ARS

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_02_arity_filtration_and_ars.ipynb](../notebooks/lesson_200_02_arity_filtration_and_ars.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Abstract Rewriting Systems, redex matching, and confluence

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of arity filtration and ars.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of arity filtration and ars over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Do both one-step rewrites of a reach d?

- **A:** Yes. b and c both rewrite to d.
- **B:** No. The two branches stay apart.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that abstract rewriting systems, redex matching, and confluence continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
rules = {"a": ("b", "c"), "b": ("d",), "c": ("d",)}

def reached(start):
    seen = {start}
    changed = True
    while changed:
        changed = False
        for word in tuple(seen):
            for nxt in rules.get(word, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    changed = True
    return seen

closed = reached("b")
assert closed == {"b", "d"}
assert "c" not in closed
print("Branch from b does not invent c:", sorted(closed))
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `02_arity_filtration` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
