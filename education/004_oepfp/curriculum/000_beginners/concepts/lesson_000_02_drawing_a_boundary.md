# Lesson 000.02 -- Drawing a Boundary: Inside vs Outside

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_02_drawing_a_boundary.ipynb](../notebooks/lesson_000_02_drawing_a_boundary.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea (For Ages 5 to 500)
- 2. Diagnostic Probe (2026 Micro-Attention Check)
- 3. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 and geometric specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea (For Ages 5 to 500)

- **For a 5-year-old:** If you draw a straight line on the sidewalk with chalk, you can walk around either side of it. If you draw two straight lines that meet, you have a corner, but the sidewalk is still open. But if you connect three lines, click-click-click, you have a **triangle**! Now there is an inside (where you can trap a pebble) and an outside.
- **For an 11-year-old:** What is the fewest number of straight line segments needed to enclose a 2D shape in a flat plane? One line cannot do it. Two lines only make an angle. Three lines make a triangle. A nondegenerate simple polygon with straight edges in the Euclidean plane requires at least 3 segments to enclose a finite area.
- **For a university student:** In algebraic topology:
  - A point is a 0-simplex.
  - A directed segment connecting two points is a 1-simplex $e = (u, v)$ with boundary $\partial_1 e = v - u$.
  - Three points connected by three line segments form a 1-cycle $z = e_0 + e_1 + e_2$ only when consistently oriented, so that $\partial_1 z = (v_1 - v_0) + (v_2 - v_1) + (v_0 - v_2) = 0$.
  - **Boundary vs. Filling:** The boundary 1-skeleton (perimeter) of a triangle has Euler characteristic $\chi = V - E = 3 - 3 = 0$. When the 2-cell (interior face) is filled, the filled triangle has $\chi = V - E + F = 3 - 3 + 1 = 1$. (A compact enclosed region like an annulus also has $\chi = 0$; compact enclosure does not require non-zero Euler characteristic.)
- **For a 500-year-old scholar:** [Declared] In Euclidean plane geometry $\mathbb{R}^2$, two intersecting lines partition the affine plane into four unbounded planar wedges. Enclosure of a bounded planar polygon with straight boundary edges requires at least 3 supporting lines. The boundary 1-cycle $z$ is closed ($\partial_1 z = 0$), forming the carrier for 1-cochains and discrete obstruction theory.

## 2. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Why can two straight lines never enclose a finite bounded area in the Euclidean plane $\mathbb{R}^2$?

- **A:** Because straight lines are infinitely thin.
- **B:** Two straight lines either never intersect (parallel) or intersect at at most one point, leaving the opposite region open to infinity.
- **C:** They could enclose a region if the Euler characteristic were zero.

*(Correct answer: **B**. In Euclidean plane geometry, two straight lines intersect at at most one point. A minimum of three straight line segments is required to form a closed polygon.)*

## 3. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Count the corners and the sides of a triangle. Are they the same number? *(Answer: Yes, 3 corners and 3 sides!)*
2. **Exercise 2 (Age 15):** Calculate the Euler characteristic of: (a) the boundary 1-skeleton of a triangle ($V - E$), and (b) the filled triangle ($V - E + F$).
3. **Exercise 3 (Age 500):** For three edges $e_0 = (0, 1), e_1 = (1, 2), e_2 = (2, 0)$, verify that the oriented sum $z = e_0 + e_1 + e_2$ satisfies $\partial_1 z = 0$, whereas unoriented $e_0 + e_1 - e_2$ fails.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
# 1. Euler characteristics
chi_skeleton = 3 - 3       # V - E = 0 (boundary 1-skeleton)
chi_filled = 3 - 3 + 1     # V - E + F = 1 (filled 2-simplex)
assert chi_skeleton == 0
assert chi_filled == 1

# 2. Oriented boundary cycle
edges = [(0, 1), (1, 2), (2, 0)]
boundary = {0: 0, 1: 0, 2: 0}
for u, v in edges:
    boundary[u] -= 1
    boundary[v] += 1
assert boundary == {0: 0, 1: 0, 2: 0}
print("Boundary orientation and Euler characteristics verified!")
```
</details>
