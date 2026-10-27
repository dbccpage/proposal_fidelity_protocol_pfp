# Review prompt for Codex: the `pfp` command line

AuthorityEffect: None. Paste everything below the line into Codex, run from the
repository root on the branch that holds `code/rust/pfp_cli`.

---

You are reviewing `code/rust/pfp_cli`, a small Rust command line called `pfp`,
in the repository `dbccpage/proposal_fidelity_protocol_pfp`. Review it as a
skeptical senior engineer who will be paged if it ever damages a user's
machine or embarrasses the project in a demo. Do not change any files. Report
only.

## What the tool is for

People drop a prompt and the reply their model produced into `pfp`, and in
under a second it shows what the pair leaves to chance: a model certifying its
own work (`"verified": true`), digests it made up, role fields that claim
authority, a prompt that dictates its answer, no instruction for when the task
can't be done, "optimal" with no bound, and so on. It also seals files into a
packet of SHA-256 hashes that anyone can replay later. The owner's bar: it must
run, never harm the user's system, visibly improve their prompts, and stay
simple and extendable.

## The contract to hold it to

1. `pfp check [FILE ...] [--prompt FILE] [--json]` never writes, never uses the
   network, never starts a process. Text is checked line by line, JSON field by
   field (JSON with duplicate keys is read as text).
2. `pfp seal FILE ... [--out PACKET]` prints by default; writes only with
   `--out`, never over an existing file; refuses absolute paths, drive letters
   and `..`.
3. `pfp replay PACKET [--root DIR]` never writes and never reads outside
   `--root`; refuses packets with unknown fields, a wrong format, or hashes that
   do not match their own contents.
4. Exit codes: 0 nothing found, 1 findings or mismatches, 2 could not run.
   Inputs over 10 MiB are refused.
5. The library (`src/lib.rs`, `check.rs`, `packet.rs`, `catalog.rs`) does no
   I/O and builds for `wasm32-unknown-unknown`. `src/main.rs` does all I/O.
6. Output never claims more than it knows: "no findings" is not "correct", and
   a matching replay proves the bytes are unchanged, not who sealed them.
7. A new detector is one `Check` implementation plus a catalog entry; a test
   fails if a code has no entry.

## Do this

1. Read `code/rust/pfp_cli/README.md`, then every file in `src/` and `tests/`,
   then how `src/check.rs` calls `core_prompt_civilization::pharmacy`
   (`code/rust/core_prompt_civilization/src/pharmacy.rs`).
2. Build and test in `code/rust/pfp_cli`: `cargo test --locked`,
   `cargo clippy --locked --all-targets -- -D warnings`, `cargo fmt --check`,
   `cargo build --locked --lib --target wasm32-unknown-unknown`.
3. Try to break each contract item above with real commands in a scratch
   folder: symlinks, `.`/`..` segments, Windows and UNC paths, a file named
   `--json`, `--out` pointing at a directory or symlink, stdin, BOM, CRLF,
   non-UTF-8, `/dev/zero`, a FIFO, a forged packet whose hashes are
   self-consistent, duplicate JSON keys, very long lines.
4. Run `pfp check` on five ordinary, well-written prompts and replies of your
   own (a support summary, a code review, a SQL question, a JSON tool call, a
   refusal). Every finding on them is a false positive: list each one.
5. Read `.github/workflows/pfp-cli.yml` and `pfp-cli-release.yml` for mistakes
   on Windows, macOS and musl, and for permission scope.
6. Check that the root `README.md` hero section and the crate README say only
   true things.

## Report

Under 800 words. Findings ranked most severe first, each with severity
(critical, high, medium, low), `file:line`, the exact command you ran and what
it printed, and the smallest fix. Mark each finding "reproduced" or
"suspected". Then list the false positives from step 4. End with the three
changes that would most improve simplicity or extendability, and a one-line
verdict: ship, ship after fixes, or do not ship.
