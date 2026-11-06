Review a list of claims about the exact discrete Hodge decomposition of an edge flow, and flag the ones that are wrong.

The complex has vertices 0, 1, 2, 3, 4, 5. Every edge is oriented from its smaller vertex to its larger vertex. The edges, in this order, are:

| position | edge |
|---|---|
| 0 | (0,1) |
| 1 | (1,2) |
| 2 | (0,2) |
| 3 | (2,3) |
| 4 | (3,4) |
| 5 | (2,4) |
| 6 | (4,5) |
| 7 | (3,5) |
| 8 | (1,5) |

The filled triangles are (0,1,2) and (2,3,4), each oriented by increasing vertex order. Triangle (3,4,5) is not filled.

Coboundary conventions: (d0 p)(u,v) = p(v) - p(u), and (d1 x)(a,b,c) = x(a,b) + x(b,c) - x(a,c).

The edge flow is f = [3, -1, 2, 0, 4, 1, -2, 5, 1], listed by edge position. Its unique decomposition is f = d0 p + d1^T q + h, where d0^T h = 0 and d1 h = 0 under the standard inner product on edges, with the potential normalised by p(0) = 0. The gradient part is d0 p, the curl part is d1^T q, and the harmonic part is h.

Claims to review:

- `c1`: The first Betti number b1 of the complex is 2.
- `c2`: The squared norm of the harmonic part is 6.
- `c3`: With p(0) = 0, the potential at vertex 4 is 9/2.
- `c4`: The curl part is zero on edge (2,4).
- `c5`: The gradient part on edge (3,5) is 5/2.
- `c6`: The harmonic part has zero divergence at vertex 3.
- `c7`: The Euler characteristic of the complex is 1.
- `c8`: The curl part is nonzero only on edges of the filled triangle (2,3,4).
- `c9`: Running the exact checker on these values returned exit status 0.

Some claims are true, some are false, and some cannot be supported by the information given.
Flag every claim that is false or not supported. Do not flag true claims.

Write one JSON object of the form {"flagged_claims": ["<id>", "<id>"]} listing the flagged claim ids.
The file must contain only the JSON object, with no code fence and no other text.
