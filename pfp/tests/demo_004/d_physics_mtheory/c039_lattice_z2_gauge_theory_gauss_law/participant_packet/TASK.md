# Challenge C039: Lattice Z2 Gauge Theory and Gauss's Law

**Domain:** `d_physics_mtheory`  
**Tier:** T3 ($1.00 ceiling, $0.10 target, <= 70B open weights, `allow_fallbacks: false`)  
**Protocol:** SG-CP v1  
**AuthorityEffect:** None  

---

## 1. Task Overview

Challenge C039 examines the discrete topological degeneracy of Kitaev's $\mathbb{Z}_2$ toric code on arbitrary cellulated closed surfaces, together with the dimensions of $\mathbb{Z}_2$ Gauss's law charge sectors on connected graphs.

Given either:
1. A 2-dimensional closed cell complex $\Sigma = (V, E, F)$ under query `"degeneracy"`, or
2. A finite connected graph $G = (V, E)$ with static vertex background charges $c_v \in \{+1, -1\}$ under query `"gauss_law_sector"`,

the task is to compute the exact topological invariants, ground state degeneracy, canonical symplectic logical Pauli operators, or Gauss sector dimensions under declared conditions.

---

## 2. Mathematical Definitions

### 2.1 Cell Complex and Operators
- The 2D cell complex $\Sigma$ consists of:
  - 0-cells (vertices) $v \in \{0, \dots, V - 1\}$.
  - 1-cells (edges) $e \in \{0, \dots, E - 1\}$, specified as pairs $[u, v]$ with $0 \le u, v < V$. If $u = v$, $e$ represents a self-loop.
  - 2-cells (faces) $p \in \{0, \dots, F - 1\}$, given as ordered closed edge walks:
    $$\partial p = [[e_{i_1}, d_1], [e_{i_2}, d_2], \dots, [e_{i_m}, d_m]]$$
    where $e_{i_j} \in \{0, \dots, E - 1\}$ and $d_j \in \{+1, -1\}$ indicates orientation.
- For each edge $e$ and face $p$, the traversal multiplicity $m(e, p) = \sum_{j: e_{i_j} = e} 1$.
- For each edge $e$ and vertex $v$, the incidence multiplicity $m(e, v)$ counts the number of edge-ends incident to $v$ ($1$ for normal edge, $2$ for self-loop).
- Physical qubits reside on edges $e \in E$, yielding Hilbert space dimension $2^E$.
- The star operator at vertex $v$ enforces the discrete $\mathbb{Z}_2$ Gauss law:
  $$A_v = \prod_{e \in E} X_e^{m(e, v) \pmod 2}$$
- The plaquette operator at face $p$ measures magnetic flux:
  $$B_p = \prod_{e \in E} Z_e^{m(e, p) \pmod 2}$$
- Over $\mathbb{F}_2$, the ranks satisfy $\operatorname{rank}(A) = V - 1$ and $\operatorname{rank}(B) = F - 1$ for closed connected surfaces.
- The Euler characteristic is $\chi = V - E + F$.
- The number of encoded logical qubits is:
  $$k = E - \operatorname{rank}(A) - \operatorname{rank}(B) = 2 - \chi = \dim_{\mathbb{F}_2} H^1(\Sigma; \mathbb{Z}_2)$$
  and the ground space degeneracy is $\text{GSD} = 2^k = 2^{2 - \chi}$.
  - For orientable surfaces of genus $g$: $\chi = 2 - 2g \implies k = 2g, \text{GSD} = 2^{2g}$.
  - For non-orientable surfaces of genus $h$: $\chi = 2 - h \implies k = h, \text{GSD} = 2^h$.

### 2.2 Canonical Symplectic Logical Operators
When $k > 0$, the solver returns $k$ pairs of logical Pauli operators $(Z_1, \dots, Z_k)$ and $(X_1, \dots, X_k)$ encoded as length-$E$ strings over $\{'I', 'X', 'Z'\}$ satisfying:
1. Commutation with Stabilizers:
   $$[Z_i, A_v] = 0, \quad [Z_i, B_p] = 0, \quad [X_j, A_v] = 0, \quad [X_j, B_p] = 0$$
2. Self-Commutation:
   $$[Z_i, Z_j] = 0, \quad [X_i, X_j] = 0 \quad \forall i, j$$
3. Symplectic Conjugation:
   $$[Z_i, X_j] = \delta_{ij} \pmod 2$$
   where $1$ denotes anticommutation and $0$ denotes commutation.
4. Non-Triviality:
   The logical operators are linearly independent modulo the stabilizer span $\langle A_v, B_p \rangle$.

### 2.3 Gauss's Law Sector Dimension
For a connected graph $G = (V, E)$ with static vertex charges $c_v \in \{+1, -1\}$:
- The Gauss sector is the subspace satisfying $A_v |\psi\rangle = c_v |\psi\rangle$ for all $v \in V$.
- Consistency requires $\prod_{v \in V} c_v = +1$.
- If $\prod_{v \in V} c_v = -1$: the sector dimension is $0$, accompanied by witness `{"charge_product": -1}`.
- If $\prod_{v \in V} c_v = +1$: the sector dimension is $2^{E - V + 1}$.

---

## 3. Input Schemas

### Degeneracy Query
```json
{
  "case_id": "tc_01",
  "query": "degeneracy",
  "vertices": [0, 1, 2, 3],
  "edges": [[0, 1], [1, 2], [2, 0], [0, 3], [1, 3], [2, 3]],
  "faces": [
    [[0, 1], [1, 1], [2, 1]],
    [[0, 1], [4, 1], [3, -1]],
    [[1, 1], [5, 1], [4, -1]],
    [[2, 1], [3, 1], [5, -1]]
  ]
}
```

### Gauss's Law Sector Query
```json
{
  "case_id": "tc_07",
  "query": "gauss_law_sector",
  "vertices": [0, 1, 2, 3],
  "edges": [[0, 1], [1, 2], [2, 3], [3, 0]],
  "charges": {"0": 1, "1": 1, "2": 1, "3": 1}
}
```

---

## 4. Output Schemas

### Degeneracy Solved
```json
{
  "id": "tc_01",
  "status": "SOLVED",
  "V": 4,
  "E": 6,
  "F": 4,
  "euler": 2,
  "rank_star": 3,
  "rank_plaquette": 3,
  "k": 0,
  "gsd": 1,
  "logicals": {"z": [], "x": []}
}
```

### Gauss Sector Solved (Non-Empty)
```json
{
  "id": "tc_07",
  "status": "SOLVED",
  "sector_dimension": 2
}
```

### Gauss Sector Solved (Empty)
```json
{
  "id": "tc_08",
  "status": "SOLVED",
  "sector_dimension": 0,
  "witness": {"charge_product": -1}
}
```

### Refusal (Out of Scope)
```json
{
  "id": "tc_09",
  "status": "OUT_OF_SCOPE",
  "witness": {"kind": "edge_not_in_two_faces", "edge": 0, "count": 1}
}
```

### Refusal (Unknown / Oversized)
```json
{
  "id": "tc_10",
  "status": "UNKNOWN",
  "refusal_code": "TOO_MANY_EDGES"
}
```

---

## 5. Refusal Taxonomy

The solver operates fail-closed with the following closed enum enforcements:
- `OUT_OF_SCOPE`:
  - `"edge_not_in_two_faces"`: Edge appears fewer or more than 2 times across face boundaries.
  - `"vertex_link_not_a_circle"`: Vertex neighborhood link is not homeomorphic to a circle.
  - `"disconnected_surface"`: Surface possesses multiple connected components.
  - `"disconnected_graph"`: Sector query graph possesses multiple connected components.
- `UNKNOWN`:
  - `"TOO_MANY_EDGES"`: Edge count $E > 300$.
  - `"MALFORMED_CASE_STRUCTURE"`: Missing mandatory keys or invalid schema types.
