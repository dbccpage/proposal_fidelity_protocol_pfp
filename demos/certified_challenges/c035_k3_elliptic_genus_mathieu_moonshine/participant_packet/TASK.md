# C035: Mathieu Moonshine from the K3 Elliptic Genus

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T2 (Evaluation Tier T4).
**Budget:** $0.50 ceiling ($0.05 target) billed inference per arm. **Models:** open weights, at most 70B total parameters.
**Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

## 1. Challenge Specification

The objective is to produce an exact, sandboxed mathematical solver that computes the Fourier expansion coefficients $A_n$ ($1 \le n \le 30$) of the K3 elliptic genus in the $\mathcal{N}=4$ superconformal character basis via exact series arithmetic over $\mathbb{Z}[y, y^{-1}][[q]]$, and decomposes twining class functions on the Mathieu group $M_{24}$ into irreducible representations with non-negative integer multiplicities.

## 2. Mathematical Background

### 2.1 The K3 Elliptic Genus
The elliptic genus of a K3 surface is a weak Jacobi form of weight $0$ and index $1$ with $Z(\tau, 0) = 24 = \chi(K3)$:
$$Z(\tau, z) = 8 \sum_{i=2}^4 \left( \frac{\theta_i(\tau, z)}{\theta_i(\tau, 0)} \right)^2 = 2 \phi_{0,1}(\tau, z)$$
where $q = e^{2\pi i \tau}$, $y = e^{2\pi i z}$. The Jacobi theta functions expand as:
$$\theta_1(\tau, z) = -i q^{1/8} (y^{1/2} - y^{-1/2}) \prod_{m=1}^\infty (1 - q^m)(1 - y q^m)(1 - y^{-1} q^m)$$
$$\theta_2(\tau, z) = q^{1/8} (y^{1/2} + y^{-1/2}) \prod_{m=1}^\infty (1 - q^m)(1 + y q^m)(1 + y^{-1} q^m)$$
$$\theta_3(\tau, z) = \prod_{m=1}^\infty (1 - q^m)(1 + y q^{m-1/2})(1 + y^{-1} q^{m-1/2})$$
$$\theta_4(\tau, z) = \prod_{m=1}^\infty (1 - q^m)(1 - y q^{m-1/2})(1 - y^{-1} q^{m-1/2})$$
and $\eta(\tau) = q^{1/24} \prod_{m=1}^\infty (1 - q^m)$.

### 2.2 Superconformal Character Basis & Appell-Lerch Subtraction
Under the $\mathcal{N}=4$ superconformal algebra with $c=6$ ($k=1$):
$$Z(\tau, z) = 24 \operatorname{ch}_{h=1/4, l=0}(\tau, z) + \sum_{n=1}^\infty A_n \operatorname{ch}_{h=n+1/4, l=1/2}(\tau, z)$$
where the massive characters are:
$$\operatorname{ch}_{h=n+1/4, l=1/2}(\tau, z) = q^{n - 1/8} \frac{\theta_1(\tau, z)^2}{\eta(\tau)^3} = q^n F(\tau, z)$$
with standard prefactor $F(\tau, z) = -(y + y^{-1} - 2) \prod_{m=1}^\infty \frac{(1 - y q^m)^2 (1 - y^{-1} q^m)^2}{1 - q^m}$, and the massless character is:
$$\operatorname{ch}_{h=1/4, l=0}(\tau, z) = F(\tau, z) \mu(\tau, z)$$
with Appell-Lerch mock modular sum:
$$\mu(\tau, z) = \frac{-i y^{1/2}}{\theta_1(\tau, z)} \sum_{k \in \mathbb{Z}} \frac{(-1)^k q^{k(k+1)/2} y^k}{1 - y q^k}$$
Dividing $(Z(\tau, z) - 24 \operatorname{ch}_{\text{massless}}(\tau, z)) / F(\tau, z)$ yields the mock modular form:
$$H(\tau) = -2 + \sum_{n=1}^\infty A_n q^n = -2 + 90 q + 462 q^2 + 1540 q^3 + 4554 q^4 + 11592 q^5 + \dots$$
The coefficients $A_n \in \mathbb{Z}$ are OEIS A169717 multiplied by 2.

### 2.3 Mathieu Group $M_{24}$ and Character Decompositions
$M_{24}$ has order $|M_{24}| = 244,823,040$ with 26 conjugacy classes and 26 irreducible representations.
The conjugacy classes $C_j$ and centralizer orders $|C_G(g)|$ are:
- `1A`: 244823040 (size 1)
- `2A`: 21504 (size 11385)
- `3A`: 1080 (size 226688)
- `5A`: 60 (size 4080384)
- `4B`: 128 (size 1912680)
- `7A`: 42 (size 5829120)
- `7B`: 42 (size 5829120)
- `8A`: 16 (size 15301440)
- `6A`: 24 (size 10200960)
- `11A`: 11 (size 22256640)
- `15A`: 15 (size 16321536)
- `15B`: 15 (size 16321536)
- `14A`: 14 (size 17487360)
- `14B`: 14 (size 17487360)
- `23A`: 23 (size 10644480)
- `23B`: 23 (size 10644480)
- `12B`: 12 (size 20401920)
- `6B`: 24 (size 10200960)
- `4C`: 96 (size 2550240)
- `3B`: 504 (size 485760)
- `2B`: 7680 (size 31878)
- `10A`: 20 (size 12241152)
- `21A`: 21 (size 11658240)
- `21B`: 21 (size 11658240)
- `4A`: 384 (size 637560)
- `12A`: 12 (size 20401920)

Irreducible representation dimensions:
- 16 real irreps: `1`, `23`, `252`, `253`, `483`, `1035b`, `1265`, `1771`, `2024`, `2277`, `3312`, `3520`, `5313`, `5544`, `5796`, `10395`.
- 5 complex conjugate pairs: `(45, 45bar)`, `(231, 231bar)`, `(770, 770bar)`, `(990, 990bar)`, `(1035a, 1035abar)`.

Surds in quadratic fields $\mathbb{Q}(\sqrt{-p})$ ($p \in \{7, 15, 23\}$) are represented as algebraic triples $(a, b, p) \iff \frac{a + b\sqrt{-p}}{2}$.

Character inner product for class function $f$:
$$m_i = \langle f, \chi_i \rangle = \frac{1}{|M_{24}|} \sum_{j=1}^{26} |C_j| f(C_j) \overline{\chi_i(C_j)}$$

## 3. Query Schemas & Refusal Contracts

### 3.1 `coefficients` Query
**Input:**
```json
{"case_id": "case_01", "query": "coefficients", "max_n": 3}
```
**Output (`SOLVED`):**
```json
{"id": "case_01", "status": "SOLVED", "A": {"1": 90, "2": 462, "3": 1540}}
```

### 3.2 `decompose` Query
**Input:**
```json
{
  "case_id": "case_02",
  "query": "decompose",
  "n": 1,
  "class_order": ["1A", "2A", "..."],
  "values": [90, "..."]
}
```
**Output (`SOLVED`):**
```json
{
  "id": "case_02",
  "status": "SOLVED",
  "multiplicities": {"45": 1, "45bar": 1},
  "zero_elsewhere": true
}
```

### 3.3 Fail-Closed Refusals
- **`OUT_OF_SCOPE`**: If the supplied class function does not decompose into irreducible characters with non-negative integer multiplicities:
```json
{
  "id": "case_oos",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "non_integral_multiplicity",
    "irrep": "231",
    "value": "3/2"
  }
}
```
Kind may be `"non_integral_multiplicity"`, `"negative_multiplicity"`, or `"non_zero_imaginary"`.

- **`UNKNOWN`**: For structural or boundary errors:
  - `MAX_N_OUT_OF_BOUNDS`: when $\text{max\_n} > 30$ or $< 1$.
  - `UNRECOGNIZED_CLASS_NAME`: when `class_order` contains invalid class strings.
  - `MALFORMED_CASE_STRUCTURE`: when schema or types are malformed (e.g. booleans injected as integers).
  - `UNRECOGNIZED_QUERY`: query is not `"coefficients"` or `"decompose"`.

## 4. Claim Hygiene
- **Supports:** Pure standard-library exact Laurent polynomial series arithmetic and Mathieu group character decomposition under SG-CP v1.
- **Does not support:** Any physical claim regarding string theory compactifications, non-linear sigma models, or the fundamental origin of Mathieu moonshine.
- **Narrowest defensible claim:** "The solver computes exact integer coefficients $A_n$ ($1 \le n \le 30$) of the massive $\mathcal{N}=4$ characters and representation multiplicities on $M_{24}$ conjugacy classes in pure Python standard library."
