# 09. Staged Mathematical Scope & Owner Boundaries

**AuthorityEffect:** None.
**Classification:** Exact Verification Scope & Rust Owner Boundaries.
**Status:** Canonical Reference.

This document formalizes the mathematical scope of the 50 Symbol Game staged demonstrations, existing Rust crate owners, and native conformance boundaries.

---

## 1. Implementation Ownership Matrix

> **Source check (2026-10-20, pin `c419cc6beb`).** Several owners named below have moved or are absent. Read the matrix with these corrections:
>
> | Cited owner | Status at the pin |
> | :--- | :--- |
> | `ow/pfp_v0.2/python/` | not found; the PFP Python package is `pfp/` (`domain/`, `use_cases/`, `infrastructure/`) |
> | `core_functional::phi1` | present: `Phi1Functional::verify_exact_certificate` in `engine/crates_rs/core_functional/src/phi1.rs` |
> | `core_homology`, `core_wdp`, `core_mub`, `core_local_green_global_red_lggr::matrix_path_kernel` | present as crates under `engine/crates_rs/` |
> | `python/infrastructure/exact_math.py` | moved: `pfp/infrastructure/exact_math.py` |
> | `core_prime_algos::licensed_lift_gate` | moved: `core_wdp::prime_algos::licensed_lift_gate` (`engine/crates_rs/core_wdp/src/prime_algos/licensed_lift_gate.rs`) |
> | `core_wdp::sql_normal_form` | not found in `core_wdp`; SQL normal-form code exists in `auto_p` (`src/compiler/sql_normal_form.rs`) and `core_symbol_game` (`src/invoke/exact.rs`) |
> | `python/infrastructure/adapters/owner_adapters.py` | not found |
> | `_intelligence/.native_owner_adapter/` receipts | not found |
>
> The "50 staged demonstrations" and the conformance list in Section 2 were not rechecked. The Section 2 claims depend on the missing adapter and receipts, so they are historical, not current evidence.

| SG Family | Existing Owner / Canonical Module | What Staged Implementation Checks | Boundary Limit |
|---|---|---|---|
| **01–08, 17, 30–36** | `ow/pfp_v0.2/python/` domain & use cases | Alphabet, literal syntax, typed interfaces, refusal, claim preservation | Typed packet establishes neither encoded claim nor model internal state. |
| **09–12, 18–19, 21, 24** | `core_functional::phi1`, `core_homology`, `python/infrastructure/exact_math.py` | Exact rational chain equations, primal/dual bounds, Hodge components | No general optimization solver inferred from fixtures. |
| **13–16, 37–38, 43, 48** | `core_wdp`, `core_prime_algos::licensed_lift_gate`, DDC | Map/closure calculations, finite capability gaps, operator preservation | Stagnation is not an exhaustion certificate or lift license. |
| **20, 44** | `core_local_green_global_red_lggr::matrix_path_kernel` | Explicit local/global predicates; defect-complex gluing | GlobalGreen continuation authority requires separate proof. |
| **22–23** | `core_wdp` Meron adapters; integer homology | Four-state weighted sign involution; integer divisibility example | No general fermion sign-problem solution claim. |
| **25, 28** | WDP geometry adapters; `core_mub` | Exact Cayley-Menger determinants and Fourier basis pair in dimension 6 | Finite geometry sample, not a general physical realization. |
| **26** | `core_wdp::sql_normal_form` | Concrete joins, FD closures, projected FD preservation | No general chase confluence theorem. |
| **27, 36** | Installed Lean compiler; tier/F/oracle sources | Proof compilation and axiom census for Bool cochain identity | Proof is only the printed target; axiom whitelist checked. |

---

## 2. Native Rust Conformance (`Phi1Functional`)

`python/infrastructure/adapters/owner_adapters.py` provides `verify_phi1(...)` and `crosscheck_candidate(...)`, calling the existing Rust `core_functional::phi1::Phi1Functional::verify_exact_certificate` directly.

- Offline native conformance executes for SG-12, 18, 19, 24, 32, 35, 36, and 41.
- Corrupt duals, corrupt primals, and corrupt reported values are rejected by Rust.
- Executable receipts are preserved under `_intelligence/.native_owner_adapter/`.
