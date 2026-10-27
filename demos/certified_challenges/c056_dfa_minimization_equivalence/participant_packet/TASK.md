# Task: Challenge C056 — DFA Minimization and Equivalence with Distinguishing Strings

## Formal Problem

Given an alphabet $\Sigma$ of at most 4 single-character symbols (e.g. `["a", "b"]`), and a task:

### 1. `"task": "MINIMIZE"`
Given a regular expression over $\Sigma$:
- Grammar:
  - Letters in $\Sigma$
  - `%` for the empty word $\varepsilon$
  - `#` for the empty language $\emptyset$
  - Juxtaposition for concatenation
  - `|` for union
  - `*` for Kleene star
  - `()` for grouping
- Return a complete minimal deterministic finite automaton (DFA) $M$ such that $L(M) = L(\text{regex})$, along with a complete Myhill-Nerode certificate:
  - `states`: total state count $k$ (states indexed $0, \dots, k-1$, with start state 0).
  - `accept`: list of accepting state indices.
  - `delta`: $k \times |\Sigma|$ transition table, where `delta[s][a_idx]` is the destination state on letter `alphabet[a_idx]`.
  - `access`: list of access words $w_0, \dots, w_{k-1}$ over $\Sigma^*$ such that $\hat{\delta}(0, w_q) = q$.
  - `separators`: dictionary mapping every pair `"p,q"` ($0 \le p < q < k$) to a suffix $z_{pq} \in \Sigma^*$ such that exactly one of $\hat{\delta}(p, z_{pq})$ and $\hat{\delta}(q, z_{pq})$ is accepting.

### 2. `"task": "EQUIV"`
Given two regular expressions $r_1$ and $r_2$ over $\Sigma$:
- If $L(r_1) = L(r_2)$:
  Return `"kind": "EQUAL"`, with minimal DFAs `dfa1` and `dfa2`, and an isomorphism bijection `bijection: {str(s1): s2}` mapping start state 0 to 0, preserving acceptance, and commuting with transitions.
- If $L(r_1) \ne L(r_2)$:
  Return `"kind": "DIFFERENT"`, with a distinguishing word `word` in the symmetric difference $(L(r_1) \setminus L(r_2)) \cup (L(r_2) \setminus L(r_1))$.

### 3. Malformed / Out of Scope Inputs
If the regex contains syntax errors, unclosed parentheses, characters outside the declared alphabet, or non-string inputs, return `"status": "OUT_OF_SCOPE"`.

## Output Formats (RFC 8785 JSON)

### Minimization:
```json
{
  "case_id": "dfa_ex_01",
  "status": "SOLVED",
  "states": 4,
  "accept": [3],
  "delta": [[1,0],[1,2],[1,3],[1,0]],
  "access": ["", "a", "ab", "abb"],
  "separators": {
    "0,1": "bb",
    "0,2": "b",
    "0,3": "",
    "1,2": "b",
    "1,3": "",
    "2,3": ""
  }
}
```

### Equivalence (Different):
```json
{
  "case_id": "dfa_ex_04",
  "status": "SOLVED",
  "kind": "DIFFERENT",
  "word": "ba"
}
```

### Equivalence (Equal):
```json
{
  "case_id": "dfa_ex_06",
  "status": "SOLVED",
  "kind": "EQUAL",
  "dfa1": {
    "states": 1,
    "accept": [0],
    "delta": [[0, 0]]
  },
  "dfa2": {
    "states": 1,
    "accept": [0],
    "delta": [[0, 0]]
  },
  "bijection": {
    "0": 0
  }
}
```

### Out of Scope:
```json
{
  "case_id": "dfa_ex_07",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "PARSE_ERROR"}
}
```
