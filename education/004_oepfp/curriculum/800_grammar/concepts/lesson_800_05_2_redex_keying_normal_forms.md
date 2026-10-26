# Lesson 800.05 -- 2. Redex Keying and Normal Forms

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_800_05_2_redex_keying_normal_forms.ipynb](../notebooks/lesson_800_05_2_redex_keying_normal_forms.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Redex Keying and Normal Forms

A term $t$ is in **Normal Form** if no reduction rule applies ($t \not\to$).
In the Symbol Game, the Layer 3 Host verifies that:
1. Every intermediate rewrite cites an admitted rule in the active contract.
2. No rewrite revisits a previously traversed state hash (cycle prevention).
3. The final token lands deterministically on an irreducible normal form or an explicit `REFUSE`.

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that hash-chained redex keying prevents infinite reduction cycles.
> - Demonstrates that confluent rewrite rules yield unique normal forms modulo $S_n$ permutations.
>
> **CANNOT-Show**:
> - Does not show that all arbitrary rewrite systems are terminating (undecidable by the Halting Problem).
> - Does not prove that an LLM will autonomously discover the optimal reduction path without host guidance.

## 4. Student Exercises

### Exercise 02.1: Termination Arguments
Why is a reduction relation guaranteed to terminate if there exists a well-founded monotone measure $\mu: A \to \mathbb{N}$ such that $x \to y \implies \mu(x) > \mu(y)$?

<details>
<summary><b>Click to reveal solution</b></summary>
Because the natural numbers $\mathbb{N}$ under the standard ordering are well-founded: there cannot exist an infinite strictly decreasing sequence $n_0 > n_1 > n_2 > \dots$ of non-negative integers. Therefore, any reduction sequence must terminate in at most $\mu(x_0)$ steps.
</details>

## 5. Anchors

- **Paper 032 Sections**: §2.4–§2.5
- **Ledger IDs**: `PO032-C09` through `PO032-C14`
- **Code**: `papers/032.../code/arity_rewrite_engine.py`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `02_arity_filtration_and_ars_rewriting`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/grammar/readme.md](../../../../../research/mssn_sn_tower/grammar/readme.md)
- [research/mssn_sn_tower/grammar/0_grammar.md](../../../../../research/mssn_sn_tower/grammar/0_grammar.md)
- [research/mssn_sn_tower/grammar/1_grammar.md](../../../../../research/mssn_sn_tower/grammar/1_grammar.md)
- [research/mssn_sn_tower/grammar/11_grammar.md](../../../../../research/mssn_sn_tower/grammar/11_grammar.md)
- [research/mssn_sn_tower/math/symbol_game/11_math_relational_arities_and_distinctions.md](../../../../../research/mssn_sn_tower/math/symbol_game/11_math_relational_arities_and_distinctions.md)
