---
name: tdvp-trace-norm-projection
description: "Verify trace-norm oblique projections onto a tangent space and their dual witness certificates."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# tdvp-trace-norm-projection

## Authority & Compliance

- **AuthorityEffect**: `None`
- **Governance**: Panepistimion / Techne / Logos Thanatos
- **Scope**: Time-Dependent Variational Principle (TDVP), Schatten-1 McLachlan Oblique Projection, Dual Witness Sign Matrix.

---

## 🏛️ Theoretical Background & Mathematical Formulation

The trace-norm Time-Dependent Variational Principle (TDVP) computes the optimal vector field $X \in T_\rho \mathcal{M}$ tangent to the state manifold $\mathcal{M}$ that minimizes the Schatten-1 norm error:

$$
P_\rho^{\|\cdot\|_1}(L) = \arg\min_{X \in T_\rho \mathcal{M}} \|X - L\|_1
$$

A dual witness matrix $W \in \partial \|\cdot\|_1(Q)$ certifies the optimality of the residual $Q = L - X^*$ whenever:

$$
\|W\|_\infty \le 1, \qquad \operatorname{Tr}(W^\dagger Q) = \|Q\|_1, \qquad \operatorname{Tr}(W^\dagger X) = 0 \quad \forall X \in T_\rho \mathcal{M}
$$

---

## 📋 Verification Protocol & Inspection Rules

1. **Subgradient Witness Invariant**: Verify that $W = \operatorname{sign}(Q) + P_{T_\rho \mathcal{M}}^\perp(V)$ satisfies $\|W\|_\infty \le 1$.
2. **Obliquity Bounds**: Confirm that the projection error $\|Q\|_1$ is monotonically non-increasing under Schatten-1 contractive operations.
3. **Floating-Point Isolation**: Perform exact rational cyclotomic verification or arbitrary-precision interval arithmetic when certifying subgradient sign boundaries.

---

## 🛠️ Verification Commands

```powershell
# Run TDVP trace-norm projection verification suite
python -m pytest engine_py/core_quantum_physics/tests/test_tdvp_projection.py -v
```
