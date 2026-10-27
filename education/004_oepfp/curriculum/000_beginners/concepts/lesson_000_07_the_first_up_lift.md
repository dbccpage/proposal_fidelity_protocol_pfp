# Lesson 000.07 -- The First Up-Lift: Context Transition MSS-0 to MSS-1

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_07_the_first_up_lift.ipynb](../notebooks/lesson_000_07_the_first_up_lift.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Context Lift $u_0$ and Forgetful Projection $d_1$
- 2. Non-Descent Refusal: New Structure Cannot Silently Descend
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 and Up/Down map specifications (`updown_maps.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Context Lift $u_0$ and Forgetful Projection $d_1$

[Pinned] In the tower architecture, moving from Level 0 to Level 1 is governed by an explicit context-map pair $(u_0, d_1)$:
- **The Up-Lift ($u_0: \text{MSS-0} \to \text{MSS-1}$):**
  At MSS-0, the ONLY legal packet is the bare distinction `Diff()` (`<>`). The lift preserves `Diff` identically:
  $$u_0(\text{Diff}) = \text{Diff}.$$
  Calling $u_0$ on any packet not active at Level 0 (such as `<0>`) is an explicit precondition violation and raises `ValueError`.
- **The Down Map ($d_1: \text{MSS-1} \to \text{MSS-0} \mid \text{NonDescentReceipt}$):**
  The forgetful map retracts terms from MSS-1 back to MSS-0 when restricted to the image of $u_0$:
  $$d_1(u_0(\text{Diff})) = \text{Diff}.$$
  Identity on old structure is preserved.

[Declared] **Glyphs vs. Numbers:**
The symbols `0` and `1` introduced at MSS-1 are initially uninterpreted wire glyphs in the active binary alphabet $\{0, 1\}$. They become numerical integers only after an explicit semantic decoding interpretation (e.g. `int(atom.word, 2)`) is declared.

## 2. Non-Descent Refusal: New Structure Cannot Silently Descend

[Pinned] A critical integrity invariant of the tower is:
> *"New structure cannot silently descend as old structure."*

If the down map $d_1$ simply returned `Diff()` whenever it encountered an Atom `<0>` or an application `op<...>`, a caller could not tell whether the term genuinely was the base distinction or whether new structure was quietly coerced to look like nothing.

To prevent this silent corruption:
- On genuinely new MSS-1 structure, $d_1$ returns an explicit, typed **`NonDescentReceipt(original=packet)`**.
- A refusal is made visible, typed, and auditable.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What does $d_1(\text{Atom("0")})$ return?

- **A:** `Diff()`, coercing the new atom to the base distinction.
- **B:** `None`.
- **C:** `NonDescentReceipt(original=Atom("0"))`, making the refusal explicit and typed.

*(Correct answer: **C**. New MSS-1 structure cannot silently coerce to old MSS-0 structure; it produces a typed `NonDescentReceipt`.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you lift a plain box into Level 1, what do you have? *(Answer: The same plain box!)*
2. **Exercise 2 (Age 15):** In Python, call $d_1(u_0(\text{Diff}()))$. What is the result? Test it in the notebook!
3. **Exercise 3 (Age 500):** Try calling $u_0(\text{Atom("0")})$. What exception is raised and why? *(Answer: ValueError, because `<0>` is not active at Level 0, violating the precondition of $u_0$.)*

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from pfp.domain.tower import grammar
from pfp.domain.tower import updown_maps

diff = grammar.Diff()
atom0 = grammar.Atom("0")

# 1. Identity on old structure
lifted = updown_maps.u_0(diff)
assert lifted == diff
assert updown_maps.d_1(lifted) == diff

# 2. Non-descent on genuinely new MSS-1 structure
receipt = updown_maps.d_1(atom0)
assert isinstance(receipt, updown_maps.NonDescentReceipt)
assert receipt.original == atom0

# 3. Precondition violation on u_0
try:
    updown_maps.u_0(atom0)
    assert False, "Expected ValueError on u_0(atom0)"
except ValueError as e:
    assert "level-0-active" in str(e).lower()

print("Up-lift u0 and down map d1 invariants verified successfully!")
```
</details>
