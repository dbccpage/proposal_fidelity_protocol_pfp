# Detailed definition: Rust Engineering Standards (2)

**AuthorityEffect:** None.

Parent: [Rust Engineering Standards](../../../../../rules/engineering/rl_rust_engineering_standards.md). Load for the matching predicate, not every task.

## Core Crate Integration Test Hermeticity Invariant (`RULE_RUST_CORE_CRATE_TEST_HERMETICITY_001`)

> **Hermetic Test Fixtures & Anti-Scratch Isolation:**
>
> 1. Integration tests within native Rust crates (`engine/crates_rs/tests/<crate>/`) must remain strictly hermetic. They must depend exclusively on canonical schemas, standard library fixtures, or local checked-in test vectors.
> 2. Core crate tests are strictly prohibited from referencing, scanning, or depending on temporary design demos, unpromoted scratch directories, or transient version folders (e.g. `ow/pfp/1_symbol_game_versions/...`).
> 3. Any experimental or transient demo tests must reside in the dedicated demo directory (`ow/ow_0_demo/` or `ow/pfp/3_code/`) and never pollute the core crate Cargo workspace.
> 4. A fixture copied into `tests/data/` from a paper package is a content copy, not a byte copy. `.gitattributes` sets `eol=lf` for JSON, YAML and TOML, so a CRLF source changes bytes on commit. Provenance comments must name the source path and source digest separately from the checked-in digest. Tests should compare parsed content or replayed results, not file digests across the two locations.

## Fail-Closed Witness & Verification Invariant (`RULE_RUST_FAIL_CLOSED_VERIFICATION_001`)

> **No Panics in Verification and Witness Checking:**
>
> 1. Verification routines, certificate checkers, and witness decoders must never invoke unhandled unwraps or expectations (`.unwrap()`, `.expect()`, unvetted numeric downcasts) on external or untrusted data.
> 2. All parsing and algebraic operations on candidate proposals must match exhaustively and return typed refusal/failure outcomes (such as `StabilizerCheckResult::Fail` or `Result::Err`) to ensure the host process fails closed deterministically.
> 3. Untrusted subprocesses must enter their configured confinement before execution. On Windows, create suspended, assign the Job Object successfully, then resume; terminate and close owned handles on setup failure. Parent exit does not establish inherited-pipe EOF: require reader success, preserve overflow/I/O failures, and return an explicit timeout/failure when collection exceeds the declared run deadline. Never default missing capture to successful empty output.
> 4. Exact modular arithmetic must not overflow before reduction. Reduce operands within the proven modulus bound or widen before multiplying; check supported-order negative values and signed extrema with and without overflow checks. The dyadic phase repair does not extend the supported root orders.

**Pattern estate:** `AP_RS_007` / `HP_RS_007`. Native finite regressions check
these specific paths; this broader rule remains CANDIDATE, not universal runtime
certification. Review scope must distinguish source-only findings from executed
reproductions, and preserve benign output/exit behavior and the public schema.

## Rustdoc Docstring Immunity & Mathematical Unicode Console Safety Invariant (`RULE_RUSTDOC_DOCSTRING_IMMUNITY_001`)

> **Docstring Preservation & Terminal Encoding Resilience:**
>
> 1. **Docstring Protection:** Lexers, comment scanners, and AST cleanup tools must treat Rustdoc outer (`///`) and inner (`//!`) doc comments as formal language attributes (`#[doc = "..."]`), maintaining parity with Python docstring protection. Tools must never classify, strip, or reroute them as inline comment slop.
> 2. **Console Encoding Resilience:** All diagnostic and reporting CLI tools scanning Rust and mathematical sources containing Unicode symbols (such as `∞`, `‖`, `≤`) must ensure standard I/O streams are UTF-8 compliant (`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`) to prevent `UnicodeEncodeError` crashes on Windows `cp1252` terminals.
