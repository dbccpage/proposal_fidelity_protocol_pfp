# Lesson 000.03 -- The Law of Crossing: Two Marks Disappear

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_03_the_law_of_crossing.ipynb](../notebooks/lesson_000_03_the_law_of_crossing.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea (For Ages 5 to 500)
- 2. Diagnostic Probe (2026 Micro-Attention Check)
- 3. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from Spencer-Brown *Laws of Form* and Grammar 000 specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea (For Ages 5 to 500)

- **For a 5-year-old:** If you take one step forward over a jump-rope, you are on the OTHER side. If you take another step forward over the jump-rope, you are back where you started! Two crossings cancel out.
- **For an 11-year-old:** In Python, if you have `x = True`, what is `not x`? It is `False`. What is `not (not x)`? It is `True` again! Inverting twice returns you to the original state. Negation is an involution: it restores the initial value, whether initially True or False.
- **For a university student:**
  - In Boolean algebra and George Spencer-Brown's *Laws of Form*, the mark represents distinction/negation.
  - **The Law of Calling:** Idempotence of calling ($\rceil \rceil = \rceil$, or $A \lor A = A$).
  - **The Law of Crossing (Involution):** Crossing twice restores the original state ($\overline{\overline{x}} = x$, or $\neg \neg A = A$). If the initial state was unmarked, two crossings return to the unmarked state; if the initial state was marked, two crossings return to the marked state.
  - **Syntax vs. Semantics:** In Grammar 000 syntax, nested application tokens such as `op<op<<>>>` do *not* automatically erase themselves during parsing. The AST faithfully preserves both nested `App` layers. Double-cross cancellation is an external semantic rewrite rule, not a syntactic parsing side-effect.
- **For a 500-year-old scholar:** [Declared] An involution on a set $X$ is a map $\mathcal{I}: X \to X$ satisfying $\mathcal{I}^2 = \mathrm{id}_X$. In algebraic cancellations over a declared closed pairing domain with equal magnitudes and opposite signs, pairing $x$ with $\mathcal{I}(x)$ such that $w(\mathcal{I}(x)) = -w(x)$ drives exact cancellation: $w(x) + w(\mathcal{I}(x)) = 0$. Sign reversal alone does not establish cancellation of arbitrary unequal weights.

## 2. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If you apply the Law of Crossing $\overline{\overline{s}} = s$ to an already marked state $s = \text{Marked}$, what is the result?

- **A:** The unmarked state, because double crossing always clears to empty.
- **B:** The marked state, because involution returns the original state $s$.
- **C:** A syntax error.

*(Correct answer: **B**. Involution $\mathcal{I}^2 = \mathrm{id}$ restores the original state $s$, not necessarily the unmarked state.)*

## 3. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you flip a light switch 2 times, is the light in its original state? What if you flip it 3 times?
2. **Exercise 2 (Age 15):** Does parsing `op<op<<>>>` in Grammar 000 simplify to `<>`? Test it below to verify syntactic preservation vs semantic cancellation!
3. **Exercise 3 (Age 500):** Given a finite state set $X = \{A, B\}$ with involution $\mathcal{I}(A) = B, \mathcal{I}(B) = A$ and signed weights $w(A) = +5, w(B) = -5$, verify that $\sum_{x \in X} w(x) = 0$. Show that if $w(B) = -4$, cancellation fails.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from pfp.domain.tower import grammar

# 1. Syntactic preservation: nested Apps are preserved in AST
packet = grammar.parse("op<op<<>>>")
assert isinstance(packet, grammar.App)
assert isinstance(packet.children[0], grammar.App)
assert isinstance(packet.children[0].children[0], grammar.Diff)

# 2. Signed pairing cancellation
weights = {"A": 5, "B": -5}
involution = {"A": "B", "B": "A"}
assert all(involution[involution[k]] == k for k in involution)
assert sum(weights.values()) == 0

# 3. Unequal weights fail cancellation
broken_weights = {"A": 5, "B": -4}
assert sum(broken_weights.values()) != 0
print("Involution and signed pairing verified successfully!")
```
</details>
