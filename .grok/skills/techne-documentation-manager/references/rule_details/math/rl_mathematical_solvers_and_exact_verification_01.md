# Detailed definition: Mathematical Solvers & Sovereign Rust Delegation (1)

**AuthorityEffect:** None.

Parent: [Mathematical Solvers & Sovereign Rust Delegation](../../../../../rules/math/rl_mathematical_solvers_and_exact_verification.md). Load for the matching predicate, not every task.

# Rule: Mathematical Solvers, Sovereign Rust Delegation & Operator Invariants

**AuthorityEffect:** None.

This rule codifies sovereign Rust math delegation, projector endomorphism purity, packed operator contraction, matrix shape purity, and native solver fallback integrity across `engine` crates.

---

## Mathematical Projector Purity Invariant

> **Projector is a Pure Endomorphism:**
>
> 1. A Projector $P: C \to C$ must be deterministic, stateless, and idempotent ($P(P(x)) = P(x)$).
> 2. Projectors are strictly forbidden from calculating $\Phi_1$, calculating $\Gamma_2$, validating `PacketEnvelope`, judging numerical exactness, or certifying solver retractions.
> 3. All $\Phi/\Gamma$ calculations belong exclusively to `engine/crates_rs/core_functional/`.

---

## Parity Seam Isolation Invariant

> **Anti-Slop Parity Discipline:**
>
> 1. Never disguise self-assignment copies as PROD parity comparisons.
> 2. Never scatter fictional/unimplemented FFI branches throughout production code; isolate FFI seams into dedicated `ffi.py` modules.
> 3. Decompose parity into `type/parity.py` (types), `parity/registry.py` (registry), `parity/mirrors/` (independent reference implementations), and `parity/checks/` (executable comparisons).

---

## Zero Python Math Re-invention & Sovereign Rust Crate Delegation Invariant

> **Sovereign Rust Math Delegation Rule:**
>
> 1. **Zero Ad-Hoc Python Mathematical Solvers:**
>    Python code in `engine` and `pfp` is strictly prohibited from re-implementing mathematical elimination algorithms, numerical solvers, simplicial complex structures, holonomy loop products, or defect functionals when sovereign Rust crates exist under `engine/crates_rs/`.
> 2. **Sovereign Foundation Ownership:**
>    - **Linear Algebra (`core_linear_algebra`)**: Fraction-free Bareiss determinants, exact LDLᵀ decomposition, Sylvester positive definiteness, exact $\mathbb{Q}$-rank via `ExactRowReduction`, and Smith Normal Form.
>    - **Simplicial Homology (`core_homology`)**: Canonical simplicial complexes, face maps, boundary/coboundary matrices ($d \circ d = 0$), Betti numbers, and chain complexes.
>    - **Discrete Holonomy (`core_holonomy`)**: Discrete connections, connection Laplacians, loop curvature, and path-ordered holonomy products.
>    - **Defect Functionals (`core_functional`)**: $\Phi_1$, $\Gamma_2$, $\Xi$ defect evaluation, obstruction mass, and exact dual witness certification.
>    - **Exact Numbers (`core_number_theory`)**: Rational, quadratic and cyclotomic scalars, finite fields, polynomials, and exact real-embedding signs.
>    - **Groups (`core_lie_theory`), Fusion (`core_fusion_categories`), Probability (`core_finite_probability`)**: Group/Lie/Weyl algebra, fusion and modular data, stochastic maps and majorization, respectively.
>    - **Kernel (`core_kernel`) and Solvers (`core_solvers`)**: Certified rational enclosures and bounded combinatorics; exact search proposals with independently replayed certificates, respectively.
> 3. **Clean Architecture Port Contract:**
>    Inward domain layers (`domain/exact/`, `domain/solvers/`) must define pure Value Objects, shape validations, and typed Domain Protocols (`domain/ports/exact_ports.py`). They must delegate all mathematical computations through domain ports to native infrastructure adapters (`infrastructure/adapters/exact_rust_adapter.py`) backed by the FFI seam (`RustSymbolGameHost`).
> 4. **Anti-Sham Parity Guard:**
>    Infrastructure adapters must never wrap back around and call Python domain math functions (circular self-assignment anti-pattern). Adapters must invoke native host actions directly.
> 5. **Physics and Program Custody:** `core_quantum_physics` owns reusable finite physics and its finite MUB kernel; CLI, FFI, campaign, paper-specific, protocol and receipt code belongs to the calling program. Foundations never depend on the physics crate, and consumers import mathematical owners directly without forwarding facades.
> 6. **Exact Wire Canonical Form:**
>    When serializing `Exact` (`num_rational::BigRational`) values for cross-boundary FFI transport, integer rationals with unit denominators must be serialized without slash (e.g. `"1"`, `"0"`, `"-5"`), never as `"1/1"`, preserving strict canonical parsing under `core_kernel::parse_exact`.

---

## Zero-Allocation Hot-Loop & Packed Operator Contraction Invariant

> **Operator Hot-Loop Discipline:**
>
> 1. **Zero Hidden Heap Allocations in Hot Paths:**
>    Mathematical and quantum operator routines (trace, purity, Frobenius norm, expectation values, and inner products) must never allocate temporary collections (e.g. `.diagonal().collect()`, intermediate `Vec` allocations) inside inner loops.
> 2. **Dual-API Contraction Contract:**
>    Operator types implementing matrix-vector contractions ($y = H x$) must provide an in-place accumulation variant (e.g. `mul_vec_accumulate(&self, x: &[C64], y: &mut [C64])`) alongside any allocating convenience method (`mul_vec(&self, x: &[C64]) -> Result<Vec<C64>, _>`), ensuring zero-allocation performance in iterative solvers and ensemble sweeps.
> 3. **BLAS Symmetric Dual Update for Packed Triangular Storage:**
>    Packed Hermitian operators storing upper-triangular coefficients must evaluate matrix-vector contractions via single-pass symmetric accumulation ($y_i += A_{ij} x_j$ and $y_j += A_{ij}^* x_i$ for $i < j$) without unpacking or branching on row-major/column-major transpositions.
> 4. **Single-Pass Quadratic Form Reduction:**
>    Expectation values $\langle\psi| H |\psi\rangle$ on packed operators must be evaluated directly via $\sum_i H_{ii} |\psi_i|^2 + 2 \operatorname{Re}\left(\sum_{i < j} H_{ij} \psi_i^* \psi_j\right)$, avoiding intermediate vector allocations and preserving exact real-valuedness by construction.

---

## Matrix-to-Vector Shape Purity & Non-Fabrication Invariant

> **Vector Conversion Shape Rule:**
>
> 1. Matrix-to-vector converters (`_exact_vector`) must never convert empty matrices with zero columns and more than one row (e.g. SymPy `Matrix.zeros(n, 0)` with $n > 1$, or NumPy `zeros((n, 0))`) into fabricated zero vectors.
> 2. Malformed matrices with zero columns and $n > 1$ rows must immediately raise `ValueError("expected vector, got matrix with shape (n, 0)")`.
> 3. Only true 0-dimensional carriers (`(0, 0)`, `(0, 1)`, `(1, 0)`) may normalize to empty vector shapes `(0, 1)`.

---

## Native Solver Fallback Integrity & Refusal Non-Swallowing Invariant

> **Native Solver Boundary & Exact Weight Preservation:**
>
> 1. **No Silent Fallback to Unconstrained Evaluators:**
>    Native solver adapters must never silently swallow native mathematical refusals, enumeration exhaustion, timeouts, or non-zero exit codes into unconstrained secondary or Python solvers.
> 2. **Typed Error Hierarchy:**
>    Transport errors, timeouts, and solver refusals must propagate as distinct typed exceptions (`NativeFunctionalRefusal`, `NativeFunctionalTimeout`, `NativeEnumerationLimitExceeded`, `NativeFunctionalUnavailable`).
> 3. **Exact Rational Weight Preservation:**
>    Adapters and solvers must never truncate, round, or cast exact rational weights to integers (`int(w)`) or floating-point approximations. Exact rational arithmetic (`fractions.Fraction` or sovereign Rust `num_rational::BigRational`) must be preserved throughout.

---

## Simplicial & Algebraic Boundary Fail-Closed Invariant

> **Structural Validator Fail-Closed Rule:**
>
> 1. **Zero Silent Skips on Missing Boundary Data:**
>    Structural validators for simplicial sets, cubical sets, model categories, and chain complexes must never treat absent boundary maps, unmapped face indices, or unpopulated horn lookups as vacuously satisfied equations (`if let Some(...)`).
> 2. **Typed Boundary Violations:**
>    All boundary lookups in algebraic identity checks ($d_i d_j = d_{j-1} d_i$, $d \circ d = 0$) and horn filling verifications must use fail-closed resolution (e.g. `ok_or_else`), returning typed errors (`SimplicialIdentityViolation`, `InnerHornFillingViolation`) if boundary data is absent.
> 3. **Universal Morphism Factorization & Identity Totality:**
>    Model category and factorization system validators must iterate over all declared morphisms in the category rather than a single sample morphism, and must explicitly verify that every object possesses an identity morphism residing in the declared weak equivalence, fibration, and cofibration sub-classes.

---
