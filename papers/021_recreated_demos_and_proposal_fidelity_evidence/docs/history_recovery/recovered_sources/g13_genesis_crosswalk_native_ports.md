# G13: Genesis Crosswalk: Binding the Three Native Ports

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T1.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to implement the
> native actions `raw_file_sha256`, `audit_genesis_anchors` and `audit_forbidden_patterns` in
> Rust, so that the genesis crosswalk demo reports findings against the sealed tag instead of
> refusing, for under $0.10.

## 2. Why This Task

This is the one genesis challenge that changes the_symbol_game and leaves 19L57G1 untouched.

`demo_genesis_crosswalk` always refuses `NO_NATIVE_PORT`. The actions listed in `REQUIRED_NATIVE_ACTIONS` in `pfp/domain/mssn_sn_demos/demo_genesis_crosswalk/checker.py` do not exist. The digest helpers that do exist, `ExactDigestPort.sha256` and `domain_digest`, are not raw file pins, and nothing audits anchors or wording.

Estate rules put checkers in Rust; Python only binds names. The task is a small T1 warm-up. It exercises Rust synthesis in the Symbol Game, OEWAS (Engine Workflows, Agents, Skills) demo plumbing, and OEEIS (Engine Epistemic Immune System) refusal of a receipt that would read as a verdict.

## 3. Formal Problem and Bounds

**Fixture.** `projects/mssn_sn_symgam/demos/demo_genesis_crosswalk/inputs/demo_genesis_crosswalk.json` has: kind `genesis`; `source_sha256` `f41255db402a73a8a20cd6c68aa0c650fee619fe8d790e8bb493159ab930e538`, the SHA-256 of the raw bytes of `pfp/infrastructure/adapters/mssn_research/genesis_crosswalk.md` in this worktree; `stage_pin` `e28f49abea3310ae4a9dc3d17ecb9ab55b267938`, a the_symbol_game commit that pins `stages.tsv`; 15 forbidden-wording regular expressions.

The compendium has 101 GEN sections and 22 "Strongest sealed witness" lines.

**Actions.** Dispatch goes through `engine/crates_rs/core_symbol_game/src/invoke.rs`, reached via `RustSymbolGameHost` in `pfp/ffi.py`.

- `raw_file_sha256` takes `{root_id, relative_path}` and returns `{sha256, byte_count}` over the exact bytes, with no newline or BOM normalisation. It gives a typed refusal for a path that escapes the root, a symbolic link, a directory, or a missing file.
- `audit_genesis_anchors` takes the compendium bytes and an anchor manifest. It extracts the backticked anchors on "Strongest sealed witness" lines, using a declared grammar, and classifies each one:
  - present in 19L57G1 at `3100c4e`;
  - present only at HEAD `b55fc96a`;
  - unresolved.

  The operator generates the manifest from the two pins. It holds names, paths and Git blob ids only, never sealed text. Anchors take several forms: Lean `Module.name`, bare names, Python `module.function`, paper paths, and research-tree names. Research trees are post-tag by construction.
- `audit_forbidden_patterns` takes `{text, patterns}` and returns every hit as `(pattern, line, column)`. The scan is plain text, and code spans are included. The regex dialect is declared, and its `\b` behaviour is compared with Python `re` on all 15 patterns.

**Receipt.** A findings receipt under a new schema name chosen in the PR. It must never carry `status: PASS` or `CHECKED`, `total_papers_verified: 101`, or `claim_hygiene_clean: true`; `is_forbidden_success_receipt` rejects each of them. Its scope string stays "integrity, anchors and wording; not mathematical verification".

## 4. Deliverable and Output Contract

A pull request to the_symbol_game containing: the Rust actions, with unit tests; the host binding; the updated `checker.py` and `use_cases/mssn_sn_demos/demo_genesis_crosswalk/run.py`; the pinned manifest; updated tests in `pfp/tests/mssn_sn_demos/test_demo_genesis_crosswalk.py`.

When an action is unbound, the refusal path stays: the demo still refuses `NO_NATIVE_PORT`. The registry row goes through U18. Nothing is copied from the sealed paths of 19L57G1.

`solve(case)` takes `{bytes, patterns, manifest}` and returns: `SOLVED` with `{digest_match, anchors: {at_tag, head_only, unresolved}, hits}`; `OUT_OF_SCOPE` for a non-genesis fixture, refused as `INVALID_DEMO_INPUT`; `UNKNOWN` with `NATIVE_BINARY_MISSING`.

## 5. Participant Packet

`TASK.md` gives the three action contracts, the anchor grammar, the manifest schema and the receipt constraints.

Public examples, each with exact input and output JSON: the unmodified compendium; a one-line compendium with one `\bsimply\b` hit; a digest request for a missing file, which returns a typed refusal.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

**Held-out variants.** One changed byte, which gives a digest mismatch; a CRLF conversion, whose raw digest must differ; a UTF-8 BOM prefix; an anchor renamed so that it is absent at both pins; an anchor present only at HEAD, for example `mu2_unique_F` in `19L57G1:lean4/Derivation/MinimalityF.lean`; a forbidden word inside a code span; the near-miss `improves` against `\bproves\b`; `../` inside `relative_path`.

**Poisoned case.** A manifest entry that labels a HEAD-only name as present at the tag. The audit must go by blob ids, not labels, and the judge checks the ids against the pins.

**Second checker.** Python `hashlib` over raw bytes, `re` over the text, and `git ls-tree` at both pins.

**Mutation suite.** The judge must reject hashing after normalisation, anchors extracted only from `Derivation.` prefixes, and a receipt that carries `PASS`.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is a shell baseline: `sha256sum`, `grep -P`, and `git grep` at both pins. It produces the correct findings, so it serves as the oracle for findings. It does not satisfy the native-port contract, so E scores 0 on binding by definition.

The comparison is cost to a verified native implementation. At this tier, A and B are expected to tie.

## 8. Budget, Models and Provenance

The ceiling is $0.10 per arm. Candidate models: `qwen/qwen-2.5-7b-instruct`; `meta-llama/llama-3.1-8b-instruct`; Qwen3 8B; Qwen3 14B.

Cargo builds run with `-j 1` from `engine/crates_rs` and count as tool cost. Candidate code runs in the sandbox.

## 9. Pass Gates and Statistics

**Capability gate.** All of the following must hold: every held-out variant is handled correctly, and the second checker agrees; the refusal path is preserved; the targeted demo and crate tests pass, run in small batches; no forbidden-success receipt is produced.

**Differentiation test.** Exact McNemar over the held-out variants, with 3 seeds per arm.

**Primary metric.** Cost per verified binding.

## 10. Interpretation

- **A pass.** The demo can report integrity, anchor and wording findings against `3100c4e`. A forbidden-word hit is a finding, not a failure of the compendium.
- **Many HEAD-only anchors.** The compendium cites post-tag material as sealed, which is worth a correction note.
- **Unresolved anchors.** These are citations to repair.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none. These are recommended:

- **Danger gate.** Signal 1 is a verdict epitope (`PASS`, `CHECKED`, "verified"). Signal 2 is a receipt field that `is_forbidden_success_receipt` rejects.
- **Thymus.** The self panel is the demo's existing refusal tests, so that `NO_NATIVE_PORT` receipts are not flagged.
- **Treg.** Damps repeated wording flags on quoted negatives.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C E I D T`, with `M` on a verdict-shaped receipt: **C** exposes the fixture and the contracts; **E** writes each action; **I** binds the actions into the demo; **D** means fewer failing variants; **T** freezes the result.

**Logged.** Failing variants, refusal-path regressions, and Cargo errors.

**Operands to mine.** Hash raw bytes, never normalised text; classify anchors by pin, using blob ids rather than labels; a findings receipt is not a verdict.

## 13. Estate Reuse and Prerequisites

**the_symbol_game.** `projects/mssn_sn_symgam/demos/demo_genesis_crosswalk`; `pfp/domain/mssn_sn_demos/demo_genesis_crosswalk/checker.py`; `pfp/use_cases/mssn_sn_demos/demo_genesis_crosswalk/run.py`; `pfp/infrastructure/adapters/mssn_research/genesis_crosswalk.md`, and `fixtures/demo_genesis_crosswalk.json` in the same directory; `engine/crates_rs/core_symbol_game`, which already depends on `sha2`; `pfp/ffi.py`; `engine/crates_rs/core_ooutwire_primitives` (`hash.rs`); the raw-file hashing precedent in `governance/contracts/contracts_operating_system/registry.py`.

**19L57G1.** Read-only. Used for the manifest, at `3100c4e` and `b55fc96a`, by name, path and blob id only.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row: [U18](../../upgrades/u18_demo_registry_unification.md).

## 14. Claim Hygiene

- **Supports:** whether the compendium's bytes match their pin; whether each cited anchor resolves at `3100c4e`, only at HEAD, or not at all; and the listed wording hits.
- **Does not support:**
  - any mathematical verification of the crosswalk;
  - identifying MSS-N rows with 19L57G1 results. These remain fenced, post-hoc comparisons in repository-native terms, with no imported classification grid;
  - any authority from a clean audit.
- **Narrowest defensible claim:** three native actions exist, they report findings against the sealed tag, and once they are bound the demo no longer refuses.
- **Next test:** the same anchor audit against H3V7N5QF at `1681998`, for the compendium's H3V7N5QF citations.
