---
documentation_contract: symbol-game-documentation/v1
title: Native Rust host reference
kind: public-contract-reference
audience:
- engineers
- coding-agents
status: supported-laboratory-surface
maturity: supported-laboratory
claim_status: source-grounded
authority_effect: "None"
source_paths:
- omega_engine/crates_rs/omega_symbol_game/Cargo.toml
- omega_engine/crates_rs/omega_symbol_game/src/lib.rs
- omega_engine/crates_rs/omega_symbol_game/src/main.rs
- omega_engine/crates_rs/tests/omega_symbol_game/host_contract.rs
- omega_engine/crates_rs/omega_symbol_game/src/protocol.rs
- omega_engine/crates_rs/omega_symbol_game/src/invoke.rs
source_revision: c419cc6beb
prerequisites: []
verification: py -3.12 -m omega_engine_pfp.scripts.docs_integrity validate
aliases: []
related:
- 09_runtime_actions_and_governor.md
- 01_digest_and_canonical_serialization.md
last_verified: 2026-10-20
verification_scope: command list and limits read from main.rs, protocol.rs and invoke.rs; no cargo build or test run
---

# 08. Native Rust Host Reference & Verification Contracts

AuthorityEffect: None.

omega_symbol_game is the supported native laboratory host for one narrow,
exact candidate-evaluation path. Its output is unsigned laboratory evidence,
not an admission or promotion decision.

## Supported consequential operation

With no operation argument, the binary reads one bounded HostRequestV1 JSON
document from standard input and writes a HostOutcomeV1 JSON document to
standard output. The supported profile is evaluate_candidate with request
schema omega.oesos.rust-prime-host-request.v1 and outcome schema
omega.oesos.rust-prime-host-outcome.v1.

The host parses strictly, recomputes request and packet identifiers, validates
the carrier manifest, performs exact replay, checks the supplied candidate
against the replayed normal form, and returns exact summaries or typed
refusals.

## Commands

| Command | Input | Output | Scope |
| --- | --- | --- | --- |
| --mcp | MCP messages on stdin | MCP responses on stdout | Serves `omega_symbol_game::mcp` (added to this table 2026-10-20) |
| --describe | none | host description JSON | Schemas, limits, registry hash, source revision, attestation |
| --describe-runtime | none | runtime description JSON | Derived adapter list only |
| --derive-carrier-manifest | CarrierDeclarationV1 JSON | carrier manifest JSON | Manifest construction |
| classify-board | board JSON | board verdict JSON | Legacy finite gauge-board classification |
| invoke | RuntimeRequestV1 JSON | RuntimeOutcomeV1 JSON | Dispatchable runtime actions |
| default | HostRequestV1 JSON | HostOutcomeV1 JSON | Supported exact candidate evaluation |

The dispatch order in [main.rs](../../../../omega_engine/crates_rs/omega_symbol_game/src/main.rs) (lines 19-127 at the 2026-10-20 pin) is: `--mcp`, `--describe`, `--describe-runtime`, then read stdin, then `--derive-carrier-manifest`, `classify-board`, `invoke`, then the default evaluation when no argument is given. Any other first argument returns the error `unsupported operation` after stdin has been read.

Use the workspace manifest:

~~~powershell
cargo run --quiet --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game -- --describe
~~~

## Resource fences

The supported request has a one-megabyte ceiling (`MAX_HOST_REQUEST_BYTES = 1_048_576`
in [protocol.rs](../../../../omega_engine/crates_rs/omega_symbol_game/src/protocol.rs)
line 19), exactly one candidate, and declared bounds for edges, vertices plus faces, dense matrix cells, Prime
writes, and timeout. Exact values use minimally encoded decimal strings and
BigRational semantics; JSON floats are refused.

The `invoke` path reads a larger prefix, `MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES = 12 * 1024 * 1024`
(12,582,912 bytes), so the large prompt-artifact actions can be identified; other runtime actions keep
the complete-envelope limit `MAX_RUNTIME_REQUEST_BYTES = 65_536` (64 KiB)
([invoke.rs](../../../../omega_engine/crates_rs/omega_symbol_game/src/invoke.rs) lines 47 and 53).
The dense-matrix cell bound is also `1_048_576` (`MAX_DENSE_MATRIX_CELLS`, protocol.rs line 22).

The declared timeout is an intake field, not an in-process wall-clock
watchdog. A deployment needing a kill boundary must enforce one outside the
process and preserve that enforcement as separate evidence.

## What a successful laboratory result means

A successful fixture can include replayed exact summaries, commitments, and
typed conformance information. It remains unsigned laboratory evidence:

- digest and commitment fields establish integrity only when their expected
  anchors are held independently;
- an outcome root does not authenticate a producer;
- partial Prime conformance remains partial;
- a local exact repair does not authorize a global admission.

Consumers must retain the reported refusal and attestation fields. Do not
relabel an unsigned local outcome as VERIFIED_EXACT or use it to promote code,
policy, or authority.

## Verification source

The host contract test is the executable construction reference:

~~~powershell
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --test host_contract
~~~

For packet formats and profile distinctions, continue with
[digest and canonical serialization](01_digest_and_canonical_serialization.md). The earlier target `ref_wire_master_canonicalization_and_codec_specification.md` is not present.
