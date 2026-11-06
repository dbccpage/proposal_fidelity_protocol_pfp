# C032: Six-Dimensional Supergravity Anomaly Cancellation

**AuthorityEffect:** None. **Status:** active. **Domain:** d_physics_mtheory. **Tier:** T3.  
**Budget:** $1.00 billed inference ceiling, $0.05 target. **Models:** Open weights, $\le 70\text{B}$ total parameters.  
**Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

---

## 1. Mathematical Task Specification

In six-dimensional $\mathcal{N}=(1,0)$ supergravity with $T$ tensor multiplets ($0 \le T \le 30$), $V$ vector multiplets and $H$ hypermultiplets, canceling local gauge and gravitational anomalies requires the 8-form anomaly polynomial to factorize via the Green-Schwarz-Sagnotti mechanism into a quadratic form in $\mathbb{R}^{1, T}$.

A candidate spectrum consists of:
- $T$: Number of tensor multiplets ($0 \le T \le 30$).
- Gauge group $G = \prod_{i=1}^k G_i$ with at most $k \le 4$ simple factors from:
  - $SU(N)$ ($2 \le N \le 8$)
  - $SO(N)$ ($7 \le N \le 14, N \ne 8$)
  - $Sp(N)$ ($1 \le N \le 4$)
  - $G_2, F_4, E_6, E_7, E_8$
- Hypermultiplets given as representations of the gauge factors, with multiplicities $x_R \in \mathbb{Q}_{>0}$ (may be half-integers $1/2, 3/2, \dots$ for pseudoreal representations).
- Neutral hypermultiplets $H_{\text{neutral}} \ge 0$.

### 1.1 Anomaly Cancellation Conditions

The solver must evaluate the spectrum against the 5 necessary conditions in strict canonical order:

1. **Condition 1 (Pure Gravitational Anomaly):**
   $$H - V + 29T = 273$$
   where $V = \sum_{i=1}^k \dim G_i$ and $H = H_{\text{neutral}} + \sum_R x_R \dim R$.

2. **Condition 2 (Irreducible Quartic Anomaly Cancellation):**
   For each simple gauge factor $G_i$ with an independent quartic Casimir ($SU(N \ge 4)$, $SO(N \ge 7)$, $Sp(N \ge 2)$):
   $$B_{\text{adj}} = \sum_R x_R B^R$$
   where $B^R$ is the quartic trace coefficient defined by $\operatorname{tr}_R F^4 = B^R \operatorname{tr} F^4 + C^R (\operatorname{tr} F^2)^2$.
   *(Groups without an independent quartic Casimir: $SU(2), SU(3), Sp(1), G_2, F_4, E_6, E_7, E_8$ have $B^R = 0$ identically and no quartic condition applies).*
   For these groups the whole quartic trace is carried by $C^R$. In particular, for $SU(2)$, $SU(3)$ and $Sp(1)$ the fundamental satisfies $\operatorname{tr} F^4 = \tfrac{1}{2} (\operatorname{tr} F^2)^2$, so the general $SU(N)$ or $Sp(N)$ quartic coefficient is folded into $C^R$ (conventions of Kumar, Morrison and Taylor 2010). Correction notice (2026-09-29): earlier versions of the reference solver and examples omitted this fold for $SU(2)$, $SU(3)$ and $Sp(1)$; the examples now use the folded values.

3. **Condition 3 (Gravitational Self-Intersection):**
   $$a \cdot a = 9 - T$$
   where $a \in \mathbb{R}^{1, T}$ is the gravitational anomaly vector.

4. **Condition 4 (Gauge Vector Intersections):**
   With group normalization factor $\lambda_i \in \{1, 2, 6, 12, 60\}$:
   $$a \cdot b_i = \frac{1}{6} \lambda_i \left( A_{\text{adj}} - \sum_R x_R A^R \right)$$
   $$b_i \cdot b_i = \frac{1}{3} \lambda_i^2 \left( \sum_R x_R C^R - C_{\text{adj}} \right)$$
   $$b_i \cdot b_j = \lambda_i \lambda_j \sum_{R_i, R_j} x_{R_i, R_j} A^{R_i} A^{R_j} \quad (i \ne j)$$

5. **Condition 5 (Realizability in Signature $(1, T)$):**
   The $(k+1) \times (k+1)$ Gram matrix of vectors $(a, b_1, \dots, b_k)$ defined by the inner products above must be realizable in signature $(1, T)$. By Sylvester's Law of Inertia, its exact inertia $(n_+, n_-, n_0)$ must satisfy:
   $$n_+ \le 1 \quad \text{and} \quad n_- \le T$$

---

## 2. Input and Output Schemas

### 2.1 Input JSON Schema

```json
{
  "id": "sg_case_01",
  "T": 7,
  "gauge_group": ["SU(4)"],
  "hypers": [
    {"multiplicity": 16, "reps": ["fund"]},
    {"multiplicity": 2, "reps": ["antisym"]}
  ],
  "neutral_hypers": 9
}
```

### 2.2 Output Schemas

#### A. All Conditions Satisfied (`PASSES_NECESSARY_CONDITIONS`)
```json
{
  "id": "sg_case_01",
  "status": "SOLVED",
  "H": 85,
  "V": 15,
  "T": 7,
  "gravitational": {"lhs": 273, "ok": true},
  "coefficients": {
    "a.a": "2",
    "a.b": ["-2"],
    "b.b": ["0"]
  },
  "quartic": [
    {"factor": 0, "group": "SU(4)", "B_adj": "8", "B_hypers": "8", "ok": true}
  ],
  "gram_inertia": {"positive": 1, "negative": 1, "zero": 0},
  "verdict": "PASSES_NECESSARY_CONDITIONS"
}
```

#### B. Condition Violated (`ANOMALOUS`)
When a condition fails, report `"verdict": "ANOMALOUS"` and name the lowest-numbered failing condition in `first_failure`:
```json
{
  "id": "sg_case_02",
  "status": "SOLVED",
  "H": 84,
  "V": 15,
  "T": 7,
  "verdict": "ANOMALOUS",
  "first_failure": {
    "condition": 1,
    "lhs": "272",
    "rhs": "273"
  }
}
```

#### C. Out of Scope (`OUT_OF_SCOPE`)
```json
{
  "id": "sg_case_03",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "half_hyper_in_nonpseudoreal_rep",
    "factor": 0
  }
}
```

#### D. Typed Refusal (`UNKNOWN`)
```json
{
  "id": "sg_case_04",
  "status": "UNKNOWN",
  "refusal_code": "GROUP_NOT_SUPPORTED"
}
```

---

## 3. Closed Refusal Catalog & Out-of-Scope Kinds

### Closed Refusal Codes
- `MALFORMED_CASE_STRUCTURE`: Input missing required fields or non-mapping.
- `GROUP_NOT_SUPPORTED`: Gauge factor not in supported catalogue or more than 4 factors.
- `REPRESENTATION_NOT_SUPPORTED`: Representation not recognized for group.
- `T_OUT_OF_BOUNDS`: $T < 0$ or $T > 30$.
- `NEUTRAL_HYPERS_OUT_OF_BOUNDS`: Neutral hypers $< 0$.
- `MULTIPLICITY_OUT_OF_BOUNDS`: Multiplicity $\le 0$ or not an integer/half-integer.
- `NON_INTEGER_HYPER_COUNT`: Total charged hyper dimension is not integer.

### Out-of-Scope Witness Kinds
- `half_hyper_in_nonpseudoreal_rep`: Half-hyper ($1/2, 3/2, \dots$) assigned to a representation that is not pseudoreal.
- `unsupported_so8_triality`: SO(8) gauge factor specified (omitted per spec due to extra quartic Pfaffian invariant).

---

## 4. Claim Hygiene & Epistemic Boundaries

- **What this evaluates:** Whether a solver can systematically and exactly compute representation dimensions, group theory trace coefficients $A^R, B^R, C^R$, evaluate anomaly cancellation conditions, and determine Gram matrix inertia in signature $(1, T)$.
- **What this does not evaluate:** The quantum non-perturbative existence of supergravity theories, string theory landscape/swampland conjectures, or continuum compactifications.
- **Narrowest defensible claim:** "The candidate solver exactly verified the algebraic anomaly cancellation and Gram inertia conditions on the evaluated 6D (1,0) supergravity spectra."
