# Task Specification: C042 SAT Encodings with DRAT Certificates

**AuthorityEffect:** None.  
**Domain:** `e_formal_math`  
**Challenge ID:** `c042_sat_with_drat_certificates`  
**Tier:** T2 ($0.50 budget ceiling, target < $0.05)  
**Models:** Open weights, parameter ceiling <= 70B  

---

## 1. Objective

Synthesize a frozen Python solver module exposing:
```python
def solve(case: dict) -> dict
```
which solves combinatorial decision problems from five mathematical families by either:
1. Emitting a verified problem-level satisfying assignment (`kind: SAT`), OR
2. Emitting a machine-verifiable DRAT (Deletion Resolution Asymmetric Tautology) refutation proof (`kind: UNSAT`) proving the judge's canonical CNF unsatisfiable.

---

## 2. The Five Mathematical Families

1. **Graph k-Colouring (`coloring`):**
   - Inputs: `n` (vertices), `k` (colours $\le 6$), `edges` ($[u, v]$ pairs).
   - Solution: `{"colour": [c_0, ..., c_{n-1}]}` with each $c_i \in \{0, \dots, k-1\}$, no monochromatic edges. Strictly `type(c) is int`.

2. **Pigeonhole Principle (`php`):**
   - Inputs: `pigeons` ($p$), `holes` ($h$), optional `blocked` pairs.
   - Solution: `{"assignment": [h_0, ..., h_{p-1}]}` where all pigeons are in distinct, non-blocked holes.
   - Standard $p > h$ instances without extra holes are unsatisfiable and require DRAT certificates.

3. **Latin-Square Completion (`latin_square`):**
   - Inputs: `order` ($N \le 12$), `prefilled` ($[r, c, v]$ triples).
   - Solution: `{"grid": [[v_{r,c} ...]]}` where each row and column is a permutation of $\{0, \dots, N-1\}$.

4. **Tseitin Parity Formulas (`tseitin`):**
   - Inputs: `vertices`, `edges`, `charges` (vertex parity $\in \{0, 1\}$).
   - Solution: `{"edge_values": [val_0, ...]}` where each edge value $\in \{0, 1\}$ satisfies $\bigoplus_{e \sim v} val_e \equiv charges[v] \pmod 2$.
   - Formulas with odd total charge are unconditionally unsatisfiable.

5. **Exact Cover & Polyomino Tiling (`tiling`):**
   - Inputs: `rows`, `cols`, `tiles` (lists of $[r, c]$ coordinates), optional `blocked`.
   - Solution: `{"selected_tiles": [t_0, ...]}` giving an exact partition of all non-blocked cells.

---

## 3. Output Schema & Contracts

Answers must strictly conform to RFC 8785 JSON:

```json
{"case_id": "c042_pub_01", "status": "SOLVED", "kind": "SAT", "solution": {"colour": [0, 1, 2]}}
{"case_id": "c042_pub_02", "status": "SOLVED", "kind": "UNSAT", "proof_format": "DRAT", "proof_text": "1 2 0\n0", "cnf_sha256": "<64-hex>"}
{"case_id": "c042_poison_01", "status": "OUT_OF_SCOPE", "witness": {"field": "edges[0]", "reason": "VERTEX_OUT_OF_RANGE"}}
{"case_id": "c042_timeout", "status": "UNKNOWN", "code": "SOLVER_TIMEOUT"}
```

### Invariants:
- All integer solutions must satisfy `type(v) is int` (rejects `bool` values `True`/`False`).
- `UNSAT` answers must bind `cnf_sha256` matching the SHA-256 hash of the judge's canonical CNF.
- DRAT proofs must terminate with the empty clause `0`.

Correction notice (2026-09-29). `UNKNOWN` is recorded as an abstention and never counts as a verified answer. `OUT_OF_SCOPE` is accepted only for a case from which the judge cannot build a canonical CNF. Some formulas are refuted without search (they contain the empty clause, or unit propagation alone reaches a conflict), so the one-line proof `0` is a valid refutation of them; verified `UNSAT` answers on such formulas are reported separately and not counted as solved. Two public examples are of this kind and are marked `trivially_refutable`.
