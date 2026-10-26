# Lesson 800.04 -- 1. Abstract Reduction Systems (ARS)

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_800_04_1_abstract_reduction_systems_ars.ipynb](../notebooks/lesson_800_04_1_abstract_reduction_systems_ars.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 02 - Arity Filtration and the Abstract Reduction System

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: established by a machine-checked Lean 4 theorem with reported kernel axioms.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Redex Matching, Substitution Modulo Group Action, and Finite Termination*

---

## 1. Abstract Reduction Systems (ARS)

In mathematical deduction, rewriting is modeled by an **Abstract Reduction System** $(A, \to)$, where $A$ is the set of symbolic terms and $\to \subseteq A \times A$ is the reduction relation.

When language models perform chain-of-thought (CoT) reasoning, they frequently fall into infinite loops or circular rewrites ($t_1 \to t_2 \to \dots \to t_1$) because token generation lacks cycle detection.

The Symbol Game resolves this via:
1. **Redex-Keyed Identification**: Every reduction step is keyed by an exact redex pattern $(l \to r)$ and substitution $\sigma$.
2. **Action Modulo Symmetric Group $S_n$**: Relational terms are normalized under carrier permutations so isomorphic states share the same canonical key.
3. **Strict Arity Filtration**: Reductions must strictly decrease term weight or contract the carrier defect:
   $$W(t_{k+1}) < W(t_k)$$

## Anchors

- Former notebook: `02_arity_filtration_and_ars_rewriting`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

This sitting checks one string rewrite, `f(g(x))` to `f(x)` to `x`. It does not build a polygraph packet.
