# C060 Task: Checker Synthesis Scored by Mutation Kill Rate

## Objective
Synthesize a total, crash-proof mathematical certificate checker exposing `def check(case: Any, cert: Any) -> Dict[str, Any]` that verifies weighted-$\ell^1$ ($\Phi_1$) cochain repair self-certificates under exact rational arithmetic.

The candidate checker is evaluated on two dual criteria:
1. **Zero Autoimmunity:** Must emit `ACCEPT` on all mathematically valid primal-dual certificates without false rejections.
2. **100% Mutation Kill Rate:** Must detect and reject all hostile certificate and schema mutations, emitting canonical rejection codes without crashing, raising exceptions, or drifting into floating-point imprecision.

## Contract & Specification
Your checker must expose:
```python
def check(case: Any, cert: Any) -> Dict[str, Any]: ...
```

### Input Arguments
- `case`: Dictionary defining the coboundary matrix $d_0 \in \mathbb{Q}^{m \times n}$, cochain $\omega \in \mathbb{Q}^m$, and positive weights $w \in \mathbb{Q}^m_{>0}$:
  ```json
  {
    "d0": [["1", "-1"], ["0", "1"]],
    "omega": ["3", "-2"],
    "w": ["1", "1"]
  }
  ```
- `cert`: Dictionary containing candidate repair $\alpha \in \mathbb{Q}^n$, residual $r \in \mathbb{Q}^m$, dual witness $y \in \mathbb{Q}^m$, and value $\text{value} \in \mathbb{Q}$:
  ```json
  {
    "alpha": ["1", "-2"],
    "r": ["0", "0"],
    "y": ["0", "0"],
    "value": "0"
  }
  ```

### Output Schema
If the certificate is completely valid:
```json
{
  "verdict": "ACCEPT",
  "code": null,
  "reason": "Valid self-certificate."
}
```
If the certificate is invalid or malformed:
```json
{
  "verdict": "REJECT",
  "code": "<REJECTION_CODE>",
  "reason": "<Explanatory human-readable reason>"
}
```

### Closed Rejection Codes
The checker must return one of the following exact typed rejection codes (evaluated in logical order):
1. `SCHEMA`: `case` or `cert` is not a `dict`, or missing required keys (`d0`, `omega`, `w` in `case`; `alpha`, `r`, `y`, `value` in `cert`), or elements are non-list/dict containers.
2. `NONCANONICAL_RATIONAL`: Any rational representation fails canonical string form:
   - Integers must be `"0"` or optional `"-"` followed by non-zero digit `[1-9]` and digits `[0-9]*` (no leading zeroes like `"01"`, no leading plus `"+1"`, no slashed integer `"1/1"`).
   - Fractions must be `"<int>/<pos_int>"` with denominator $> 1$ and $\gcd(|p|, q) == 1$.
   - Any float, boolean, null, whitespace, or invalid character is rejected under this code.
3. `DIMENSION`: Dimension mismatch between matrix rows/cols, vectors $w$, $\omega$, $r$, $y$ (length $m$), or $\alpha$ (length $n$), or empty dimensions ($m=0$ or $n=0$).
4. `NONPOSITIVE_WEIGHT`: Any weight $w_e \le 0$.
5. `RESIDUAL_MISMATCH`: The residual fails $r = \omega - d_0 \alpha$ under exact rational matrix-vector arithmetic.
6. `PRIMAL_VALUE_MISMATCH`: The declared value fails $\text{value} = \sum_{e=1}^m w_e |r_e|$ or $\text{value} < 0$.
7. `DUAL_NOT_IN_COKERNEL`: The dual witness fails $d_0^T y = 0$.
8. `DUAL_BOUND_VIOLATED`: Any dual coordinate fails $|y_e| \le w_e$.
9. `DUAL_VALUE_MISMATCH`: The dual evaluation fails $y^T \omega = \text{value}$.

## Critical Invariants
- **Total Arithmetic:** Never raise exceptions on unparseable, malformed, or hostile inputs. All exceptions must be caught and converted to `SCHEMA` or `NONCANONICAL_RATIONAL`.
- **Zero Floating-Point:** All calculations must use `fractions.Fraction` or exact integer arithmetic. Never cast to `float`.
- **Canonical Ordering:** Precedence of checks must proceed from structural (`SCHEMA`, `NONCANONICAL_RATIONAL`, `DIMENSION`, `NONPOSITIVE_WEIGHT`) to algebraic (`RESIDUAL_MISMATCH`, `PRIMAL_VALUE_MISMATCH`, `DUAL_NOT_IN_COKERNEL`, `DUAL_BOUND_VIOLATED`, `DUAL_VALUE_MISMATCH`).
