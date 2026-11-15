# PAPER001-PYTHON-REFERENCE-SOLVER-GOVERNOR-REVIEW: Python Reference Solver and Governor Review

AuthorityEffect: None.

- Archive claim: [ATL-P001-009](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("The paper-local Python reference returns a primal potential and dual circulation only after independent verification, caps tree enumeration at 100,000 per component, and its governor admits only strictly decreasing potential updates.", [paper_claim_ledger.md:21](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L21))
- Audit derivation node: [PAPER001-PYTHON-REFERENCE-SOLVER-GOVERNOR-REVIEW](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-PYTHON-REFERENCE-SOLVER-GOVERNOR-REVIEW`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

The paper-local Python reference returns a primal potential and dual circulation only after independent verification, caps tree enumeration at 100,000 per component, and its governor admits only strictly decreasing potential updates.

## 2. Context & Scope

This derivation audits the paper-local Python reference solver and governor implementation (`symbol_game_governor.py`) on finite 1-dimensional cell complexes (graphs) without 2-cells.
Specifically, it analyzes:
1. The independent primal-dual verification gate: verifying dual capacity bounds, flow conservation divergence, objective balance, zero duality gap, and exact rational scalar types before returning a `Phi1Certificate`.
2. The tree enumeration resource bound: enforcing an explicit cap of 100,000 spanning trees (`MAX_SPANNING_TREES`) evaluated independently per connected component, raising `SpanningTreeLimitExceeded` if reached.
3. The discrete manifold governor descent discipline: evaluating candidate updates under `MoveType.CUT`, admitting updates if and only if candidate section defect strictly decreases, while refusing defect increases, stationary idempotent loops, and non-decreasing cuts without mutating state.
4. The executable test coverage establishing independent certificate verification, rapid limit triggering on $K_8$, per-component reset across disjoint subgraphs, and complete governor refusal and descent controls.

## 3. Hypotheses & Definitions

- **Pinned Reference Source**:
  - `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/symbol_game_governor.py`: Core module implementing `compute_exact_phi_1`, `verify_phi_1_certificate`, `_spanning_trees`, `SymbolGameGovernor`, `L1SymbolGameGovernor`, and associated data structures.
- **Graph Carrier and Data Invariants**:
  - Finite directed graph $G = (V, E)$ without self-loops, represented by vertices $V$ and directed weighted edges $E = \{(u, v, w_e)\}$.
  - Edges represented by `Edge(u, v, weight)` dataclass requiring non-empty distinct string endpoints $u \neq v$ (irreflexivity) and positive integer weight $w_e \ge 1$. Self-loops and non-positive weights raise `ValueError`.
  - Edge reports $c \in \mathbb{Q}^E$ represented by dictionary `claims` mapping edge tuples $(u, v)$ to exact rational numbers (`fractions.Fraction`).
  - Candidate potential $s \in \mathbb{Q}^V$ represented by dictionary `section` mapping vertex strings to exact rational numbers.
- **Arithmetic Representation**:
  - Exact rational arithmetic via `fractions.Fraction` or integer types exclusively; floating-point values and booleans produce `TypeError` or `ValueError`.
- **Component Decomposition**:
  - Connected components $C_1, \ldots, C_k$ identified via breadth-first search on undirected edge adjacency.
- **Enumeration Cap**:
  - `MAX_SPANNING_TREES = 100_000` enforced per connected component.
- **Governor Move Vocabulary**:
  - Discrete moves in `MoveType` (`ASSERT`, `CUT`, `VERIFY`, `RETRACT`, `LIFT_REQUEST`) resulting in `GovernorStepOutcome` with `StepVerdict` (`ASSERTED`, `DESCENT`, `EXACT`, `HOLD`, `REFUSAL`, `FAIL`).

## 4. Derivation / Audit Review

### 4.1 Independent Primal/Dual Verification Routine Structure
The function `verify_phi_1_certificate(vertices, edges, claims, certificate) -> bool` (lines 336–372) independently checks candidate certificates:
1. **Problem Well-Formedness (`_problem_is_well_formed`)**:
   - Confirms that edge endpoints belong to declared vertex set, edge weights are strictly positive exact rationals, no duplicate edges exist, and all claim keys belong to the declared edge set.
2. **Domain and Carrier Coverage**:
   - Verifies that `set(certificate.primal_potentials) == set(vertices)` and `set(certificate.dual_circulations) == {(u, v) for u, v, _ in edges}`.
   - Verifies that all scalar values (`phi_1`, `duality_gap`, potentials, circulations) are exact rationals.
3. **Dual Feasibility**:
   - Capacity constraint: verifies $|x_e| \le w_e$ for every edge $e \in E$.
   - Flow conservation (divergence): calculates net outgoing flow at every vertex:
     $$\operatorname{div}(v) = \sum_{e=(v, w)} x_e - \sum_{e=(u, v)} x_e = 0 \quad \forall v \in V.$$
4. **Primal-Dual Objective Balance & Zero Duality Gap**:
   - Computes weighted primal residual defect:
     $$D_c(s^\star) = \sum_{e=(u, v) \in E} w_e |c_e - (s^\star_v - s^\star_u)|.$$
   - Computes dual circulation value:
     $$\langle c, x^\star \rangle = \sum_{e \in E} c_e x^\star_e.$$
   - Verifies that $\operatorname{div}(v) = 0$ for all $v$, $D_c(s^\star) = \langle c, x^\star \rangle = \Phi_1([c])$, and `duality_gap == 0`.
5. **Output Gating in `compute_exact_phi_1`**:
   - Lines 578–580 enforce that candidate output is certified before return:
     ```python
     if not verify_phi_1_certificate(vertices, edges, claims, certificate):
         raise ArithmeticError("Primal-dual certificate failed independent verification")
     return certificate
     ```
   - Unverified potentials or dual flows are rejected with `ArithmeticError`.

### 4.2 Spanning Tree Enumeration Cap per Component
The recursive generator `_spanning_trees(component, component_edges, limit)` (lines 375–415) enumerates spanning trees for a connected component using inclusion/exclusion with union-find cycle detection:
1. **Target Formulation**:
   - For a component with $n_{comp}$ vertices, each spanning tree contains exactly $target = n_{comp} - 1$ edges.
2. **Cap Enforcement**:
   - Upon assembling a candidate tree of size $target$:
     ```python
     if len(chosen) == target:
         if len(trees) == limit:
             raise SpanningTreeLimitExceeded(
                 f"more than {limit} spanning trees in a component of {len(component)} vertices"
             )
         trees.append(tuple(chosen))
         return
     ```
3. **Per-Component Scope**:
   - In `compute_exact_phi_1` (lines 508–528), the solver identifies connected components and invokes `_spanning_trees(comp, comp_edges, MAX_SPANNING_TREES)` separately for each component.
   - The threshold `MAX_SPANNING_TREES = 100_000` is evaluated independently for each connected component rather than across the full graph.
   - If tree count reaches 100,000 in any component, execution terminates with `SpanningTreeLimitExceeded` (subclass of `RuntimeError`) rather than returning an approximate or partial minimum.
4. **Behavior on Dense Graphs and Disjoint Resets**:
   - On complete graph $K_8$ ($8^6 = 262,144$ spanning trees), `_spanning_trees` reaches the 100,000 threshold and halts in ~0.15s.
   - On graphs with multiple disconnected components, tree counters reset for each component, ensuring that earlier subgraphs do not deplete the quota allocated to subsequent components.

### 4.3 Governor Monotonic Descent and Rejection of Non-Decreasing Updates
In `SymbolGameGovernor.execute_move(MoveType.CUT, payload)` (lines 773–827), candidate potential updates $s_{t+1}$ are evaluated against current section defect $D_c(s_t)$:
1. **Defect-Increasing Update Rejection**:
   - If proposed defect $D(s_{t+1}) > D(s_t)$, the update is refused:
     ```python
     if proposed_defect > current_defect:
         outcome = GovernorStepOutcome(
             turn=self.turn, move_type=mt, verdict=StepVerdict.REFUSAL,
             defect=current_defect, phi_1=current_phi1, admitted=False,
             feedback=f"Refused: DefectIncrease. Proposed defect {proposed_defect} exceeds current defect {current_defect}.",
             evidence_sha256=sha,
         )
         return self._record_outcome(outcome, step_record)
     ```
2. **Stationary and Non-Decreasing Update Rejection**:
   - If proposed defect $D(s_{t+1}) == D(s_t)$, the update is refused:
     - If $s_{t+1} == s_t$, feedback records `"Refused: IdempotentStationaryLoop. CUT proposes no state change."`
     - If $s_{t+1} \neq s_t$, feedback records `"Refused: NonDecreasingCut. Proposed defect ... does not strictly decrease current defect ..."`
     - In both cases, `admitted = False`, `verdict = StepVerdict.REFUSAL`, and section state remains unchanged.
3. **Strict Descent Admission**:
   - Only when $D(s_{t+1}) < D(s_t)$ is the update admitted:
     - `self.section` is updated to $s_{t+1}$.
     - `admitted = True`.
     - `verdict` is assigned `StepVerdict.EXACT` (if $D(s_{t+1}) = 0$), `StepVerdict.HOLD` (if $D(s_{t+1}) = \Phi_1([c])$), or `StepVerdict.DESCENT`.

## 5. Verification Evidence & Test Execution

The claim is supported by four executable test suites in the repository:

1. **Exact Duality and Independent Verification on Weighted Triangle (`test_zenodo_regression_suite.py::test_regression_2_triangle_phi_1_five`)**:
   - Evaluates weighted triangle ($w = (1, 2, 2)$, $c = (1, 2, 2)$).
   - Verifies `cert.phi_1 == 5`, `duality_gap == 0`, and `cert.verify(vertices, edges, claims)` passes.
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_zenodo_regression_suite.py -k test_regression_2_triangle_phi_1_five -v
     ```
     Result: 1 passed; 0 failed.

2. **Dual Feasibility & Over-Capacity Rejection (`test_review_regressions.py::test_degenerate_multicycle_dual_is_feasible`)**:
   - Evaluates multicycle graph with 4 vertices and 5 edges.
   - Confirms `verify_phi_1_certificate(vertices, edges, claims, cert)` passes for the reference solver output.
   - Confirms that an invalid certificate candidate with over-capacity flow ($|x_e| = 2 > w_e = 1$) fails verification.
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_review_regressions.py -k test_degenerate_multicycle_dual_is_feasible -v
     ```
     Result: 1 passed; 0 failed.

3. **Governor Monotonic Descent and Rejection Controls (`test_governor.py::test_governor_monotonic_descent_and_rejection`)**:
   - Configures 3-vertex triangle and asserts edge claims.
   - Verifies that a defect-increasing CUT proposal is refused (`admitted == False`, `verdict == StepVerdict.REFUSAL`, `"DefectIncrease" in feedback`).
   - Verifies that a non-moving stationary CUT proposal is refused (`admitted == False`, `verdict == StepVerdict.REFUSAL`, `"IdempotentStationaryLoop" in feedback`).
   - Verifies that a gradient-consistent CUT proposal strictly descends defect and is admitted (`admitted == True`, `defect <= init_defect`).
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_governor.py -k test_governor_monotonic_descent_and_rejection -v
     ```
     Result: 1 passed; 0 failed.

4. **Standalone Audit Witness (`tests/test_paper001_reference_governor_review.py`)**:
   - `test_primal_dual_independent_verification_and_refusal`: evaluates certificate criteria (capacity bounds, divergence-free circulation, objective agreement, zero duality gap, exact rational types) and confirms `compute_exact_phi_1` raises `ArithmeticError` if certificate verification fails.
   - `test_component_tree_cap_100k_and_per_component_reset`: evaluates that $K_8$ raises `SpanningTreeLimitExceeded` at 100,000 trees in ~0.15s, and tests that disjoint components each under 100,000 trees succeed without cross-component cap accumulation.
   - `test_governor_strictly_decreasing_updates_and_rejections`: evaluates `DefectIncrease` refusal, `IdempotentStationaryLoop` refusal, `NonDecreasingCut` refusal on iso-defect updates, verifies zero state mutation on refusal, and evaluates strict descent admission.
   - Command:
     ```bash
     python -m pytest tests/test_paper001_reference_governor_review.py -v
     ```
     Result: 3 passed; 0 failed.

## 6. Limits and Non-Claims

- **Exponential Computational Complexity**: Spanning tree enumeration scales with graph size (bounded by $n^{n-2}$ via Cayley's formula for complete graphs). The reference implementation uses explicit tree enumeration; no polynomial-time complexity is asserted.
- **Per-Component Tree Cap Scope**: The 100,000 tree limit per component is verified statically and confirmed on $K_8$; the solver halts rather than returning an approximate minimum when the limit is exceeded.
- **Local Step Monotonicity vs. Global Convergence**: The governor descent rule enforces that each admitted CUT move strictly decreases the candidate potential defect $D_c(s)$. This establishes local monotonic improvement; it does not claim polynomial-time convergence to the global optimum $\Phi_1([c])$ on general instances, nor does it assert finite termination for arbitrary rational descent sequences (such as sequence $D_t = 2^{-t}$ from PFP001-07).
- **Finite 1-Dimensional Graphs Only**: Evaluates 1-cochains on finite directed graphs; higher-dimensional cell complexes ($C^k$ for $k \ge 2$) are outside the scope of this solver.
- **Host Runtime Trust Boundary**: Execution assumes an untampered Python interpreter and exact integer/Fraction arithmetic; does not authenticate network callers or external system processes.

## 7. Claim Hygiene Summary

1. **What it supports**: Demonstrates through source inspection and test execution that the paper-local Python reference solver (`symbol_game_governor.py`) returns primal potentials and dual circulations only upon passing independent verification (`verify_phi_1_certificate`), halts with `SpanningTreeLimitExceeded` if any connected component reaches 100,000 spanning trees, resets tree enumeration across disjoint components, and that its governor admits only strictly decreasing candidate potential updates under `MoveType.CUT` while refusing defect-increasing, stationary, and non-decreasing cuts without mutating state. Supported by pytest tests in `test_zenodo_regression_suite.py`, `test_review_regressions.py`, `test_governor.py`, and `tests/test_paper001_reference_governor_review.py`.
2. **What it does not support**: Does not support polynomial-time scaling for general graphs (tree enumeration is worst-case exponential); does not establish global polynomial-time reachability of the quotient minimum via heuristic CUT proposals; does not evaluate higher-dimensional cochain complexes; does not evaluate machine learning weights or language models.
3. **Narrowest defensible claim**: For finite directed graphs with declared vertices, non-loop edges, and positive rational penalties, `compute_exact_phi_1` gates return on an independent primal-dual verification check, halts with `SpanningTreeLimitExceeded` if a component contains 100,000 spanning trees, and `SymbolGameGovernor.execute_move` rejects CUT updates that do not strictly decrease candidate defect.
4. **Next test needed**: Derivation ATL-P001-010 (Paper 001 formal scope of Lean declarations: pair cancellation, triangle sign gauge, and non-authority policy type).

## 8. Cross-References & Provenance

- Archive Claim: [ATL-P001-009](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP001-09](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L21)
- DAG Review Node: `PAPER001-PYTHON-REFERENCE-SOLVER-GOVERNOR-REVIEW`
- Review Registry: `dag/reviews/additional_paper_001_support.json`
- Pull Request Target: `derivation/atl-p001-009`
