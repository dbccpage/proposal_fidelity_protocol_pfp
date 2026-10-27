# Challenge C043: Ramsey and van der Waerden Lower-Bound Constructions

**AuthorityEffect:** None · **Domain:** `e_formal_math` · **Tier:** T3  
**Protocol:** [SG-CP v1](../../01_challenge_protocol.md)  
**Parent Catalog:** `c043_ramsey_vdw_constructions.md`  

---

## 1. Problem Specification

Produce a frozen module exposing `def solve(case: dict) -> dict` that synthesizes valid colourings avoiding forbidden monochromatic sub-structures (cliques in complete graphs or arithmetic progressions in sequences), below known theoretical bounds and under pre-coloured side constraints.

### Supported Problem Types:

1. **Two-Colour Ramsey (`ramsey2`):**
   * Input: `{"type": "ramsey2", "s": s, "t": t, "n": n, "fixed": [...]}`
   * Target: Edge colouring $\chi: E(K_n) \to \{0, 1\}$ containing:
     * No monochromatic $K_s$ in colour 0.
     * No monochromatic $K_t$ in colour 1.
   * Edge representation: Lexicographic pair order $(0,1), (0,2), \dots, (0,n-1), (1,2), \dots, (n-2, n-1)$.
   * Total edges: $m = \binom{n}{2} = \frac{n(n-1)}{2}$. Output `colours` must be a string of length $m$ over `{"0", "1"}`.

2. **Three-Colour Triangle (`ramsey3`):**
   * Input: `{"type": "ramsey3", "n": n, "fixed": [...]}`
   * Target: Edge colouring $\chi: E(K_n) \to \{0, 1, 2\}$ with no monochromatic triangle ($K_3$) in any of the three colours.
   * Total edges: $m = \binom{n}{2}$. Output `colours` must be a string of length $m$ over `{"0", "1", "2"}`.
   * Known bound: $R(3,3,3) = 17$, so solutions exist for $n \le 16$.

3. **Van der Waerden (`vdw`):**
   * Input: `{"type": "vdw", "r": r, "k": k, "n": n, "fixed": [...]}`
   * Target: Element colouring $\chi: \{0, 1, \dots, n-1\} \to \{0, \dots, r-1\}$ containing no monochromatic $k$-term arithmetic progression $a, a+d, a+2d, \dots, a+(k-1)d$ ($d \ge 1$).
   * Output `colours` must be a string of length $n$ over `{"0", ..., str(r-1)}`.

4. **Side Constraints (`fixed`):**
   * For Ramsey: A list of fixed edges `[u, v, colour]` or `[edge_index, colour]`. The returned colouring must match all fixed edges.
   * For Van der Waerden: A list of fixed elements `[position, colour]`. The returned colouring must match all fixed positions.

5. **Infeasibility (`OUT_OF_SCOPE`):**
   * If fixed constraints already contain a forbidden monochromatic structure, emit:
     ```json
     {"status": "OUT_OF_SCOPE", "witness": {"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": [...]}}
     ```
   * If an instance is provably infeasible via SAT, emit a verified DRAT refutation:
     ```json
     {"status": "OUT_OF_SCOPE", "witness": {"reason": "PROVABLY_INFEASIBLE_SAT", "proof_type": "DRAT", "drat_proof": [...]}}
     ```
   * If unsolved within limits:
     ```json
     {"status": "UNKNOWN", "code": "NOT_FOUND_WITHIN_LIMIT"}
     ```

---

## 2. Wire Formats & Schemas

### Input Case Schema
```json
{
  "case_id": "c043_pub_01",
  "type": "ramsey2",
  "s": 3,
  "t": 3,
  "n": 5,
  "fixed": []
}
```

### Successful Solution Schema
```json
{
  "case_id": "c043_pub_01",
  "status": "SOLVED",
  "kind": "COLOURING",
  "colours": "0110011010"
}
```

---

## 3. Reference Bounds & Theoretical Values
* $R(3, 3) = 6$
* $R(4, 4) = 18$ (Paley graph $P_{17}$ provides a 2-colouring of $K_{17}$ with no monochromatic $K_4$)
* $R(3, 3, 3) = 17$ (Greenwood & Gleason 1955, $K_{16}$ has a triangle-free 3-colouring)
* $W(2, 3) = 9$
* $W(2, 4) = 35$ (Chvátal 1970)
* $W(2, 5) = 178$ (Stevens & Shantaram 1978)
* $W(2, 6) = 1132$ (Kouril & Paul 2008)
