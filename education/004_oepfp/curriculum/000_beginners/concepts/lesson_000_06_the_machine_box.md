# Lesson 000.06 -- The Machine Box: Applications and Grouping

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_06_the_machine_box.ipynb](../notebooks/lesson_000_06_the_machine_box.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: The Application Box `op<...>`
- 2. Syntactic Grouping vs. Operad Laws
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: The Application Box `op<...>`

[Declared] In Grammar 000, the third packet form is the **Application Box**:
```text
op<packet*>
```
- It begins with the reserved three-character prefix `op<` and closes with `>`.
- Inside the box, it holds zero or more child packets in strict linear sequence.
- An application with zero children is written `op<>` (the empty application).
- An application can hold any combination of `Diff`, `Atom`, and nested `App` children.

### Opcode and Arguments Convention
By convention in Grammar 000:
- If `children` is nonempty and the first child is an `Atom`, its word is called the **opcode**:
  `p.opcode == p.children[0].word`.
- The remaining children `p.children[1:]` are the **arguments**.
- The **arity** of the application is the number of arguments: `len(p.arguments)`.
- For example, `op<<add><1><0>>` has opcode `"add"`, 2 arguments (`<1>`, `<0>`), and arity 2.

## 2. Syntactic Grouping vs. Operad Laws

[Declared] **Pedagogical Boundary:**
- An application box `App(children)` is a purely **syntactic grouping tree node**.
- Parsing `op<...>` groups children into an ordered tuple. It does *not* by itself evaluate an algebraic operation, reduce a function, or enforce operadic composition laws.
- Operad substitution laws, typing relations, and reduction semantics are external evaluation models defined in downstream runtime engines.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What AST does Grammar 000 produce when parsing `op<>`?

- **A:** `Diff()`, because the inside is empty.
- **B:** `App(())`, an application node with an empty tuple of children.
- **C:** A syntax error, because an application must have at least one child.

*(Correct answer: **B**. The production is `app ::= op<packet*>`, admitting zero children. `op<>` parses as `App(children=())`.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you put three toys inside an application box: `op<<toy1><toy2><toy3>>`, how many children does the box have? *(Answer: 3 children!)*
2. **Exercise 2 (Age 15):** Parse `op<<mul><2><3>>`. What is its opcode, its arity, and its arguments?
3. **Exercise 3 (Age 500):** Verify that `App` enforces immutability and preserves child ordering: `op<<0><1>>` is not equal to `op<<1><0>>`.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from omega_engine_pfp.domain.tower import grammar

# 1. Empty application
empty_app = grammar.parse("op<>")
assert isinstance(empty_app, grammar.App)
assert len(empty_app.children) == 0

# 2. Multi-child application with opcode and arguments
app = grammar.parse("op<<mul><2><3>>")
assert isinstance(app, grammar.App)
assert app.opcode == "mul"
assert app.arity() == 2
assert [c.word for c in app.arguments] == ["2", "3"]

# 3. Order sensitivity
app_rev = grammar.parse("op<<mul><3><2>>")
assert app != app_rev
print("Application box invariants verified successfully!")
```
</details>
