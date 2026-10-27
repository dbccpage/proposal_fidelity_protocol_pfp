# C016: Cohomology Rings: Telling Spaces Apart with Cup Products

## Problem Statement

Given two finite simplicial complexes $X$ and $Y$ of dimension $\le 4$ and a degree pair $(p, q)$ with $p + q \le 4$:
1. Check whether rational Betti numbers match in all degrees: $b_k(X) == b_k(Y)$ for $k \in \{0, 1, 2, 3, 4\}$. If not, return status `OUT_OF_SCOPE` with a witness naming the degree of mismatch.
2. For each complex, compute a basis for $H^p$ and $H^q$ as cocycles.
3. Compute all Alexander-Whitney cup products $\alpha_i \smile \beta_j$ on $(p+q)$-simplices:
   $$ (\alpha \smile \beta)[v_0, \dots, v_{p+q}] = \alpha[v_0, \dots, v_p] \cdot \beta[v_p, \dots, v_{p+q}]. $$
4. Determine the rank of the cup product map $H^p \times H^q \to H^{p+q}$.
5. Certificate requirements:
   - For rank $r > 0$, provide $r$ cycle witnesses $z_k$ ($\partial z_k = 0$) evaluating to nonzero numbers on independent products.
   - For products that are exact (coboundaries), provide primitives $\gamma$ with $\delta \gamma = \alpha_i \smile \beta_j$.
6. Return `verdict`: `"DISTINGUISHED"` if ranks differ, and `"NOT_DISTINGUISHED_BY_THIS_PRODUCT"` otherwise.

## Output Contract

```json
{
  "id": "case_id",
  "status": "SOLVED",
  "verdict": "DISTINGUISHED",
  "X": {
    "rank": "1",
    "basis_p": [{"[0, 1]": "1"}],
    "basis_q": [{"[0, 1]": "1"}],
    "nonzero": [{"i": "0", "j": "0", "cycle": {"[0, 1, 2]": "1"}, "value": "1"}],
    "primitives": []
  },
  "Y": {
    "rank": "0",
    "basis_p": [{"[0, 1]": "1"}],
    "basis_q": [{"[0, 1]": "1"}],
    "nonzero": [],
    "primitives": [{"i": "0", "j": "0", "gamma": {"[0, 1]": "1/2"}}]
  }
}
```
