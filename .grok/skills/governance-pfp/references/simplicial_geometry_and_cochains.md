# Simplicial Geometry & Discrete Cochains

AuthorityEffect: None.

## 1. Simplicial Homology & Boundary Relations

1. **Complex Structure:** A $k$-simplex $\sigma_k = [v_0, v_1, \dots, v_k]$ has dimension $k = |V| - 1$.
2. **Boundary Operator:** The simplicial boundary operator $\partial_k: C_k \to C_{k-1}$ is defined by:
   $$\partial_k [v_0, \dots, v_k] = \sum_{i=0}^k (-1)^i [v_0, \dots, \hat{v}_i, \dots, v_k]$$
   satisfying the fundamental topological identity $\partial_{k-1} \circ \partial_k = 0$.
3. **Coboundary Operator:** The discrete coboundary operator $\delta^0: C^0 \to C^1$ assigns to each vertex potential $\phi \in C^0(V; \mathbb{Q})$ the edge difference:
   $$(\delta^0 \phi)(e_{uv}) = \phi(v) - \phi(u)$$

## 2. Metric Simplicial Geometry & Gram Matrices

1. **Exact Rational Metric:** All squared edge lengths $s_{ij} = d(v_i, v_j)^2$ must be strictly positive rationals ($s_{ij} \in \mathbb{Q}_{>0}$). Floating-point metric values are forbidden in discrete decision paths.
2. **Gram Matrix Embeddability:** For a $k$-simplex with base vertex $v_0$ and vertices $v_1, \dots, v_k$, the Gram matrix $G \in \mathbb{Q}^{k \times k}$ has entries:
   $$G_{ij} = \frac{1}{2} \left( s_{0i} + s_{0j} - s_{ij} \right)$$
3. **Positive Definiteness:** By Sylvester's criterion, the simplex embeds into Euclidean space $\mathbb{R}^k$ if and only if $G$ is strictly positive definite:
   $$\det(G_m) > 0 \quad \text{for all leading principal minors } m = 1, \dots, k$$

## 3. Cochain Defects, CUT Moves & Obstructions

1. **Boundary Defect $\Phi_1$:** For a carrier cochain $c \in C^1(E; \mathbb{Q})$, the boundary defect measures the distance to the exact coboundary subspace:
   $$\Phi_1(c) = \min_{\phi \in C^0} \|c - \delta^0 \phi\|_1$$
2. **The CUT Move:** An exact gauge transformation shifting edge values by vertex potentials:
   $$c'(e_{uv}) = c(e_{uv}) - (\phi(v) - \phi(u))$$
   A candidate CUT move is admissible if and only if it satisfies monotonic descent: $\Phi_1(c') < \Phi_1(c)$.
3. **Survivor Obstruction $\Gamma_2$:** A cycle $C = \sum e_i$ with non-zero holonomy sum $\sum_{e \in C} c(e) \neq 0$ represents a non-trivial cohomology class $[c] \in H^1(G; \mathbb{Q})$. No vertex potential transformation can eliminate this defect ($\Gamma_2 > 0$).
4. **Dual Circulation Witness:** Optimality ($\Phi_1(c) = \text{val}$) is certified without duality gap only by exhibiting an explicit dual circulation $w \in C_1(G; \mathbb{Q})$ satisfying:
   $$d_0^T w = 0 \quad \text{and} \quad \|w\|_\infty \le 1$$
