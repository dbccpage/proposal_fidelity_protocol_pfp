# 4D Supersymmetric CDT, Nicolai Map & Wheeler-DeWitt Super-Hamiltonian

`AuthorityEffect: None.`
Governance: Panepistimion / Techne / Logos Thanatos.

---

## 1. Theoretical Background & Formulation

In 4D Causal Dynamical Triangulations (CDT), coupling fermionic matter typically induces severe sign fluctuations in the fermion determinant $\det(D_F)$. In supersymmetric extensions ($N=1$ or $N=2$ discretized supergravity on causal triangulations):

### A. Topological Witten Index
$$\Delta_{\text{Witten}} = \operatorname{Tr}\left((-1)^F e^{-\beta H_{\text{SUSY}}}\right) = n_B^0 - n_F^0$$
remains an exact topological invariant independent of the temperature parameter $\beta$.

### B. Nicolai Map Cancellation
A non-perturbative Nicolai transformation $N(\phi) = \xi$ transforms the coupled action into a Gaussian measure whose Jacobian determinant matches the Grassmann path integral:
$$\det\left(\frac{\delta N}{\delta \phi}\right) = \operatorname{det}(D_F)$$
guaranteeing a positive-definite effective measure and eliminating the sign problem ($\langle \operatorname{Sign} \rangle = 1.0$) on admitting complexes.

### C. Wheeler-DeWitt Super-Hamiltonian Constraint
The supersymmetry algebra $\{Q, Q^\dagger\} = 2 \mathcal{H}_{\text{super}}$ ensures that physical states annihilate both supercharges, maintaining boundary nilpotence $\partial^2 = 0$ on all foliation slices.

---

## 2. Verification Protocol

1. **Topological Invariance**: Verify $\frac{\partial \Delta_{\text{Witten}}}{\partial \beta} = 0$ across variation in inverse temperature $\beta$.
2. **Jacobian Positivity**: Check that the Nicolai map Jacobian determinant satisfies $\det\left(\frac{\delta N}{\delta \phi}\right) > 0$ on all sampled Pachner $(4,1), (3,2), (2,3), (1,4)$ moves.
3. **Boundary Nilpotence**: Verify $\partial_{k-1} \circ \partial_k = 0$ across all simplicial boundary chains.
4. **Claim Scoping**: Verify all reports explicitly scope results to the discrete finite-dimensional simplicial complex.

---

## 3. Formal Verification Commands

```powershell
# Run formal Lean 4 verification of SUSY Witten index and Nicolai cancellation
lake env lean scratch/test_susy_witten.lean
```
