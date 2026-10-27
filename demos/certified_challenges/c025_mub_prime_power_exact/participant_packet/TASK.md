# C025: Exact Mutually Unbiased Bases in Prime-Power Dimensions

**AuthorityEffect:** None. **Status:** active. **Domain:** c_quantum. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total parameters.
**Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

## 1. Task Description

Given a dimension $d$ ($2 \le d \le 10$) and requested number of bases $k$ ($2 \le k \le d + 1$), optionally with a fixed first basis $B_0$, construct a set of $k$ mutually unbiased bases in exact cyclotomic arithmetic over $\mathbb{Q}(\zeta_m)$, or return a typed refusal where the problem is open or impossible.

Mutually unbiased bases satisfy:
1. Within-basis orthogonality: $\langle v, w \rangle = 0$ for $v \ne w$ in the same basis, with $\langle v, v \rangle = N_v$ (declared rational squared norm).
2. Across-basis unbiasedness: $d \cdot |\langle v, w \rangle|^2 = N_v N_w$ for all $v \in B_i, w \in B_j$ ($i \ne j$).
3. Complete basis dimensions: exactly $k$ bases of $d$ vectors each.
4. Fixed $B_0$ preservation: if $B_0$ is provided, one returned basis must equal $B_0$ up to per-vector global phases in the field and permutations.

## 2. Refusal Invariants

- **Open Problem Refusal:** For $d = 6$ and $k \ge 4$, the existence of 4 or more MUBs is an open problem in quantum information theory. Solvers must refuse with:
  ```json
  {"id": "<case_id>", "status": "UNKNOWN", "refusal_code": "OPEN_PROBLEM"}
  ```
  Any claim of 4 or more MUBs in $d = 6$ is a critical error.
- **Out of Scope Refusal:** For any $k > d + 1$, at most $d + 1$ MUBs can exist in dimension $d$. Solvers must refuse with:
  ```json
  {"id": "<case_id>", "status": "OUT_OF_SCOPE", "witness": {"requested": k, "max_possible": d + 1}}
  ```

## 3. Field Element Encoding

Field elements in $\mathbb{Q}(\zeta_m)$ are represented as lists of $m$ rational strings, the coefficients of $\zeta_m^0, \zeta_m^1, \dots, \zeta_m^{m-1}$.
Rationals with unit denominator are serialized without slash (e.g. `"1"`, `"-2"`, `"0"`), non-integers with slash (e.g. `"1/2"`, `"-3/4"`).

Example coordinate in $\mathbb{Q}(\zeta_3)$:
`["1", "0", "0"]` $= 1$
`["0", "1", "0"]` $= \zeta_3$

## 4. Input & Output Contract

Input JSON:
```json
{
  "case_id": "mub_01",
  "dimension": 3,
  "num_bases": 4,
  "fixed_first_basis": null
}
```

Output JSON:
```json
{
  "id": "mub_01",
  "status": "SOLVED",
  "cyclotomic_order": 3,
  "bases": [
    [
      {
        "norm2": "1",
        "entries": [["1", "0", "0"], ["0", "0", "0"], ["0", "0", "0"]]
      },
      ...
    ],
    ...
  ]
}
```
