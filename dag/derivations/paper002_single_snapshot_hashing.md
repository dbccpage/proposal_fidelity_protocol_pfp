# PAPER002-SINGLE-SNAPSHOT-HASHING: Single Snapshot Hashing

AuthorityEffect: None.

- Archive claim: [ATL-P002-010](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("Checking and hashing use the same snapshotted matrix.", [paper_claim_ledger.md:25](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L25))
- Audit derivation node: [PAPER002-SINGLE-SNAPSHOT-HASHING](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER002-SINGLE-SNAPSHOT-HASHING`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

The matrix checker and presentation digest generator consume the same immutable in-memory snapshot of a one-shot matrix input, ensuring that single-pass streams and iterators cannot produce divergent digests or empty-matrix evaluations.

## 2. Context & Hypotheses

- **One-Shot Traversal Hazard**:
  In Python, iterators and generator expressions are stateful and exhausted after a single traversal. Passing an iterator to a function that reads it multiple times results in empty subsequent reads.
- **Historical Vulnerability**:
  Prior to the 2026-09-24 repair, `exact_matrix_digest` and `search_exact_matrix` iterated over input matrices without caching. An iterator of a valid matrix could be hashed or checked as an empty matrix.
- **Repair Implementation**:
  In `code/genesis_alpha/frontier_search.py`, both `exact_matrix_digest` and `search_exact_matrix` eagerly construct an immutable tuple of tuples upon entry:
  ```python
  rows = tuple(tuple(row) for row in matrix)
  ```

## 3. Derivation / Evidence

### 3.1 Code Inspection of Entry Points
1. In `exact_matrix_digest`:
   ```python
   def exact_matrix_digest(matrix: Sequence[Sequence[Union[int, Fraction]]]) -> str:
       rows = tuple(tuple(row) for row in matrix)
       matrix_sign_graph(rows)  # validate the same snapshot that is serialized
       canonical = [["{}/{}".format(Fraction(value).numerator, Fraction(value).denominator)
                     for value in row] for row in rows]
       return _canonical_sha256({"exact_real_symmetric_matrix": canonical})
   ```
   The argument is captured into `rows`. Both `matrix_sign_graph` (validation) and canonical serialization (digesting) consume `rows`.
2. In `search_exact_matrix`:
   ```python
   def search_exact_matrix(
       matrix: Sequence[Sequence[Union[int, Fraction]]], key: PresentationKey, ...
   ) -> SearchReceipt:
       rows = tuple(tuple(row) for row in matrix)
       matrix_digest = exact_matrix_digest(rows)
       if key.hamiltonian_digest != matrix_digest:
           raise ValueError("presentation Hamiltonian digest does not match exact matrix")
       vs, es = matrix_sign_graph(rows)
       return search_sign_graph(vs, es, key, ...)
   ```
   The argument is captured into `rows`. Both the digest calculation and the graph construction consume `rows`.

### 3.2 Executable Verification with One-Shot Iterators
When passing a one-shot iterator `iter(triangle)` to `exact_matrix_digest`:
- The iterator is drained into `rows` during the tuple comprehension.
- The computed digest matches `exact_matrix_digest(triangle)`.
- When passing `iter(triangle)` to `search_exact_matrix`:
  - `key.hamiltonian_digest` matches `matrix_digest`.
  - `matrix_sign_graph` receives the populated `rows`.
  - The search executes on the intended matrix rather than an empty matrix.
  - A mismatched key produces a refusal with `ValueError("presentation Hamiltonian digest does not match exact matrix")`.

## 4. Limits and Non-Claims

- **Memory Bound**:
  Eager snapshotting realizes the matrix in system memory ($O(n^2)$ space). It does not provide an out-of-core or distributed streaming solution.
- **Runtime Environment**:
  The property holds within standard Python object execution and does not protect against external memory corruption.

## 5. Claim Hygiene Summary

1. **What it supports**:
   Supports that `exact_matrix_digest` and `search_exact_matrix` snapshot one-shot iterators into immutable in-memory tuples, binding digest calculation and graph validation to the identical data.
2. **What it does not support**:
   Does not support out-of-core streaming for arbitrarily large matrices exceeding RAM.
3. **Narrowest defensible claim**:
   Under the repaired implementation, one-shot matrix inputs are snapshotted into immutable tuples, preventing iterator exhaustion divergence between hashing and checking.
4. **Next test needed**:
   Validation with custom generator streams and non-standard sequence implementations.

## 6. Cross-References & Provenance

- Archive Claim: [ATL-P002-010](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP002-10](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L25)
- Provenance Record: `atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/code/PROVENANCE.md` (2026-09-24 repair)
- Verification Test: `tests/test_paper_002_search_trace.py`
