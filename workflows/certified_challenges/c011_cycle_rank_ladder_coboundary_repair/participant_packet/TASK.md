# C011: Cycle-Rank Ladder: Minimum-L1 Coboundary Repair

**AuthorityEffect:** None. **Status:** active. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm ($0.05 target). **Models:** open weights, at most 70B total parameters.
**Protocol:** SG-CP v1.

---

## 1. Formal Problem & Mathematical Bounds

Let $G = (V, E)$ be a directed finite graph without self-loops (parallel edges permitted).
Each edge $e \in E$ is directed from $u = \operatorname{tail}(e)$ to $v = \operatorname{head}(e)$, with claim $c_e \in \mathbb{Q}$ and capacity weight $w_e \in \mathbb{Q}_{> 0}$.

For a 0-cochain (potential) $\phi \in \mathbb{Q}^V$, the coboundary $\delta \phi \in \mathbb{Q}^E$ is defined by:
$$(\delta \phi)_e = \phi(\operatorname{head}(e)) - \phi(\operatorname{tail}(e))$$

The cohomological obstruction $\Phi_1(c)$ is the weighted $L_1$ quotient distance from $c$ to the coboundary subspace:
$$\Phi_1(c) = \min_{\phi \in \mathbb{Q}^V} \sum_{e \in E} w_e |c_e - (\delta \phi)_e|$$

A cochain $c$ is exact if and only if $\Phi_1(c) = 0$.
The optimal repair $r \in \mathbb{Q}^E$ is $r = c - \delta \phi^*$, so that the repaired cochain $c - r = \delta \phi^*$ is a genuine coboundary.

By Linear Programming (LP) duality, the obstruction satisfies:
$$\Phi_1(c) = \max \left\{ \sum_{e \in E} c_e y_e : y \text{ a circulation}, |y_e| \le w_e \ \forall e \in E \right\}$$
where a circulation $y \in \mathbb{Q}^E$ satisfies flow conservation at every vertex:
$$\sum_{e: \operatorname{head}(e) = v} y_e - \sum_{e: \operatorname{tail}(e) = v} y_e = 0 \quad \forall v \in V$$

A pair of primal potential $\phi$ and dual circulation $y$ certifies optimality with zero duality gap if and only if complementary slackness holds:
- $y_e = w_e \cdot \operatorname{sign}(r_e)$ whenever $r_e \neq 0$
- $|y_e| \le w_e$ whenever $r_e = 0$
- $\sum_{e \in E} w_e |r_e| = \sum_{e \in E} c_e y_e = \Phi_1(c)$

### Bounds
- Cycle rank $b_1 = |E| - |V| + (\text{number of connected components}) \in [0, 16]$.
- Vertices $|V| \le 60$.
- Edges $|E| \le 200$.
- Weight denominators $\le 12$.
- Rational claims $|c_e| \le 10^{20}$ (arbitrary precision rational arithmetic).

---

## 2. Canonical Rational Number Encoding

All rational numbers in JSON wire payloads must follow RFC 8785 canonical string format:
- Integers must be encoded as plain integer strings (e.g. `"0"`, `"1"`, `"-3"`, `"8"`).
- Fractions must be reduced coprime strings `f"{p}/{q}"` with $q > 1$ and $\gcd(|p|, q) = 1$ (e.g. `"5/12"`, `"-1/3"`).
- Strictly forbidden: `"1/1"`, unreduced fractions (`"2/4"`), floats (`"1.0"`), and decimals (`"0.5"`).
- Omitted repair and dual entries are interpreted as exactly zero.

---

## 3. Closed Refusal List

When an input case is malformed or out of declared bounds, the solver must fail closed with `status: "UNKNOWN"` and a refusal code from this strict closed list:
1. `VERTEX_COUNT_OUT_OF_BOUNDS`: Vertices list is empty ($|V| < 1$) or exceeds bound ($|V| > 60$).
2. `EDGE_COUNT_OUT_OF_BOUNDS`: Edge count exceeds bound ($|E| > 200$) or cycle rank $b_1 > 16$.
3. `INVALID_CAPACITY`: Edge weight is not a valid positive rational or denominator exceeds 12 when enforced.
4. `NEGATIVE_WEIGHT`: Edge weight is nonpositive ($w_e \le 0$) when refusal is expected.
5. `DISCONNECTED_GRAPH`: Graph has multiple connected components when connectivity is strictly required.
6. `MALFORMED_EDGE_SPEC`: Edge structure missing required fields, non-string endpoint, or duplicate edge ID.
7. `INVALID_TARGET_DEFECT`: Target defect or target $\Phi_1$ is negative or malformed rational.
8. `MALFORMED_CASE_STRUCTURE`: Input is not a JSON object, missing `id`, or contains type violations (such as booleans as numbers).

---

## 4. Input & Output Wire Schemas

### Input Schema
```json
{
  "id": "ex01_diamond",
  "vertices": ["a", "b", "c", "d"],
  "edges": [
    {"id": "a->b", "u": "a", "v": "b", "claim": "1", "weight": "1"},
    {"id": "b->c", "u": "b", "v": "c", "claim": "2", "weight": "2"},
    {"id": "c->a", "u": "c", "v": "a", "claim": "3", "weight": "3"},
    {"id": "b->d", "u": "b", "v": "d", "claim": "1", "weight": "1"},
    {"id": "d->a", "u": "d", "v": "a", "claim": "2", "weight": "2"}
  ]
}
```

### Output Schemas

#### 1. SOLVED
```json
{
  "id": "ex01_diamond",
  "status": "SOLVED",
  "phi1": "8",
  "potential": {
    "a": "0",
    "b": "-3",
    "c": "-3",
    "d": "-2"
  },
  "repair": {
    "a->b": "4",
    "b->c": "2"
  },
  "dual": {
    "a->b": "1",
    "b->c": "2",
    "c->a": "2",
    "b->d": "-1",
    "d->a": "-1"
  }
}
```

#### 2. OUT_OF_SCOPE
Returned when the graph contains a self-loop, unknown endpoints, or nonpositive weights in discovery settings:
```json
{
  "id": "ex09_oos_nonpositive_weight",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "edge": "e_bad",
    "reason": "NONPOSITIVE_WEIGHT"
  }
}
```

#### 3. UNKNOWN (Refusal)
```json
{
  "id": "ex12_unknown_vertex_count",
  "status": "UNKNOWN",
  "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS",
  "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS"
}
```

---

## 5. Deliverable Requirements

A pure Python standard library module exposing:
```python
def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    ...
```
No external packages (e.g. `scipy`, `numpy`, `cvxpy`, `networkx`) are permitted.
Execution runs strictly sandboxed via `runner.py`.
