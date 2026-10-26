# Challenge C027: Kochen-Specker Sets and Contextuality Certificates

**AuthorityEffect:** None. **Status:** Active. **Domain:** c_quantum. **Tier:** T3.  
**Budget Ceiling:** $1.00 billed inference per arm. **Target Cost:** < $0.05.  
**Models:** Open weights, at most 70B total parameters. **Protocol:** SG-CP v1.

---

## 1. Task Objective

Synthesize an exact, deterministic solver module exposing:

```python
def solve(case: dict) -> dict
```

that decides whether a set of rays in $\mathbb{R}^d$ ($d \in \{3, 4\}$) with coordinates in $\mathbb{Z}[\sqrt{2}]$ admits a non-contextual $\{0, 1\}$ colouring satisfying:
1. **Orthogonality constraint:** for every orthogonal pair of rays $(u, v)$ ($u \cdot v = 0$ in $\mathbb{Q}(\sqrt{2})$), $c_u + c_v \le 1$.
2. **Context constraint:** for every complete orthogonal basis $C$ (context of size $d$), $\sum_{r \in C} c_r = 1$.

If colourable: returns a valid $\{0, 1\}$ colouring vector.  
If uncolourable: returns an uncolourable subset and a certificate (such as an exact parity proof).  
If malformed or out of bounds: returns a typed refusal (`OUT_OF_SCOPE` or `UNKNOWN`).

---

## 2. Input Specification

A case dictionary contains:
- `case_id`: String identifier (e.g. `"ks_07"`).
- `dimension`: Integer $d \in \{3, 4\}$.
- `vectors`: List of up to 60 non-zero vectors. Each vector has $d$ coordinates. Each coordinate is given as a pair $[a, b]$ representing the quadratic integer $a + b\sqrt{2} \in \mathbb{Z}[\sqrt{2}]$.

### Ray Merging & Orthogonality

- Parallel vectors ($u = c v$ for non-zero $c \in \mathbb{Q}(\sqrt{2})$) represent the same projective ray and must be merged.
- Inner product $u \cdot v = \sum_{k=0}^{d-1} u_k v_k$ is evaluated exactly over $\mathbb{Q}(\sqrt{2})$:
  $$(a_1 + b_1\sqrt{2})(a_2 + b_2\sqrt{2}) = (a_1 a_2 + 2 b_1 b_2) + (a_1 b_2 + b_1 a_2)\sqrt{2}$$
- Orthogonality requires both the rational part and the $\sqrt{2}$ part of the inner product to be identically 0.

---

## 3. Output Contract

Responses must be RFC 8785 canonical JSON matching one of:

### A. Colourable Ray Set
```json
{
  "id": "ks_08",
  "status": "SOLVED",
  "colourable": true,
  "colouring": [1, 0, 0, 0, ...]
}
```
Validation rules:
- Every colouring value is 0 or 1.
- No two orthogonal rays are both coloured 1.
- Every complete context sums to exactly 1.

### B. Uncolourable Kochen-Specker Set (Parity Proof)
```json
{
  "id": "ks_07",
  "status": "SOLVED",
  "colourable": false,
  "subset": [0, 1, 2, ...],
  "certificate": {
    "kind": "parity",
    "contexts": [[0, 1, 4, 9], ...]
  }
}
```
Validation rules:
- `contexts` contains an odd number of contexts ($m \equiv 1 \pmod 2$).
- Every context is a valid orthogonal basis of size $d$.
- Every ray in `subset` appears an even number of times across the listed contexts.

### C. Refusal: Out of Scope
```json
{
  "id": "ks_09",
  "status": "OUT_OF_SCOPE",
  "witness": {"kind": "zero_vector", "index": 5}
}
```

### D. Refusal: Bounds Exceeded
```json
{
  "id": "ks_10",
  "status": "UNKNOWN",
  "refusal_code": "TOO_MANY_VECTORS"
}
```
Triggered when input contains $> 60$ vectors.
