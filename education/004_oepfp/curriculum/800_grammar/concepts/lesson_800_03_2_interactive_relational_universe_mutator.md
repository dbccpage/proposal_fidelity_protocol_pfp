# Lesson 800.03 -- 2. Interactive Relational Universe Mutator

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_800_03_2_interactive_relational_universe_mutator.ipynb](../notebooks/lesson_800_03_2_interactive_relational_universe_mutator.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Interactive Relational Universe Mutator

Use the interactive widget below to construct relational states over declared carrier alphabets.
Try adding distinct pairs $(a \to b)$, and observe what happens when you attempt to add a reflexive self-loop $(a \to a)$.

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that discrete diagonal excision $\Delta = \emptyset$ mechanically prevents self-referential tautological loops.
> - Demonstrates that relational state spaces can be deterministically enumerated and checked under finite symmetric group actions.
>
> **CANNOT-Show**:
> - Does not derive the physical nature of space-time or continuum geometry from discrete graph relations.
> - Does not prove that finite carrier alphabets are sufficient to represent all continuous mathematical theories.

## 4. Student Exercises

### Exercise 01.1: Arity Combinatorics
Given a carrier alphabet of $n = 3$ symbols $\{a, b, c\}$, how many non-reflexive directed pairs $(u, v)$ can be formed under diagonal excision?

<details>
<summary><b>Click to reveal solution</b></summary>
Total pairs in $V \times V$ is $n^2 = 3^2 = 9$.
The diagonal $\Delta = \{(a,a), (b,b), (c,c)\}$ has $n = 3$ pairs.
Under diagonal excision, the number of valid irreflexive relations is $n^2 - n = 9 - 3 = 6$ pairs: $(a,b), (a,c), (b,a), (b,c), (c,a), (c,b)$.
</details>

## 5. Anchors

- **Paper 032 Sections**: §2.1–§2.3
- **Ledger IDs**: `PO032-C04` through `PO032-C08`
- **Code**: `notebook_lib/governor_adapter.py`, `0_research_briefs/01_mss0_core_axioms_and_exhaustion.md`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `01_mss0_to_sn_relational_foundations`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/grammar/readme.md](../../../../../research/mssn_sn_tower/grammar/readme.md)
- [research/mssn_sn_tower/grammar/0_grammar.md](../../../../../research/mssn_sn_tower/grammar/0_grammar.md)
- [research/mssn_sn_tower/grammar/1_grammar.md](../../../../../research/mssn_sn_tower/grammar/1_grammar.md)

Frontier sitting already on disk: [N0_the_genesis_distinction.md](../../600_mssn_frontier/N0_the_genesis_distinction/N0_the_genesis_distinction.md). It is a different folder. This lesson does not replace it.
