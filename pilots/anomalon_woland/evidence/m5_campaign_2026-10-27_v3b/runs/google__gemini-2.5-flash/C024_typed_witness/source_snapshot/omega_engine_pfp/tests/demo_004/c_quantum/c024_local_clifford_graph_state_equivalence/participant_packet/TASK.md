# Task: C024 Local-Clifford Equivalence of Graph States

**AuthorityEffect:** None. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md). **Domain:** c_quantum. **Tier:** T3.

---

## 1. Problem Definition

Given two simple undirected graphs $G = (V, E)$ and $G' = (V, E')$ on the fixed labelled vertex set $V = \{0, 1, \dots, n-1\}$ with $2 \le n \le 16$:

1. **Validity Check**:
   Verify that $G$ and $G'$ are valid simple undirected graphs:
   - $2 \le n \le 16$.
   - No self-loops ($u \ne v$ for all $\{u, v\} \in E$).
   - No multi-edges or duplicate edges.
   - All vertex indices within $[0, n-1]$.
   If any condition fails, return status `OUT_OF_SCOPE` with a certified defect witness.

2. **Local Complementation ($G * v$)**:
   Local complementation at vertex $v \in V$, denoted $G * v$, replaces the induced subgraph on the neighborhood $N(v) = \{u \in V : \{u, v\} \in E\}$ by its graph complement:
   - For all distinct $u, w \in N(v)$, the edge $\{u, w\}$ is toggled: present $\leftrightarrow$ absent.
   - All other edges in $G$ remain unchanged.
   - Local complementation is an involution: $(G * v) * v = G$.

3. **Equivalence Decision & Certificates**:
   Decide whether $G'$ is local-Clifford equivalent to $G$, meaning $G'$ can be reached from $G$ by a finite sequence of local complementations:
   $$G' = G * v_1 * v_2 * \cdots * v_m$$
   Vertex labels are fixed; no relabelling or graph isomorphism is permitted.

   - **When Equivalent (`equivalent: true`)**:
     Emit a valid vertex sequence `sequence: [v_1, v_2, ..., v_m]`.
     The judge verifies that applying $G * v_1 * \cdots * v_m$ yields exactly $G'$ (identical edge sets).

   - **When Not Equivalent (`equivalent: false`)**:
     Emit a checkable separating invariant certificate.
     The primary invariant is the **cut-rank** $\rho_G(A)$:
     For $A \subseteq V$, $\rho_G(A) = \operatorname{rank}_{\mathbb{F}_2}(\Gamma[A, V \setminus A])$ where $\Gamma$ is the adjacency matrix over $\mathbb{F}_2$.
     The cut-rank function is invariant under local complementation (Bouchet 1991, Oum 2005).
     A subset $A$ with $\rho_G(A) \ne \rho_{G'}(A)$ certifies non-equivalence.
     Certificate schema:
     `{"kind": "cut_rank", "subset": list(A), "rank_g": r_g, "rank_g_prime": r_gp}`.

   - **When the bounded search is inconclusive (`UNKNOWN`)**:
     Emit `refusal_code: "ORBIT_SEARCH_BUDGET_EXHAUSTED"` and a typed
     `orbit_search_budget_exhausted` witness. Reaching a state budget without
     finding an orbit intersection or a separating invariant is not evidence
     of non-equivalence and must never be reported as `equivalent: false`.

---

## 2. Input Specification

A JSON object with schema:
```json
{
  "id": "c024_case_001",
  "num_vertices": 4,
  "g": [[0, 1], [1, 2], [2, 3]],
  "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]]
}
```

- `id`: Unique case identifier string.
- `num_vertices`: Integer $n \in [2, 16]$.
- `g`: List of edges `[u, v]` for graph $G$.
- `g_prime`: List of edges `[u, v]` for graph $G'$.

---

## 3. Output Specification

### Equivalent Graphs (`SOLVED`, `equivalent: true`)
```json
{
  "id": "c024_case_001",
  "status": "SOLVED",
  "equivalent": true,
  "sequence": [1]
}
```

### Non-Equivalent Graphs (`SOLVED`, `equivalent: false`)
```json
{
  "id": "c024_case_nonequiv",
  "status": "SOLVED",
  "equivalent": false,
  "witness": {
    "kind": "cut_rank",
    "subset": [0, 3],
    "rank_g": 2,
    "rank_g_prime": 1
  }
}
```

### Inconclusive Bounded Search (`UNKNOWN`)

```json
{
  "id": "c024_case_budget",
  "status": "UNKNOWN",
  "refusal_code": "ORBIT_SEARCH_BUDGET_EXHAUSTED",
  "witness": {
    "kind": "orbit_search_budget_exhausted",
    "states_visited": 25000,
    "max_orbit_states": 25000
  }
}
```

### Out of Scope Malformed Inputs (`OUT_OF_SCOPE`)
```json
{
  "id": "c024_case_bad",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "self_loop",
    "edge": [2, 2]
  }
}
```

---

## 4. Verification Protocol

The judge packet employs dual independent checkers:
1. **Checker 1 (Exact Row-wise $\mathbb{F}_2$ Simulation)**: Fast adjacency simulator tracking edge toggles under local complementations and computing cut-ranks via Gaussian elimination over $\mathbb{F}_2$.
2. **Checker 2 (Independent NumPy Simulation & Rank Evaluation)**: Independent matrix verification path confirming edge sets and independent $\mathbb{F}_2$ submatrix ranks.
