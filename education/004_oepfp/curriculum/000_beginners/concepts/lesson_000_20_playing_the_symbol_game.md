# Lesson 000.20 -- Playing The Symbol Game: Candidate Moves, Host Referees, and Monotonic Non-Increase

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_20_playing_the_symbol_game.ipynb](../notebooks/lesson_000_20_playing_the_symbol_game.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Two-Player Protocol and Host Referee
- 2. The Mechanics: Proposal, Recomputation, and Monotonic Non-Increase
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Symbol Game specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Two-Player Protocol and Host Referee

[Pinned] The Symbol Game is structured as a two-player retraction protocol between:
1. **The Proposer:** An external agent or model that proposes candidate transitions or state representations $c'$.
2. **The Host Referee:** An autonomous execution kernel that inspects the candidate move, recomputes all topological invariants from scratch, and emits a binding verdict.

Crucially, the Proposer's self-reported claims carry `AuthorityEffect: None`. The Host referee does not trust candidate assertions; it executes independent verification over exact rational arithmetic.

## 2. The Mechanics: Proposal, Recomputation, and Monotonic Non-Increase

[Pinned] To prevent unbounded divergence and govern state transitions, the Host referee enforces a strict admission policy:
1. **Syntax, Domain, and Carrier Validity:** The candidate move must be well-formed, adhere strictly to the declared fixed carrier graph and cycle, and use exact rational coordinates ($\mathbb{Q}$). Floating-point values, non-finite values (such as NaN), and booleans are strictly refused: `REFUSED_DOMAIN`.
2. **Operation Typing (Section CUT vs. Relational Repair):**
   - **Section CUT ($s \to s'$, or shift $c' = c - ds$):** Adjusts vertex potential section elevations. Because vertex potential shifts are coboundaries, they preserve the edge circulation and gauge class ($[c'] = [c]$). The Host recomputes the section defect:
     $$D_c(s) = \sum_{e=(u,v)} w_e |c_e - (s(v) - s(u))|.$$
     A CUT move is admitted if and only if circulation is preserved and section defect does not increase ($D_{\text{new}} \le D_{\text{old}}$). If a proposed CUT attempts to alter circulation, it is refused: `REFUSED_COHOMOLOGY_BREACH`. If it increases section defect, it is refused: `REFUSED_DEFECT_INCREASE`.
   - **Relational Repair ($c \to c'$):** Modifies the edge claims themselves (e.g. retracting a contradictory assertion). This alters the gauge class and admits moves if the minimal obstruction does not increase: $\Phi_1(c') \le \Phi_1(c)$.
3. **Monotonicity vs. Finite Termination:**
   Monotonic defect non-increase guarantees that defect never worsens along admitted trajectories. However, continuous rational numbers do not form a finite state space: an infinite sequence of strictly improving steps (such as $c_k = (2^{-k}, 0, 0)$) or stationary shifts can continue indefinitely without finite termination. A true finite halting guarantee requires an operational step quota, integer lattice quantization, or a well-founded termination rank.

### Canonical Triangle Case Study

Consider our canonical 3-vertex triangle with initial cochain $c = (2, -1, 0)$ and circulation $\langle c, z \rangle = 1$:
- **Candidate 1 (Valid Elevator Move):** Proposer shifts vertex potential by $s_1 = (0, 1, 0)$, yielding residual $c' = (1, 0, 0)$.
  Host recomputes: circulation $= 1$, section defect $D_c(s_1) = 1 \le D_c(s_0) = 3$, $\Phi_1 = 1$. Verdict: `ADMITTED` (`MonotonicDescent`).
- **Candidate 2 (Illegal Defect Increase under CUT):** Proposer shifts vertex potential to $s_3 = (0, -1, 0)$, producing residual $c'' = (3, -2, 0)$.
  Host recomputes: circulation $= 1$, but section defect $D_c(s_3) = 5 > D_c(s_0) = 3$. Verdict: `REFUSED_DEFECT_INCREASE`.
- **Candidate 3 (Class-Altering Move under CUT):** Proposer submits $c = (0, 0, 0)$ under move type `CUT`.
  Host recomputes: circulation changed from $1 \to 0$. Verdict: `REFUSED_COHOMOLOGY_BREACH`. (Under `RELATIONAL_REPAIR`, it would be admitted because $\Phi_1$ drops $1 \to 0$).
- **Candidate 4 (Illegal Edge Modification):** Proposer alters edge values to $c''' = (2, 2, 2)$.
  Host recomputes: circulation $\langle c''', z \rangle = 6$, minimal defect $\Phi_1(c''') = 6 > 1$. Verdict: `REFUSED_DEFECT_INCREASE`.
- **Candidate 5 (Malformed Types or Float):** Proposer provides floating-point values or NaNs (`1.0`, `float('nan')`).
  Verdict: `REFUSED_DOMAIN`.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Under the Symbol Game governor rules, why does the Host referee recompute $\Phi_1(c')$ and section defect $D_c(s)$ instead of accepting the Proposer's reported values?

- **A:** Recomputing is faster than parsing reported text.
- **B:** Proposer outputs have `AuthorityEffect: None` and are untrusted proposals; only host recomputation over exact rational arithmetic prevents uncertified defect increases.
- **C:** The Host referee needs floating point rounding.

*(Correct answer: **B**. External proposals carry no authority; the host recomputes exact rational invariants independently to enforce monotonic non-increase.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** You are playing a cleanup game. If your friend offers to help clean your room, but brings in 5 more toys instead of putting any away, do you accept or refuse? *(Answer: Refuse! That increases the mess!)*
2. **Exercise 2 (Age 15):** In Python, write an exact referee function that accepts an elevator move shifting $c = (2, -1, 0)$ to $c' = (1, 0, 0)$ and rejects an illegal move to $(3, -2, 0)$ that increases section defect.
3. **Exercise 3 (Age 500):** Implement the full two-player referee check below using `fractions.Fraction` with strict type validation (rejecting floats/NaNs) and assert that valid shifts are admitted while defect-increasing moves are refused.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

def _parse_exact_q(val, name: str) -> Q:
    if isinstance(val, bool):
        raise TypeError(f"{name} must be exact int or Fraction, got bool")
    if isinstance(val, float):
        raise TypeError(f"{name} must be exact int or Fraction, got float {val}")
    try:
        return Q(val)
    except Exception as e:
        raise TypeError(f"{name} cannot be converted to Fraction: {e}")

def compute_section_defect(c, s, edges, weights=None):
    total = Q(0)
    for (u, v), val in zip(edges, c):
        w = weights.get((u, v), 1) if weights else 1
        d_uv = s[v] - s[u]
        total += Q(w) * abs(val - d_uv)
    return total

def evaluate_move(c_old, c_new, edges, cycle, move_type="CUT"):
    # 1. Enforce declared fixed carrier and cycle
    EXPECTED_EDGES = ((0, 1), (1, 2), (2, 0))
    EXPECTED_CYCLE = {(0, 1): 1, (1, 2): 1, (2, 0): 1}
    if tuple(edges) != EXPECTED_EDGES or cycle != EXPECTED_CYCLE:
        return {"admitted": False, "verdict": "REFUSED_CARRIER", "reason": "unsupported carrier or cycle"}
    
    # 2. Check dimensions
    if len(c_old) != len(edges) or len(c_new) != len(edges):
        return {"admitted": False, "verdict": "REFUSED_SYNTAX", "reason": "dimension mismatch"}
    
    # 3. Validate exact rational coordinates (reject float, bool, NaN)
    try:
        c_old_q = tuple(_parse_exact_q(x, "c_old") for x in c_old)
        c_new_q = tuple(_parse_exact_q(x, "c_new") for x in c_new)
    except TypeError as e:
        return {"admitted": False, "verdict": "REFUSED_DOMAIN", "reason": str(e)}
    
    # 4. Host recomputes exact circulations independently
    circ_old = sum(val * cycle[e] for e, val in zip(edges, c_old_q))
    circ_new = sum(val * cycle[e] for e, val in zip(edges, c_new_q))
    
    phi1_old = abs(circ_old)
    phi1_new = abs(circ_new)
    
    if move_type == "CUT":
        if circ_new != circ_old:
            return {
                "admitted": False,
                "verdict": "REFUSED_COHOMOLOGY_BREACH",
                "reason": "Section CUT cannot alter circulation or gauge class",
                "circ_old": circ_old,
                "circ_new": circ_new,
            }
        
        # In Lesson 17 residual convention (r = c - ds), representative mass equals section defect D_c(s)
        d_old = sum(abs(x) for x in c_old_q)
        d_new = sum(abs(x) for x in c_new_q)
        
        if d_new > d_old:
            return {
                "admitted": False,
                "verdict": "REFUSED_DEFECT_INCREASE",
                "d_old": d_old,
                "d_new": d_new,
                "phi1": phi1_old,
            }
        
        status = "MonotonicDescent" if d_new < d_old else "IdempotentStationary"
        return {
            "admitted": True,
            "verdict": "ADMITTED",
            "status": status,
            "d_old": d_old,
            "d_new": d_new,
            "phi1": phi1_old,
            "mass_old": d_old,
            "mass_new": d_new,
        }
        
    elif move_type == "RELATIONAL_REPAIR":
        if phi1_new > phi1_old:
            return {
                "admitted": False,
                "verdict": "REFUSED_DEFECT_INCREASE",
                "phi1_old": phi1_old,
                "phi1_new": phi1_new,
            }
        status = "MonotonicDescent" if phi1_new < phi1_old else "IdempotentStationary"
        return {
            "admitted": True,
            "verdict": "ADMITTED",
            "status": status,
            "phi1_old": phi1_old,
            "phi1_new": phi1_new,
            "mass_old": sum(abs(x) for x in c_old_q),
            "mass_new": sum(abs(x) for x in c_new_q),
        }
    else:
        return {"admitted": False, "verdict": "REFUSED_UNKNOWN_OPCODE", "reason": f"unknown move_type {move_type}"}

edges = ((0, 1), (1, 2), (2, 0))
cycle = {(0, 1): 1, (1, 2): 1, (2, 0): 1}

# Test Candidate 1: valid elevator move (CUT)
c_init = tuple(map(Q, (2, -1, 0)))
c_valid = tuple(map(Q, (1, 0, 0)))
res1 = evaluate_move(c_init, c_valid, edges, cycle, move_type="CUT")
assert res1["admitted"] and res1["verdict"] == "ADMITTED"
assert res1["d_new"] == Q(1) < res1["d_old"]

# Test Candidate 2: bad elevator move that increases section defect (CUT)
c_worse = tuple(map(Q, (3, -2, 0)))
res2 = evaluate_move(c_init, c_worse, edges, cycle, move_type="CUT")
assert not res2["admitted"] and res2["verdict"] == "REFUSED_DEFECT_INCREASE"
assert res2["d_new"] == Q(5) > res2["d_old"]

# Test Candidate 3: class-altering move under CUT
c_zero = tuple(map(Q, (0, 0, 0)))
res3 = evaluate_move(c_init, c_zero, edges, cycle, move_type="CUT")
assert not res3["admitted"] and res3["verdict"] == "REFUSED_COHOMOLOGY_BREACH"

# Test Candidate 4: relational repair admitting (0, 0, 0)
res4 = evaluate_move(c_init, c_zero, edges, cycle, move_type="RELATIONAL_REPAIR")
assert res4["admitted"] and res4["verdict"] == "ADMITTED"
assert res4["phi1_new"] == Q(0) < res4["phi1_old"]

# Test Candidate 5: defect increase under relational repair
c_bad = tuple(map(Q, (2, 2, 2)))
res5 = evaluate_move(c_init, c_bad, edges, cycle, move_type="RELATIONAL_REPAIR")
assert not res5["admitted"] and res5["verdict"] == "REFUSED_DEFECT_INCREASE"
assert res5["phi1_new"] == Q(6) > res5["phi1_old"]

# Test Candidate 6: float input rejected
res6 = evaluate_move((1.0, 0.0, 0.0), c_valid, edges, cycle)
assert not res6["admitted"] and res6["verdict"] == "REFUSED_DOMAIN"

# Test Candidate 7: NaN input rejected
res7 = evaluate_move((float("nan"), 0.0, 0.0), c_valid, edges, cycle)
assert not res7["admitted"] and res7["verdict"] == "REFUSED_DOMAIN"

# Test Candidate 8: unsupported carrier rejected
res8 = evaluate_move(c_init, c_valid, ((0, 1), (1, 2)), cycle)
assert not res8["admitted"] and res8["verdict"] == "REFUSED_CARRIER"

print("Symbol Game referee protocol verified successfully!")
```
</details>
