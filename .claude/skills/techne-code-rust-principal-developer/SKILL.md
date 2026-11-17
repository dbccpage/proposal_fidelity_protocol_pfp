---
name: techne-code-rust-principal-developer
description: "Use to implement Rust sprint stories. Fix compile errors, write meaningful tests, keep evidence."

operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "unknown"
---

# techne-code-rust-principal-developer

## Constraints

## Cryptographic Lifecycle Management: Rotation vs Revocation

## Compilation Hygiene

### BTreeMap/BTreeSet Ordered Key Derives (`RULE_RUST_ORDERED_KEY_DERIVE_001`)

**Failure Mode:** `E0277: the trait bound T: std::cmp::Ord is not satisfied` when calling `.entry(k).or_insert(v)` on a `BTreeMap`.
**Prevention:**
Always derive `PartialOrd, Ord` on enums and value objects representing:
- Transition system owners and effect kinds
- Cost orderings and grammar search tags
- Multiset counting keys for governance equivalence

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum EffectOwner { ... }
```

**Source:** core_governance session 2026-05-27 (GovernanceError enum compilation failure)
**Fix:** Rename the field (e.g., `source` → `src`, `source_id`, or `origin`):

### thiserror v2 Reserved Field Names

**Source:** Sprint 0021-0022 MSS-N Grammar Pipeline implementation
**MANDATORY Pre-Implementation Check**:

## Type and Enum Verification

### Immutable Execution Boundaries

## Type-State Constraints

**Source:** Integration audit session 2026-02-22 (4 build attempts before success)
**Note:** PowerShell `$_` syntax gets mangled in Git Bash. Use explicit `-match` syntax
**Prevention:** Close rust-analyzer (stop LSP in IDE) before long builds.
**Fix:**
**Cause:** Stale `cargo` / `rustc` / `rust-analyzer` processes holding `.cargo-lock` files.
**Symptom:** `cargo check` / `cargo build` hangs with "Blocking waiting for file lock on build directory".

### Windows: Cargo Build Lock Contention

## Platform-Specific Troubleshooting

## PyO3 Bridge (DORMANT — no bridge exists)

**Source:** QUIP implementation session 2026-02-20 (compilation error)

## Rand API Rule

**Source:** QUIP implementation session 2026-02-20
**Unitary operators cannot change a maximally mixed state.** For any unitary U:

## Density Matrix Evolution: Kraus vs Unitary

## Packed Operator & Linear Algebra Hot-Loop Patterns

**Source:** Benchmark session 2026-09-27 (CMatrix vs PackedHermitian across d in {2, 4, 8, 16})

### 1. Zero Hidden Allocations in Scalar Reductions
Never call intermediate collecting helpers (e.g. `.diagonal().collect()`, temporary `Vec`s) inside hot operator loops (trace, purity, Frobenius norm).
```rust
// CANONICAL PATTERN: zero-allocation direct loop over diagonal indices
pub fn trace(&self) -> f64 {
    let dim = self.dim;
    let mut tr = 0.0;
    for i in 0..dim {
        tr += self.data[packed_index(dim, i, i)].re;
    }
    tr
}
```

### 2. BLAS Symmetric Dual Update (`zhpmv` style)
For upper-triangular packed storage, accumulate both output elements symmetrically in a single 1D pass:
```rust
for i in 0..dim {
    let a_ii = self.data[packed_index(dim, i, i)].re;
    y[i] += C64::new(a_ii * x[i].re, a_ii * x[i].im);
    for j in (i + 1)..dim {
        let a_ij = self.data[packed_index(dim, i, j)];
        y[i] += a_ij * x[j];
        y[j] += a_ij.conj() * x[i];
    }
}
```

### 3. Dual-API Contraction Contract & Single-Pass Quadratic Forms
Provide `mul_vec_accumulate(&x, &mut y)` for in-place zero-allocation loops. Compute \(\langle\psi| H |\psi\rangle\) directly via \(\sum_i H_{ii} |\psi_i|^2 + 2 \operatorname{Re}\sum_{i < j} H_{ij} \psi_i^* \psi_j\).


**Source:** FSP Invocation session 2026-02-19 (15-agent synthesis)

### Categorical Lift and Descent

## Categorical Meta-Patterns

### Test Assertion Discipline

## Testing Strategies

**Source:** Trial Run 000 Bug 2 — kernel space mismatch in `row_echelon()` (2026-02-20)

### Kernel Computation via Augmented History

## GF(2) Linear Algebra Patterns

**Source:** Symbol Game implementation session 2026-05-22 (LP grammar `nn<x>=0,y>=0>` parsing fix)
**Common mistake:** Checking `prev != '='` instead of `next != '='`. In `>=`, the `>` comes BEFORE the `=`, so the check must look ahead.
**Pattern:** Check the *next* character before counting `>` as a bracket:

### Operator vs Delimiter Disambiguation in Parsers

**Source:** Symbol Game implementation session 2026-05-22 (symbol_game standalone package fix)
**When to use:** Standalone packages in `engine/products/` that have their own dependencies (e.g., `symbol_game`, `simplex_cosmos`) but should not be part of the main workspace build.
**Fix:** Add an empty `[workspace]` table to the package's `Cargo.toml`:
**Symptom:** `cargo check` fails with "package believes it's in a workspace when it's not"

### Standalone Package Workspace Configuration

**Binary pattern**:
**CRITICAL Crate Root Verification**:
**Solution**: Use `crate::reactor` for library-level imports.
**Issue**: `super::reactor` fails when module is `include!`'d in a binary context.

### Import Paths: `super::` vs `crate::` ext

**Pattern**: If a type is used across module boundaries, all its essential methods must also be public.
**Anti-pattern**: Making structs public but leaving methods private blocks composition.
**Required public exports:**

### Making Types Public for Cross-Module Composition

**Source:** Sprint 020 retrospective (integration test compilation blocked by missing child modules)

### Module Pre-stubbing (MANDATORY)

## Module Composition & Visibility

**Source:** Session 2026-02-19 architectural discussion
**What Rust CAN uniquely express:** Affine logic via ownership model. Resource-constrained

## Rust Type System Limits (for catkit development)

## Known Defect Handling

## Removed: Ascent Tower, FSP, Kaggle (code no longer in tree)

**Family:** code-generation (see [family_registry.md](../_shared/family_registry.md))

## Related Skills

## Single-File Evaluator & Engine Placement Law

## Source

**Source:** Tower audit session 2026-03-22 (L060_2 manifest v2: diagenesis_functor + map_colimit Goo fields)

### Goo Declaration in Manifest

**Source:** Tower audit session 2026-03-22 (527 tears refactored across 34 files, 65+ classified irreducible)
**Note:** Simple reachability queries (e.g., "is node A reachable from node B?") CAN be expressed functionally via `std::iter::successors` fixed-point expansion. Only classify BFS/DFS as irreducible when the traversal requires a queue/stack with order-dependent processing or mutable path accumulation.

### Irreducible Patterns (Goo -- do NOT refactor)

**Requires:** `use itertools::iproduct;` for cartesian products (already a dependency).

## Procedural-to-Categorical Replacement Patterns

**Source:** Tower audit session 2026-03-22 (47 errors fixed across 20+ files, patterns 1-3 covered ~90%)
**Source:** Session 2026-03-24 (proof_solver.rs E0382 fix in search_step)
**Root cause:** `bool::then(|| {...})` takes ownership of captured variables in the closure. The `unwrap_or` fallback then tries to use the same variables — double move. A `match` avoids this because only one arm executes and ownership flows linearly.

### 4. try_fold + nested closures causing double-move (E0382)

### 3. Imperative escape hatch (E0597, E0500)

### 2. Collect-then-mutate (E0502)

### 1. Reference-before-move (E0507, E0382)

## Borrow-Checker Fix Taxonomy

**Let the compiler close the loop.** After the scoped edit, `cargo check --workspace
**4. Renaming a`#[derive(Serialize)]` enum is a data migration.** Previously-persisted JSON
**3. Strings are wire format; decide per surface.** Rust variant renames must NOT propagate
**2. Method renames follow the receiver's type, not the method name.** Rename `.foo()` only
**1. Scope by import, not by name.** A file is a real consumer only if it references the

## API Rename / Cross-Crate Migration Taxonomy

### Source-Scanning Matcher Hygiene

### Recursive Closures

### `Box<dyn Fn>` with Generics

### Structural Invariants

**Enforcement**: Any downstream claim whose evidence type is in `contract.forgets` must be stripped or rejected by the governance engine.

### Categorical Governance

### Law Witnessing Rule

### Algebraic Adjunctions

### Transactional State Transitions

### Cryptographic and Governance Hygiene

**FORBIDDEN**: Bypassing linearity by adding `restore_from_id()` or ID-based token re-instantiation methods. Once an affine token is consumed, it must never be "cloned" or "restored" from raw data without an explicit, verifiable `Active` state check and an exclusive `move` from the registry.

### Affine Resource Management

## Trait Bound Patterns

**YAML canonical source of truth:**

## core_contracts Crate Architecture

**Source:** core_governance session 2026-05-27

## core_governance Crate Conventions

**Fail-closed arithmetic:** in cost/quota math, saturate the FINAL result, never an

## Test Quality Law

## Evidence Capture

**Two silent-failure traps found at main tip, 2026-07-28** — both make a *green-looking*

## Build Policy

## Definition-First Rule

## Completion Rule

## Coding Protocol

## Required Skills

## Authority

**Source:** Autoskill session 2026-07-17 (Φ₁ emitter placement — operator reuse-crates directive).
**Operator directive (2026-07-17):** "Look at existing Rust crates inside engine

## Crate-First Rule (survey before writing machinery)

## Crate Layer Separation (Dependency Inversion)

**Rule:** If you add a field to a struct, grep for all constructors of that
**coupled file pairs** to the **same agent**. A coupled pair is any two files

## Shared-File Coordination Rule (Multi-Agent)

**Source:** core_governance session 2026-05-27 (edition 2024→2021 fix, directory redirect)
**Post-spawn verification:** After subagent completion, always check:

## Subagent Workspace Convention Transmission

## Prime Directive

## status: canonical-candidate

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
