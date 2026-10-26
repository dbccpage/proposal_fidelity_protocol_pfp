# Lesson 200.24 -- Governor Integration with Lean 4: Multi-Simplex Regge Triangulations and Hinge Holonomy Verification

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_24_governor_integration_with_lean_4.ipynb](../notebooks/lesson_200_24_governor_integration_with_lean_4.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Connecting Runtime Governors to Formal Proof Kernels
- 2. 4-Simplex Multi-Simplex Geometry and Gram Matrix Positivity
- 3. Hinge Curvature Holonomy and the Lean 4 Level 21 Regge Countermodel
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Lean 4 kernel specifications (`Level21DiscreteRegge.lean`) and target checkers (`stage_021.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Connecting Runtime Governors to Formal Proof Kernels

[Declared] In Track 100 and Track 200, we built software adapters, packet envelopes, and $L_1$ homology retractors. In production verification systems, runtime governors do not invent mathematical truths on the fly; they enforce specifications mechanized in interactive proof kernels like **Lean 4**.

When evaluating candidate higher-dimensional discrete spacetimes (such as 4D Regge complexes), the runtime governor inspects candidate geometric payloads against the exact formal clauses proved in Lean 4 (`Level21DiscreteRegge.lean`) and checked in Stage 21 (`stage_021.py`).

## 2. 4-Simplex Multi-Simplex Geometry and Gram Matrix Positivity

[Pinned] A single 4-simplex $\sigma^4$ has 5 vertices $\{0, 1, 2, 3, 4\}$ and $\binom{5}{2} = 10$ edges.
To specify metric geometry over exact arithmetic without floating point rounding, the candidate supplies 10 squared edge lengths:
$$\ell_{ij}^2 \in \mathbb{Q}^+ \quad (0 \le i < j \le 4).$$

To verify that these 10 lengths correspond to a genuine, non-degenerate Euclidean 4-simplex, the governor constructs the **Gram matrix** $G \in \mathbb{Q}^{4 \times 4}$ based at vertex 0:
$$G_{ab} = \frac{\ell_{0a}^2 + \ell_{0b}^2 - \ell_{ab}^2}{2} \quad (a, b \in \{1, 2, 3, 4\}).$$

The 4-simplex is geometrically embeddable if and only if $G$ is strictly positive definite ($G \succ 0$):
$$\det(G_{1..k, 1..k}) > 0 \quad \text{for all } k \in \{1, 2, 3, 4\}.$$
If any leading principal minor is non-positive, the governor issues a typed refusal: `R021_GRAM_NOT_POSITIVE`.

## 3. Hinge Curvature Holonomy and the Lean 4 Level 21 Regge Countermodel

[Pinned] Curvature in a 4D Regge complex concentrates on its 10 **triangular hinges (bones)** $\{a, b, c\} \subset \{0, 1, 2, 3, 4\}$.
Around each hinge, link transports form a path-ordered rotation loop in $SO(4)$.

### Clause C3: Refusal of Scalar Sum Closure
An unconstrained model or candidate generator often calculates that the scalar sum of dihedral deficit angles around a loop vanishes:
$$\sum \text{exponents} = 0.$$
It then falsely declares `closure: "identity"`.

Formal Lean development [`Level21DiscreteRegge.lean`](../../../../../../lean4/Level21DiscreteRegge.lean) proves `scalar_sum_does_not_certify_closure`:
The ordered loop product of two quarter-turn generators in $SO(4)$ satisfies:
$$U = R_{yz} R_{xz} R_{yz}^{-1} R_{xz}^{-1} \ne I_{4\times 4}.$$

Under the Stage 21 governor contract (`stage_021.py`), when a loop declares `closure: "identity"` but the ordered product deviates from $I$ while exponents cancel, the governor triggers clause C3:
$$\text{verdict} = \text{REFUSED\_SCALAR\_SUM\_CLOSURE} \quad (\text{Code: } \texttt{R021\_SCALAR\_SUM\_CLOSURE}).$$

Only when the ordered matrix product genuinely equals $I$ does the governor emit an `ADMITTED` receipt.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Under the Stage 21 governor contract (`stage_021.py`), what typed refusal code is emitted when a candidate declares `closure: "identity"` on a loop whose scalar exponent sum is zero, but whose ordered $SO(4)$ matrix product is not the identity?

- **A:** `R021_GRAM_NOT_POSITIVE`
- **B:** `R021_SCALAR_SUM_CLOSURE`
- **C:** `R021_NOT_ROTATION`

*(Correct answer: **B**. Clause C3 specifically identifies and refuses candidates that attempt to substitute a vanishing scalar angle sum for genuine non-abelian matrix holonomy closure.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you glue 4 flat building blocks together, does checking the length of the outside edges ensure the building won't collapse inside? *(Answer: No! You have to check that all the interior connections fit together!)*
2. **Exercise 2 (Age 15):** In Python, construct the Gram matrix for the regular unit 4-simplex (all 10 squared lengths equal 1), and verify that all 4 leading principal minors are strictly positive.
3. **Exercise 3 (Age 500):** Implement the complete Stage 21 governor evaluator below using `fractions.Fraction` and assert that it admits the genuine regular 4-simplex, refuses degenerate Gram matrices with `R021_GRAM_NOT_POSITIVE`, and refuses the Lean 4 countermodel loop with `R021_SCALAR_SUM_CLOSURE`.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q
from itertools import combinations

def det_q(matrix):
    rows = [[Q(x) for x in row] for row in matrix]
    n = len(rows)
    sign = Q(1)
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            return Q(0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            sign = -sign
        scale = rows[col][col]
        sign *= scale
        for r in range(col + 1, n):
            factor = rows[r][col] / scale
            for c in range(col, n):
                rows[r][c] -= factor * rows[col][c]
    return sign

def mat_mul4(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def transpose4(A):
    return [[A[j][i] for j in range(4)] for i in range(4)]

def identity4():
    return [[Q(1 if i == j else 0) for j in range(4)] for i in range(4)]

def evaluate_stage_021(payload):
    # 1. Parse and verify 10 squared edge lengths
    lengths = {}
    for u, v, val in payload["squared_lengths"]:
        lengths[(min(u, v), max(u, v))] = Q(val)
    if set(lengths.keys()) != set(combinations(range(5), 2)):
        return {"verdict": "R_SCHEMA", "reason": "Expected 10 edge lengths on 5 vertices"}
    
    # 2. Build 4x4 Gram matrix based at vertex 0
    rest = [1, 2, 3, 4]
    def sq(a, b):
        return Q(0) if a == b else lengths[(min(a, b), max(a, b))]
    
    gram = [[(sq(0, a) + sq(0, b) - sq(a, b)) / Q(2) for b in rest] for a in rest]
    
    # 3. Check Gram positivity (all 4 leading principal minors > 0)
    for k in range(1, 5):
        submatrix = [row[:k] for row in gram[:k]]
        if det_q(submatrix) <= Q(0):
            return {"verdict": "R021_GRAM_NOT_POSITIVE", "failed_minor": k}
    
    # 4. Check rotation generators in SO(4)
    I4 = identity4()
    generators = {}
    for name, mat in payload.get("generators", []):
        mat_q = [[Q(x) for x in row] for row in mat]
        if mat_mul4(mat_q, transpose4(mat_q)) != I4 or det_q(mat_q) != Q(1):
            return {"verdict": "R021_NOT_ROTATION", "generator": name}
        generators[name] = mat_q
    
    # 5. Check ordered loops around triangular hinges
    for loop in payload.get("loops", []):
        hinge = loop["hinge"]
        if len(set(hinge)) != 3 or not set(hinge) <= set(range(5)):
            return {"verdict": "R_SCHEMA", "reason": "Invalid hinge"}
        
        product = identity4()
        exponents = {name: 0 for name in generators}
        for letter in loop["word"]:
            inv = letter.endswith("-")
            name = letter[:-1] if inv else letter
            factor = transpose4(generators[name]) if inv else generators[name]
            product = mat_mul4(product, factor)
            exponents[name] += -1 if inv else 1
        
        closed = (product == I4)
        if loop["closure"] == "identity" and not closed:
            if all(exp == 0 for exp in exponents.values()):
                return {"verdict": "R021_SCALAR_SUM_CLOSURE", "hinge": hinge}
            return {"verdict": "R021_CLOSURE_MISMATCH", "hinge": hinge}
    
    return {"verdict": "ADMITTED", "gram_minors": [det_q([r[:k] for r in gram[:k]]) for k in range(1, 5)]}

# Test 1: Regular 4-simplex with Lean 4 countermodel loop
payload_negative = {
    "squared_lengths": [[a, b, "1/1"] for a, b in combinations(range(5), 2)],
    "generators": [
        ["Rx", [["1", "0", "0", "0"], ["0", "0", "-1", "0"], ["0", "1", "0", "0"], ["0", "0", "0", "1"]]],
        ["Ry", [["0", "0", "1", "0"], ["0", "1", "0", "0"], ["-1", "0", "0", "0"], ["0", "0", "0", "1"]]],
    ],
    "loops": [{"closure": "identity", "hinge": [0, 1, 2], "word": ["Rx", "Ry", "Rx-", "Ry-"]}],
}

res_neg = evaluate_stage_021(payload_negative)
assert res_neg["verdict"] == "R021_SCALAR_SUM_CLOSURE"

# Test 2: Degenerate 4-simplex with collapsed edge
payload_degenerate = dict(payload_negative)
payload_degenerate["squared_lengths"] = [[a, b, "0/1" if (a, b) == (0, 1) else "1/1"] for a, b in combinations(range(5), 2)]
res_deg = evaluate_stage_021(payload_degenerate)
assert res_deg["verdict"] == "R021_GRAM_NOT_POSITIVE"

# Test 3: Genuinely closed loop
payload_positive = dict(payload_negative)
payload_positive["loops"] = [{"closure": "identity", "hinge": [0, 1, 2], "word": ["Rx", "Rx-"]}]
res_pos = evaluate_stage_021(payload_positive)
assert res_pos["verdict"] == "ADMITTED"
assert res_pos["gram_minors"] == [Q(1), Q(3, 4), Q(1, 2), Q(5, 16)]

print("Governor integration with Lean 4 Level 21 Regge verified successfully!")
```
</details>
