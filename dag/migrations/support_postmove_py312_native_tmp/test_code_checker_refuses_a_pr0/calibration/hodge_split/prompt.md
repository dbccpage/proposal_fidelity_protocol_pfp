Compute the exact discrete Hodge decomposition of an edge flow on a finite 2-complex and write it as one JSON object.

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

Coboundary conventions:

- d0 maps a vertex function p to the edge function (d0 p)(u,v) = p(v) - p(u).
- d1 maps an edge function x to the triangle function (d1 x)(a,b,c) = x(a,b) + x(b,c) - x(a,c).

The edge flow is f = [3, -1, 2, 0, 4, 1, -2, 5, 1], listed by edge position.

Find the unique decomposition f = d0 p + d1^T q + h, where h satisfies d0^T h = 0 and d1 h = 0, using the standard inner product on edges. Normalise the potential by p(0) = 0.

Required JSON fields. Write every rational value as a string in lowest terms, such as "-3/2" or "4".

- `b0`, `b1`: the Betti numbers of the complex over the rationals (integers).
- `euler_characteristic`: vertices minus edges plus filled triangles (integer).
- `potential`: p at vertices 0 to 5 (6 rational strings, with p(0) = "0").
- `gradient`: d0 p by edge position (9 rational strings).
- `curl`: d1^T q by edge position (9 rational strings).
- `harmonic`: h by edge position (9 rational strings).
- `harmonic_norm_squared`: the sum of the squares of the entries of h (rational string).

The file must contain only the JSON object, with no code fence and no other text.
