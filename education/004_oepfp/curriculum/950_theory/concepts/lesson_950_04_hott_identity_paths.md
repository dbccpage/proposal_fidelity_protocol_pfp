# Lesson 950.04 -- 1. Homotopy Type Theory (HoTT) View of Mathematical Deductions

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_950_04_hott_identity_paths.ipynb](../notebooks/lesson_950_04_hott_identity_paths.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 07 - Constructive HoTT Identity Paths & Primitive Difference

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: established by a machine-checked Lean 4 theorem with reported kernel axioms.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Homotopy Type Theory Identity Types, Symmetry Involution, and the Quotient Setoid*

---

## 1. Homotopy Type Theory (HoTT) View of Mathematical Deductions

In standard set theory, equality $x = y$ is a static truth value (True or False). In **Homotopy Type Theory (HoTT)**, equality is an **Identity Type** $\text{Id}_A(x, y)$, whose terms are **paths** (witnesses or proofs) connecting $x$ to $y$:
$$p: x =_A y$$

### Why LLM Embeddings Hallucinate Equivalence
Dense language models compute similarity using cosine distance in $\mathbb{R}^d$:
$$\text{sim}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$
Because vector space is continuous, distinct concepts with high cosine similarity easily blur together, producing false equivalences without proof witnesses.

In the Symbol Game:
1. **Paths are Witnesses**: Two states are equivalent only if an explicit, constructive path connects them.
2. **Symmetry Involution**: Every path $p: x = y$ has a formal inverse $p^{-1}: y = x$, satisfying $(p^{-1})^{-1} = p$.
3. **Path Concatenation**: Paths compose via transitivity: $p \cdot q: x = z$.

## 2. Machine-Checked Lean 4 Proof

The HoTT identity path properties are formalized and verified in Lean 4:
- **Source**: `lean4/IdentityTypes.lean`
- **Theorem**: `IdentityTypes.symm_involution`: `(symm (symm p)) = p`
- **Theorem**: `IdentityTypes.trans_assoc`: `(trans (trans p q) r) = (trans p (trans q r))`

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that HoTT identity paths provide explicit, checkable witnesses of deduction transitions.
> - Demonstrates that constructive path operations obey symmetry involution and transitivity.
>
> **CANNOT-Show**:
> - Does not claim that higher homotopy groups ($\pi_n(S^3)$) are computed by this finite graph path algebra.

## 4. Student Exercises

### Exercise 07.1: Path Composition
Given path $p: A \to B$ and path $q: C \to D$, can they be composed? Under what exact condition is composition defined?

<details>
<summary><b>Click to reveal solution</b></summary>
No, they cannot be composed in general. Path composition $p \cdot q$ is defined if and only if the target of the first path matches the source of the second path ($B = C$).
</details>

## 5. Anchors

- **Paper 032 Sections**: §3.2, §6
- **Ledger IDs**: `PO032-C43` through `PO032-C48`
- **Code**: `papers/032.../code/hott_symbol_game.py`
- **Lean 4**: `lean4/IdentityTypes.lean`

## Anchors

- Former notebook: `07_constructive_hott_identity_paths`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/_theory/README.md](../../../../../research/mssn_sn_tower/_theory/README.md)
- [research/mssn_sn_tower/_theory/03_the_symbol_game.md](../../../../../research/mssn_sn_tower/_theory/03_the_symbol_game.md)
- [research/mssn_sn_tower/_theory/09_authority_fences.md](../../../../../research/mssn_sn_tower/_theory/09_authority_fences.md)
- [research/mssn_sn_tower/math/symbol_game/0_math_primitive_difference_and_distinction.md](../../../../../research/mssn_sn_tower/math/symbol_game/0_math_primitive_difference_and_distinction.md)
