# C044: Finite Group Identification with Isomorphism Witnesses

**Domain:** `e_formal_math`  
**Tier:** `T3`  
**Protocol:** `SG-CP v1`  
**AuthorityEffect:** None  

## Problem Specification

Identify finite groups $G$ of order $|G| \le 64$ by producing an explicit isomorphism to a catalogued representative from the shipped SmallGroups library, or separate two groups $(G, H)$ by a recomputable algebraic invariant.

### Input Presentations
Groups are presented in one of three standardized schemas:
1. **Permutation group (`perm`)**:
   `{"presentation": "perm", "degree": d, "gens": [[p_0, ..., p_{d-1}], ...]}`
   where $d \le 16$.
2. **Matrix group over finite field (`matrix`)**:
   `{"presentation": "matrix", "p": p, "dim": n, "gens": [[[...], ...], ...]}`
   where $p \le 7$ and dimension $n \le 3$.
3. **Full Cayley table (`table`)**:
   `{"presentation": "table", "order": n, "table": [[...], ...]}`
   where element `0` is the identity.

### Tasks
1. **`IDENTIFY`**:
   Return the representative ID `[order, index]` from `catalog/small_groups_catalog.json` and the images of the generators in that representative's table:
   ```json
   {"case_id": "...", "status": "SOLVED", "kind": "IDENTIFIED", "rep_id": [order, index], "images": [img_1, img_2, ...]}
   ```
2. **`COMPARE`**:
   Given two groups $G$ and $H$:
   - If isomorphic: return `{"case_id": "...", "status": "SOLVED", "kind": "ISOMORPHIC", "images": [img_1, ...]}`
   - If non-isomorphic: return a separating invariant from the canonical menu:
     ```json
     {"case_id": "...", "status": "SOLVED", "kind": "NOT_ISOMORPHIC", "invariant": "element_order_histogram", "G_value": {...}, "H_value": {...}}
     ```

### Canonical Invariant Menu
- `element_order_histogram`: multiset / frequency map of element orders $\mathrm{ord}(x)$.
- `centre_order`: $|Z(G)|$.
- `derived_subgroup_order`: $|[G, G]|$.
- `abelianization_factors`: invariant factors $d_1 | d_2 | \dots | d_k$ of $G / [G, G]$.
- `conjugacy_class_sizes`: sorted list of conjugacy class sizes.
- `solutions_xk_eq_e`: count of $x \in G$ satisfying $x^k = e$ for divisors $k$ of $|G|$.

### Refusals & Out of Scope
The solver must emit `OUT_OF_SCOPE` with a verifiable witness if:
- Table is not associative (`NOT_ASSOCIATIVE`, witnessed by triple $[i, j, k]$).
- Missing identity or inverse (`MISSING_IDENTITY_OR_INVERSE`, witnessed by element).
- Generators generate $> 64$ elements (`EXCEEDS_MAX_ORDER`).
