# C037: Fusion Rules from the Verlinde Formula

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T3.
**Budget:** $0.50 ceiling ($0.05 target) billed inference per arm. **Models:** open weights, at most 70B total parameters.
**Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

## 1. Challenge Objective
Synthesize an exact, sandboxed mathematical solver in pure Python standard library that computes the central charge $c \in \mathbb{Q}$, conformal weights $h \in \mathbb{Q}$, and complete fusion coefficients $N_{ij}^k \in \mathbb{Z}_{\ge 0}$ of hidden Virasoro minimal models $M(p, p')$ and WZW models $SU(2)_k$, derived from the Verlinde formula in exact arithmetic, without floating-point approximations.

## 2. Mathematical Pipeline

### 2.1 SU(2)_k WZW Models ($1 \le k \le 20$)
1. **Primaries:**
   Primaries are labeled by twice the spin: an integer $a \in \{0, 1, \dots, k\}$.
   The vacuum primary is $a = 0$, represented as label `[0]`.

2. **Central Charge and Conformal Weights:**
   $$c = \frac{3k}{k+2}$$
   $$h_a = \frac{a(a+2)}{4(k+2)}, \quad a \in \{0, 1, \dots, k\}$$

3. **Modular S-Matrix and Verlinde Formula:**
   $$S_{ab} = \sqrt{\frac{2}{k+2}} \sin\left(\frac{\pi (a+1)(b+1)}{k+2}\right), \quad 0 \le a, b \le k$$
   $$N_{ab}^c = \sum_{m=0}^k \frac{S_{am} S_{bm} S_{cm}}{S_{0m}} = \frac{2}{k+2} \sum_{m=0}^k \frac{\sin\left(\frac{\pi(a+1)(m+1)}{k+2}\right) \sin\left(\frac{\pi(b+1)(m+1)}{k+2}\right) \sin\left(\frac{\pi(c+1)(m+1)}{k+2}\right)}{\sin\left(\frac{\pi(m+1)}{k+2}\right)}$$
   Each term evaluates into the cyclotomic field $\mathbb{Q}(\zeta_{4(k+2)})$, summing to an exact non-negative integer.

4. **Combinatorial Truncation (Clebsch-Gordan Rule):**
   $$N_{ab}^c = 1 \iff |a - b| \le c \le \min(a + b, 2k - a - b) \text{ and } a + b + c \equiv 0 \pmod 2$$
   and $0$ otherwise.

### 2.2 Virasoro Minimal Models $M(p, p')$
1. **Admissible Parameters:**
   Coprime integers $p > p' \ge 2$, with $p \le 13$.

2. **Central Charge:**
   $$c = 1 - \frac{6(p - p')^2}{p p'}$$

3. **Kac Table and Primary Fields:**
   Kac labels are pairs $(r, s)$ with $1 \le r \le p' - 1$ and $1 \le s \le p - 1$, subject to the identification:
   $$(r, s) \sim (p' - r, p - s)$$
   The number of distinct physical primaries is $N_{\mathrm{prim}} = \frac{(p - 1)(p' - 1)}{2}$.
   The vacuum primary is $(1, 1)$, represented as label `[1, 1]`, with $h_{1,1} = 0$.

4. **Conformal Weights:**
   $$h_{r,s} = \frac{(p r - p' s)^2 - (p - p')^2}{4 p p'}$$

5. **Canonical Representative Convention:**
   For each equivalence class $\{(r, s), (p' - r, p - s)\}$, the canonical representative is the pair satisfying:
   $$(s, r) \le (p - s, p' - r)$$
   Canonical primaries are ordered lexicographically by $(r, s)$:
   $$(r_1, s_1) < (r_2, s_2) \iff r_1 < r_2 \text{ or } (r_1 = r_2 \text{ and } s_1 < s_2)$$
   Under this ordering, the vacuum primary `[1, 1]` is always first.

6. **Fusion Ring:**
   The fusion rules of $M(p, p')$ are isomorphic to the tensor product of $SU(2)_{p'-2}$ (for $r-1$) and $SU(2)_{p-2}$ (for $s-1$), factored through the Kac identification:
   $$\mathcal{N}_{(r_1, s_1), (r_2, s_2)}^{(r_3, s_3)} = N^{(SU(2)_{p'-2})}_{r_1-1, r_2-1, r_3-1} \cdot N^{(SU(2)_{p-2})}_{s_1-1, s_2-1, s_3-1}$$
   The fusion coefficient for canonical primary $k$ in $i \times j$ is:
   $$N_{ij}^k = \mathcal{N}_{i, j}^{(r_k, s_k)} + \mathcal{N}_{i, j}^{(p'-r_k, p-s_k)}$$
   listing every nonzero $N_{ij}^k \ge 1$ with $i \le j$ in the canonical primary ordering.

## 3. Query Schemas & Wire Contracts

### 3.1 Input Schema
Input is a JSON object declaring either an $SU(2)_k$ model or a Virasoro minimal model:

**SU(2)_k Query:**
```json
{
  "case_id": "su2_k02",
  "model": "su2",
  "k": 2
}
```

**Minimal Model Query:**
```json
{
  "case_id": "min_m04_03",
  "model": "minimal",
  "p": 4,
  "p_prime": 3
}
```

### 3.2 Output Schema (`SOLVED`)
```json
{
  "id": "min_m04_03",
  "status": "SOLVED",
  "central_charge": "1/2",
  "primaries": [
    {"label": [1, 1], "h": "0"},
    {"label": [1, 2], "h": "1/16"},
    {"label": [2, 1], "h": "1/2"}
  ],
  "fusion": [
    [[1, 1], [1, 1], [1, 1], 1],
    [[1, 1], [1, 2], [1, 2], 1],
    [[1, 1], [2, 1], [2, 1], 1],
    [[1, 2], [1, 2], [1, 1], 1],
    [[1, 2], [1, 2], [2, 1], 1],
    [[1, 2], [2, 1], [1, 2], 1],
    [[2, 1], [2, 1], [1, 1], 1]
  ]
}
```
* `central_charge`: reduced rational string (`"1/2"`, `"-22/5"`, `"1"`).
* `primaries`: list of primary objects containing `label` (e.g. `[a]` for $SU(2)$, `[r, s]` for minimal) and reduced rational conformal weight `h`.
* `fusion`: list of 4-element entries `[label_i, label_j, label_k, N_{ij}^k]` for every $N_{ij}^k > 0$, with $i \le j$ in the canonical primary ordering.

### 3.3 Fail-Closed Refusal Schemas
1. **`OUT_OF_SCOPE`**: If minimal model parameters are not coprime ($\gcd(p, p') > 1$) or ordering is invalid ($p \le p'$ or $p' < 2$):
```json
{
  "id": "bad_coprime",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "not_coprime",
    "gcd": 2
  }
}
```
2. **`UNKNOWN`**: For out-of-bounds parameters or unlisted families:
   * `LEVEL_OUT_OF_BOUNDS`: when $k < 1$, $k > 20$, or $p > 13$.
   * `UNLISTED_MODEL_FAMILY`: when `model` is not in `{"su2", "minimal"}`.
   * `MALFORMED_CASE_STRUCTURE`: when types or structure violate the schema or boolean types are injected.
```json
{
  "id": "bad_level",
  "status": "UNKNOWN",
  "refusal_code": "LEVEL_OUT_OF_BOUNDS"
}
```

## 4. Claim Hygiene
* **Supports:** Exact rational and cyclotomic evaluation of fusion coefficients, central charges, and conformal weights for $SU(2)_k$ ($k \le 20$) and Virasoro minimal models ($p \le 13$) in pure standard library.
* **Does not support:** Claims regarding non-rational CFTs, higher-rank WZW models (such as $SU(3)_k$), or physical conformal field theories beyond the stated domain.
* **Narrowest defensible claim:** "The solver computes exact fusion coefficients, central charges, and conformal weights for declared rational CFT families using exact cyclotomic and combinatorial operations."
* **Next test needed:** Extension to $SU(3)_k$ and affine Lie algebras requiring rank-2 weight lattice and Kostant multiplicity machinery.
