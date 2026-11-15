# PAPER001-NATIVE-FOREST-SOLVER-REVIEW: Native Forest Solver Review

AuthorityEffect: None.

- Archive claim: [ATL-P001-008](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("The native Rust solver enumerates spanning forests exactly, caps the search at 100,000 forests, refuses with `EnumerationLimit` beyond the cap, and returns `phi1`, `gauge`, and `forests_checked`.", [paper_claim_ledger.md:20](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L20))
- Audit derivation node: [PAPER001-NATIVE-FOREST-SOLVER-REVIEW](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-NATIVE-FOREST-SOLVER-REVIEW`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

The native Rust solver `solver_graph_phi1_distance` (`solve_graph_phi1`) enumerates spanning forests on finite directed graphs with positive rational edge penalties and exact rational reports, caps the search at 100,000 completed forests (`MAX_FORESTS`), refuses with `GraphPhi1Error::EnumerationLimit` when the forest count reaches the cap, and returns a result payload containing `phi1`, `gauge`, and `forests_checked`.

## 2. Context & Scope

This derivation audits the native Rust implementation of the 1-cochain quotient defect minimizer (`graph_phi1`) on finite 1-dimensional cell complexes (graphs) without 2-cells.
Specifically, it analyzes:
1. The role of the native Rust solver in the Proposal Fidelity Protocol architecture: evaluating exact quotient distance $\Phi_1(c) = \min_{f \in \mathbb{Q}^V} \|c - Bf\|_{1, w}$.
2. The spanning forest enumeration algorithm: parameterizing graph potential classes by spanning forest trees and tree-cotree decompositions.
3. The bounded search mechanism: enforcing an explicit resource cap of 100,000 completed forests to prevent unbounded compute on graphs with high spanning tree count.
4. The refusal semantics: emitting an explicit typed error (`EnumerationLimit`) rather than an unverified or approximate partial minimum when the declared cap is reached.
5. The interface boundaries between the native Rust solver crate, its standalone CLI binary, and external callers (such as the Python governor adapter `native_functional.py`).

## 3. Hypotheses & Definitions

- **Pinned Rust Source Implementations**:
  - `code/rust/core_solvers/src/solver_graph_phi1_distance.rs`: Core library module implementing `solve_graph_phi1`, `solve_graph_phi1_with_limit`, data types, and unit tests.
  - `code/rust/core_solvers/src/bin/solve_graph_phi1.rs`: Standalone executable reading JSON from standard input, delegating to `solve_graph_phi1`, and emitting JSON to standard output.
  - Caller interface: `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/native_functional.py`.
- **Graph Carrier and Data Invariants**:
  - Finite directed graph $G = (V, E)$ with $|V| = n$ vertices and $|E| = m$ directed edges.
  - Distinct vertices: input array of unique string identifiers $V = \{v_0, \ldots, v_{n-1}\}$. Duplicate vertex identifiers produce `GraphPhi1Error::DuplicateVertex`.
  - Non-loop edges: each directed edge $e = (u \to v)$ joins distinct declared vertices $u \neq v$ with $u, v \in V$. Missing vertices produce `GraphPhi1Error::UnknownEndpoint`; self-loops $u = v$ produce `GraphPhi1Error::SelfEdge`.
  - Exact rational penalties and reports: each edge has positive penalty $w_e \in \mathbb{Q}_{>0}$ and report $c_e \in \mathbb{Q}$, represented with exact rational arithmetic via `num_rational::BigRational`. Non-positive weights ($w_e \le 0$) produce `GraphPhi1Error::NonPositiveWeight`; non-rational strings produce `GraphPhi1Error::InvalidRational`.
- **Spanning Forest Target**:
  - Connected components: computed via disjoint-set union-find (`union` and `root`), yielding $k \ge 1$ connected components.
  - Forest edge target: each spanning forest contains $target = |V| - k = n - k$ edges.
- **Search Cap Constant**:
  - `const MAX_FORESTS: usize = 100_000;` defined in `solver_graph_phi1_distance.rs:39`.
- **Result Payload (`GraphPhi1Result`)**:
  - `phi1: String`: exact quotient defect $\Phi_1(c)$ encoded as a rational string.
  - `gauge: BTreeMap<String, String>`: minimizing vertex potential $f^\star$ mapping each vertex identifier to its exact rational string.
  - `forests_checked: usize`: total count of completed spanning forests evaluated.

## 4. Derivation / Audit Review

### 4.1 Input Validation and Data Representation (`parse_graph_edges`)
In `solver_graph_phi1_distance.rs` (lines 94–126), the function `parse_graph_edges` iterates over the declared vertex sequence and constructs a mapping `names: BTreeMap<String, usize>`. If `names.insert(...)` encounters an existing key, the function halts with `Err(GraphPhi1Error::DuplicateVertex)`.
For each raw edge in `input.edges`:
- Resolves endpoints $u$ and $v$ against `names`; returns `Err(GraphPhi1Error::UnknownEndpoint)` if either endpoint is absent.
- Checks $u \neq v$; returns `Err(GraphPhi1Error::SelfEdge)` if $u == v$.
- Parses `weight` and `claim` as `BigRational` instances via `FromStr`; returns `Err(GraphPhi1Error::InvalidRational)` upon parse failure or zero denominator.
- Verifies $w_e > 0$; returns `Err(GraphPhi1Error::NonPositiveWeight)` if $w_e \le 0$.

### 4.2 Component Detection and Target Calculation
In `solver_graph_phi1_distance.rs` (lines 156–166), connected components are identified using union-find on the validated edges:
- Initializes `all_parent: Vec<usize> = (0..n).collect()`.
- Iterates over all edges, performing `union(&mut all_parent, edge.u, edge.v)`.
- Counts distinct component roots: `components = (0..n).map(|i| root(&all_parent, i)).collect::<BTreeSet<_>>().len()`.
- Sets spanning forest size target: `target = n - components`.

### 4.3 Recursive Forest Enumeration (`enumerate`)
In `solver_graph_phi1_distance.rs` (lines 270–325), `enumerate` searches the space of spanning forests using recursive backtracking:
1. **Base Case (`chosen.len() == target`)**:
   - Checks the evaluation limit: `if *checked == limit { return Err(GraphPhi1Error::EnumerationLimit); }`.
   - Increments the forest counter: `*checked += 1`.
   - Traverses the chosen forest edges via BFS/DFS (`build_forest_gauge`) to determine vertex potentials $f \in \mathbb{Q}^V$ that set residual $c_e - (f_v - f_u) = 0$ on all forest tree edges.
   - Evaluates total weighted defect $D_c(f) = \sum_{e \in E} w_e |c_e - (f_v - f_u)|$ via `weighted_residual`.
   - If $D_c(f) < *best$, records the candidate: `*best = cost; *best_gauge = gauge`.
   - Returns `Ok(())`.
2. **Pruning Condition**:
   - `if next >= edges.len() || chosen.len() + edges.len() - next < target { return Ok(()); }`.
   - If the remaining unexamined edges cannot supply enough edges to reach `target`, the recursive branch terminates.
3. **Branching**:
   - **Include Edge**: Copies `parent` array and attempts `union(&mut included_parent, edge.u, edge.v)`. If the edge connects two previously disjoint components (acyclic extension), pushes `next` into `chosen` and recurses with `next + 1`.
   - Backtracks by popping `next` from `chosen`.
   - **Exclude Edge**: Recurses with `next + 1` with unchanged `parent` and `chosen`.

### 4.4 Refusal Semantics Under Enumeration Limit
When the total count of evaluated spanning forests reaches `limit` (bound to `MAX_FORESTS = 100_000` in `solve_graph_phi1`), attempting to evaluate an additional forest triggers:
```rust
if *checked == limit {
    return Err(GraphPhi1Error::EnumerationLimit);
}
```
This error propagates through the call stack via the `?` operator, immediately halting search execution. The solver returns `Err(GraphPhi1Error::EnumerationLimit)` without returning an unverified or approximate partial minimum.

### 4.5 Dual Certification and Output Construction (`certify_graph_phi1`)
Before returning a successful result (lines 128–149 and 182–194):
- The best potential found during enumeration is verified against an independent exact dual solver via `core_functional::phi1::Phi1Functional::evaluate_exact_witness`.
- Any certification failure returns `Err(GraphPhi1Error::FunctionalRefusal(...))`.
- Upon successful verification, constructs `GraphPhi1Result`:
  - `phi1`: certified quotient defect string,
  - `gauge`: map of vertex identifiers to rational potential strings,
  - `forests_checked`: exact integer count of evaluated spanning forests.

## 5. Verification Evidence & Test Execution

The claim is verified by three targeted unit tests in `code/rust/core_solvers/src/solver_graph_phi1_distance.rs`:

1. **Refusal Under Enumeration Limit (`enumeration_limit_refuses_instead_of_returning_partial_minimum`, lines 570–583)**:
   - Evaluates a 6-vertex, 9-edge Kagome trimer ring fixture (`kagome_request()`) with first Betti number $b_1 = 4$, which contains 54 spanning trees.
   - When called with `limit = 54`, the solver evaluates all 54 trees and succeeds (`forests_checked == 54`).
   - When called with `limit = 53`, the solver encounters the cap and returns `Err(GraphPhi1Error::EnumerationLimit)` rather than returning a partial minimum.
   - Execution command:
     ```bash
     cargo test --manifest-path code/rust/Cargo.toml -p core_solvers --lib enumeration_limit_refuses_instead_of_returning_partial_minimum
     ```
     Result: 1 passed; 0 failed.

2. **Input Validation Rejections (`rejects_unknown_endpoint_self_edge_and_bad_rational`, lines 612–647)**:
   - Verifies input validation refusals:
     - Edge referencing unlisted vertex produces `GraphPhi1Error::UnknownEndpoint`.
     - Self-loop edge $(a \to a)$ produces `GraphPhi1Error::SelfEdge`.
     - Decimal float string `"0.5"` produces `GraphPhi1Error::InvalidRational`.
     - Zero denominator string `"1/0"` produces `GraphPhi1Error::InvalidRational`.
   - Execution command:
     ```bash
     cargo test --manifest-path code/rust/Cargo.toml -p core_solvers --lib rejects_unknown_endpoint_self_edge_and_bad_rational
     ```
     Result: 1 passed; 0 failed.

3. **Multi-Cycle Exact Solution (`kagome_trimer_multi_cycle_b1_4`, lines 411–440 & 520–549)**:
   - Solves the Kagome trimer fixture under unit weights and unit claims.
   - Verifies that the solver returns exact defect `result.phi1 == "9"` and records `result.forests_checked == 54`.
   - Execution command:
     ```bash
     cargo test --manifest-path code/rust/Cargo.toml -p core_solvers --lib kagome_trimer_multi_cycle_b1_4
     ```
     Result: 2 passed (both `tests` and `paper_conformance` module copies); 0 failed.

4. **Python Adapter Boundary Verification (`test_proposed_boundaries.py`)**:
   - `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_proposed_boundaries.py`:
   - `test_refusal_timeout_and_nonzero_exit_keep_typed_errors`: confirms that a native refusal with reason `"EnumerationLimit"` is converted into a typed `NativeFunctionalRefusal` exception without fallback substitution.
   - Execution command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_proposed_boundaries.py -k test_refusal_timeout_and_nonzero_exit_keep_typed_errors -v
     ```
     Result: 1 passed; 0 failed.

## 6. Limits and Non-Claims

- **No Dual Circulation in Response Payload**: The `GraphPhi1Result` struct returns `phi1`, `gauge`, and `forests_checked`. It does not return the optimal dual circulation vector $y^\star \in \mathbb{Q}^E$. Although the solver evaluates a dual witness internally during certification, the dual circulation is not exposed in the returned response.
- **Worst-Case Exponential Complexity (No Polynomial-Time Scaling)**: The number of spanning forests grows rapidly with graph size (bounded by $n^{n-2}$ or Kirchhoff's Matrix Tree Theorem). The recursive search evaluates candidate trees branch-by-branch; no polynomial-time complexity is asserted.
- **Cap Scope Bounded to Completed Forests**: The 100,000 threshold bounds evaluated completed spanning forests (`*checked`). It does not bound intermediate recursion tree depth, pruned cyclic edge extensions, or memory consumption of `BigRational` representations.
- **Unpinned Binary in Python Adapter**: The Python adapter `native_functional._find_binary()` locates the binary via environment variable `CORE_FUNCTIONAL_GRAPH_BIN` or filesystem search in `target/release/` and `target/debug/`. It does not verify a cryptographic hash (such as SHA-256) of the binary before invocation.
- **Finite 1-Dimensional Graphs Only**: The solver operates exclusively on finite 1-dimensional cell complexes with rational edge weights and reports; it does not solve higher-dimensional cochain complexes ($C^k$ for $k \ge 2$).
- **No Machine Learning Claims**: Does not evaluate language model weights, embeddings, or token predictions.

## 7. Claim Hygiene Summary

1. **What it supports**: Demonstrates through source inspection and test execution that the native Rust solver (`solver_graph_phi1_distance.rs`) enumerates spanning forests for finite graphs with positive rational weights, caps search at 100,000 completed forests (`MAX_FORESTS`), returns an explicit `EnumerationLimit` error rather than a partial minimum when the cap is reached, and returns a verified result payload containing `phi1`, `gauge`, and `forests_checked`. Supported by cargo unit tests `enumeration_limit_refuses_instead_of_returning_partial_minimum`, `rejects_unknown_endpoint_self_edge_and_bad_rational`, and `kagome_trimer_multi_cycle_b1_4`.
2. **What it does not support**: Does not support polynomial-time scaling for general graphs (spanning forest enumeration is worst-case exponential); does not return the dual circulation vector in the output payload; does not establish cryptographic hash-pinning in the Python caller adapter (`native_functional.py`); does not bound recursion stack depth or arithmetic bit length.
3. **Narrowest defensible claim**: For finite directed graphs with declared unique vertices, non-loop edges, and positive rational penalties, `solve_graph_phi1` enumerates spanning forests in lexicographic edge order, refuses with `EnumerationLimit` when the number of completed spanning forests reaches 100,000, and returns `phi1`, vertex `gauge`, and `forests_checked` upon successful certification.
4. **Next test needed**: Derivation ATL-P001-009 (Paper-local Python reference returns primal potential and dual circulation only after independent verification, caps tree enumeration at 100,000 per component, and governor admits only strictly decreasing potential updates).

## 8. Cross-References & Provenance

- Archive Claim: [ATL-P001-008](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP001-08](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L20)
- DAG Review Node: `PAPER001-NATIVE-FOREST-SOLVER-REVIEW`
- Review Registry: `dag/reviews/additional_paper_001_support.json`
- Pull Request: #120
