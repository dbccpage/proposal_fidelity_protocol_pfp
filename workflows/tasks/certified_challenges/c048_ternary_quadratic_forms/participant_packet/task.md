# C048: Ternary Quadratic Forms: Rational Point or Local Obstruction

**Domain:** e_formal_math
**Tier:** T2
**Protocol:** SG-CP v1

## Problem Description

Given integers $a, b, c$ ($|a|, |b|, |c| \le 10^{18}$), determine whether the ternary quadratic form:

$$a x^2 + b y^2 + c z^2 = 0$$

admits a non-trivial rational point $(x, y, z) \in \mathbb{Z}^3 \setminus \{(0, 0, 0)\}$.

By the Hasse-Minkowski theorem and Legendre's theorem, a non-trivial integer solution exists if and only if there are no local obstructions, which is equivalent to the condition that the Hilbert symbol:

$$(-ac, -bc)_v = +1 \quad \text{for every place } v \in \{\infty, 2, \text{odd primes } p\}.$$

If a rational point exists, return integers $(x, y, z) \ne (0, 0, 0)$ satisfying the equation.
If no rational point exists, exhibit a place $v \in \{\text{"inf"}, \text{"2"}, \text{"p"}\}$ where the Hilbert symbol is $-1$.

## Output Schema

Your solution must implement `solve(case: dict) -> dict`.

### Rational Point
```json
{
  "case_id": "tq_ex_01",
  "status": "SOLVED",
  "kind": "RATIONAL_POINT",
  "x": "1",
  "y": "1",
  "z": "1"
}
```

### Local Obstruction
```json
{
  "case_id": "tq_ex_02",
  "status": "SOLVED",
  "kind": "LOCAL_OBSTRUCTION",
  "place": "2"
}
```

### Obstruction at Infinity
```json
{
  "case_id": "tq_ex_03",
  "status": "SOLVED",
  "kind": "LOCAL_OBSTRUCTION",
  "place": "inf"
}
```
