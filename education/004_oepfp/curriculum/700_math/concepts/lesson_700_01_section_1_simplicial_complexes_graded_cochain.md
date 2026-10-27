# Lesson 700.01 -- Section 1: Simplicial Complexes & Graded Cochain Algebra ($C^0, C^1, C^2$)

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_01_section_1_simplicial_complexes_graded_cochain.ipynb](../notebooks/lesson_700_01_section_1_simplicial_complexes_graded_cochain.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

### Claim Typing Legend
- `[Pinned]`: Directly verified against explicit code fixture, verified solver receipt, or test harness.
- `[Proved]`: a finite check in this notebook. Not a general proof.
- `[Declared]`: Mathematical definition, axiomatic specification, or interface contract.
- `[Open]`: Unresolved conjecture or boundary condition under theoretical research.

---

### Anchors & Provenance
- **Paper 032 Anchor**: *The Symbol Game: Three-Layer Sovereignty and Discrete $L_1$ Projection*.
- **Domain Package**: `pfp.domain.ddc` (Discrete Deformation Calculus).
- **Formal Theory**: Lean 4 formalization `PrimitiveDifference.lean` and CODA Discrete Deformation Calculus.

---

## Section 1: Simplicial Complexes & Graded Cochain Algebra ($C^0, C^1, C^2$)

### [Declared] Graded Cochain Complex Definition
Let $K = (V, E, F)$ be a finite 2-truncated cell complex over exact rational coefficients $\mathbb{Q}$.
- $C^0(K; \mathbb{Q}) = \mathbb{Q}^V$ is the space of 0-cochains (vertex potentials $f: V \to \mathbb{Q}$).
- $C^1(K; \mathbb{Q}) = \mathbb{Q}^E$ is the space of 1-cochains (edge claims $h: E \to \mathbb{Q}$), with anti-symmetry $h(v, u) = -h(u, v)$.
- $C^2(K; \mathbb{Q}) = \mathbb{Q}^F$ is the space of 2-cochains (face curvatures $\omega: F \to \mathbb{Q}$).

### [Declared] Graded Coboundary Operators
1. The **0-coboundary** $d^0: C^0 \to C^1$ assigns to each directed edge $e = (u, v)$ the potential difference:
   $$(d^0 f)(u, v) = f(v) - f(u)$$
2. The **1-coboundary** $d^1: C^1 \to C^2$ evaluates the oriented circulation around each triangular 2-cell $F = (u, v, w)$:
   $$(d^1 h)(u, v, w) = h(v, w) - h(u, w) + h(u, v)$$

### [Pinned] Nilpotency on one complex

The identity $d^1 \circ d^0 = 0$ for every cochain is background from the math shelf chapter on cochains. This notebook does not decide that chapter's repair-versus-quotient question. The cell checks $d^1 \circ d^0$ on one finite complex.

For any vertex potential $f \in C^0$, substitution gives:
$$(d^1 (d^0 f))(u, v, w) = (f(w) - f(v)) - (f(w) - f(u)) + (f(v) - f(u)) = 0$$
This nilpotency holds algebraically over $\mathbb{Q}$ with exact zero defect.

## Anchors

- Former notebook: `00_advanced_discrete_deformation_algebra`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md](../../../../../research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md)

Frontier sitting already on disk: [N3_simplices_and_exact_betti_numbers.md](../../600_mssn_frontier/N3_simplices_and_exact_betti_numbers/N3_simplices_and_exact_betti_numbers.md). It is a different folder. This lesson does not replace it.
