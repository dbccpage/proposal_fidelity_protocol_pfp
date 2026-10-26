# Python to Rust migration

AuthorityEffect: None.

The native executable now serves MCP directly: `omega_symbol_game --mcp`.
Python is unnecessary for this transport and its native action execution.
This change also moves exact cochain scoring, ranking, signed transport, and
the production Q40 solve/check path and swarm reply controls to native owners.
The remaining Python estate includes substantial orchestration and verification
contracts. Its migration remains open; an existing Rust filename establishes
ownership, not behavioral equivalence.

## Native driver prompt-policy binding

The production `TurnDriverController.next_prompt()` route now preserves the
supplied lowercase SHA-256 regime pin and obtains a canonical native prompt ID
from the complete typed state, effective normalized policy and rendered-body
digest/count. Policy set order and duplicates normalize; empty kill/reply lists
use the existing defaults. Raw state text remains identity-bearing, while each
rendered text fragment normalizes CRLF/bare CR before joining LF separators.
The identity domain is `omega.symbol-game.turn-driver.prompt-identity.v1`.

Malformed policies and unknown state/policy fields refuse. CLI `invoke` also
rejects duplicate JSON keys before decoding. CLI and MCP retain parsed payload
types, preventing serde private-number objects from masquerading as integers,
while preserving real arbitrary-precision values and existing request limits.
The controller propagates native prompt refusals with the complete
native outcome in refusal details. Labels are limited to 256 UTF-8 bytes and
64 raw entries per policy list; declared `max_tokens` is in `1..=1,048,576`.
This binds configuration and does not enforce provider billing or generation.

The source review and targeted checks (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/woland/native_driver_prompt_binding_20261013/README.md`; digestion `_ic/woland/native_driver_prompt_binding_20261013_digestion.md`)
retain earlier pins and the completed 126-row reconciliation at its original Git
snapshot. Native Rust callers now supply the explicit regime pin to
`compile_prompt_artifact` and handle `Result` from `driver::next_prompt`.
The legacy native artifact shape and residual vocabulary remain; this closes
driver context binding, not full Python artifact parity, unseen regime-file
verification, mathematical step acceptance or the complete turn lifecycle.

## Python prompt-artifact contract

The native `prompt_artifact` action owns canonical compilation, structured body
rendering, wire admission and the existing reply-field presence check. Its
`compile`, `render`, `validate` and `validate_reply` operations use
`omega_symbol_game_runtime::prompt_artifact`. Canonical artifacts carry every
Python field, including `family` and obstruction `prior_report_digests`.
Layer A uses the published tagged `omega-canonical-v1` payload and
length-delimited `omega.symbol-game.prompt-artifact-payload.v1` digest. Layer B
binds the exact body bytes and byte count. Regime IDs hash normalized regime
bytes; arbitrary byte inputs and `normalize_body=false` remain supported.

Compilation sorts its declared sets and obstruction/demand records; admission
checks wire ordering without repairing it. Nullable fields must be present.
Nested Python value-object normalization, residual/dual-witness constraints,
resource limits and arbitrary-precision integer magnitudes are retained. Float
magnitudes remain outside the canonical identity algebra, though the renderer
can display them. The native compiler rejects explicit identity overrides.
Python's legacy application alias remains outside canonical wire admission.

The existing `validate_reply_residual` action now requires canonical admission
before checking reply fields. Presence is a substring test for compatibility;
it is not mathematical verification or a typed reply parser. The legacy driver
context artifact remains a separate profile pending turn-lifecycle migration.
Native compile/render/validation is available through the existing PFP/OEOS
process seam; Python persistence, payload construction and elimination receipts
remain separate migration work.

Both native transports and OEOS permit a 12 MiB complete runtime envelope only
for the two artifact actions, supporting a 1 MiB body encoded as integer bytes.
Other runtime actions retain their previous limits. MCP keeps its 1 MiB limit
for unrelated methods and permits the artifact envelope plus 4 KiB framing.
All finite transport ceilings remain distinct from Python's unbounded regime
input domain. The default strict JSON parser retains its 4 MiB ceiling.

Python's application compiler and renderer now delegate to the domain versions,
repairing typed-ID sorting/join failures. Constructor checks reject nonboolean
dual flags and invalid reply labels before emitting wire. Rendering uses the
residual value `Open` rather than enum implementation text. Stored artifacts,
prompt versions and historical receipts are unchanged. The
[parity evidence](../../../_ic/woland/python_prompt_artifact_parity_20261013/README.md)
records exact sources, independent review and targeted checks.

## Optional agent SDK integration

Google's framework is the Agent Development Kit (ADK). Its
[runner-wide plugins](https://adk.dev/plugins/) provide model/tool lifecycle
hooks. An optional Woland adapter is worth a bounded evaluation when a concrete
session, tool-integration or deployment need justifies it. No SDK dependency is
added by this migration.

Keep PFP compilation/admission, replay custody and the durable run-wide budget
ledger below the SDK adapter. Every model dispatch, retry and subagent call must
reserve cost through that boundary; callbacks alone cannot establish a hard
$0.05 cap. Compare one existing task through the adapter with its current route
using the same cheap model, seed, checker and total cap. Measure first-shot
acceptance, actual cost and replay equivalence before expanding adoption. New
mathematics and model-performance improvements require their own verified
evidence; adopting an SDK establishes neither.

## Current inventory and retained review

The source-binding reconciliation at
`20d9d41c684f6a88ff856b8434dfe97202a8b5fe` resolves 126 stale raw-byte
commitments in the 14,390-path map. For 124 rows, the previous digest matches
an exact CRLF projection of the current LF Git bytes; this relation does not
establish that a historical CRLF Git blob exists. Two evidence-reader rows
match genuine historical mixed-line-ending Git blobs. The
reconciliation receipt (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/woland/rust_map_reconciliation_20261013/README.md`; digestion `_ic/woland/rust_map_reconciliation_20261013_digestion.md`)
preserves every previous row and distinguishes those byte relations from an
intentional resolver repair: Windows device names, trailing-dot/space aliases
and embedded NUL now receive typed path refusals before resource or Git I/O.

Only current source hashes, applicable byte sizes and current test declarations
are refreshed, including five inherited declaration-list omissions or old names
whose source hashes were already correct. Baseline pins, introduction records, native targets and parity
statuses remain literal. The gate still compares raw bytes and refuses even
newline-only drift until explicitly reviewed. This reconciliation establishes
current accounting and the tested resolver behavior; native migration remains
open. Earlier slice inventories and refusals below retain their historical scope.

The Education application and pilot directories are now retired. Remaining
pilots live under `omega_engine_woland/tests/pilots`; PFP remains the application
owner. The relocation inventory (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/woland/pilot_owner_migration_20261013/README.md`; digestion `_ic/woland/pilot_owner_migration_20261013_digestion.md`)
binds all 6,798 original pilot files to the fixed pre-move revision and records
current import/documentation edits separately. Prompt profile `1.0.4` pins the
new defining source locations without changing published `1.0.0`–`1.0.3` bytes.
That map refresh covered the slice's current bindings and five new prompt
resources only. Its inherited stale rows remain a historical observation in
`current_review.education_retirement`; the later reconciliation above records
their disposition without rewriting that snapshot. This ownership cleanup does
not establish Rust parity or complete the wider native migration.

The pilot-relocation reconciliation based on
`81ac733a24195aa48a77a68df84593d7250e45f6` accounts for **14,378 current paths**.
It adds 8,113 missing rows: 1,025 Python files, 5,160 JSON files, 1,763 YAML
files, 150 Markdown files and 15 JSONL files. Each new row binds its current
bytes and its exact pre-move Git source path/blob/SHA-256. Compared with the
original relocation, 7,921 remain byte-identical, 101 changed in the move only,
and 91 changed afterward (11 of those also changed in the move). Thus 112
changed in the move in total. This inventory does not endorse those edits as
semantic equivalence or reissue historical results.

The new `pilot_relocation_inventory` partition records path and byte accounting;
its protocols have not received a fresh semantic or native-parity review.
Nine existing rows also receive current hashes after inspecting their inherited
owner/path and moved-fixture changes. Original baseline fields, prior-map
recovery and immutable source-introduction records remain intact. No corpus,
prompt, case, historical result or receipt is rewritten by this reconciliation.

The complete map is approximately 15 MB. Its reader now has a bounded 16 MiB
allowance, with the original 1 MiB per-source bound and all path, digest,
coverage and native-owner checks retained. The sections below describe earlier
inventories at their respective revisions rather than the current path count.

[file_map.json](file_map.json) accounts for the current Git-tracked PFP estate,
including source, schemas, tests, retained evidence and generated fixtures.
The 2026-10-13 reconciliation starts at `e09492620a7219b76be114c10c0c2729c6283700`:
5,533 current paths replace 4,821 prior rows, retiring 178 absent paths and
adding 890 previously unmapped paths. The previous map remains recoverable by
its exact Git revision/path/SHA-256 in `current_review.previous_map`; no old map,
fixture, prompt profile or receipt was rewritten to fit the new inventory.

The subsequent C051-C055 relocation at `5f722a745b33bdc5e3baf15452820f5b206cbfb0`
adds 719 paths, bringing current coverage to 6,252. The supplemental inventory
records 65 Python syntax/import inspections, 639 JSON parses and 15 Markdown
text inventories. Git records 706 identical relocations, eight edited relocations
and five new test harnesses. That initial inventory was structural only and
found `omega_engine_projects` references in 22 Python files. The subsequent
C051-C055 repair updates active imports, script root discovery and current
command examples. Focused loading and public-example checks cover these entry
points; they do not certify live models, original protocols or native parity.
Judge/solver implementations, fixture JSON and historical Markdown stay unchanged.
The map keeps the original relocation fields and the initial open-reference count
as historical observations; `current_review.c051_c055_import_repair` records the
current repair separately. A new regression file brings coverage to 6,253 paths.

The shared formal-math and synthesis matrix helpers now live in PFP
`infrastructure/formal_matrix.py` and `infrastructure/synthesis_matrix.py`.
Both moves preserve every source byte and public API; active helper callers use
the current owner. The existing migration manifest binds their pre-move source
and actual introduction commits, while frozen snapshots retain their old paths.
Two runtime modules and a focused ownership regression bring map coverage to
6,256 paths. C059 also receives its missing CLI `sys` import and a current command.
Original task/judge data, model lists and historical results are unchanged.
Fresh-process import/help checks are not installed-wheel or live-run evidence;
legacy Education task imports and old transport tests remain separate residuals.

The next current-consumer slice adds an explicit bounded CLI to the existing
formal helper and repairs C043-C050/C056-C058 imports at their Education owners.
It retains original direct-call semantics and records deliberate CLI selections
in the existing run record. Two focused controls bring coverage to 6,258 paths.
The original helper introduction hashes above stay immutable; the current map
hash describes this later canonical implementation. See the
[usage examples](../../../omega_engine_education/documentation/004_oepfp/docs/18_woland_original_challenge_play.md)
for selected commands and the distinction from original full-profile protocols.

C041/C042 experiment consumers now reuse the same accounted PFP gateway across
methods, cases and retraction rounds. Their CLIs require explicit model, method
and spend/call/output bounds; qualified task imports let both judges coexist.
Malformed replies retain their raw evidence, and unknown cost stops the sweep
without becoming zero in C041 reports. Two focused test files bring the current
map to 6,260 paths. Original formatters and mathematical checker bodies remain;
historical commitments, task data and recorded results are not regenerated.
These experimental prompt methods do not implement neural attention/logit hooks.
Installed M1-E, original full protocols and native parity remain open.

Merged provider retirement at `8d43a0f9bbc57b327b884aa1a90a9fdf8052972f`
also changed current PFP provider imports and four pilot fixture path references.
Those inherited source diffs were reviewed and their current map rows refreshed.
Historical map fields and relocation-introduction digests retain their original
meaning; this source refresh does not reissue provider or installed-wheel tests.

Four custody source/test files changed on merged main after the preceding map.
Their current definitions and byte commitments are refreshed after source review;
that metadata refresh does not claim new execution of their custody controls.

In the preceding 5,533-path review, every changed/new Python source received
full AST inspection of imports,
declarations and call sites. Exact prior source blobs were recovered for 245
changed Python files; 175 have identical ASTs after ownership-prefix
normalization. This is source review, not an execution or native parity result.
Structured assets were parsed where valid; the malformed retained
`tests/normal_forms/json/receipt_tranche3_advanced_relational_nfs.json` remains
byte-identical and is explicitly marked unparsed historical data. Its assertions
are not validation evidence. Tests remain controls awaiting their named execution.

Relevant native successors were checked in source, including split stabilizer
modules, cohomology admission, convex kernels and the exact L1 dispatch. Corrected
paths identify candidate/source owners only. Changed behavior without fresh parity
is marked unestablished; the thimble remains an archived research metaphor and
the distribution certificate's absent upstream Lean obligations remain open.
No unrelated Rust file substitutes for a missing counterpart.

The original six-part review of 4,803 starting files remains historical provenance
in the baseline fields and previous Git map. Its earlier native/check results
are retained below and in [validation.md](validation.md), without reissuing them
for the current tree. Current source hashes bind the reviewed current bytes;
baseline hashes retain their distinct original meaning.

The former symbol manifest contained invented targets such as
`omega_symbol_game_runtime::__init__::__getattr__`. Its replacement
[migration_manifest.json](../../migration_manifest.json) points to this
file-based map and explicitly leaves unsupported migration claims open.

After changing a source, review its row and update the digest deliberately.
Persist edited text using repository LF bytes before recording reviewed hashes;
staging normalization must not invalidate the current map. Do not normalize
unrelated or historical artifacts to satisfy this gate.
The coverage gate detects unstaged tracked modifications and staged additions:

```bash
python -m omega_engine_pfp.infrastructure.migration_fitness
```

The gate verifies complete Git coverage, immutable reviewed source bytes,
duplicate-key rejection, safe paths, and existing native owners. A passing gate
does not establish mathematical or wire parity.

Recover the preceding map without modifying this checkout:

```bash
git show e09492620a7219b76be114c10c0c2729c6283700:omega_engine_pfp/documentation/rust_migration/file_map.json
```

Its digest is recorded in `current_review.previous_map`. A missing Git object
does not authorize substituting the current map or rewriting historical claims.

## Build and run the standalone native server

```bash
cargo build --locked -j 1 --manifest-path omega_engine/crates_rs/Cargo.toml \
  -p omega_symbol_game --bin omega_symbol_game
omega_engine/crates_rs/target/debug/omega_symbol_game --describe-runtime
omega_engine/crates_rs/target/debug/omega_symbol_game --mcp
```

For a distributable optimized executable, use the same build command with
`--release` and the executable under `target/release`. Validation here uses
the debug executable. Normal operating-system libraries remain prerequisites.
No Python interpreter, Python packages, repository working directory, or
run-time model provider is required for MCP action execution.

Configure a plugin or MCP client with the absolute path to the built binary:

```json
{
  "mcpServers": {
    "symbol-game": {
      "command": "/absolute/path/to/omega_symbol_game",
      "args": ["--mcp"]
    }
  }
}
```

The server supports newline-delimited JSON-RPC 2.0 initialization, initialized
notifications, ping, tools/list, and tools/call. It negotiates supported MCP
versions 2025-06-18, 2025-03-26, and 2024-11-05. Tool names derive from the native
action registry. The filesystem actions `run_folder_seal` and
`run_folder_verify` retain their CLI contracts and are excluded from MCP.
Runtime tools accept `{"payload": ...}`; `omega_prime_host` accepts
`{"request": ...}`. Native outcomes are retained in structuredContent and
text content, with isError reflecting native dispatch refusal. Native solver
or checker verdicts remain in the complete result, including UNKNOWN/FAIL
values returned by successful dispatch. AuthorityEffect remains None.

Ordinary messages retain a one-MiB framing limit and embedded runtime requests
retain their 65,536-byte ceiling. The architecture DAG has its existing 266,240-byte
runtime envelope; the two canonical artifact actions use 12 MiB runtime and
12 MiB plus 4 KiB MCP envelopes. Frames beyond the largest bounded reader close
the session without draining an unbounded tail. Duplicate keys, invalid IDs, uninitialized tool calls, unknown
tools, and undeclared tool arguments refuse. Computation and result limits
remain each owner's contract; clients should configure their process timeout.
Proposal-ranking and turn-driver actions describe candidate claims and ordering.
Their scores or accepted declared metrics do not grant exact certification.

## Migration sequence and exit gates

| Stage | Native owner | Required work and retirement condition |
| --- | --- | --- |
| Exact kernels and wire operations | `omega_linear_algebra`, `omega_homology`, `omega_holonomy`, `omega_functional`, `omega_solvers`, `omega_symbol_game` | Use direct native actions. Retire Python algorithms only after positive, refusal, exact-rational and tampering controls run through the native seam. Scoring, signed transport and Q40 are implemented here. |
| Unified service transport | `omega_symbol_game::mcp` and `invoke` | Implemented stdio MCP. Keep Python CLI/API as presentation over explicit ports. The distinct symgam classifier contract uses the canonical OEOS transport without binary fallback. |
| Prompt/turn semantics | `omega_symbol_game_runtime::prompt_artifact`, `prompt_turn`, `driver`, `frontier`, `turn_records` | Canonical Python artifact compilation, rendering and strict wire/body admission now have a native owner. Migrate the separate legacy driver context profile and remaining turn lifecycle. Replay actual mathematics before terminal routing; declared-metric step bookkeeping cannot replace the exact evaluator. |
| Code-change lifecycle | `omega_symbol_game_runtime::code_change`, `diff_parser` | Preserve task and rolling run-root anchors, admission and gate receipt formats. Port persistent session and publication lifecycle; test outsider paths, protections, drift and stale anchors before deleting Python orchestration. |
| Replay, events and repositories | `omega_replay`, `omega_trace`, `omega_symbol_game_runtime::event_outbox` | Reconcile Unicode slug semantics, JSONL chain profiles, event transaction and crash behavior. Preserve external receipt anchors and all historical source bytes. |
| Provider execution and custody | `omega_trace`, `omega_policy`, `omega_sandbox`; provider adapters remain in their own bounded context | Native equivalent of both durable dispatch barriers, budget reservation, authenticated artifact custody and explicit transport policy is missing. Complete crash/replay controls before retiring the Python provider gateway. No paid calls were needed for this migration. |
| Evidence/research and installed demos | `omega_symbol_game_runtime::research_evidence`, `omega_symbol_game::epics`, relevant foundation crates | Intake bookkeeping is distinct from independent source-pin, Lean audit and reach-checker replay. Embed or explicitly package pinned demo resources and preserve scenario IDs/receipt schemas. Unconfigured research/CEC evaluation now refuses. |
| Web/API presentation | Native host plus an explicit service adapter | Port HTTP/SSE sessions and cancellation after lifecycle ownership is native. Preserve thin Python presentation until the replacement passes functional routing and state tests. No full native web service is claimed. |

Historical quantum source and its prior rich-reference test are retained
byte-identically under
[retired_quantum_reference](../../tests/fixtures/retired_quantum_reference/README.md).
The compact native certificate contract replaces those aliases in the active
Q40 route. Educational composition roots inject a native StabilizerPort; an unbound
call returns a typed refusal. POSIX process isolation is unavailable and refuses
before launching submitted code, replacing the unrestricted fallback.

See [validation.md](validation.md) for executed evidence and current limitations.
