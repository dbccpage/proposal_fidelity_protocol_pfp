# PO-001 Quick Start (v2.0)

Cover maps give local comparisons. They extend uniquely to a strict presheaf when every saturated-chain product agrees. Otherwise, declared comparable-pair maps have composition defect

$$K_{c,b,a}=r_{b,a}r_{c,b}-r_{c,a}.$$

The core identities are

$$\begin{aligned}
(d_1d_0s)_{c,b,a}&=K_{c,b,a}s(c),\\
(d_2K(s))_{d,c,b,a}&=K_{c,b,a}(r_{d,c}s(d))-K_{c,b,a}s(c),\\
\delta_2K&=0,\\
\delta_2\delta_1T&=K\circ T-T\circ K.
\end{aligned}$$

On the full section space, $K=0$ exactly when $d_1d_0=0$. The operator identity $\delta_2K=0$ does not make $\delta_2\delta_1$ vanish or define a generic $H^2$ quotient.

## Read and replay

From the package root:

```bash
python -m pip install -e .
python scripts/verify_package.py
```

The [notebook](../jupyter_notebooks/00_enter_po001.ipynb) contains asserted exact examples. The [manuscript](../covering_edge_descent.md), [ledger](../covering_edge_descent_claim_ledger.md), and [review](review_2026_10_02.md) explain their evidential limits. Lean sources are separate from the fresh Python replay.

## Check the inference before using it

| Tempting inference | Required correction |
|---|---|
| A spanning forest supplies a flat completion preserving all cover maps. | All saturated cover-chain products must agree; a diamond with products $1/4$ and $1/6$ refutes the inference. |
| $K=-A$ on every triple. | This specialization requires both inner legs to be covers; longer triples retain mixed terms. |
| $\delta_2K=0$ constructs a lax 2-presheaf. | Categories, typed compositor 2-cells, units, and coherence still need construction. |
| Bell marginal flatness proves noncontextuality. | A PR box has flat marginal maps and no nonnegative normalized global probability extension; its declared gluing distance is $2$. |
| A cost-two ledger charge is a measured curvature norm. | The charge is assigned by convention; an independent norm needs separate evidence. |
| A face-poset cocycle proves Regge geometry. | The fixtures supply no metric or deficit-angle identification. |

These are useful study questions: state the missing hypothesis, identify a counterexample, and explain exactly what the cited finite test establishes.
