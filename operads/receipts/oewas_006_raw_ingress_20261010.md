# OEWAS006: refuse duplicate candidate JSON keys at raw ingress

AuthorityEffect: None. Full epic status remains `RESEARCH_HOLD`.

Base and unchanged local HEAD: `ae33a85a60559c727295be055cff79d0c8a20a5c`.
Branch: `codex/oewas-006-raw-ingress`.
Worktree: `C:/Users/a343o/.codex/worktrees/oewas-002-workflow/the_symbol_game`.

## Behavior and scope

`pharmacy::decode_candidate_bytes` previously parsed directly into `serde_json::Value`, allowing later duplicate keys to overwrite earlier authority claims. For example, `{"persona":"admin","persona":"worker"}` could lose its admin marker before detection. The existing public `decode_candidate_bytes` and `ingest_and_detect` boundaries now refuse duplicate decoded keys in every JSON object with the existing `HostIngestError::JsonSyntax` variant. This includes escaped equivalent spellings, nested maps and arrays, duplicate neutral fields, identical duplicate values, and either authority-value order. Uniqueness is per object and uses exact decoded string equality; this is not Unicode normalization or case folding.

A private serde visitor validates the document before the existing Value decoder runs. The separate validation pass leaves arbitrary-precision numeric conversion to the original parser. Huge signed integers, `1e400`, ordinary numbers, scalar roots, and valid unique sibling keys retain their existing behavior. BOM, unsupported encoding, invalid UTF-8, malformed/trailing JSON and nonstandard constants retain their typed failures. Corrected bytes are a fresh candidate; a clean report remains zero-authority evidence, not admission.

Source inspection found the runtime JCS parser depends on this crate, so importing it would create a dependency cycle and impose different numeric/canonical-wire semantics. The EIS ordered-member decoder is private to a different host-check model and RawValue feature. This repair adds no dependency, manifest change, public error variant, second detector, wire schema or receipt verifier.

## Executed TDD and independent controls

The new 17-case public-boundary file was formatted and SHA-256 pinned before changing production source. Actual RED was **10 passed, 7 failed** (exit 101): duplicate candidates returned success. Minimal GREEN was **17 passed** (exit 0). The test bytes are unchanged between RED, GREEN, mutations and final verification. RED production bytes were independently checked against the exact base Git blob.

Ten controls were already GREEN before implementation; they are reuse, not fabricated RED-to-GREEN cycles. Unique escaped/nested persona authority still yields PersonaAuthorityLeak and Refuse through actual ingestion. Neutral persona remains healthy. Literal expected raw, compact sorted-JSON and top-level version-label-stripped semantic digests were generated with .NET SHA256 and independently rechecked with Python hashlib, without calling crate digest helpers. Equivalent encodings preserve equal normalized/semantic identities and distinct raw identities; a version-label change alters normalized identity while preserving semantic identity. These are this crate's existing digest policies, not JCS canonical-wire claims.

Final restored-source verification ran exactly three named integration targets in one crate: **33 tests passed**: raw binding 17, existing authority fuzz 15, frozen pharmacy overlap 1. The overlap test uses checked-in Python projection fixtures; this is not a fresh Python run or complete Python/native parity certification. All existing tracked crate fixtures, the manifest, Cargo.lock and adjacent tests were verified unchanged.

## Production mutations and restoration

Five compiling source mutants were killed by actual public-boundary assertions:

| Mutant | Observed targeted failure |
| --- | --- |
| Duplicate guard bypass preserving set insertion | 7 failed, 10 filtered out |
| Object recursion replaced by IgnoredAny | 1 failed, 16 filtered out |
| Array recursion replaced by IgnoredAny | 1 failed, 16 filtered out |
| Persona-inspection branch bypass | 1 failed, 16 filtered out |
| Raw-byte hash replaced by normalized-byte hash | 1 failed, 16 filtered out |

Each production mutation was applied in place, tested in a fresh Cargo invocation, and restored using exact saved source bytes in `finally`. The mutation manifest binds exact edits, commands, source/test hashes, raw logs and restoration hashes. The initial duplicate-guard mutant used a bare `if false`, making BTreeSet's type uninferrable (E0282). That compile-refusal log is retained separately and explicitly excluded from the five killed mutants. The corrected compiling mutant preserves insertion and bypasses its refusal decision.

## Execution custody and limits

Every Cargo build/test/lint command selected only `core_prompt_civilization`, used the canonical workspace manifest, `--offline --locked`, `-j 1`, and one existing shared target cache. Cargo metadata verified the tracked effective lockfile before compilation; free space exceeded 5 GiB before each Cargo build. No host package was selected. The stable OO5 host at `C:/Users/a343o/source/repos/the_symbol_game/engine/crates_rs/target/debug/core_symbol_game.exe` retained SHA-256 `70e90235311421dda175bddc76b6c848171edb638b36dbef2eab1995422ef4b9` and size 28,354,048 bytes. That existing executable was not rebuilt and does not attest to deployment of this library source repair.

Scoped Clippy exited 0 with unused imports and unused variables denied. It retained two warnings in unchanged `lamarckian.rs` (manual_range_contains) and `society.rs` (manual_div_ceil); this is not a warning-free crate claim. Rustfmt checks on the two authored files and `git diff --check` passed. Raw logs retain captured bytes under the narrow receipt `.gitattributes` rule; new source, tests, JSON and Markdown use LF without BOM. The JSON receipt binds exact commands, versions, source/test/log hashes and unchanged baseline files; its own digest is intentionally external.

This cold adapter allocates a key set and parses twice. No allocation threshold, performance gain, universal panic-freedom or full-workspace validation was measured or claimed. Raw receipt transplantation remains held because no production consumer/schema was selected for that assertion. Allocation-sensitive kernel selection, broader workspace inventory/parity, AST analysis, cryptographic delegation and full epic completion remain unresolved. No live provider, publication, authority promotion or mathematical proof certification occurred.

Reviewer/builder `/root/tdd_review` performed the implementation and recorded these runs; parent `/root` owns independent review and publishing. No Git index, commit, push or PR operation was performed by this agent.
