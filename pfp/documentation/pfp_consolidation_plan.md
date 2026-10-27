# PFP consolidation and native refactoring

AuthorityEffect: None.

The final application owner is `pfp`. Move the existing educational
PFP implementation into the corresponding Symbol Game layers, refactor both
native crates, verify the integrated implementation, then rename the combined
Python owner. The final state has one implementation and no compatibility app,
re-export shim, copied runtime or retired package left on the active import path.
The `symbol-game` and `level-engine` commands remain available alongside `pfp`.

The delivery target is a working, cost-effective, repeatable PFP demonstration
with collated results and a clear usage guide. The fixed pilot grid and generator
are retired; executing every experimental combination is not a completion gate.
Extend the procedure for a concrete improvement question or to discover new LLM
and system failure modes, then apply useful findings to existing guidance or code.
PFP remains work in progress; observed needs determine further engineering.

Filesystem helpers now live in `infrastructure`: `contract_loading` owns gate,
schema and mode catalog reads; `normal_form_loading` owns contract-file audits;
`type_register` owns file resolution and the AST census; `model_loading.load_yaml_model`
loads a file and validates the same domain model. The retired PFP domain helper
import paths are removed. Domain `from_yaml` methods parse YAML text only;
path-taking callers use `load_yaml_model(Model, path)`. Domain mathematics,
validation rules and pure model identities remain unchanged. Task-family tokens
are a generated pure vocabulary checked against the canonical YAML catalog.

## Inventory and move

The pre-move inspection found 659 PFP non-cache files, 331 Python files and 116
test modules; Symbol Game contained 4,692 files, 1,413 Python files and 138 test
modules. These are inventory observations, not implementation completion counts.
Repeat the tracked-file inventory after merged changes before moving files.

| Source | Combined owner before final rename | Required handling |
| --- | --- | --- |
| `education/pfp/domain/` | `symbol_game/domain/` | Preserve every defining module and its validation behavior. |
| `education/pfp/use_cases/` | `symbol_game/use_cases/` | Keep injected ports, stage transitions and typed failures. |
| `education/pfp/controllers/` | `symbol_game/controllers/` | Preserve controller operations; bind canonical infrastructure. |
| `education/pfp/infrastructure/` | `symbol_game/infrastructure/` | Move evaluators, catalogs, generators, YAML, campaign adapters and replay tools together. |
| `education/pfp/frontend/cli.py` | `symbol_game/entrypoints/cli/pfp.py` | Preserve all commands and meaningful process exit codes. |
| `education/pfp/frontend/normal_forms_cli.py` | `symbol_game/entrypoints/cli/pfp_normal_forms.py` | Repair import depth and direct-script root discovery. |
| `education/pfp/frontend/view.py` | `symbol_game/entrypoints/cli/pfp_view.py` | Repair relative imports after increased nesting. |
| PFP `tests/`, `scripts/`, `type_register/`, `_canonical_types/` | Corresponding combined application directories | Preserve test discovery, census roots, generation commands and asset links. |

Only nine equal-relative-path collisions were found, all package `__init__.py`
files: root, controllers, domain, domain/aggregates, domain/contracts,
domain/entities, domain/value_objects, infrastructure and use_cases. Concrete
modules did not collide. Resolve initialization without dropping APIs or adding
eager infrastructure imports to domain. Exported names such as `CandidateId`,
`ReceiptId`, `DomainError` and `ModesManifest` have distinct existing meanings;
migrate callers to defining modules rather than silently replacing one type.
Inspect every existing lazy public export before changing package initializers.

After integration and verification, atomically rename the combined directory to
`pfp`, update active consumers and rerun the verification scope.
The intermediate name is not a second permanent application.

## Behavior that must survive and become executable

- All 74 catalog seeds retain their exact UTF-8 prompt bytes and SHA-256 values.
  The 50 MSS-N entries retain parity with the existing seed catalog. Each seed
  receives an applicable checker for its own task; a generic envelope validator,
  constant answer or candidate-supplied PASS is insufficient.
- Modes and stages change actual prompt preparation, candidate dispatch and
  verification. Requested sequences execute in declared order with typed
  refusal for unsupported coordinates. A declaration or planned matrix row is
  never evidence that its mode or stage ran.
- Each checker distinguishes a correct candidate, an incorrect candidate, absent
  required evidence and unavailable execution. Include mutations that previously
  passed due to defaults or self-attested booleans, and benign controls.
- Exact rational/integer semantics, boundary/coboundary orientation, dual-witness
  requirements, old-image retraction and claim/authority ceilings survive the
  move and native changes. Preserve refusal codes unless an explicit migration
  contract replaces them. Native/Python parity covers both acceptance and refusal.
- Provider dispatch retains one reservation/settlement ledger, exact monetary
  units, identity validation and bounded continuation. Unknown billing remains
  unknown. Saved-response replay makes zero provider calls. A timeout, malformed
  reply, missing native host or unavailable checker cannot become acceptance.
- The frozen matrix keeps IDs, lineage, development/held-out separation, model
  assignments and its reproducible YAML/CSV bytes. Old model IDs require explicit
  preflight refusal or a reviewed new campaign, never silent substitution.

## Native crates

Refactor `core_symbol_game` and `core_symbol_game_runtime` as part of this
integration, not merely as a directory rename. Inventory every exported Rust item,
host command, request/response wire shape, environment override and Python FFI
consumer first. Split responsibilities along existing domain/application/host
boundaries; reuse the existing workspace and ports. Keep the host protocol and
exact arithmetic behavior observable through its existing public commands.

Acceptance requires compiling both crates and dependent workspace consumers,
running their complete unit/integration tests, checking host dispatch and typed
refusals, and demonstrating Python-to-host parity on frozen positive and negative
vectors. Old textbook-RSA fixtures remain arithmetic fixtures. Historical fixture
success never grants production authentication or mathematical authority.

## Active consumers and installation

Update `pyproject.toml` scripts, package discovery, exclusions and package-data
keys. The previous packaging omitted educational PFP entirely; inclusion of
Python modules alone therefore does not prove its YAML/templates ship. Verify an
installed wheel from outside the repository, including prompt/schema/taxonomy,
mode/stage/normal-form assets, web resources, tower resources and Level Engine
package-data boundaries. Preserve the v1 evidence exclusion policy.

Migrate Python imports, dynamic `import_module` strings, subprocess `-m` commands,
documentation source paths and CLI defaults throughout active consumers. These
include education scripts/pilot checkers/replay runners, Adversary runtime/adapters,
operations Level Engine and CI routing, providers, governance, cognitive
operations, immune-system consumers, host command location and `.github` routes.
Update `pytest.ini`, test manifests and changed-file classifiers; preserve the
ability to run the merged PFP tests rather than only the former judge-audit subset.
Update canonical agent guidance and its selected generated host projections.

Audit `Path(__file__).parents[N]`, relative imports and resource lookups explicitly.
Frontend moves increase nesting; application-root renaming changes marker names.
Use the imported application or explicit resource context for package resources,
and repository markers only for operations that actually require a checkout.

## Historical bytes and replay

Do not bulk-rewrite old namespace strings inside source-bound history. Preserve
raw provider outputs, config/source hashes, stage receipts, `source_snapshot/`,
`_legacy_source_archives/`, sealed manifests, vendor pins, Lean build/audit custody,
and existing Adversary receipts. The Level Engine v1 tree and v2 historical
certificates/manifests contain provenance package names; those are not active
import instructions and their byte hashes must not change.

Current resource locators, including Level Engine `installed_context()`, use the
new owner. Historical v1 still resolves the recorded full Git revision/path and
validates recorded bytes; absent objects return `HISTORICAL_BYTES_UNAVAILABLE`.
No cross-version fallback or manufactured replacement digest is permitted.

The challenge campaign snapshot replayer invokes a legacy module inside a clean
detached historical checkout. Keep historical command selection tied to that
checkout/revision while routing new runs through `pfp`. Test both
paths. Dossier `prepare.py` Git-show locations remain historical locators, and
older checker drift continues to refuse incompatible replay rather than being
repinned. Historical receipts need not claim the new implementation was executed.

## Completion checklist

1. Inventory every tracked source/asset and public API with a destination;
   account for nine initializer collisions and every active consumer.
2. Merge all PFP layers and assets, implement all remaining seed checkers and
   mode/stage execution, and preserve the existing Symbol Game/Level Engine APIs.
3. Complete both Rust crate refactorings and migrate their workspace consumers.
4. Run the merged PFP and Symbol Game suites, native unit/integration suites,
   provider/FFI/custody consumer tests, architecture checks and mutation controls.
   Record existing failures separately; never weaken a gate to obtain a green run.
5. Run bounded live checks through the real provider path, retain raw responses,
   costs and checker outcomes, then replay those runs offline with zero dispatch.
6. Rename the integrated Python owner to `pfp`; remove old active
   roots and imports, update scripts/resources/test routes and generated guidance.
7. Recheck imports, all affected tests, host parity and an installed wheel from
   outside the checkout; verify preserved history by byte hashes and Git replay.
8. Open the separate implementation PR with exact scope, commands, outcomes and
   unresolved findings. The goal remains open until every requirement above has
   direct current evidence; inventory and planning do not substitute for delivery.

## Bounded implementation handoff — 2026-10-12

The user stopped further pilot tuning and requested collation and delivery.
The full pilot grid was not run and has now been deleted with its generator.
Remaining errors are follow-up work, not grounds for extending this delivery
into another tuning campaign. Targeted failure discovery remains a secondary
goal when it produces useful antibodies, patterns or implementation repairs.

The combined active owner is `pfp`; the former educational PFP
and Symbol Game runtime roots have been removed. Its public commands are
`pfp`, `symbol-game` and `level-engine`. Both native crates now separate
requests, exact operations, host execution, parsing and certificate checking
within their existing owners. No new runtime framework or concurrency was added.

| Observation | Result and scope |
| --- | --- |
| Real OpenRouter run | `DEMO_07`, mode 2, stages 1–8, model `qwen/qwen3.8-flash`: all requested stages passed; terminal `Verified`; 7 provider calls; reported cost 6,544 microusd ($0.006544). |
| Offline replay of that capture | Same eight-stage result; zero provider calls. The displayed 6,544 microusd is the original capture's cost, not new spending. |
| Tampered capture control | A changed stage-4 raw provider response was refused, CLI exit 2, zero provider calls. |
| Earlier bounded attempts | Pricing-profile refusals, transport ambiguity/HTTP 429 and a wrong candidate identity were observed. Known unsuccessful Qwen attempt cost: 4,193 microusd. Unknown billing stays unknown; successful-run cost is not the campaign's total cost. |
| Applied live repairs | Model-visible stage schemas bind the selected candidate ID, including negative controls; safe typed HTTP/transport codes remain diagnosable. Neither change relaxes host acceptance. |
| Seed and mode implementation | 74 seed dispatch paths. Modes 3, 6 and 15 explicitly require unavailable model/session hooks; no success is fabricated. |
| Focused migration repairs | 62 packet-contract/runtime-replay cases passed; 86 selected seed/resource cases passed across narrow runs. These totals overlap other validation and are not summed. |
| Installed wheel | Built and installed outside the checkout. All 12,651 intended package/code/asset paths present; 24/27 probes successful, including the three CLI helps, eight stage assets, twenty mode assets, seed/NF catalogs and finite positive/negative controls. |
| Installed capability limits | Two additional the city imports require canonical Rust DDC source context. Generic offline fixtures cannot supply a mathematical seed witness. These are explicit limits, not claims of standalone native execution. |
| Broad Python diagnostic | JUnit recorded 4,970 tests, 660 failures, 126 errors and 7 skips. Native-host/vendor files and pure Python dependencies disappeared during the attempt. This is not a clean-suite result; it also exposed real moved-path bugs subsequently repaired. |
| Native validation | The two refactored crates' complete suites passed before the final Python owner rename. A later four-crate rerun remained in dependency compilation and was stopped when the user ended further tuning; no final-build PASS is claimed for that attempt. |
| Preserved history | Historical Git blobs remain unchanged across the owner move, including vendor pins, recorded registry bytes, receipts and v1/v2 evidence. Tests that wrote into tracked evidence were followed by restoring the original bytes. |

Corrections include merged-layer import cycles, moved CLI/resource roots,
package-data omissions, current contract module bindings, missing-source typed
refusals, and historical replay refusing absent runtime sources rather than
crashing. The Reach reader recognizes only the exact legacy/current owner
identities while retaining the recorded registry digest, source commit, path
and checker hash; it does not rewrite those historical records.

The new eleven Reach resource controls remain unexecuted at the user's stop.
The combined attempt could not collect an existing vendor-dependent Reach
module. Other retained findings include obsolete frozen type-census assumptions,
an already-unsorted taxonomy assertion, an already-missing pilot README section,
and the inherited `use_cases/modes.py` infrastructure dependency. Do not repin
history or weaken assertions to label these green. Reproduce only the specific
failure needed for the next concrete repair.

The scoped Adversary learning result is applied code: prompt constraints match the
validator, unavailable sources remain unavailable, and replay cannot silently
cross changed source identities. No new receipt garden or framework is needed.

The temporary shared Adversary exchange state disappeared before final observation
submission. Scoped IDE learning was applied in the existing code and summarized
above; a final backend completion transition is not claimed. This does not change
the observed live/replay results or the preservation of tracked historical blobs.
