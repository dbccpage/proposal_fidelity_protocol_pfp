# Lesson 000.17 -- Flattening the Slope: Section Defect $D$ vs. Gauge Obstruction $\Phi_1$

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_17_flattening_the_slope.ipynb](../notebooks/lesson_000_17_flattening_the_slope.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. Section Defect $D_c(s)$ vs. Primary Obstruction $\Phi_1([c])$
- 2. Section Moves (CUT) vs. Relational Repairs
- 3. Governor Admission Policy: Monotonic Defect Non-Increase
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Symbol Game governor specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. Section Defect $D_c(s)$ vs. Primary Obstruction $\Phi_1([c])$

[Pinned] To understand the Symbol Game, we must rigorously distinguish two different quantities:
1. **The Section Defect $D_c(s)$ (Representative $L_1$ Defect):**
   Given fixed edge claims $c$ and a chosen vertex section potential $s: V \to \mathbb{Q}$:
   $$D_c(s) = \sum_{e=(u,v)} w_e |c_e - (s(v) - s(u))|.$$
   $D_c(s)$ measures how poorly the current vertex section $s$ explains the edge claims $c$.
2. **The Primary Obstruction $\Phi_1([c])$ (Gauge-Invariant Minimum):**
   $$\Phi_1([c]) = \min_{s \in C^0} D_c(s).$$
   $\Phi_1([c])$ is the irreducible topological and algebraic obstruction of the entire gauge equivalence class $[c]$.

[Declared] **Key Theorem:**
A vertex potential move (section CUT) can reduce the section defect $D_c(s)$.
However, it **cannot** change $\Phi_1([c])$! Shifting vertex potential merely changes the chosen representative; the minimum over all potentials remains completely invariant.

## 2. Section Moves (CUT) vs. Relational Repairs

In the practitioner governor (`l1_symbol_game_governor.py`), two distinct operations exist:
- **Section CUT ($s \to s'$):** Adjusts vertex elevations. Can decrease $D_c(s)$ down toward $\Phi_1([c])$. Leaves edge claims $c$ and $\Phi_1([c])$ unchanged.
- **Relational Repair ($c \to c'$):** Modifies the edge claims themselves (e.g. conceding a contradiction). This alters the gauge class $[c]$ and can reduce $\Phi_1$.

## 3. Governor Admission Policy: Monotonic Defect Non-Increase

[Pinned] When a learner or agent proposes a section CUT $s \to s'$, the governor evaluates the new defect $D_{\text{new}} = D_c(s')$ against $D_{\text{old}} = D_c(s)$:
1. **Strict Improvement ($D_{\text{new}} < D_{\text{old}}$):** **ADMITTED** (descent step).
2. **Stationary Move ($D_{\text{new}} == D_{\text{old}}$):** **ADMITTED** (`IdempotentStationary`).
3. **Defect Increase ($D_{\text{new}} > D_{\text{old}}$):** **REFUSED** (`DEFECT_INCREASE`).

### Worked Demonstration on the Canonical Triangle
Let unit weights $w = (1, 1, 1)$, edges $((0, 1), (1, 2), (2, 0))$, and edge claims $c = (2, -1, 0)$.
Notice the relationship to the gauge shift $\phi$ from Lessons 15–16: because the residual is $c - ds = c + d(-s)$, an improving section potential corresponds to $s = -\phi$.
- **Initial section $s_0 = (0, 0, 0)$:**
  $$D_c(s_0) = |2 - 0| + |-1 - 0| + |0 - 0| = 2 + 1 + 0 = 3.$$
- **Candidate 1 (Elevator shift $s_1 = (0, 1, 0)$, where $s_1 = -\phi$):**
  $d s_1 = (1, -1, 0)$. The residual $c - d s_1 = (1, 0, 0)$.
  $$D_c(s_1) = |1| + |0| + |0| = 1.$$
  $D$ drops $3 \to 1$ $\implies$ **ADMITTED** (strict descent).
- **Candidate 2 (Global shift $s_2 = (1, 2, 1)$):**
  $d s_2 = (1, -1, 0)$. The residual is still $(1, 0, 0)$.
  $$D_c(s_2) = 1 == D_c(s_1) \implies \text{\textbf{ADMITTED (IdempotentStationary)}}.$$
- **Candidate 3 (Bad move $s_3 = (0, -1, 0)$):**
  $d s_3 = (-1, 1, 0)$. The residual $c - d s_3 = (3, -2, 0)$.
  $$D_c(s_3) = |3| + |-2| + |0| = 5 > 1 \implies \text{\textbf{REFUSED (DEFECT\_INCREASE)}}.$$

Across all these moves, $\Phi_1([c]) = 1$ remained constant!

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If a vertex potential move reduces section defect from $D=3$ to $D=1$, what happened to $\Phi_1([c])$?

- **A:** $\Phi_1([c])$ decreased from 3 to 1.
- **B:** $\Phi_1([c])$ remained 1 the entire time, because vertex shifts cannot change gauge-invariant obstruction.
- **C:** $\Phi_1([c])$ became 0.

*(Correct answer: **B**. Vertex moves reduce section defect $D$ toward $\Phi_1$, but $\Phi_1$ is an invariant of the edge claims.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If a hill has height 3 and you smooth it down to height 1, did the bump get smaller?
2. **Exercise 2 (Age 15):** Calculate $D_c(s)$ for $c = (2, -1, 0)$ and $s = (0, 1, 0)$. What is the residual on each edge?
3. **Exercise 3 (Age 500):** Verify that the mathematical admission rule admits $s_1 = (0, 1, 0)$ ($D: 3 \to 1$), admits stationary $s_2$ ($D: 1 \to 1$), and refuses $s_3$ ($D: 1 \to 5$).

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

edges = ((0, 1), (1, 2), (2, 0))
c = (Q(2), Q(-1), Q(0))

def section_defect(c, s):
    d = tuple(s[v] - s[u] for u, v in edges)
    return sum(abs(ce - de) for ce, de in zip(c, d))

# 1. Initial defect: s0 = (0, 0, 0)
s0 = (Q(0), Q(0), Q(0))
D0 = section_defect(c, s0)
assert D0 == Q(3)

# 2. Improving move: s1 = (0, 1, 0)
s1 = (Q(0), Q(1), Q(0))
D1 = section_defect(c, s1)
assert D1 == Q(1)
assert D1 < D0  # ADMITTED: Strict descent

# 3. Stationary move: s2 = (1, 2, 1)
s2 = (Q(1), Q(2), Q(1))
D2 = section_defect(c, s2)
assert D2 == D1  # ADMITTED: IdempotentStationary

# 4. Refused increase: s3 = (0, -1, 0)
s3 = (Q(0), Q(-1), Q(0))
D3 = section_defect(c, s3)
assert D3 == Q(5)
assert D3 > D1  # REFUSED: DEFECT_INCREASE

print("Section defect D, admission policy, and Phi_1 invariance verified successfully!")
```
</details>
