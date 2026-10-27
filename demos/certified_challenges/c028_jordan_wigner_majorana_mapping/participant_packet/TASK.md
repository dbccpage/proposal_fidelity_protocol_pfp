# Challenge C028: Fermion-to-Qubit Mappings with Exact CAR Checks

**AuthorityEffect:** None. **Status:** Active. **Domain:** c_quantum. **Tier:** T2.  
**Budget Ceiling:** $0.50 billed inference per arm. **Target Cost:** < $0.05.  
**Models:** Open weights, at most 70B total parameters. **Protocol:** SG-CP v1.

---

## 1. Task Objective

Synthesize an exact, deterministic solver module exposing:

```python
def solve(case: dict) -> dict
```

that maps hidden fermionic Hamiltonians to exact qubit Hamiltonians under a declared linear encoding matrix $M \in \mathbb{F}_2^{N \times N}$ (Jordan–Wigner, Parity, Bravyi–Kitaev, or arbitrary invertible linear encodings), computing the $2N$ Majorana images as signed Pauli strings satisfying the canonical anticommutation relations (CAR) exactly, and expanding $H$ into a sum of distinct Pauli strings with real rational coefficients.

---

## 2. Input Specification & Conventions

A case dictionary contains:
- `case_id` or `id`: String identifier (e.g. `"fq_06"`).
- `num_modes`: Integer $N$ with $1 \le N \le 12$.
- `encoding`: $N \times N$ matrix over $\mathbb{F}_2$ (binary integers 0 and 1). Occupation vector $n \in \mathbb{F}_2^N$ is stored as qubit computational basis state $|M n \pmod 2\rangle$.
- `terms`: List of fermionic terms. Each term has:
  - `coeff`: Pair of strings `[c_re, c_im]` representing Gaussian rational coefficient $c_{\text{re}} + i c_{\text{im}} \in \mathbb{Q}(i)$.
  - `ops`: List of up to 4 operators `[["kind", mode_idx], ...]`, where `kind` is `"ann"` ($a_j$) or `"dag"` ($a_j^\dagger$), and $0 \le \text{mode\_idx} < N$.

### Canonical Conventions
1. **Majorana Operators**:
   $$\gamma_{2j} = a_j + a_j^\dagger, \quad \gamma_{2j+1} = -i(a_j - a_j^\dagger) = i(a_j^\dagger - a_j)$$
   satisfying $\{\gamma_k, \gamma_l\} = 2 \delta_{kl} I$ and $\gamma_k^2 = I$.
   Inverting these relations gives:
   $$a_j = \frac{1}{2}(\gamma_{2j} + i \gamma_{2j+1}), \quad a_j^\dagger = \frac{1}{2}(\gamma_{2j} - i \gamma_{2j+1})$$

2. **Fock Basis Ordering**:
   $$a_j^\dagger |n\rangle = (-1)^{\sum_{k < j} n_k} |n + e_j\rangle \quad \text{if } n_j = 0, \text{ else } 0$$
   $$a_j |n\rangle = (-1)^{\sum_{k < j} n_k} |n - e_j\rangle \quad \text{if } n_j = 1, \text{ else } 0$$

3. **General Linear Encoding**:
   Qubit state $|x\rangle$ stores $|M n \pmod 2\rangle \iff n = M^{-1} x \pmod 2$.
   - For even Majorana $\gamma_{2j}$: represented by $X(M_{*, j}) Z(p^{(j)})$ where $p^{(j)}_l = \sum_{k < j} (M^{-1})_{kl} \pmod 2$.
   - For odd Majorana $\gamma_{2j+1}$: represented by $i X(M_{*, j}) Z(q^{(j)})$ where $q^{(j)}_l = p^{(j)}_l + (M^{-1})_{jl} \pmod 2$.

4. **Pauli Multiplication Rules with Phases**:
   $$X Y = i Z, \quad Y Z = i X, \quad Z X = i Y$$
   $$Y X = -i Z, \quad Z Y = -i X, \quad X Z = -i Y$$
   $$X^2 = Y^2 = Z^2 = I$$
   For Pauli strings, phases multiply across each qubit position, tracking powers of $i$.

---

## 3. Standard Encodings for $N \le 8$

### Jordan-Wigner Encoding ($M = I_N$)
$$M_{\text{JW}} = \begin{pmatrix} 1 & 0 & \dots & 0 \\ 0 & 1 & \dots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \dots & 1 \end{pmatrix}$$

### Parity Encoding ($M_{ij} = 1$ for $i \ge j$)
$$M_{\text{Parity}}^{(4)} = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 1 & 1 & 0 & 0 \\ 1 & 1 & 1 & 0 \\ 1 & 1 & 1 & 1 \end{pmatrix}$$

### Bravyi-Kitaev Encoding
For $N=4$:
$$M_{\text{BK}}^{(4)} = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 1 & 1 & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 1 & 1 & 1 & 1 \end{pmatrix}$$
For $N=8$:
$$M_{\text{BK}}^{(8)} = \begin{pmatrix}
1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
1 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
1 & 1 & 1 & 1 & 0 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 & 1 & 1 & 0 & 0 \\
0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1
\end{pmatrix}$$

---

## 4. Output Contract

Responses must be RFC 8785 canonical JSON matching one of:

### A. Solved Case
```json
{
  "id": "fq_06",
  "status": "SOLVED",
  "majoranas": ["+XI", "+YI", "+ZX", "+ZY"],
  "hamiltonian": [["XX", "1/2"], ["YY", "1/2"]]
}
```
Validation rules:
- `majoranas`: List of $2N$ strings with explicit `+` or `-` prefix followed by $N$ Pauli characters $\in \{I, X, Y, Z\}$.
- Majoranas must square to $I$ and pairwise anticommute.
- `hamiltonian`: List of pairs `[pauli_str, coeff_str]` sorted lexicographically by Pauli string.
- All coefficients must be real rationals with zero terms removed.

### B. Refusal: Out of Scope (Singular Encoding)
```json
{
  "id": "fq_07",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "singular_encoding",
    "kernel_vector": [1, 1]
  }
}
```

### C. Refusal: Out of Scope (Non-Hermitian Hamiltonian)
```json
{
  "id": "fq_poison_03",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "non_hermitian_hamiltonian",
    "details": "..."
  }
}
```

### D. Refusal: Unknown (Exceeds Mode Bound)
```json
{
  "id": "fq_08",
  "status": "UNKNOWN",
  "refusal_code": "TOO_MANY_MODES"
}
```
