# Challenge C026: Frustration-Free Projector Hamiltonians

**AuthorityEffect:** None. **Status:** Active. **Domain:** c_quantum. **Tier:** T3.  
**Budget Ceiling:** $1.00 billed inference per arm. **Target Cost:** < $0.05.  
**Models:** Open weights, at most 70B total parameters. **Protocol:** SG-CP v1.

---

## 1. Task Objective

Synthesize an exact, deterministic solver module exposing:

```python
def solve(case: dict) -> dict
```

that decides whether a hidden sum of local rational projectors $H = \sum_i w_i \tilde{P}_i$ has a zero-energy ground state, returning:
1. If frustration-free ($\dim K > 0$): an exact basis for the common kernel $K = \bigcap_i \ker(\tilde{P}_i)$.
2. If frustrated ($\dim K = 0$): an exact left inverse certificate $L$ such that $L \cdot M = I_D$, where $M$ is the vertically stacked matrix of extended projectors.
3. If malformed or out of bounds: a typed refusal (`OUT_OF_SCOPE` or `UNKNOWN`).

---

## 2. Input Specification

A case dictionary contains:
- `case_id`: String identifier (e.g. `"ff_03"`).
- `local_dims`: List of integers $[d_0, d_1, \dots, d_{n-1}]$, with $d_s \in \{2, 3\}$ and total dimension $D = \prod_{s=0}^{n-1} d_s \le 64$.
- `terms`: List of up to 20 local projector terms. Each term contains:
  - `support`: List of distinct site indices $S \subseteq \{0, \dots, n-1\}$ with $|S| \le 3$.
  - `weight`: Non-zero rational string $w_i > 0$ (e.g. `"1"`, `"7/3"`).
  - `matrix`: Row-major matrix of dimension $d_S \times d_S$, where $d_S = \prod_{s \in S} d_s$. Matrix entries are Gaussian rationals represented as 2-element lists `["a", "b"]` encoding $a + b \cdot i \in \mathbb{Q}(i)$.

### Extension Convention

A local term $P$ on support sites $S = (s_1, \dots, s_k)$ is extended to an operator $\tilde{P}$ on $\mathcal{H} = \bigotimes_{s=0}^{n-1} \mathbb{C}^{d_s}$ by placing $P$ on the specified sites and identity $I_{d_j}$ on all other sites $j \notin S$. In computational basis order (row-major integer indexing $x = \sum_s x_s \prod_{r > s} d_r$), the matrix elements are:
$$\tilde{P}_{x, y} = P_{x|_S, y|_S} \prod_{j \notin S} \delta_{x_j, y_j}$$

---

## 3. Output Contract

The solver must return RFC 8785 canonical JSON matching one of the following schemas:

### A. Frustration-Free Ground Space
```json
{
  "id": "ff_03",
  "status": "SOLVED",
  "frustration_free": true,
  "kernel_dim": 4,
  "kernel_basis": [
    [["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"], ["0", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
    ...
  ]
}
```
Validation rules:
- `kernel_basis` contains exactly `kernel_dim` vectors.
- Each vector has dimension $D$.
- Annihilation: $\tilde{P}_i v = 0$ for all terms $i$ and all basis vectors $v$.
- Linear independence: $\mathrm{rank}(\text{kernel\_basis}) = \text{kernel\_dim}$.
- Stacked rank identity: $\text{kernel\_dim} = D - \mathrm{rank}(M)$, where $M = [\tilde{P}_1; \dots; \tilde{P}_m]$.

### B. Frustrated Certificate (Trivial Kernel)
```json
{
  "id": "ff_04",
  "status": "SOLVED",
  "frustration_free": false,
  "certificate": {
    "kind": "left_inverse",
    "matrix": [ ... D rows of m*D Gaussian rational entries ... ]
  }
}
```
Validation rules:
- Matrix $L$ has dimension $D \times (m \cdot D)$.
- Left-inverse identity: $L \cdot M = I_D$ exactly over $\mathbb{Q}(i)$.

### C. Out-of-Scope (Malformed Projectors)
```json
{
  "id": "ff_05",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "term": 2,
    "reason": "not_idempotent",
    "entry": [1, 3]
  }
}
```
Reason must be `"not_hermitian"` or `"not_idempotent"`, naming the offending row/col in `entry`.

### D. Refusal (Out of Bounds)
```json
{
  "id": "ff_06",
  "status": "UNKNOWN",
  "refusal_code": "DIMENSION_OUT_OF_BOUNDS"
}
```
Triggered when total dimension $D > 64$, or support contains invalid site indices.

---

## 4. Reference Facts

1. **Hard-core triangle:** For qubits on a triangle with terms $|11\rangle\langle 11|$ on edges $(0,1)$, $(1,2)$, $(0,2)$, the ground space is spanned by independent set states $\{|000\rangle, |100\rangle, |010\rangle, |001\rangle\}$. Thus $\dim K = 4$.
2. **Singlet triangle:** For qubits on a triangle with singlet projectors $\frac{1}{2}(|01\rangle - |10\rangle)(\langle 01| - \langle 10|)$ on each pair, the ground space is the fully symmetric subspace, $\dim K = 4$.
3. **Triplet triangle:** For qubits on a triangle with triplet projectors $I - |s\rangle\langle s|$ on each pair, no state can be simultaneous singlet on all pairs: $K = \{0\}$ and the system is frustrated.
