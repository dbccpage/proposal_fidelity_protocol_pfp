# Lesson 800.02 -- 1. The Historical Roots: MSS-0 and the Genesis of Distinction

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_800_02_1_historical_roots_mss_0_genesis_distinction.ipynb](../notebooks/lesson_800_02_1_historical_roots_mss_0_genesis_distinction.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 01 - From MSS-0 to S_n Relational State Spaces

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Carrier Marks, Arity Stages (S_0 ... S_5), Irreflexivity, and Diagonal Excision*

---

## 1. The Historical Roots: MSS-0 and the Genesis of Distinction

Grammar 1 says the normative level-0 packet is only `<>`. That wire is lesson 800.01.
This sitting does not parse it. The check is one refused self-loop.
Grammar 0 records that a witnessed basic relation is strictly irreflexive. A vertex set is not MSS-0.

### The Principle of Irreflexivity and Diagonal Excision
A fundamental invariant of relational deduction is **diagonal excision**:
$$\Delta = \{(x, x) \mid x \in V\} = \emptyset$$
Self-loops $(x \to x)$ are strictly excised from valid relational carrier states. A relation must connect distinct carrier tokens to prevent vacuous tautological loops ($x = x$).

## Anchors

- Former notebook: `01_mss0_to_sn_relational_foundations`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

This check matches the irreflexivity sentence in `research/mssn_sn_tower/grammar/0_grammar.md`. It is not Grammar 1's void packet.
