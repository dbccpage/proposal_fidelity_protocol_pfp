# Task: C020 Spectral Sequence Pages of a Double Complex

## Problem Description

Given a first-quadrant double complex over $\mathbb{F}_2$:
- $C_{p,q} = \mathbb{F}_2^{n(p,q)}$ for $0 \le p, q \le 5$, with $n(p,q) \le 4$.
- Horizontal boundary maps $d^h: C_{p,q} \to C_{p-1, q}$.
- Vertical boundary maps $d^v: C_{p,q} \to C_{p, q-1}$.
- Commutation / anti-commutation over $\mathbb{F}_2$: $d^h d^h = 0$, $d^v d^v = 0$, and $d^h d^v = d^v d^h$.

Total complex: $\mathrm{Tot}_n = \bigoplus_{p+q=n} C_{p,q}$ with differential $D = d^h + d^v$.

For the requested filtration (`"columns"`, `"rows"`, or `"both"`):
1. Compute the $E^2$ page dimensions $\dim E^2_{p,q}$.
2. Compute the rank of all non-zero differentials $d_r$ for $r \ge 2$:
   - For column filtration: $d_r: E^r_{p,q} \to E^r_{p-r, q+r-1}$.
   - For row filtration: $d_r: E^r_{p,q} \to E^r_{p+r-1, q-r}$.
3. Compute the $E^\infty$ page dimensions $\dim E^\infty_{p,q}$.
4. Compute total homology dimensions $\dim H_n(\mathrm{Tot})$.

## Verification Invariants

- Page recursion identity:
  $$\dim E^{r+1}_{p,q} = \dim E^r_{p,q} - \mathrm{rank}(d_r \text{ leaving } (p,q)) - \mathrm{rank}(d_r \text{ arriving at } (p,q))$$
- Abutment identity:
  $$\sum_{p+q=n} \dim E^\infty_{p,q} = \dim H_n(\mathrm{Tot})$$

## Input Format

```json
{
  "id": "c020_01_worked_example",
  "filtration": "columns",
  "dims": {
    "2,0": 1,
    "1,0": 1,
    "1,1": 1,
    "0,1": 1
  },
  "d_h": {
    "2,0": [[1]],
    "1,1": [[1]]
  },
  "d_v": {
    "1,1": [[1]]
  }
}
```

## Output Format

```json
{
  "status": "SOLVED",
  "filtration": "columns",
  "E2": {
    "2,0": "1",
    "0,1": "1"
  },
  "differentials": [
    {
      "r": "2",
      "from": "2,0",
      "rank": "1"
    }
  ],
  "Einf": {},
  "tot_homology": {}
}
```

If $d^h d^v \ne d^v d^h$, $d^h d^h \ne 0$, or $d^v d^v \ne 0$:
```json
{
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "DH_DV_NOT_COMMUTING",
    "generator": "1,2:0"
  }
}
```
