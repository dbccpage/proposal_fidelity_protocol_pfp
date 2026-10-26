# C017: Nonabelian Lattice Holonomy and Flatness

## Problem Statement

Given an $L \times M$ square lattice ($2 \le L, M \le 12$) with open or periodic boundaries and a finite group $G \in \{S_3, Q_8, \mathrm{SL}(2, \mathbb{F}_3)\}$:
1. Verify group consistency and edge anti-symmetry: $U_{vu} = U_{uv}^{-1}$. If violated, return `OUT_OF_SCOPE` with an inverse mismatch witness.
2. Calculate ordered holonomies around all plaquettes:
   $$ U(P) = U_{v_0 v_1} \cdot U_{v_1 v_2} \cdot U_{v_2 v_3} \cdot U_{v_3 v_0} $$
3. Return:
   - `NOT_FLAT` with a non-flat plaquette and its holonomy if any plaquette has $U(P) \ne e$.
   - `PURE_GAUGE` with a gauge $g: V \to G$ if every edge satisfies $g_u \cdot U_{uv} \cdot g_v^{-1} = e$.
   - `FLAT_NONTRIVIAL` (periodic lattices only) if all plaquettes are flat, but the global holonomies around noncontractible loops A and B are not both identity.

### Verification rules

- A `NOT_FLAT` plaquette may be listed from any of its four vertices and in either orientation; `holonomy` must be the ordered product along the order given (reversing the orientation inverts it, changing the start vertex conjugates it).
- `FLAT_NONTRIVIAL` loops must be closed nearest-neighbour walks along existing edges that start and end at `base`, and their winding vectors must generate the torus (for example one loop around each direction).
- Inputs outside the declared bounds are refused with `{"status": "UNKNOWN", "refusal": <code>, "refusal_code": <code>}` using `LATTICE_SIZE_OUT_OF_BOUNDS` ($L$ or $M$ not an integer in $[2, 12]$) or `MALFORMED_INPUT` (boundary not `open`/`periodic`, or group or edges of the wrong type). A refusal on an in-scope case is rejected.
- An `OUT_OF_SCOPE` inverse witness must cite an edge (`"edge": "u->v"`) that has the stated defect (`INVERSE_MISMATCH` or `MISSING_REVERSE_EDGE`); `INVALID_GROUP` applies when the table is not a group.

## Output Contract

```json
{"status": "SOLVED", "verdict": "NOT_FLAT", "plaquette": ["0,0", "1,0", "1,1", "0,1"], "holonomy": "s"}
{"status": "SOLVED", "verdict": "PURE_GAUGE", "gauge": {"0,0": "e", "0,1": "r"}}
{"status": "SOLVED", "verdict": "FLAT_NONTRIVIAL", "base": "0,0", "loop_a": ["0,0", "0,1", "0,2", "0,0"], "hol_a": "r", "loop_b": ["0,0", "1,0", "2,0", "0,0"], "hol_b": "r2"}
```
