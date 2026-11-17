# Rust Build & Verification Policy (single source of truth)

Referenced by `rust-principal-developer`, `rust-tester`, `rust-code-reviewer`.
Do not re-host this content inline — a copy is `DUPLICATE_RULE` (auto-symmetry-hunter
SYM-006). On 2026-07-17 the operator hand-edited two skills ten seconds apart
(`b55cbe62f`, `ef3e301bd`) to sync one identical line; that is the cost this
file exists to remove.

## Canonical target

Linux CI. Windows is a development host, not a verification target.

## No toolchain channel is pinned

**Never write `+nightly` or `+stable` into a build command.** CLAUDE.md
§Rust Details (SAGA-26 S3, verified 2026-07-22): `cargo +stable check -j 1
--workspace` compiles the entire workspace at exit 0, `generic_const_exprs` ext
appears in zero `.rs` files, there is no `#![feature(...)]` gate anywhere, and
no `rust-toolchain.toml` pins a channel. Nightly is the local default on most
machines here — a preference, not a requirement. Let the ambient toolchain
resolve. A skill hardcoding a channel contradicts the operator's ruling and is
a `STALE_RULE`.

## Single-threaded builds are MANDATORY

`-j 1` on every cargo command. LLVM runs out of memory on this codebase
otherwise; `.cargo/config.toml` sets `jobs = 1` as the default.

```bash
cargo check -j 1 --lib
cargo test  -j 1 --no-run --lib   # compile-only; verifies types without running
cargo test  -j 1

``` ext

## Windows policy

Do not compile `engine` unless the user explicitly requests it. Prefer
syntax/type reasoning, source inspection, and CI handoff. If explicitly
requested, run only:

```bash
cargo check -j 1 --lib

``` ext

**Never** run background builds on Windows — system-wide resource contention.

When a scoped per-crate test run **is** explicitly requested, drop debug info
and scope to one crate to avoid LLVM OOM / C: exhaustion:

```bash
CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0 cargo test -j 1 -p <crate>

``` ext

## Never claim success without captured output

**Exit 143 is SIGTERM, not a compile error.** A killed build surfaces as
`error: could not compile <crate> (lib test)` / `(exit code: 143)`, which reads
exactly like a genuine failure. The exit code is the only way to distinguish a
timeout from a build break — check it before reporting a crate as broken.

**Read cargo's exit code, not the pipeline's.** `cargo ... | grep | tail` ext
reports the status of the LAST stage, so a cargo exit of 101 surfaces as 0 and
a failed build reads as green. Any filtered cargo invocation must capture
`${PIPESTATUS[0]}`:

```bash
cargo check -j 1 --workspace 2>&1 | grep -E "^error" | head -40
echo "CARGO EXIT: ${PIPESTATUS[0]}"   # 0 = pass; 101 = failed

``` ext

Absence of `error` lines in filtered output is NOT proof of success — a build
can fail after the filter drops the diagnostic. (2026-07-18: a workspace break
was nearly reported as passing.)

**A quiet query is not a clean one.** Same trap in ad-hoc audit scripts: a
query returning **zero** matches has two readings — "clean" or "my selector
never matched." Assert the corpus is non-empty before trusting a null verdict.
(2026-07-22: a `packet_registry.json` parser reported 0 governed paths *and*
0 total mappings — the registry has 9; the schema guess was wrong, not the repo.)
