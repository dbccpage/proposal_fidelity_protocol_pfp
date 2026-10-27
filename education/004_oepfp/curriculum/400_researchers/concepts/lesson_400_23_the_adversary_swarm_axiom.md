# Lesson 400.23 — The Adversary Swarm Axiom

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_23_the_adversary_swarm_axiom.ipynb](../notebooks/lesson_400_23_the_adversary_swarm_axiom.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Enforcing zero unpriced rewrite density across multi-agent swarms

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of the adversary swarm axiom.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of the adversary swarm axiom over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Does one unpriced rewrite get admitted?

- **A:** No. The unpriced count is 1.
- **B:** Yes. A priced rewrite covers the batch.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that enforcing zero unpriced rewrite density across multi-agent swarms continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
rewrites = ({"priced": True}, {"priced": True})
unpriced = sum(1 for item in rewrites if not item["priced"])
assert unpriced == 0
print("A fully priced batch is not this refusal")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Adversary Swarm Axiom` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
