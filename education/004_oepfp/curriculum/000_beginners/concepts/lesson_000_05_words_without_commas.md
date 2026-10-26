# Lesson 000.05 -- Words Without Commas: Self-Delimiting Syntax

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_05_words_without_commas.ipynb](../notebooks/lesson_000_05_words_without_commas.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea (For Ages 5 to 500)
- 2. Diagnostic Probe (2026 Micro-Attention Check)
- 3. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 specifications (Parsing Laws 1, 5, and 6).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea (For Ages 5 to 500)

- **For a 5-year-old:** When you snap toys into plastic eggs: `(egg)(egg)(egg)`, you do not need tape between them to know where one egg ends and the next begins. Each egg has its own shell.
- **For an 11-year-old:** In Python lists, we write commas: `[apple, banana, cherry]`. But if every item is enclosed in its own delimiters, like `op<<apple><banana><cherry>>`, the closing delimiter `>` tells you the child is finished, and the next `<` or `op<` tells you a new one is starting. Inside an application box, commas are redundant.
- **For a university student:**
  - **Parsing Law 5:** *"Siblings require no commas because every child is self-delimiting."* Every packet is either `<>` (`Diff`), `<word>` (`Atom`), or `op<...>` (`App`).
  - **Parsing Law 1:** A valid wire stream represents *exactly one* outer packet. Thus, writing multiple sibling tokens at top level, such as `<0><1>`, is an immediate syntax violation (trailing content after outer packet). To hold siblings, they must be wrapped inside an application box: `op<<0><1>>`.
  - **Round-Trip Property:** While testing `serialize(parse(x)) == x` on a single fixture demonstrates correctness for that fixture, establishing it for arbitrary nesting requires structural induction over the three grammar productions (`Diff`, `Atom`, `App`).
- **For a 500-year-old scholar:** [Declared] In formal grammar, bracketed Polish prefix notation ensures that every subterm uniquely encodes its own termination. Because each child recursively consumes its own delimiters, the parser requires exactly one character of lookahead without ambiguous backtracking.

## 2. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What does Grammar 000 do if given `<0><1>` at the top level without an outer `op<...>` box?

- **A:** It parses both as a list of two atoms.
- **B:** It raises `GrammarError` because Parsing Law 1 forbids trailing content after the first outer packet.
- **C:** It automatically wraps them into an `op<...>`.

*(Correct answer: **B**. Top-level input must be exactly one complete outer packet. Multiple siblings must be grouped inside `op<<0><1>>`.)*

## 3. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Count the children inside `op<<cat><dog><mouse>>`. *(Answer: Exactly 3 children!)*
2. **Exercise 2 (Age 15):** Try parsing `op<<0>,<1>>` (with a comma). Verify the exact `GrammarError` raised!
3. **Exercise 3 (Age 500):** Verify by structural induction and test execution that `serialize(parse(x)) == x` holds for `Diff`, `Atom`, and nested `App`.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from omega_engine_pfp.domain.tower import grammar

# 1. Parsing siblings inside an App
app = grammar.parse("op<<0><1>>")
assert isinstance(app, grammar.App)
assert len(app.children) == 2
assert app.children[0].word == "0"
assert app.children[1].word == "1"

# 2. Parsing Law 1: top-level multiple packets rejected
try:
    grammar.parse("<0><1>")
    assert False, "Expected GrammarError for multiple top-level packets"
except grammar.GrammarError as e:
    assert "more than one outer packet" in e.reason

# 3. Comma rejected inside App
try:
    grammar.parse("op<<0>,<1>>")
    assert False, "Expected GrammarError for comma inside App"
except grammar.GrammarError as e:
    assert "unterminated" in e.reason.lower() or "bare content" in e.reason.lower()

print("Self-delimiting syntax and Parsing Law 1 verified successfully!")
```
</details>
