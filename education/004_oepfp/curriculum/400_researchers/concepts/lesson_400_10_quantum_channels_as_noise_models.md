# Lesson 400.10 — Quantum Channels as Noise Models

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_10_quantum_channels_as_noise_models.ipynb](../notebooks/lesson_400_10_quantum_channels_as_noise_models.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Depolarizing and amplitude-damping models of model hallucination

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of quantum channels as noise models.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of quantum channels as noise models over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Where does the diagonal (1, 0) go under p = 1/2 and uniform noise?

- **A:** (3/4, 1/4).
- **B:** (1/2, 1/2). The channel forgets the state entirely.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that depolarizing and amplitude-damping models of model hallucination continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
state = (Fraction(1), Fraction(0))
uniform = (Fraction(1, 2), Fraction(1, 2))
weight = Fraction(1)
result = tuple((1 - weight) * state[index] + weight * uniform[index] for index in range(2))
assert result == (Fraction(1, 2), Fraction(1, 2))
print("Full noise reaches the uniform state")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `quantum_channel.rs` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
