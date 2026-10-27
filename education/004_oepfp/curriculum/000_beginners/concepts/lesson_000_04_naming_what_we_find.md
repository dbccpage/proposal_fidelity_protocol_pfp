# Lesson 000.04 -- Naming What We Find: Atoms and the Alphabet

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_04_naming_what_we_find.ipynb](../notebooks/lesson_000_04_naming_what_we_find.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea (For Ages 5 to 500)
- 2. Diagnostic Probe (2026 Micro-Attention Check)
- 3. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea (For Ages 5 to 500)

- **For a 5-year-old:** When you discover a cool toy, you put a name tag on it: "Dino", "0", or "1". In our symbol game, whenever we name something, we wrap the word in delimiters `<` and `>`: `<0>`, `<1>`, or `<star>`.
- **For an 11-year-old:** In programming, an **Atom** is a single named symbol. It is not broken down into smaller syntax pieces. In Grammar 000, an atom has the shape `<word>`, where the word is made of letters and digits.
- **For a university student:**
  - **Alphabet & Words:** The declared alphanumeric alphabet is $\Sigma_{36} = \{0..9, a..z\}$. Letters generate words via concatenation: `word ::= alnum+`.
  - **Atom Payloads:** An `Atom` must have a *nonempty* word payload (`len(word) >= 1`). The empty brackets `<>` are reserved exclusively for the primitive difference (`Diff`), never an empty atom.
  - **Recursive Syntax:** Packets form a recursive sum type:
    ```text
    packet ::= diff | atom | app
    diff   ::= <>
    atom   ::= <word>
    app    ::= op<packet*>
    ```
- **For a 500-year-old scholar:** [Declared] In formal language theory, $\Sigma_{36}$ generates the free monoid $\Sigma_{36}^*$. Words in $\Sigma_{36}^+$ serve as atomic labels enclosed in delimiters. Parsing Law 4 requires atomic words to draw exclusively from $\Sigma_{36}$, rejecting whitespace, punctuation, commas, or uppercase glyphs at the lexer boundary.

## 2. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What does Grammar 000 produce when given `<>` versus `<0>`?

- **A:** Both produce an `Atom`.
- **B:** `<>` produces `Diff()`, while `<0>` produces `Atom("0")`.
- **C:** `<>` is an error, while `<0>` produces an integer.

*(Correct answer: **B**. The empty delimiters `<>` yield the unique base distinction Diff. An Atom requires a nonempty word payload.)*

## 3. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Can you parse an atom called `<dinosaur>`? Test it below!
2. **Exercise 2 (Age 15):** What happens if you try to construct `Atom("")` directly? Test it in the notebook!
3. **Exercise 3 (Age 500):** Why does Grammar 000 reject uppercase characters like `<Atom>` or punctuation like `<a,b>`? *(Answer: Because the lexer enforces $\Sigma_{36} = [0-9a-z]$, guaranteeing deterministic 1-character lookahead and zero character normalization ambiguity.)*

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from pfp.domain.tower import grammar

# 1. Valid atoms
p1 = grammar.parse("<dinosaur>")
assert isinstance(p1, grammar.Atom)
assert p1.word == "dinosaur"

# 2. Empty payload rejected for Atom
try:
    grammar.Atom("")
    assert False, "Expected ValueError on empty Atom"
except ValueError as e:
    assert "nonempty" in str(e).lower()

# 3. Disallowed characters rejected
try:
    grammar.parse("<a,b>")
    assert False, "Expected GrammarError on comma"
except grammar.GrammarError as e:
    assert "unterminated" in e.reason.lower() or "expected '>'" in str(e).lower()

print("Atom syntax and payload invariants verified!")
```
</details>
