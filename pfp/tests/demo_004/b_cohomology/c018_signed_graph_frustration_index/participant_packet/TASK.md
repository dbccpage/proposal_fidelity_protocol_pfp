# C018: Frustration Index of Signed Graphs

## Problem Statement

Given a simple graph $G = (V, E)$ with edge signs $\sigma_e \in \{+1, -1\}$:
1. Verify graph validity (no self loops, valid signs $\in \{+1, -1\}$). If invalid, return `OUT_OF_SCOPE`.
2. Find a switching $s: V \to \{+1, -1\}$ minimizing the number of negative edges under $s$:
   $$ l(\Sigma) = \min_{s} |\{uv \in E : s_u \sigma_{uv} s_v = -1\}| $$
3. Return:
   - `SOLVED` if the frustration index $l$ is certified optimal:
     - via `exhaustive` search (replaying all $2^{|V|-1}$ switchings for $|V| \le 20$), OR
     - via `packing` (a set of $k = l$ closed walks that pairwise share no edge, each traversing negative edges an odd number of times).
   - `UNKNOWN` with refusal `OPTIMALITY_UNCERTIFIED` and certified bounds `upper` and `lower` when optimality cannot be certified. This status is admissible only for $|V| > 20$; for $|V| \le 20$ an exhaustive certificate always exists and `SOLVED` is required. `upper` must equal the number of negative edges under the submitted `switching`, and that switching must be locally optimal: flipping any single vertex must not lower the count (equivalently, no vertex has more negative than positive incident edges under the switching, which also gives `upper` $\le |E|/2$). `lower` must be certified by `lower_bound: {"kind": "packing", "cycles": [...]}` listing exactly `lower` closed walks that pairwise share no edge, each traversing negative edges an odd number of times (counted with multiplicity); the packing must be maximal (the edges outside it form a balanced signed graph), and `lower < upper` (if the bounds meet, return `SOLVED`).
4. Counts (`l`, `upper`, `lower`) are canonical non-negative integers written as decimal strings (plain JSON integers are also accepted); floats and booleans are rejected.

## Output Contract

```json
{"status": "SOLVED", "l": "2", "switching": {"1": "-1"}, "deleted": [["0", "1"], ["2", "3"]], "lower_bound": {"kind": "exhaustive"}}
{"status": "SOLVED", "l": "2", "switching": {}, "deleted": [["0", "1"], ["3", "4"]], "lower_bound": {"kind": "packing", "cycles": [["0", "1", "2"], ["3", "4", "5"]]}}
{"status": "UNKNOWN", "refusal": "OPTIMALITY_UNCERTIFIED", "upper": "15", "lower": "2", "switching": {"2": "-1"}, "lower_bound": {"kind": "packing", "cycles": [["0", "1", "2"], ["3", "4", "5"]]}}
{"status": "OUT_OF_SCOPE", "witness": {"edge": ["0", "0"], "reason": "SELF_LOOP"}}
```
