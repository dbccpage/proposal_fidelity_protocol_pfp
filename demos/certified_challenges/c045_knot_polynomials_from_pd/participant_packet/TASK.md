# C045: Knot Polynomials from Planar Diagrams

**Domain:** `e_formal_math`  
**Tier:** `T3`  
**Protocol:** `SG-CP v1`  
**AuthorityEffect:** None  

## Problem Specification

Compute topological polynomial invariants of oriented knots given by their Planar Diagram (PD) presentation:
1. **Writhe ($w$)**: Total signed sum of crossings $\sum \epsilon(c) \in \mathbb{Z}$.
2. **Kauffman Bracket ($\langle K \rangle$)**: State-sum polynomial in the Laurent ring $\mathbb{Z}[A, A^{-1}]$.
3. **Jones Polynomial ($V(t)$)**: Ambient-isotopy knot invariant in $\mathbb{Z}[t, t^{-1}]$, normalized by $V(t) = (-A^3)^{-w} \langle K \rangle |_{A = t^{-1/4}}$ with $V(\bigcirc) = 1$.
4. **Alexander-Conway Polynomial ($\Delta(t)$)**: Symmetric normalized polynomial $\Delta(t) = \Delta(t^{-1}) \in \mathbb{Z}[t, t^{-1}]$ with $\Delta(1) = 1$, computed from Fox derivatives / the Alexander arc matrix.
5. **Knot Catalog Identification**: Classify knots up to 7 crossings into Rolfsen notation ($0_1, 3_1, 4_1, 5_1, 5_2, 6_1, 6_2, 6_3, 7_1$).

### Input PD Schema
A knot diagram is presented as a list of 4-tuples `[i, j, k, l]`:
- Edge labels are positive integers $1, \dots, 2n$.
- Strands meet at crossing in counterclockwise cyclic order:
  - $i$: incoming under-strand.
  - $j$: over-strand edge.
  - $k$: outgoing under-strand ($k = (i \bmod 2n) + 1$).
  - $l$: over-strand edge.
- If over-strand flows $l \to j$, crossing sign is $+1$ (right-handed).
- If over-strand flows $j \to l$, crossing sign is $-1$ (left-handed).

### Tasks
1. **`COMPUTE_POLYNOMIALS`**:
   Return writhe, Kauffman bracket, Jones polynomial, Alexander polynomial, and matched knot ID:
   ```json
   {
     "case_id": "...",
     "status": "SOLVED",
     "writhe": 3,
     "kauffman_bracket": {"-7": 1, "-3": -1, "5": -1},
     "jones_polynomial": {"1": 1, "3": 1, "4": -1},
     "alexander_polynomial": {"-1": 1, "0": -1, "1": 1},
     "identified_knot": "3_1",
     "chirality": "RIGHT_HANDED"
   }
   ```

2. **`IDENTIFY`**:
   Return identified Rolfsen knot ID, chirality, and essential invariants.

3. **`COMPARE`**:
   Given two knot diagrams `pd_1` and `pd_2`:
   - If polynomial signatures match: return `{"kind": "SAME_INVARIANTS", ...}`
   - If they differ: return `{"kind": "DIFFERENT_INVARIANTS", "separating_invariant": "...", "val_1": {...}, "val_2": {...}}`

### Refusals & Out of Scope
The solver must refuse invalid inputs with `status: "REFUSED"` and a verifiable witness:
- `EDGE_LABEL_MULTIPLICITY`: label does not appear exactly twice or is out of range $1 \dots 2n$.
- `NON_PLANAR`: combinatorial rotation system Euler characteristic $V - E + F \ne 2$ (face count $F \ne n + 2$).
- `ORIENTATION_INCONSISTENT`: understrand or overstrand violates oriented knot traversal.
- `INVALID_CROSSING_COUNT`: empty/negative or exceeds maximum bound $n > 12$.
