# C036: Genus-Zero Invariants of the Quintic via Mirror Symmetry

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T2.
**Budget:** $0.50 ceiling ($0.05 target) billed inference per arm. **Models:** open weights, at most 70B total parameters.
**Protocol:** SG-CP v1.

## 1. Challenge Objective
Synthesize a sandboxed mathematical solver in pure Python standard library that computes genus-zero Gopakumar-Vafa instanton numbers $n_k \in \mathbb{Z}$ and Gromov-Witten invariants $N_k \in \mathbb{Q}$ of one-parameter Calabi-Yau threefolds in weighted projective space $\mathbb{WP}(w_1, w_2, w_3, w_4, w_5)$ with degree $d = \sum_{i=1}^5 w_i$ up to curve degree $D \le 10$, using exact rational series arithmetic over $\mathbb{Q}[[z]]$ and $\mathbb{Q}[[q]]$.

## 2. Mathematical Pipeline
For a pinned one-parameter family with weights $w = (w_1, \dots, w_5)$ and degree $d = \sum_{i=1}^5 w_i$:

1. **Fundamental Period $\varpi_0(z)$:**
   $$\varpi_0(z) = \sum_{n=0}^D \frac{(dn)!}{\prod_{i=1}^5 (w_i n)!} z^n \in \mathbb{Q}[[z]]$$
   with $\varpi_0(0) = 1$.

2. **Logarithmic Period $\varpi_1(z)$ via Frobenius Method:**
   $$\varpi_1(z) = \varpi_0(z) \log z + \widetilde{\varpi}_1(z)$$
   where $\widetilde{\varpi}_1(z) \in \mathbb{Q}[[z]]$ is given by differentiating coefficients with respect to the index parameter $\rho$:
   $$\widetilde{\varpi}_1(z) = \sum_{n=1}^D \frac{(dn)!}{\prod_{i=1}^5 (w_i n)!} \left[ d H_{dn} - \sum_{i=1}^5 w_i H_{w_i n} \right] z^n$$
   where $H_m = \sum_{j=1}^m \frac{1}{j}$ denotes the $m$-th harmonic number ($H_0 = 0$). Note $\widetilde{\varpi}_1(0) = 0$.

3. **Mirror Map $q(z)$ and Series Inversion $z(q)$:**
   $$q(z) = z \exp\left( \frac{\widetilde{\varpi}_1(z)}{\varpi_0(z)} \right) = z \left( 1 + \sum_{k=1}^D \frac{1}{k!} \left( \frac{\widetilde{\varpi}_1(z)}{\varpi_0(z)} \right)^k \right) \pmod{z^{D+2}}$$
   Invert the power series $q(z) = z + c_2 z^2 + \dots$ to find $z(q) = q + \sum_{k=2}^{D} a_k q^k \pmod{q^{D+1}}$.
   The first $D$ coefficients of $z(q)$ form `mirror_map_coeffs` = $[a_1, a_2, \dots, a_D]$ where $a_1 = 1$.

4. **Yukawa Coupling and Classical Intersection $\kappa$:**
   $$\kappa = \frac{d}{\prod_{i=1}^5 w_i}$$
   In the flat coordinate $t = \frac{1}{2\pi i} \log q$, the Yukawa coupling expands as:
   $$K(q) = \kappa + \sum_{k=1}^D k^3 N_k q^k = \kappa + \sum_{k=1}^D n_k \frac{k^3 q^k}{1 - q^k} \pmod{q^{D+1}}$$

5. **Gromov-Witten Invariants $N_k$:**
   $$N_k = \frac{1}{k^3} [q^k] K(q) \in \mathbb{Q}$$

6. **Gopakumar-Vafa Instanton Numbers $n_k$ (Multiple-Cover Inversion):**
   $$N_k = \sum_{j \mid k} \frac{n_{k/j}}{j^3} \iff n_k = \sum_{j \mid k} \mu(j) \frac{N_{k/j}}{j^3}$$
   where $\mu(j)$ is the Möbius function. Every $n_k$ evaluates to an exact integer ($n_k \in \mathbb{Z}$).

## 3. Pinned One-Parameter Families

Correction notice (2026-09-29): earlier versions of this list gave wrong values for the sextic $n_3$, the octic $n_2$ and $n_3$, and the decic $n_1$ and $n_2$. The values below are those computed by the reference solver and asserted by the package tests.

The challenge evaluates inputs against 4 canonical smooth one-parameter hypersurface families with $h^{1,1} = 1$:
1. **Quintic**: $\mathbb{WP}(1, 1, 1, 1, 1)$, $d = 5$, $\kappa = 5$, $\mu = 5^5 / 1^5 = 3125$.
   * $n_1 = 2875, n_2 = 609250, n_3 = 317206375, n_4 = 242467530000$.
2. **Sextic**: $\mathbb{WP}(1, 1, 1, 1, 2)$, $d = 6$, $\kappa = 3$, $\mu = 6^6 / (1^4 \cdot 2^2) = 11664$.
   * $n_1 = 7884, n_2 = 6028452, n_3 = 11900417220$.
3. **Octic**: $\mathbb{WP}(1, 1, 1, 1, 4)$, $d = 8$, $\kappa = 2$, $\mu = 8^8 / (1^4 \cdot 4^4) = 65536$.
   * $n_1 = 29504, n_2 = 128834912, n_3 = 1423720546880$.
4. **Decic**: $\mathbb{WP}(1, 1, 1, 2, 5)$, $d = 10$, $\kappa = 1$, $\mu = 10^{10} / (1^3 \cdot 2^2 \cdot 5^5) = 800000$.
   * $n_1 = 231200, n_2 = 12215785600$.

## 4. Query Schemas & Wire Contracts

### 4.1 Input Schema
```json
{
  "case_id": "gw_quintic_01",
  "weights": [1, 1, 1, 1, 1],
  "degree": 5,
  "max_curve_degree": 3
}
```
* `weights`: list of 5 positive integers.
* `degree`: positive integer.
* `max_curve_degree`: positive integer $1 \le D \le 10$.

### 4.2 Output Schema (`SOLVED`)
```json
{
  "id": "gw_quintic_01",
  "status": "SOLVED",
  "kappa": "5",
  "gv": {
    "1": "2875",
    "2": "609250",
    "3": "317206375"
  },
  "gw": {
    "1": "2875",
    "2": "4876875/8",
    "3": "8564575000/27"
  },
  "mirror_map_coeffs": ["1", "-770", "171525"]
}
```
* `kappa`: canonical rational string (`"5"` or `"num/den"`).
* `gv`: dict mapping degree string `"k"` to exact integer string $n_k$.
* `gw`: dict mapping degree string `"k"` to reduced rational string $N_k$ (`"int"` or `"num/den"` with $\gcd(\text{num}, \text{den}) = 1$).
* `mirror_map_coeffs`: list of $D$ string rationals for coefficients $a_1, \dots, a_D$ of $z(q)$.

### 4.3 Fail-Closed Refusals
1. **`OUT_OF_SCOPE`**: If the hypersurface is not Calabi-Yau ($d \ne \sum_{i=1}^5 w_i$):
```json
{
  "id": "gw_bad_cy",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "not_calabi_yau",
    "degree": 6,
    "weight_sum": 5
  }
}
```
2. **`UNKNOWN`**: For unpinned families or boundary errors:
   * `FAMILY_NOT_IN_PINNED_LIST`: when $d = \sum w_i$ but the sorted weight vector is not among the 4 pinned families.
   * `MAX_CURVE_DEGREE_OUT_OF_BOUNDS`: when $D < 1$ or $D > 10$.
   * `MALFORMED_CASE_STRUCTURE`: when types or structure violate the JSON schema or boolean types are injected.
```json
{
  "id": "gw_unlisted",
  "status": "UNKNOWN",
  "refusal_code": "FAMILY_NOT_IN_PINNED_LIST"
}
```

## 5. Claim Hygiene
* **Supports:** Exact rational series arithmetic for one-parameter Calabi-Yau mirror symmetry predictions in pure standard library.
* **Does not support:** Physical string dualities, enumerative geometry beyond one-parameter projective hypersurfaces, or unverified Calabi-Yau claims.
* **Narrowest defensible claim:** "The solver computes exact genus-zero Gopakumar-Vafa integers and Gromov-Witten rationals for 4 pinned one-parameter families up to degree $D \le 10$ using rational power series operations."
* **Next test needed:** Expansion to multi-parameter Calabi-Yau threefolds with Picard-Fuchs PDEs in multiple moduli.
