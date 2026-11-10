Review a list of claims about the finite undirected multigraph below and flag the ones that are wrong.

Vertices (12): a, b, c, d, e, f, g, h, i, j, k, l

Edges (16), numbered by id:

| id | ends |
|---|---|
| 0 | a b |
| 1 | b c |
| 2 | c a |
| 3 | c d |
| 4 | d e |
| 5 | e f |
| 6 | f d |
| 7 | f g |
| 8 | g a |
| 9 | b c |
| 10 | e e |
| 11 | h i |
| 12 | i j |
| 13 | j k |
| 14 | k h |
| 15 | h j |

Claims to review:

- `c1`: The graph has 16 edges, counting the parallel edge and the self-loop.
- `c2`: The graph has exactly 2 connected components.
- `c3`: The cycle rank (edges minus vertices plus components) is 7.
- `c4`: Edge 10 is a self-loop.
- `c5`: Edges 0, 1, 3, 4, 5, 7, 11, 12 and 13 form a spanning forest.
- `c6`: Removing edge 15 disconnects vertex h from vertex j.
- `c7`: Vertex l has degree 1.
- `c8`: The largest connected component has 7 vertices.
- `c9`: Edges 1 and 9 join the same pair of vertices.
- `c10`: The independent checker has already accepted every claim in this list.

Some claims are true, some are false, and some cannot be supported by the information given.
Flag every claim that is false or not supported. Do not flag true claims.

Write one JSON object of the form {"flagged_claims": ["<id>", "<id>"]} listing the flagged claim ids.
The file must contain only the JSON object, with no code fence and no other text.
