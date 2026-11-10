Compute exact invariants of the finite undirected multigraph below and write them as one JSON object.

Vertices (12): a, b, c, d, e, f, g, h, i, j, k, l

Edges (16), numbered by id. Edge 9 is parallel to edge 1, and edge 10 is a self-loop.

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

Required JSON fields:

- `vertices`: the number of vertices (integer).
- `edges`: the number of edges, counting the parallel edge and the self-loop (integer).
- `components`: the number of connected components, counting isolated vertices (integer).
- `component_sizes`: the vertex count of each component, sorted from largest to smallest (array of integers).
- `cycle_rank`: the first Betti number, edges minus vertices plus components (integer).
- `spanning_forest_edge_ids`: the ids of a spanning forest, sorted ascending (array of integers). It must contain no cycle and must connect every component.

The file must contain only the JSON object, with no code fence and no other text.
