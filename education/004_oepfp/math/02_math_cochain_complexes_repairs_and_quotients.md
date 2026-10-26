---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 02: Cochain Complexes, Repairs, and Quotients'
kind: mathematical-reference
audience:
- researchers
- engineers
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - discrete_cochain_complex_over_field
    - coboundary_repair_operator_d0
    - coboundary_closure_operator_d1
    - exact_repair_subspace
    - quotient_repair_space
  prose_theorems:
    - coboundary_nilpotence
    - quotient_equivalence_characterization
  lean_theorems: []
  finite_computations: []
  declared_policies:
    - rational_field_specialization
  applications: []
  open_conjectures: []
coefficient_domain: "Declared Field K (Specializing to ℚ)"
runtime_dependency: "Chapter 01 (Primitive Difference, Directed Cuts, and Rigidity)"
governance_dependency: "None"
---

# Chapter 02: Cochain Complexes, Repairs, and Quotients

**Status:** Canonical Mathematics Specification (Spine Chapter 02)  
**Authority:** None. Linear algebra over declared fields and discrete algebraic topology.

## Listen, then watch

This block is a recording plan. It was not recorded on 2026-10-22. The picture in section 1 is the same triangle. AuthorityEffect: None.

**Plain opening.** Heights on three posts make slopes that add to zero when you walk back to the start. A measured loop that adds to something else is not a set of heights.

**Terms at first use.** A height is a number on a post. A slope on a directed step is the height at the end minus the height at the start. A loop is a walk that returns to its start. Later, the slope map is called d zero, and the space of all slopes that come from heights is called the exact repairs.

**One number before the general case.** Put heights 0, 3 and 1 on posts A, B and C. The slope from A to B is 3 minus 0, which is 3. From B to C it is 1 minus 3, which is minus 2. From C to A it is 0 minus 1, which is minus 1. The loop sum is 3, plus minus 2, plus minus 1, which is 0. The general fact, proved by cancellation in section 1, is that every height-made loop sums to 0.

**A check you can fail.** Suppose the measured slopes are 4, minus 2 and 8. Each number could be a slope of some pair of heights. Their sum is 10, not 0. If you accept them as one height assignment because each edge looks possible, the check fails.

**Spoken segment.** Duration: 40 seconds. One idea: these three heights close, and the measured loop of 10 does not.

> Heights zero, three and one. From the first post to the second, the slope is three. From the second to the third, one minus three is minus two. From the third back to the first, zero minus one is minus one. Three, minus two, minus one, is zero. Now hear a different loop: four, minus two, and eight. Four minus two is two, and two plus eight is ten. Ten is not zero, so those three measurements are not heights of one set of posts.

**Check with no screen.** Add three, minus two, and minus one. If you said one, you dropped a minus. The sum is zero.

**Video beats.**

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:12 | heights 0, 3, 1 | "Three posts. Heights zero, three and one." |
| 0:12–0:28 | slopes 3, −2, −1 | "The slopes are three, minus two, and minus one." |
| 0:28–0:38 | sum = 0 | "Three, minus two, minus one, is zero. Height-made loops close." |
| 0:38–0:50 | 4, −2, 8 → 10 | "Four, minus two, and eight add to ten. Ten is not zero. These are not heights." |

---

## 1. Altitudes and Slopes: Discrete Intuition

Imagine three observation posts located on discrete peaks: $A$, $B$, and $C$.

```text
       A
      / \
     /   \
    B --- C
```

- Each post has an assigned potential (a scalar value on the vertex): $\alpha_A, \alpha_B, \alpha_C \in K$.
- The directed edge from post $A$ to post $B$ has a slope (elevation difference):
  $$\Delta \alpha_{AB} = \alpha_B - \alpha_A$$

If we sum these differences along a closed cycle $A \to B \to C \to A$:
$$(\alpha_B - \alpha_A) + (\alpha_C - \alpha_B) + (\alpha_A - \alpha_C) = 0$$

The sum of gradient differences around any closed combinatorial loop is **identically zero**.

Now suppose a detector measures edge values $x \in K^E$ directly, recording differences that sum to $+10$ around the loop. No vertex potential assignment $\alpha \in K^V$ can ever reproduce this observation. The discrepancy cannot be absorbed by re-zeroing the nodes; it is a non-trivial circulation.

---

## 2. The Finite Cochain Complex over a Declared Field $K$

We formalize these configurations using finite cochain complexes over a declared field $K$:

$$C^0 \xrightarrow{\;d_0\;} C^1 \xrightarrow{\;d_1\;} C^2$$

where the composition satisfies fundamental topological nilpotence:
$$d_1 \circ d_0 = 0$$

> **Declared Field Specification:**  
> The scalar domain is a declared field $K$. For exact rational runtime execution and linear programming dual certificates, the system specializes to $K = \mathbb{Q}$. Other fields (such as $\mathbb{R}$ or finite fields $\mathbb{F}_p$) are permitted only when explicitly declared.

### 2.1 The Cochain Spaces

- **$C^0$ (0-cochains):** Functions $\alpha: V \to K$ assigning potential values to vertices (local gauge parameters). Dimension is $|V|$.
- **$C^1$ (1-cochains):** Functions $c: E \to K$ assigning values to oriented edges (observed differences, flows, or defects). Dimension is $|E|$.
- **$C^2$ (2-cochains):** Functions $\beta: F \to K$ assigning values to declared oriented 2-cells (faces). Dimension is $|F|$.

### 2.2 Cellular Topology Specification: 1-Skeletons vs. 2-Cells

A critical distinction must be maintained between a graph cycle and a filled 2-cell:

1. **Pure 1-Skeleton Complexes:**  
   In a pure graph (1-skeleton), $C^2 = 0$ and $d_1 = 0$ identically. The sum around a graph cycle evaluates cycle circulation in the chain space $\mathcal{Z}_1 = \ker(\partial_1)$.
2. **Declared 2-Cells:**  
   To evaluate a non-trivial 2-coboundary operator $d_1: C^1 \to C^2$, the complex must explicitly declare **filled 2-cells** (oriented triangular or polygonal faces). If an oriented triangular 2-cell $\sigma = [A, B, C]$ is declared with boundary $\partial_2 \sigma = (A \to B) + (B \to C) + (C \to A)$, then $C^2 = K^{\{\sigma\}}$ and:
   $$(d_1 c)(\sigma) = c(A \to B) + c(B \to C) + c(C \to A)$$
   Edges alone do not create a 2-cell unless the 2-cell is explicitly declared in the cell complex presentation.

### 2.3 Coboundary Operators

- **$d_0: C^0 \to C^1$ (Vertex Coboundary / Repair Map):** Computes edge differences from vertex potentials:
  $$(d_0 \alpha)(u \to v) = \alpha(v) - \alpha(u)$$
- **$d_1: C^1 \to C^2$ (Face Coboundary / Closure Map):** Computes face circulations by summing edge values around declared 2-cell boundaries.
- **Nilpotence ($d_1 \circ d_0 = 0$):**
  $$(d_1(d_0 \alpha))([u, v, w]) = (\alpha(v) - \alpha(u)) + (\alpha(w) - \alpha(v)) + (\alpha(u) - \alpha(w)) = 0$$

---

## 3. Exact Repairs and the Quotient Space

Suppose an edge discrepancy pattern $x \in C^1$ is observed. Can $x$ be eliminated by adjusting vertex potentials $\alpha \in C^0$?

### 3.1 The Space of Exact Repairs: $B^1$

The subspace of edge differences that can be produced by vertex re-assignments is the image of $d_0$:
$$B^1 = \operatorname{im}(d_0) \subseteq C^1$$

If $x \in B^1$, there exists $\alpha \in C^0$ such that $x = d_0 \alpha$. The cochain $x$ is called **exact** (gauge-equivalent to zero).

### 3.2 The Quotient Space Modulo Exact Repairs: $Q^1$

Factoring out all admitted exact repairs yields the quotient vector space:
$$Q^1 = C^1 / B^1 = C^1 / \operatorname{im}(d_0)$$

Two cochains $x, y \in C^1$ define the same quotient class $[x] = [y] \in Q^1$ if and only if they differ by an exact repair:
$$[x] = [y] \iff x - y \in \operatorname{im}(d_0) \iff \exists \alpha \in C^0 \text{ such that } x = y + d_0 \alpha$$

> **Discipline Invariant (Quotient Class vs. System Obstruction):**  
> A non-zero class $[x] \ne [0] \in Q^1$ is an equivalence class modulo the declared vertex repair operator $d_0$. Calling every non-zero quotient class an "irreducible system defect" is premature: whether $[x]$ represents an irreducible obstruction to system evolution depends on the complete declared repair grammar, including external contexts, higher cells, and candidate extension operators. Within this chapter, $Q^1$ is strictly the vector space of 1-cochains modulo exact 0-coboundaries.

---

## 4. Key Takeaways

1. **Exact Repairs ($B^1 = \operatorname{im} d_0$):** Differences that can be scrubbed away by choosing a different vertex potential assignment.
2. **Quotient Space ($Q^1 = C^1 / \operatorname{im} d_0$):** Cochain classes remaining after factoring out all admitted vertex adjustments.
3. **Topological Nilpotence ($d_1 \circ d_0 = 0$):** Applying an exact repair never introduces curvature on declared 2-cells.
