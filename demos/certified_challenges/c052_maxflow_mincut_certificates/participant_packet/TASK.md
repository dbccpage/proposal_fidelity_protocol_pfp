# Task: Challenge C052 — Max-Flow with Min-Cut Certificates

## Formal Problem

Given a directed multigraph $G = (V, E)$ with nodes $V = \{0, \dots, N-1\}$, source $s$, sink $t$ ($s \ne t$), and integer capacities $0 \le \operatorname{cap}_e \le 10^{18}$ on directed arcs $e = (u, v, \text{cap})$.

Compute:
1. An exact maximum feasible flow vector $f$ where each arc carries an integer flow $0 \le f_e \le \operatorname{cap}_e$.
2. Flow conservation: for every node $v \notin \{s, t\}$, total inflow equals total outflow.
3. An exact minimum $s$–$t$ cut certificate represented by the vertex subset $S \subseteq V$ containing $s$ and not containing $t$ ($s \in S$, $t \notin S$).
4. The cut capacity $\operatorname{cap}(S) = \sum_{e = (u, v) \in E: u \in S, v \notin S} \operatorname{cap}_e$ must exactly equal the total net flow value $\operatorname{val}(f) = \sum_{e = (s, v)} f_e - \sum_{e = (u, s)} f_e$.
5. Complementary slackness: all forward cut edges ($u \in S, v \notin S$) must be fully saturated ($f_e = \operatorname{cap}_e$), and all backward cut edges ($u \notin S, v \in S$) must carry zero flow ($f_e = 0$).

## Input Format

RFC 8785 JSON:
```json
{
  "case_id": "mf_ex_01",
  "n": 4,
  "s": 0,
  "t": 3,
  "arcs": [
    [0, 1, "3"],
    [0, 2, "2"],
    [1, 2, "1"],
    [1, 3, "2"],
    [2, 3, "3"]
  ]
}
```
Capacities may be given as non-negative integer decimal strings or integers.

## Output Format

If feasible and solvable:
```json
{
  "case_id": "mf_ex_01",
  "status": "SOLVED",
  "value": "5",
  "flow": ["3", "2", "1", "2", "3"],
  "cut_S": [0]
}
```
- `value`: exact net flow value as canonical decimal string.
- `flow`: list of canonical decimal strings matching the exact input order of `arcs`.
- `cut_S`: list of strict integer node IDs ($s \in S, t \notin S$) defining the minimum cut.

If the input is malformed or out of scope ($s == t$, negative capacity, node ID $\ge N$ or $< 0$):
```json
{
  "case_id": "mf_ex_06",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "SOURCE_EQUALS_SINK"}
}
```
