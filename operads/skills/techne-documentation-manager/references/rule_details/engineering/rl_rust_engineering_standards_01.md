# Detailed definition: Rust Engineering Standards (1)

**AuthorityEffect:** None.

Parent: [Rust Engineering Standards](../../../../../rules/engineering/rl_rust_engineering_standards.md). Load for the matching predicate, not every task.

# Rule: Rust Engineering & Workspace Execution Standards

**AuthorityEffect:** None.

This rule codifies native Rust crate exclusivity, Cargo workspace execution roots, ordered key trait derivation, crate collision prevention, test hermeticity, and fail-closed verification routines across engine operations. Cross-reference subsystem retirement and adapters: [`rl_subsystem_retirement_and_adapter_invariants.md`](../../../../../rules/engineering/rl_subsystem_retirement_and_adapter_invariants.md).

---

## Exclusive Native Rust Crate Adoption Invariant (`RULE_RUST_CRATES_RS_EXCLUSIVE_001`)

> **Native Rust Crate Authority:**
>
> 1. All root-level engines, solvers, operators, functional evaluators, and pipelines must adopt native Rust crates under `omega_engine/crates_rs` exclusively.
> 2. Legacy Python crate prototypes (`omega_engine/crates/` and `engine/_legacy/symbol_game_recovery/python/`) are permanently deleted/retired and must never be imported by new or refactored code.
> 3. When legacy Python runtimes are retired, dependent verification surfaces must fail closed with a typed `Refusal("RUNTIME_RETIRED", ...)` rather than throwing unhandled `ModuleNotFoundError`.
> 4. Python-to-Rust crossings must proceed strictly through canonical process or C-ABI FFI seams (`omega_engine_operating_system/python/adapters/rust_host/ffi.py`) with explicit outcome roots framed under `omega.oesos.rust-prime-host-outcome.v1`.

## Rust Cargo Workspace Manifest Path Invariant (`RULE_CARGO_WORKSPACE_ROOT_001`)

> **Cargo Workspace Execution Root:**
>
> 1. The canonical native Rust Cargo workspace root is located at `omega_engine/crates_rs/Cargo.toml`. The repository root does not contain a top-level `Cargo.toml`.
> 2. All Cargo commands (`cargo check`, `cargo test`, `cargo build`, `cargo clippy`) must be executed either with working directory set to `omega_engine/crates_rs` or by explicitly providing `--manifest-path omega_engine/crates_rs/Cargo.toml`.
> 3. Single-threaded `-j 1` compilation must remain strictly enforced across all Cargo invocations.
> 4. **Git Worktree Shared Target Cache:** When executing Cargo commands inside isolated git worktrees (`.worktrees/<name>` or temp checkout paths), agents MUST set `$env:CARGO_TARGET_DIR = "<primary_repo_root>/omega_engine/crates_rs/target"` (or pass `--target-dir`). Never allow an isolated worktree to generate a redundant 30 GB local `target/` cache, which exhausts disk budget and triggers MSVC linker failures (`LNK1140`/`LNK1201`).
> 5. **Sequential Single-Crate Test Execution:** Never execute multi-crate concurrent test sweeps across the workspace. Run tests sequentially on individual packages (`cargo test -j 1 --manifest-path omega_engine/crates_rs/Cargo.toml -p <crate> --lib`) to avoid Windows file lock collisions on `target/` and prevent transitive dev-dependency build bloat.
> 6. **Incremental Build Cache Disk Hygiene (`os error 112` Mitigation):** Repeated test and check cycles expand `omega_engine/crates_rs/target/debug/incremental` to 15–30+ GB. When free disk space drops below 5 GB or a build fails with OS error 112 ("There is not enough space on the disk"), agents must selectively purge the incremental cache (`Remove-Item -Recurse -Force "omega_engine/crates_rs/target/debug/incremental"`) rather than running a full `cargo clean`. This instantly reclaims 15–20 GB while preserving pre-compiled dependency rmeta artifacts in `target/debug/deps/`.


> **Pattern estate:** `AP_RS_001` / `HP_RS_001`, `AP_RS_003` / `HP_RS_003` (`.agents/patterns/anti/rust/`).

## Rust Ordered Key Collection Invariant (`RULE_RUST_ORDERED_KEY_DERIVE_001`)

> **Ordered Key Traits and Replay Boundaries (policy candidate):**
>
> 1. Domain identifiers/status types used as ordered collection keys must have a coherent total order. Derive or implement `PartialEq, Eq, PartialOrd, Ord` only when payloads and equality support it; `Hash`, `Copy` and serialization traits are separate usage requirements. Do not blanket-derive `Ord` on arbitrary float/error/JSON payload carriers.
> 2. A trait detector must compare complete names: `PartialOrd` is not `Ord`. Raw enum counts are review leads; comments, strings, test scopes, macros and actual collection use require triage.
> 3. At exact report, witness, certificate and receipt boundaries, use ordered collections or explicit canonicalization before observable iteration/serialization. Internal hash lookup is permitted when the consuming boundary sorts its output. Sorting console text does not sort separately serialized map fields.
> 4. Compare final report bytes across different insertion orders. Ordering keys alone does not canonicalize random IDs, timestamps or unordered nested payloads.
> 5. Distinguish actual map keys from values and `Result` errors. Resolve manual `Eq`, `Hash` and `Ord` together; custom equality can forbid structural derives. Test NaNs, signed zeros, mixed variants, integer extrema and repeated ordered-set insertion/lookup. Label derive-only scanner rows unverified; missing `Ord` is not itself a defect.
> 6. For name-bearing tapes, canonicalize semantic names before interning and traversal; allocated symbol IDs encode history. Test reversed interning and neighbor order while preserving dependency/refusal behavior.
> 7. At documented canonical JSON/hash/identity boundaries, explicitly sort nested object keys. Test additive `serde_json/preserve_order` feature unification against default golden bytes, opposing nested insertion and changed array order. Preserve source-ordered presentation and array order. Extracted loose-source harnesses do not establish active-package integration.

**Pattern estate:** `AP_RS_002` / `HP_RS_002`. The registry retains CANDIDATE:
a text scanner does not enforce every key type or wire boundary.

## Rust Crate File Collision Prevention Invariant (`RULE_RUST_CRATE_COLLISION_PREVENTION_001`)

> **Domain Factorization over Filename Matching:**
>
> 1. When porting legacy Python modules into existing native Rust crates, agents must inspect the target crate for existing identically-named files prior to writing.
> 2. If an existing module already implements mature functionality (e.g., `omega_solvers::solver_of_solvers`), the incoming module's specific bounded responsibility must be factored into an orthogonal domain module (e.g., `plan_grammar.rs`), avoiding name collisions or destructive overwrites.

## Omega Engine Tests Rust Exclusivity Invariant (`RULE_OMEGA_ENGINE_TESTS_RUST_EXCLUSIVE_001`)

> **Rust Tests Only in `omega_engine/tests`:**
>
> 1. `omega_engine/tests` is dedicated exclusively to native Rust workspace, integration, and unit tests.
> 2. It must never contain Python test files, fixtures, or module packages (`test_*.py`, `__init__.py`, `conftest.py`).
> 3. All Python tests across the repository reside in their respective operational contexts (e.g., `omega_engine_operations/tests/`, `research/papers/.../code/tests/`, `bench/.../tests/`).

## Review & Audit Cargo Compilation Restraint (`RULE_RUST_REVIEW_CARGO_RESTRAINT_001`)

> **Review Fencing & Immediate Process Termination:**
>
> 1. **Code Review Restraint:** When performing code reviews, PR inspections, or markdown documentation repairs, agents must not launch whole-workspace or multi-crate `cargo build` / `cargo test` processes. Scope checks to `cargo check -p <crate>` or targeted single-test functions only when Rust code is modified.
> 2. **Immediate Task Halting:** When a user signals to stop compilation (e.g., "stop the Rust build") or when disk/CPU constraints require it, running compilation tasks must be terminated immediately via `manage_task kill`, rather than awaiting background completion.
