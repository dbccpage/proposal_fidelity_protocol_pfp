# Detailed definition: Mathematical Solvers & Sovereign Rust Delegation (2)

**AuthorityEffect:** None.

Parent: [Mathematical Solvers & Sovereign Rust Delegation](../../../../../rules/math/rl_mathematical_solvers_and_exact_verification.md). Load for the matching predicate, not every task.

## Mathematical Content Hash State Totality Invariant

> **Content Digest State Completeness Rule:**
>
> 1. **Complete State Commitment:**
>    Cryptographic content hashes (`content_hash`) of algebraic structures (differential graded categories, chain complexes, derived categories) must commit to the full internal state, including hom-complex differential matrices, identity morphisms, composition tables, chain-map components, and mapping cone structures.
> 2. **Mutation Resistance:**
>    A mathematical content hash is invalid if perturbing a differential matrix or chain map leaves the digest unchanged.
> 3. **Source Dependency Fail-Closed Discipline:**
>    Run harnesses and receipt generators must never emit fallback dummy digests (e.g. `"0" * 64`) when declared source dependencies (such as `Master.lean`) are missing. Missing dependencies must raise `FileNotFoundError` immediately.

---

## Exact Linear Algebra Boundaries & Unimodularity Invariant (`RULE_EXACT_LINALG_BOUNDS_AND_CONVERSIONS_001`)

> **Arithmetic & Transformation Boundaries:**
>
> 1. **Fallible Sparse-to-Dense Conversions:** Any method expanding sparse matrix storage into dense arrays or matrices must be fallible (`Result<DenseMatrix, ShapeOverflowError>`), validating matrix dimension products via checked multiplication (`rows.checked_mul(cols)`). Conversions must never trigger unhandled allocator aborts.
> 2. **Pre-Check Integer Widening:** Conversions from exact rational numbers to signed integer numerators must widen raw values to arbitrary-precision integers (`BigInt`) *before* testing divisibility or sign negation, preventing signed arithmetic overflow on extreme values (such as `i64::MIN / -1`).
> 3. **Wide Intermediate Modular Arithmetic:** Prime field arithmetic ($F_p$) multiplication must widen operands to wide registers (`u128` or `i128`) prior to modular reduction, preventing integer overflow during intermediate multiplication for large moduli $p$.
> 4. **Smith Normal Form Unimodularity Verification:** Verifiers for Smith Normal Form decompositions ($A = U \cdot S \cdot V$) must verify that transformation matrices $U$ and $V$ are unimodular ($\det(U), \det(V) \in \{+1, -1\}$) in addition to exact reconstruction $U \cdot S \cdot V = A$.
