# Lesson 000.10 -- The Stage Gatekeeper: Syntax vs. Level Activation

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_10_the_stage_gatekeeper.ipynb](../notebooks/lesson_000_10_the_stage_gatekeeper.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Three Tiers of Validity
- 2. Level Activation: MSS-0 and MSS-1 Gates
- 3. Scope Map: Transition from Grammar to Graph Cochains
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 specifications (`grammar.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Three Tiers of Validity

[Pinned] In the tower architecture, an expression must pass three distinct verification tiers:
1. **Raw Syntactic Validity (`parse`):** Is the string a well-formed Grammar 000 packet? For example, `<2>` is syntactically well-formed (an `Atom` with word `"2"` over $\Sigma_{36}$).
2. **Context Level Activation (`is_active_at_level`):** Is the packet admitted at the declared stage $n$?
   - **Level 0 (MSS-0):** The ONLY admitted packet is `Diff()` (`<>`). All Atoms and Apps are inactive.
   - **Level 1 (MSS-1):** Active alphabet is strictly binary `{"0", "1"}`. An atom `<2>` parses syntactically, but is **inactive** at Level 1 because `'2'` is outside `{0, 1}`.
   - **Undeclared Levels ($n \ge 2$):** Calling `is_active_at_level(p, n)` raises `ValueError`, because higher levels are governed by explicit algebraic and geometric opcodes, not an unconstrained tower of arbitrary alphabets.
3. **Semantic Validity:** Does the packet satisfy operation-specific contracts (e.g. valid graph topologies, non-increase in defect, or conservation laws)?

## 2. Level Activation: MSS-0 and MSS-1 Gates

| Packet | Syntax Valid? | Active at Level 0? | Active at Level 1? |
| :--- | :--- | :--- | :--- |
| `<>` (`Diff`) | Yes | **Yes** | **Yes** |
| `<0>` (`Atom`) | Yes | **No** (Atoms forbidden at L0) | **Yes** |
| `<1>` (`Atom`) | Yes | **No** | **Yes** |
| `<2>` (`Atom`) | Yes | **No** | **No** (Glyph '2' not in binary alphabet) |
| `op<<0>>` (`App`) | Yes | **No** (Apps forbidden at L0) | **Yes** |

## 3. Scope Map: Transition from Grammar to Graph Cochains

[Declared] **Pedagogical Scope & Boundary Transition:**
Lessons 01 through 10 investigated the foundational **syntactic and context levels** of Grammar 000 (tokens, ASTs, $u_0/d_1$ maps, and level gates).

Starting in **Lesson 11**, the curriculum transitions into **discrete chains, cochains, and graph obstruction theory**:
- **The Graph Adapter:** In Lessons 11–19, we study simplicial complexes, directed edges, 1-cycles, and 1-cochains with coefficients in $\mathbb{Q}$.
- **Status of the Model:** The graph/cochain calculus is a **declared educational adapter**. It is not an automatic algebraic entailment forced by raw grammar alone, nor does it define the complete S(n) tower. It provides the concrete playground where section defects $D$, boundary operators $\partial_1$, coboundary operators $d^0$, and primary obstructions $\Phi_1$ are computed with exact arithmetic.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What happens if you run `is_active_at_level(parse("<2>"), level=1)`?

- **A:** It returns `True`, because `2` is an alphanumeric character.
- **B:** It raises `GrammarError`.
- **C:** It returns `False`, because the declared active alphabet for Level 1 is binary `{"0", "1"}`.

*(Correct answer: **C**. `<2>` parses as valid syntax, but is rejected by the Level 1 activation gate.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Can a red toy go through a gate that only allows green toys?
2. **Exercise 2 (Age 15):** Test `is_active_at_level` on `<>` and `<0>` at level 0. Verify the exact boolean returned!
3. **Exercise 3 (Age 500):** Verify that calling `is_active_at_level(packet, level=2)` raises `ValueError` declaring that higher levels are not governed by raw alphabet extension.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from omega_engine_pfp.domain.tower import grammar

diff = grammar.parse("<>")
atom0 = grammar.parse("<0>")
atom2 = grammar.parse("<2>")

# 1. Level 0 gate
assert grammar.is_active_at_level(diff, 0) is True
assert grammar.is_active_at_level(atom0, 0) is False

# 2. Level 1 binary gate
assert grammar.is_active_at_level(diff, 1) is True
assert grammar.is_active_at_level(atom0, 1) is True
assert grammar.is_active_at_level(atom2, 1) is False  # '2' outside {'0', '1'}

# 3. Undeclared level raises ValueError
try:
    grammar.is_active_at_level(diff, 2)
    assert False, "Expected ValueError on undeclared level 2"
except ValueError as e:
    assert "no declared active alphabet for level 2" in str(e).lower()

print("Stage gatekeeper and level activation verified successfully!")
```
</details>
