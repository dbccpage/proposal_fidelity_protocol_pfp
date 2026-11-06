# Challenge C038: Combinatorial Curvature and Discrete Gauss-Bonnet

**Challenge ID:** `c038_regge_combinatorial_curvature`  
**AuthorityEffect:** None  
**Domain:** `d_physics_mtheory`  
**Tier:** T2 (Ceiling: $0.50, Target: $0.05, Open Weights $\le 70\text{B}$, `allow_fallbacks: False`)  
**Protocol:** SG-CP v1  

---

## 1. Overview & Objective

Challenge C038 evaluates a participant solver synthesizing exact combinatorial curvature algorithms across closed triangulated surfaces and simple connected graphs. The solver exposes a single entry point:
```python
def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    ...
```
The solver must operate strictly within the pure Python standard library using exact rational arithmetic (`fractions.Fraction`) with zero floating-point approximation.

---

## 2. Mathematical Formalization & Invariants

### 2.1 Query Type 1: `"surface"` (Closed 2-Manifold Verification & Discrete Gauss-Bonnet)

An input query of type `"surface"` provides a triangulated complex:
```json
{
  "case_id": "rc_01",
  "query": "surface",
  "triangles": [[0, 1, 2], [0, 2, 3], ...]
}
```
with at most 200 triangles on labelled integer vertices.

#### Closed 2-Manifold Conditions:
The solver must verify the closed 2-manifold hypothesis before evaluating geometric invariants:
1. **Edge Regularity**: Every undirected edge $e = \{u, v\}$ must appear in exactly 2 triangles. If an edge appears in $< 2$ or $> 2$ triangles, the surface fails the 2-manifold condition.
2. **Vertex Link Condition**: For every vertex $v$, its link graph $\operatorname{Lk}(v)$ is defined on the neighborhood $N(v) = \{u \mid \{u, v\} \in E\}$ with edges $\{u, w\}$ whenever $\{v, u, w\}$ is a triangle in the complex. The link graph $\operatorname{Lk}(v)$ must form a single connected 2-regular cycle of length $\deg(v) \ge 3$. If $\operatorname{Lk}(v)$ is disconnected or non-2-regular (such as at a pinched vertex where multiple cones meet), the surface fails the 2-manifold condition.
3. **Connectedness**: The dual triangle adjacency graph must form a single connected component.

#### Topological & Curvature Invariants:
When the closed 2-manifold conditions are satisfied:
- **Element Counts**: $V = |\bigcup_{t} t|$, $E = |\{\{u, v\} \subset t\}|$, $F = |\{\text{triangles}\}|$. For closed triangulated surfaces, $3F = 2E$.
- **Euler Characteristic**: $\chi = V - E + F$.
- **Orientability**: Evaluated via consistent orientation propagation (e.g. breadth-first traversal across shared edges). Returns `true` if all triangles can be oriented consistently; `false` otherwise.
- **Classification**:
  - Orientable surface of genus $g = (2 - \chi) // 2$: `{"orientable_genus": g}`.
  - Non-orientable surface of genus $h = 2 - \chi$: `{"non_orientable_genus": h}`.
- **Combinatorial Vertex Curvature**:
  In 2D equilateral Regge calculus, the deficit angle at vertex $v$ is $\epsilon_v = 2\pi - \deg(v)\frac{\pi}{3} = \frac{\pi}{3}(6 - \deg(v))$. The normalized combinatorial curvature is:
  $$k_v = \frac{\epsilon_v}{2\pi} = 1 - \frac{\deg(v)}{6} = \frac{6 - \deg(v)}{6}$$
  Formatted as an exact canonical reduced rational string `"num/den"` or integer literal.
- **Discrete Gauss-Bonnet Identity**:
  Under the declared assumptions, the sum of combinatorial curvatures satisfies:
  $$\sum_{v \in V} k_v = \sum_{v \in V} \left(1 - \frac{\deg(v)}{6}\right) = V - \frac{2E}{6} = V - \frac{E}{3} = V - E + F = \chi$$

---

### 2.2 Query Type 2: `"graph"` (Forman & Ollivier-Ricci Curvature with Exact Transport Certificates)

An input query of type `"graph"` provides a simple connected graph:
```json
{
  "case_id": "rc_07",
  "query": "graph",
  "edges": [[0, 1], [1, 2], [2, 0], [2, 3]],
  "alpha": "0"
}
```
with at most 60 vertices, at most 200 edges, and rational laziness $\alpha \in [0, 1)$.

#### Curvatures & Certificates:
For every undirected edge $\{u, v\}$ with $u < v$:
1. **Forman-Ricci Curvature**:
   $$F(u, v) = 4 - \deg(u) - \deg(v)$$
   Emitted as an exact integer.
2. **Probability Measures**:
   For node $x \in V_G$:
   $$m_x(z) = \begin{cases} \alpha & \text{if } z = x \\ \frac{1 - \alpha}{\deg(x)} & \text{if } z \in N(x) \\ 0 & \text{otherwise} \end{cases}$$
3. **Wasserstein-1 Optimal Transport**:
   The $L_1$ transport cost between measures $m_u$ and $m_v$ under graph geodesic metric $d_G$ is:
   $$W_1(m_u, m_v) = \min_{\pi \ge 0} \sum_{i, j \in V_G} \pi(i, j) d_G(i, j)$$
   subject to the marginal constraints:
   $$\sum_{j} \pi(i, j) = m_u(i) \quad \forall i \in V_G, \qquad \sum_{i} \pi(i, j) = m_v(j) \quad \forall j \in V_G$$
4. **Kantorovich Dual Potential & Zero Duality Gap**:
   By Kantorovich duality:
   $$W_1(m_u, m_v) = \max_{\phi} \sum_{w \in V_G} \phi(w) (m_u(w) - m_v(w))$$
   subject to the 1-Lipschitz condition on all graph edges:
   $$|\phi(x) - \phi(y)| \le 1 \quad \forall \{x, y\} \in E_G$$
   The solver must supply both a feasible transport plan $\pi(i, j)$ and a 1-Lipschitz dual potential $\phi: V_G \to \mathbb{Z}$ satisfying strong duality with zero duality gap:
   $$\sum_{i, j} \pi(i, j) d_G(i, j) = \sum_{w} \phi(w)(m_u(w) - m_v(w)) = W_1$$
5. **Ollivier-Ricci Curvature**:
   Since $d_G(u, v) = 1$ for adjacent vertices:
   $$\kappa(u, v) = 1 - W_1(m_u, m_v)$$
   Formatted as a canonical reduced rational string `"num/den"` or integer literal.

---

## 3. Schemas and Refusal Protocol

### 3.1 Solved Schemas
- **Surface Output**:
```json
{
  "id": "rc_01",
  "status": "SOLVED",
  "V": 6,
  "E": 12,
  "F": 8,
  "euler": 2,
  "orientable": true,
  "classification": {"orientable_genus": 0},
  "vertex_curvature": {"0": "1/3", "1": "1/3", "2": "1/3", "3": "1/3", "4": "1/3", "5": "1/3"}
}
```
- **Graph Output**:
```json
{
  "id": "rc_07",
  "status": "SOLVED",
  "edges": [
    {
      "edge": [0, 1],
      "forman": 0,
      "ollivier": "1/2",
      "plan": [{"from": 1, "to": 0, "mass": "1/2"}, {"from": 2, "to": 2, "mass": "1/2"}],
      "potential": {"0": "0", "1": "1", "2": "0", "3": "0"}
    }
  ]
}
```

### 3.2 Refusal Protocols (Fail-Closed)
- **`OUT_OF_SCOPE`**: Non-manifold surfaces or invalid graphs must be refused fail-closed with a structured diagnostic witness:
  - `{"kind": "edge_not_two_triangles", "edge": [u, v], "count": c}`
  - `{"kind": "vertex_link_not_a_cycle", "vertex": v}`
  - `{"kind": "surface_disconnected", "components": k}`
  - `{"kind": "graph_disconnected", "components": k}`
  - `{"kind": "self_loop", "vertex": v}`
  - `{"kind": "multigraph", "edge": [u, v]}`
- **`UNKNOWN`**: Inputs that exceed parameter bounds or exhibit malformed syntax:
  - `"TOO_MANY_TRIANGLES"` ($F > 200$)
  - `"GRAPH_TOO_LARGE"` ($V > 60$ or $E > 200$)
  - `"INVALID_ALPHA"` ($\alpha < 0$ or $\alpha \ge 1$, or non-rational)
  - `"MALFORMED_CASE_STRUCTURE"`

---

## 4. Verification & Constraints
- Zero floating-point arithmetic allowed; all rationals must be canonical reduced strings or integer literals.
- Booleans (`True`, `False`) are strictly rejected in integer fields (`type(x) is int and not isinstance(x, bool)`).
- Schema whitelists are enforced; unexpected extra keys cause verification rejection.
