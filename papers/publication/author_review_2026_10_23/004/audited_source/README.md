# Audited source for PFP IV

This directory holds an immutable copy of the source examined for PFP IV,
version 0.1.0 (2026-10-02). The repository that contains the original tree is
private. The tar in this directory is the copy a reader can inspect and use
for the reproduction route in the paper.

## Identity

- Source commit: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
- `omega_symbol_game` crate tree: `75d77aa5e1f30dfc102f00c8f7cb6159418dec63`.
- Historical native-run commit in the September report:
  `1c7092c3db2ab2fa65999cf2555aff7733b97b99`. At that commit the same crate
  tree is `75d77aa5e1f30dfc102f00c8f7cb6159418dec63`.
- This archive is that baseline. It is not a copy of a later main branch.
  The crate tree on later commits differs.

Machine fields are in `REVISION.json`. Member digests are in
`SOURCE_MEMBERS.sha256`: one line per file, the SHA-256 digest, two spaces,
then the repository-relative path. That manifest does not include the tar,
this note, or `REVISION.json`.

## Archive

- File: `pfp-iv-native-source-52cb5457.tar.gz`.
- Format: pax. Regular files: 7875. Mode `100644` on every member.
- No symlinks and no gitlinks.
- Member prefix inside the tar: `pfp-iv-native-source-52cb5457/`.
- Member modification time: 2026-10-02 12:00:00 UTC.
- SHA-256 of the tar:
  `a7be14eb339d476debaf06264f4334c83018127840853404018ad6972361e557`.
- SHA-256 of `SOURCE_MEMBERS.sha256`:
  `952625ad741692c9860ee1bd2670fdf38b05416377cdcb08263873708a1be73d`.

Extract from this directory:

```powershell
tar -xzf pfp-iv-native-source-52cb5457.tar.gz
```

The extracted root is `pfp-iv-native-source-52cb5457/`.

## What is inside

The members are the files at the source commit under:

- `LICENSE` and `LICENSING.md` (PolyForm Noncommercial 1.0.0).
- `omega_engine/crates_rs`, including `Cargo.lock` and the workspace manifest.
- `omega_engine/tests`, which the workspace lists as a member.
- `omega_engine/kernel`.
- `omega_engine_governance/contracts/contracts_the_symbol_game`.
- `omega_engine_governance/contracts/contracts_packets`.
- `omega_engine_pfp`.
- `omega_engine_providers`.
- `omega_engine_operating_system/python`.

The workspace member list was not reduced. A shorter member list would make
`cargo test --locked` fail to load the workspace. A copy of `host.rs` alone
is not this archive.

No `rust-toolchain` or `rust-toolchain.toml` file exists at this commit. The
historical runner recorded in the September report is Rust 1.98.0
(`x86_64-pc-windows-msvc`).

`omega_symbol_game/build.rs` includes `../contract_shapes_build.rs` and looks
for the symbol-game contract directory included above. It sets
`OMEGA_HOST_SOURCE_REVISION` from the environment or from `git describe`, and
otherwise records `UNSTAMPED`. An extracted copy has no `.git` directory, so a
build that does not set that variable is unstamped.

## Reproduction commands

From the extracted root, with Rust 1.98.0 and the locked dependency set:

```powershell
cargo test -j 1 --locked --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --test host_contract
cargo test -j 1 --locked --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --test foundation_contract
cargo test -j 1 --locked --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --test invoke_contract
cargo test -j 1 --locked --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --test native_cli_intake
```

On Windows, set `CARGO_TARGET_DIR` to a short directory outside this archive.
Do not point it at another checkout's `omega_engine/crates_rs/target`.

The four Python tests named by the paper are:

- `omega_engine_pfp/tests/test_packet_contracts.py`
- `omega_engine_pfp/tests/test_exact_functional_port.py`
- `omega_engine_pfp/tests/test_functional_boundary.py`
- `omega_engine_pfp/tests/test_ffi_seam_isolation.py`

Their top-level imports are present in this archive. Imports reached only
while those tests run were not enumerated here.

This October repair did not execute Cargo and did not execute those four
Python tests. The retained native counts live in the package directory
`docs/historical_native_run/`, beside this archive. Raw Cargo standard output
for the four targets was not retained.

This archive assigns no authorization and changes no jurisdiction.
