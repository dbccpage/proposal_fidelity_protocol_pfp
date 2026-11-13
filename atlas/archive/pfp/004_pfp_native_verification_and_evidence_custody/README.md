# PFP IV: Native Verification and the Custody of Finite Evidence

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Author-review preprint

[Read the complete paper](paper.md). It explains the native interfaces, packet
identities, encoding profiles, exact replay path, worked refused-admission
outcome, threat model, and reproduction plan. PFP is the Proposal Fidelity
Protocol; Symbol Game is the legacy name. The directory name is kept for stable
links.

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`. The native
fixture's expected values are source-derived assertions at that commit. No new
native compilation or execution is claimed by this release. Section 9 of the
paper identifies the retained September author-run report separately from
current package checks.

| Artifact | Purpose |
| --- | --- |
| [Paper](paper.md) | Standalone systems paper |
| [Claim ledger](paper_claim_ledger.md) | Scoped claims and exact evidence |
| [Weighted-cycle note](docs/completion_supplement.md) | Elementary mathematical example and the companion code's calculation path |
| [Change history](paper_change_log.md) | Current revision, withdrawn claims, and earlier versions |
| [Description](docs/descriptions.md) and [references](docs/references.md) | Deposit description and bibliography |

## Interfaces that must remain distinct

The default Rust host supports one same-carrier exact-replay path. A complete
laboratory execution still refuses admission with
`PRIME000_CONFORMANCE_PARTIAL` and `UNSIGNED_LAB_ATTESTATION`.
The same crate also exposes a broader `invoke` dispatcher and an additive
foundation library. Their contracts must be evaluated individually.

The packet codec uses tagged domain encoding; it explicitly does not claim
RFC 8785. Complete envelope custody belongs to the actual packet and host
protocol checks, not the weaker `PacketCodec.verify` helper.

## What this package contains

The repository that holds the pinned source is private. The public copy is
[the audited source archive](audited_source/README.md),
`audited_source/pfp-iv-native-source-52cb5457.tar.gz`, taken from commit
`52cb5457f6c485ba548cfd292f6012a941ed22cf`. The GitHub links in the paper name
that revision. The other files in this package are companion material:

- `code/`: legacy Python modules retained from the package's former manuscript
  (a graph governor, a packet firewall host, an arity rewrite engine, identity
  paths, a content-addressed repair log, a sparse-landing certificate builder, a
  retired scaling entry point, and three historical benchmarks with their
  receipts), plus `code/tests/`. The governor's `compute_phi1` uses exact
  Python enumeration when `CORE_FUNCTIONAL_GRAPH_BIN` is unset. With a
  configured native executable, it calls that calculator and propagates every
  native refusal or error. Its `step_cut`
  refuses a relational CUT that omits a declared edge (status
  `IncompleteProposal`) instead of reading the omission as a zero claim. See the
  [weighted-cycle note](docs/completion_supplement.md).
- `code/attention_entropy_kv_norm_benchmark.py` and its receipt: a historical
  measurement of attention entropy and key-value cache norms on one small
  open-weights model for one prompt pair. The paper does not use it, and its
  receipt does not support the entropy or memory reductions once described for
  it. Its tests load no model and need the optional PyTorch and NumPy
  dependencies.
- `lean4/`: six small Lean modules from the former manuscript, a generated
  `Census.lean`, and `axiom_report.txt` (86 theorems; axioms used are at most
  `propext`, `Quot.sound`, and `Classical.choice`). They do not formalize the
  native host.
- Release tooling: `verify_deposit.py`, `tools/`, `scripts/`, and
  `code/deposit_paths.py`.

The historical benchmark receipts in `code/` keep their original bytes and
scope; they are not results of this paper. The September native record and
the two pipeline receipts from that window are in
[docs/historical_native_run/](docs/historical_native_run/README.md). The
pipeline receipts do not name the four Cargo targets.

## Running the package checks

From this directory, with Python 3.12 (`py -3.12` on Windows):

```powershell
py -3.12 -m pytest code/tests/test_weighted_cycle_supplement.py -q
py -3.12 -m pytest code/tests/test_l1_symbol_game_governor.py -q
py -3.12 -m ruff check code
cd lean4; lake build; cd ..
py -3.12 tools/replay_lean_axiom_census.py --replay .
py -3.12 verify_deposit.py
```

Run the other files in `code/tests/` the same way, one file per command. The
tests make no network call. Without the `attention` optional dependencies the
attention-benchmark test file skips and says why.

## Native reproduction plan

Extract [the audited source archive](audited_source/README.md) and run these
commands from the extracted root `pfp-iv-native-source-52cb5457/`. On Windows,
set `CARGO_TARGET_DIR` to a short directory outside the archive. Do not point
it at another checkout's `engine/crates_rs/target`.

```powershell
cargo test -j 1 --locked --manifest-path engine/crates_rs/Cargo.toml -p core_symbol_game --test host_contract
cargo test -j 1 --locked --manifest-path engine/crates_rs/Cargo.toml -p core_symbol_game --test foundation_contract
cargo test -j 1 --locked --manifest-path engine/crates_rs/Cargo.toml -p core_symbol_game --test invoke_contract
cargo test -j 1 --locked --manifest-path engine/crates_rs/Cargo.toml -p core_symbol_game --test native_cli_intake
```

A historical author-run report records all four targets on 2026-09-28 EDT
(2026-09-29 UTC), with 12, 11, 32 and 9 passing tests under Rust 1.98.0.
The `core_symbol_game` crate tree at the recorded run commit
`1c7092c3db2ab2fa65999cf2555aff7733b97b99` is
`75d77aa5e1f30dfc102f00c8f7cb6159418dec63`, the same tree as the code
baseline. The October 2 package-local receipt does not record a fresh run of
these native targets. Raw Cargo standard output was not retained.
Python targets are `test_packet_contracts.py`, `test_exact_functional_port.py`,
`test_functional_boundary.py`, and `test_ffi_seam_isolation.py` under
`pfp/tests/`. Collect first and preserve native skips. A
scripted host validates adapter handling, not native computation.

## Toolchain and verification record

- Python 3.12.10, pytest 8.3.5, ruff 0.14.13 (rule selection pinned in
  `pyproject.toml`).
- Lean 4.34.0-rc1 through `lean4/lean-toolchain`; no Mathlib dependency.
- Rendering tools on the build host for this revision: pandoc 3.7.0.2 and
  XeLaTeX (MiKTeX-XeTeX 4.16, MiKTeX 25.12).

The dated review receipt recorded with this revision lists each command, tool
version, exit status, and tested scope. `verify_deposit.py` checks the manifest
and the two-way file census. `tools/rebuild_release.py --check` separately
checks the release archive.

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/uploads/23114538> (DOI: `10.5281/zenodo.23114538`, v0.1.0 Preprint).
Deposited October 3, 2026. Earlier internal revision 2.8.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

The current package-local execution record is
[docs/release_validation_2026_10_02_review_repairs.json](docs/release_validation_2026_10_02_review_repairs.json).
It records the selected current checks. Historical review receipts, including
`docs/release_validation_2026_10_01.json` and
`docs/release_validation_2026_10_02.json`, keep their original dates.

## 2026-10-23 author-review extension

The current manuscript adds the evidence-bound harness study. New PDFs are built in the collection's `publication/author_review_2026_10_23/` directory. Existing package PDFs, archives and deposited metadata retain their historical identities. See Paper 029 for source mapping and campaign reproduction. The live campaign is NOT_RUN.

Working-tree `MANIFEST.sha256` and `SHA256SUMS` describe the current author-review
revision. Historical release ZIPs and their embedded manifests retain their original
bytes and deposited identities; these working manifests do not redeposit them.
