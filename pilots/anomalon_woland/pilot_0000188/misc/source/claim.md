# Dossier 1: Exact F2 Chain Complex & Frustrated Spin Triangle Parity Obstruction

## 1. Mathematical Claim

**Claim Identifier:** `CLM-DEMO4-F2-SPIN-001`  
**Epistemic Posture:** Finite discrete chain complex and syndrome check over the binary field $\mathbb{F}_2$.  
**Target Statement:**  
On the 3-vertex triangular 1-skeleton complex $K = (V, E, F)$ over the finite field $\mathbb{F}_2 = \{0, 1\}$:
1. The coboundary sequence satisfies exact nilpotence:
   $$d_1 \circ d_0 = 0 \pmod 2$$
2. The uniform antiferromagnetic bond requirement cochain $c_{\mathrm{afm}} = (1, 1, 1)^T \in C^1(K; \mathbb{F}_2)$ exhibits a non-zero face curl:
   $$d_1 c_{\mathrm{afm}} = 1 + 1 + 1 \equiv 1 \pmod 2 \ne 0$$
3. By exact nilpotence, no vertex spin configuration $s \in C^0(K; \mathbb{F}_2) \cong \mathbb{F}_2^3$ can satisfy $d_0 s = c_{\mathrm{afm}}$.
4. For every vertex spin assignment $s$, the residual defect $r = c_{\mathrm{afm}} - d_0 s \pmod 2$ has Hamming weight $\|r\|_0 \ge 1$.
5. The optimal spin configuration $s^* = (0, 1, 0)^T$ achieves the minimal residual defect $\|c_{\mathrm{afm}} - d_0 s^*\|_0 = 1$ (leaving exactly one frustrated bond).

---

## 2. Epistemic Ledger (Claim Hygiene Rule)

### 2.1 What This Dossier Supports
- Demonstrates in this finite toy setting that an odd cycle of antiferromagnetic bonds over $\mathbb{F}_2$ cannot be simultaneously satisfied due to non-zero face curl ($d_1 c \ne 0$).
- Demonstrates exact syndrome decoding isolating the frustrated bond location without continuous or probabilistic approximations.
- Verifies that coboundary nilpotence $d_1 d_0 = 0 \pmod 2$ holds algebraically on the discrete triangle.

### 2.2 What This Dossier Does NOT Support
- Does **not** establish quantum spin-1/2 operators, Pauli algebra, or continuous Hilbert space dynamics.
- Does **not** establish macroscopic thermodynamic frustration or spin glass phase transitions.
- Does **not** solve non-Abelian gauge theory or continuous gauge invariance.

### 2.3 The Narrowest Defensible Claim
*On the finite triangle 1-skeleton complex over $\mathbb{F}_2$, the constant-1 cochain $c = (1, 1, 1)^T$ has non-vanishing face curl $d_1 c = 1 \pmod 2$, algebraically excluding $c \in \operatorname{im}(d_0)$ and certifying that every vertex spin configuration leaves at least one frustrated bond.*

### 2.4 Next Test Needed
Scale to planar triangular and kagome lattices with first Betti number $b_1 \ge 2$, testing syndrome decoders against multiple competing frustrated loops.
