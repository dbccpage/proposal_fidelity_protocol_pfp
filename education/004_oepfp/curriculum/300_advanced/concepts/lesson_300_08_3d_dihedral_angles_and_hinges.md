# Lesson 300.08 — 3D Dihedral Angles and Hinges

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_08_3d_dihedral_angles_and_hinges.ipynb](../notebooks/lesson_300_08_3d_dihedral_angles_and_hinges.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Computing dihedral angles and Regge hinge deficit angles

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of 3d dihedral angles and hinges.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of 3d dihedral angles and hinges over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What combinatorial hinge deficit does a vertex of five sixth-turns have?

- **A:** 1/6. No dihedral cosine is computed.
- **B:** The radian dihedral of a regular tetrahedron.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that computing dihedral angles and regge hinge deficit angles continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
hinge_turns = tuple(Fraction(1, 4) for _ in range(3))
assert Fraction(1) - sum(hinge_turns) == Fraction(1, 4)
print("Three quarter-turns leave deficit 1/4")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `N5_first_deficit_angle` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
