# Lesson 000.08 -- Tree Branches from Brackets: AST Tree Structures

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_08_tree_branches_from_brackets.ipynb](../notebooks/lesson_000_08_tree_branches_from_brackets.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Nested Packets as Ordered Syntax Trees
- 2. Tree Traversal, Depth, and Leaves
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Nested Packets as Ordered Syntax Trees

[Declared] In Grammar 000, application boxes can contain other applications as children. This recursive nesting creates an **Ordered Abstract Syntax Tree (AST)**:
- **Leaf nodes**:
  - **Structural leaves**: Any terminal node with no children: `Diff()`, `Atom(word)`, and childless `App(())` (`op<>`).
  - **Data leaves**: Terminal nodes carrying payload or ground distinction: `Diff()` and `Atom(word)`.
- **Branch nodes**: `App(children)` nodes holding an ordered tuple of subtrees.

Consider the nested wire string:
```text
op<<0>op<<1><>>>
```
This produces an AST with:
- Root: `App`
  - Child 0: `Atom("0")` (leaf)
  - Child 1: `App` (branch)
    - Sub-child 0: `Atom("1")` (leaf)
    - Sub-child 1: `Diff()` (leaf)

## 2. Tree Traversal, Depth, and Leaves

[Executed] We can analyze the structural properties of any packet tree:
- **Tree Depth (App Nesting Depth)**: The maximum nesting depth of `App` nodes (depth 0 for an Atom or Diff; depth 1 for childless `App(())`; depth 2 for `op<<0>op<<1><>>>`).
- **Leaf Count**: The total number of terminal Diff and Atom nodes across the entire tree.
- **Node Count**: The total number of nodes (branches + leaves).

Every nested packet is an ordered tree that serializes back deterministically without loss of structure or ordering.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** In the packet `op<<0>op<<1><>>>`, how many total leaves (terminal nodes) exist?

- **A:** 2 leaves: `<0>` and `<1>`.
- **B:** 3 leaves: `<0>`, `<1>`, and `<>`.
- **C:** 4 leaves.

*(Correct answer: **B**. `Diff()` is an actual terminal node of the AST, so the leaves are `<0>`, `<1>`, and `<>`.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Look at a tree with two main branches. Each branch has twigs. Can you draw a tree for `op<<branch1><branch2>>`?
2. **Exercise 2 (Age 15):** Parse `op<op<<0>>op<<1>>>`. What is its depth, and what are its children? Test it in the notebook!
3. **Exercise 3 (Age 500):** Write a recursive function `collect_leaves(packet)` and verify that it extracts all terminal nodes in strict left-to-right order.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from pfp.domain.tower import grammar

packet = grammar.parse("op<<0>op<<1><>>>")

def collect_leaves(p):
    if isinstance(p, (grammar.Diff, grammar.Atom)):
        return [p]
    leaves = []
    for c in p.children:
        leaves.extend(collect_leaves(c))
    return leaves

def tree_depth(p):
    if not isinstance(p, grammar.App) or not p.children:
        return 0
    return 1 + max(tree_depth(c) for c in p.children)

leaves = collect_leaves(packet)
assert len(leaves) == 3
assert isinstance(leaves[0], grammar.Atom) and leaves[0].word == "0"
assert isinstance(leaves[1], grammar.Atom) and leaves[1].word == "1"
assert isinstance(leaves[2], grammar.Diff)
assert tree_depth(packet) == 2

print("Tree branches and leaf extraction verified successfully!")
```
</details>
