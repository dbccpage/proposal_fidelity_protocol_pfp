# Lesson 000.09 -- Reading with One Eye Open: Recursive-Descent Parsing

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_09_reading_with_one_eye_open.ipynb](../notebooks/lesson_000_09_reading_with_one_eye_open.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: One-Character Lookahead and Reserved Prefixes
- 2. Maximal Recognition: `<op>` vs. `op<...>`
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 specifications (Parsing Laws 5 and 6).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: One-Character Lookahead and Reserved Prefixes

[Pinned] Why is Grammar 000 called "reading with one eye open"?
Because a recursive-descent parser requires **at most one choice inspection** at every position in the wire stream:
1. **Application Check:** Look at the next 3 characters. If they match the literal reserved prefix `op<`, consume `op<` and parse children until `>`.
2. **Atom / Diff Check:** If the next character is `<`, consume `<` and read an alphanumeric word run until `>`. If the word is empty, produce `Diff()`; otherwise produce `Atom(word)`.
3. **Syntax Error:** If the next character is neither `op<` nor `<`, the parser halts immediately with a `GrammarError` flagging bare, unwrapped content.

Because every child is self-delimiting, the parser needs zero global bracket counting or complex backtracking.

## 2. Maximal Recognition: `<op>` vs. `op<...>`

[Pinned] Parsing Law 6 requires maximal recognition of the reserved prefix:
- `op<>` begins with `op<`, so it is parsed as an empty application `App(())`.
- `<op>` begins with `<`, so it is parsed as an `Atom(word="op")`.
- `op<<0>>` is an application holding child `<0>`.

### Error Localization with `GrammarError`
When an input violates grammar rules, `GrammarError` records:
- The exact zero-indexed character position where failure was detected (`e.position`).
- An honest mechanical diagnostic reason (`e.reason`).

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What does Grammar 000 produce when parsing `<op>` versus `op<>`?

- **A:** Both produce the same application.
- **B:** `<op>` produces `Atom("op")`, while `op<>` produces `App(())`.
- **C:** `<op>` is an invalid reserved keyword.

*(Correct answer: **B**. Because `<op>` starts with `<`, the prefix `op` is inside the atom delimiters. `op<>` starts with the reserved prefix `op<`, creating an App.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Can you tell the difference between a box labelled `<cat>` and an open box `op<<cat>>`?
2. **Exercise 2 (Age 15):** If you pass `"<unterminated"` to `grammar.parse()`, at what character position does the parser report the error? Test it in the notebook!
3. **Exercise 3 (Age 500):** Verify that the parser rejects unclosed applications like `op<<0>` and detects trailing characters after outer packets like `<0>extra`.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from omega_engine_pfp.domain.tower import grammar

# 1. Distinguishing <op> from op<>
atom_op = grammar.parse("<op>")
app_op = grammar.parse("op<>")
assert isinstance(atom_op, grammar.Atom) and atom_op.word == "op"
assert isinstance(app_op, grammar.App) and len(app_op.children) == 0

# 2. Syntax error localization
try:
    grammar.parse("<unterminated")
    assert False, "Expected GrammarError"
except grammar.GrammarError as e:
    assert e.position == 13
    assert "unterminated" in e.reason.lower()

# 3. Unclosed application detection
try:
    grammar.parse("op<<0>")
    assert False, "Expected GrammarError"
except grammar.GrammarError as e:
    assert "unclosed application" in e.reason.lower()

print("Parser lookahead and error reporting verified successfully!")
```
</details>
