# Solver Verification Protocol & Terminal Routing Runbook

**AuthorityEffect:** None.  
**Domain Context:** `governance-exact-solvers`

This reference documents the procedural verification workflows, diagnostic recomputation steps, and terminal route dispatch sequences for exact rational mathematical solvers.

---

## 1. Problem-Bound Terminal Route Verification Sequence

1. **Pre-Branch Problem Consistency Verification:**
   - Problem-bound consistency checks MUST execute before dispatching to either terminal branch (`EXACT_REPAIR` or `STABILIZED_SURVIVOR`).
   - If an active registry is supplied alongside explicit `packet` or `defect` arguments:
     - Compare candidate problem data and digests against the registry.
     - Any mismatch, missing problem data, conflicting argument, or unverified repair equation MUST immediately fail closed with an explicit typed refusal (`Refusal("PROBLEM_DATA_MISMATCH")` or `status="UNAVAILABLE"`).
     - **Epistemic Distinction:** Do NOT route missing evidence to `OPEN_OBSTRUCTION`. An open obstruction $\Gamma_2 > 0$ strictly requires an independently verified, replayed cycle obstruction witness.

2. **Exact Repair Branch Verification:**
   - In the exact branch:
     - Verify input and observer digests.
     - Verify that the $\Phi_1$ certificate satisfies the exact repair equation ($x + d_0 f = 0$ with residual $= 0$).
     - Verify the $\Gamma_2$ boundary certificate.
     - Independently recompute the diagnosis from verified data.

3. **Single-Pass Iterator Preservation:**
   - Diagnostic recomputation must not re-consume single-pass input iterators or generator arguments.
   - Solvers and verifiers must recompute diagnosis using the realized, validated exact column vector $x$ (e.g. `diagnose(bound_packet, x)`), ensuring iterators and sequences exhibit identical routing.

---

## 2. Complementary Slackness & Dual Saturation Formulation

For the weighted $L_1$ quotient problem on an oriented graph with incidence matrix $B$, edge weights $w_e > 0$, cochain $c$, and flow $f$:
$$\min_f \sum_e w_e |r_e| \quad \text{where } r = c - B f$$
$$\max_y \langle c, y \rangle \quad \text{subject to } B^T y = 0, \ |y_e| \le w_e$$

At an optimal primal-dual pair $(f^*, y^*)$:
1. **Saturation Condition on Non-Zero Residuals:**
   $$r_e \ne 0 \implies y_e = w_e \operatorname{sign}(r_e)$$
2. **Freedom on Zero Residuals:**
   $$r_e = 0 \implies y_e \in [-w_e, w_e] \quad \text{subject to } B^T y = 0$$
   Non-tree edge flows are NOT fixed to zero solely because residuals vanish. Optimal solutions may require splitting circulation flow across multiple zero-residual non-tree paths using exact rational linear feasibility (Fourier-Motzkin elimination or exact simplex).

---

## 3. Strict Type & Array Normalization Discipline

1. **Strict Boolean Validation:**
   ```python
   if type(v) is not bool:
       raise TypeError(f"Expected strict boolean, got {type(v).__name__}")
   ```
   Do not use `isinstance(v, bool) and not isinstance(v, int)` because Python `bool` inherits from `int` (which causes `isinstance(True, int)` to be `True`, rejecting all booleans).

2. **Array Dataclass Normalization:**
   Array wrappers implementing `__eq__` and `__hash__` must canonicalize data in `__post_init__`:
   - Cast to canonical dtype (`np.float64` or `np.int64`) with contiguous C-order layout (`np.ascontiguousarray(arr)`).
   - Canonicalize signed zeros (`arr[arr == 0.0] = 0.0`).
   - Freeze array writability (`arr.flags.writeable = False`).
   - If mutable or non-normalized state cannot guarantee byte immutability, declare `__hash__ = None`.
