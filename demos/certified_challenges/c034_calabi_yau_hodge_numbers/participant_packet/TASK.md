# C034 Task: Calabi-Yau Hodge Numbers from Reflexive Polytopes

**AuthorityEffect:** None. **Protocol:** SG-CP v1. **Domain:** d_physics_mtheory. **Tier:** T2.

## 1. Mathematical Background
A 4-dimensional lattice polytope $\Delta \subset \mathbb{R}^4$ with vertices in $\mathbb{Z}^4$ is **reflexive** if:
1. The origin $(0, 0, 0, 0)$ is in the strict interior of $\Delta$.
2. The origin is the unique interior lattice point of $\Delta$, i.e., $\text{int}(\Delta) \cap \mathbb{Z}^4 = \{(0, 0, 0, 0)\}$.
3. Every facet $F$ of $\Delta$ lies on an affine hyperplane $\langle u, x \rangle = -1$ for some dual lattice point $u \in \mathbb{Z}^4$. Equivalently, its polar dual polytope $\Delta^* \subset \mathbb{R}^4$, defined by:
   $$\Delta^* = \{ y \in \mathbb{R}^4 \mid \langle y, x \rangle \ge -1 \quad \forall x \in \Delta \}$$
   is also a lattice polytope with vertices in $\mathbb{Z}^4$.

By Batyrev's theorem (1994), any 4-dimensional reflexive polytope $\Delta$ determines a family of Calabi–Yau threefold hypersurfaces $X$ in a Gorenstein toric Fano variety. The Hodge numbers $h^{1,1}(X)$ and $h^{2,1}(X)$ are given by:
$$h^{1,1}(X) = l(\Delta^*) - 5 - \sum_{\text{codim }\theta^* = 1} l^*(\theta^*) + \sum_{\text{codim }\theta^* = 2} l^*(\theta^*) l^*(\theta)$$
$$h^{2,1}(X) = l(\Delta) - 5 - \sum_{\text{codim }\theta = 1} l^*(\theta) + \sum_{\text{codim }\theta = 2} l^*(\theta) l^*(\theta^*)$$
where:
- $l(P) = |P \cap \mathbb{Z}^4|$ is the total number of lattice points in polytope $P$.
- $l^*(\theta) = |\text{relint}(\theta) \cap \mathbb{Z}^4|$ is the number of lattice points in the relative interior of face $\theta$.
- For a face $\theta \prec \Delta$ of dimension $k$, its dual face $\theta^* \prec \Delta^*$ has dimension $4 - 1 - k = 3 - k$.
  - Facets of $\Delta^*$ have codimension 1 in $\Delta^*$ ($\dim \theta^* = 3$), dual to vertices of $\Delta$.
  - 2-dimensional faces of $\Delta^*$ have codimension 2 in $\Delta^*$ ($\dim \theta^* = 2$), dual to edges of $\Delta$ ($\dim \theta = 1$).
- The topological Euler characteristic is $\chi(X) = 2(h^{1,1}(X) - h^{2,1}(X))$.
- Reading duality: If input polytope $P$ is read as $\Delta^*$, the associated Calabi-Yau is the mirror manifold with $h^{1,1}$ and $h^{2,1}$ interchanged.

Reference value: for $\Delta^* = \operatorname{conv}\{e_1, e_2, e_3, e_4, -e_1 - e_2 - e_3 - e_4\}$, the quintic threefold, $(h^{1,1}, h^{2,1}) = (1, 101)$ with $\chi = -200$.

## 2. Input Specification & Bounds
- Input is an RFC 8785 canonical JSON mapping with fields:
  - `case_id` (or `id`): string identifier.
  - `reading`: `"primal"` (polytope is $\Delta$) or `"dual"` (polytope is $\Delta^*$).
  - `vertices`: array of $V$ points, where each point is a 4-element array of integers $[x_1, x_2, x_3, x_4]$.
- Bounds:
  - Coordinate bound: $|x_i| \le 30$ for all coordinates.
  - Vertex bound: $V \le 40$ input points.
  - Affine dimension: $\dim(P) = 4$.

## 3. Output Contract
The solver must expose `def solve(case: Mapping[str, Any]) -> dict[str, Any]` returning:

1. For valid reflexive polytopes (`status: "SOLVED"`):
```json
{
  "id": "cy_01",
  "status": "SOLVED",
  "reflexive": true,
  "h11": 1,
  "h21": 101,
  "euler": -200,
  "face_data": {
    "l_delta": 126,
    "l_delta_star": 6,
    "facets_delta_star": [
      {"normal": [4, -1, -1, -1], "interior_points": 0}
    ],
    "codim2_products": []
  }
}
```

2. For non-reflexive or lower-dimensional polytopes (`status: "OUT_OF_SCOPE"`):
```json
{
  "id": "cy_non_ref",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "facet_distance",
    "normal": [1, 1, 0, 0],
    "distance": 2
  }
}
```
Witness kinds:
- `"facet_distance"`: facet hyperplane is $\langle u, x \rangle = -d$ with $d \ne 1$.
- `"origin_not_interior"`: origin is not strictly in the interior of the convex hull.
- `"dimension_deficient"`: affine dimension $< 4$.
- `"multiple_interior_points"`: strictly more than one interior lattice point.

3. For out-of-bounds or malformed inputs (`status: "UNKNOWN"`):
```json
{
  "id": "cy_oob",
  "status": "UNKNOWN",
  "refusal_code": "COORDINATES_OUT_OF_BOUNDS"
}
```
Closed refusal enums:
- `COORDINATES_OUT_OF_BOUNDS`: any $|x_i| > 30$.
- `TOO_MANY_VERTICES`: number of input points $> 40$.
- `MALFORMED_CASE_STRUCTURE`: missing fields, non-integer coordinates, invalid list shapes.
- `INVALID_READING_SPECIFIER`: reading not in `["primal", "dual", "delta", "delta_star"]`.
- `DIMENSION_LESS_THAN_FOUR`: affine dimension $< 4$.
