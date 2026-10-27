# Migration validation

AuthorityEffect: None.

## C029 current independent optimality check (2026-10-14)

Base: `cba7e58c0e7b4c38aef800efe320f635f47b12b1`. The retained C029 second
checker calls the reference matching solver. Current challenge execution now
uses a separate exact GF(2) coset checker alongside the retained primary
matching-certificate judge. It derives a kernel from the supplied parity matrix,
checks syndrome and weight, and searches for a strictly cheaper correction.
Its pruning bound uses only coordinates that remaining kernel vectors cannot
change. A tied optimum is accepted.

A toric L=4 rectangle control exposes the shared-checker failure: the retained
primary accepts a weight-4 correction and positive odd-set duals even though a
weight-3 correction has the same syndrome. The new coset checker finds weight 3
and rejects the heavier candidate. The composed route therefore reports checker
disagreement instead of accepting it. This is a concrete reason to retain the
primary matching-dual repair as open work, not silently recertify old results.

The current checker is included in the existing source bindings. The historical
C029 subtree, including its old checker, task, cases, commitments and receipts,
is unchanged. Current-map rows describe this Python implementation and its
controls; previous baseline hashes and Rust ownership claims stay unchanged.

Validation: 54 focused checks passed, followed by the additional toric
counterexample check. Controls include independent brute-force comparison,
tied minima, original maximum dimensions (kernel 25 and 26), suboptimal
corrections, poisoned matching dependencies, refusal witnesses and replay
source drift. An actual current-IDE `challenge start/submit` of
`c029_base_02_rot_d3_sub1` completed with both judges accepting correction `[0]`
at weight 3; `challenge replay` reproduced acceptance with zero provider calls.
This was one IDE proposal, not a paid or matched model experiment.

This closes the selected current-route dependency on the matching solver for
second-checker optimality. It does not establish the original matching-dual
semantics, Rust judges, decoder-program synthesis or matched hidden campaign.

## Pilot entrypoint parity for numbered stages (2026-10-14)

Base: `cba7e58c0e7b4c38aef800efe320f635f47b12b1`. A direct exercise using the
existing storage, deterministic canonical provider and explicit host fixture
showed that `execute_pilot` stopped at stage 5 but retained an old ACCEPTED
answer. `run_for_pilot` also projected the same prompt under a different seed
field. These were current public-API handoff defects, not observed LLM failures.

Both APIs now use one pilot-to-seed execution path. The updated pilot summary
records current progress and clears prior answer acceptance. The current
pipeline receipt remains the owner of stage responses and the host verdict;
this change does not manufacture an answer evaluation from stage completion.

The worker observed the seed mismatch and stale acceptance before repair; 26
focused checks passed afterward, including the existing canonical-stage controls.
Root repeated the original offline two-API probe: both now send the same seed,
and the stopped summary is NOT_RUN with no extracted answer. The original pilot
retains its prior state. These use explicit fixtures, not a live model or a claim
that the fixture host verifies arbitrary tasks.

Assembly with PR #974 (`6bf844f04db58df2c2564445c32e5bf719c68d58`) exposed a
second reuse path: its declared response field survived a new pipeline, and the
evaluator accepted that old raw reply. The new summary now clears this response
while the original pilot retains it for explicit offline rechecking. PR #975
depends on #974 so the combined handoff is reviewed together, with its original
commit retained in history. No remote PR merge or historical rewrite is implied.
Two failing assembled-path controls preceded the reset; 71 focused integration
checks then passed. Root repeated the full and stopped probes: the original
reply remains on the input, while later evaluation of either new summary stays
NOT_RUN with no extracted answer. Original offline reply checking still works.

Original stage schemas, prompt templates, host checkers and historical files
remain unchanged. The map updates current owners and controls without repinning
earlier source custody. This bounded consumer repair is not provider-performance
evidence, native parity or complete PFP/Adversary migration closure.

## Typed pilot-response handoff (2026-10-14)

Base: `4e62f5f91999f785bd676f08f760a8ecc2b04877` (PR #973's observation-preserving
transitions). A direct probe with the existing `PilotSpec`, `SeedPrompt` and
`PilotResponse` models imported a claimed ACCEPTED status, then evaluation lost
the candidate and returned NOT_RUN. A response naming another pilot was also
converted without refusal. No dynamic test-only observation attribute should
be necessary to connect these public typed APIs.

The handoff now retains the existing response contract in the aggregate, checks
declared identities and re-evaluates actual raw text through the current parser
and original checker. Stored verdicts remain source data. Missing/malformed raw
text cannot fall back to a favorable parsed cache. This builds on the prior
transition repair rather than duplicating it.

The worker observed seven deciding failures before repair; 56 focused checks
then passed, covering the typed handoff, preceding transition controls and
original YAML/schema compatibility. Root repeated the four original public-API
probes: a valid reply is ACCEPTED, another pilot's reply refuses, a raw wrong
answer overrides a favorable cache, and malformed raw text remains MALFORMED.
The retained response preserves its original claims while local status records
the current check.

The current map records changed owners and controls without rewriting earlier
baseline hashes. Existing response/specification YAML schemas, checkers,
scientific sources and historical receipt files remain unchanged. This is an
offline typed handoff, not provenance authentication, historical replay renewal,
native parity or full PFP/Adversary migration closure.

## Pilot transition evidence preservation (2026-10-14)

Base: `cba7e58c0e7b4c38aef800efe320f635f47b12b1`. Direct public-API probes
reproduced three defects: a PASS transition supplied its own evidence string,
an ACCEPTED transition copied the oracle into a missing observation, and a
rejected `evaluate_result` call left the original object ACCEPTED with a wrong
answer. A valid explicit transition already worked and remains supported.

The repair applies the existing evidence-separation rule to the aggregate and
its evaluation consumer. Copy and mutating transitions validate the proposed
state without manufacturing missing observations; rejected changes preserve the
original. The consumer retains checker-produced answers instead of the oracle,
including the existing checkers' valid representation differences. No original
checker or scientific obligation is replaced.

The worker observed seven deciding failures before repair and 26 focused checks
passed afterward. Root repeated the original public transition probes: missing
evidence/answers refuse, an invalid mutating evaluation preserves the original,
and a valid explicit transition succeeds. Direct evaluation-use-case probes
retain determinant and epistemic observations, retain an incorrect answer and
clear a missing answer. The original checker source remains byte-identical.

Current map bindings cover this slice's current Python owners, controls and
validation note. Historical baselines, YAML, original challenge sources and
receipt bytes remain unchanged. Local invariant consistency is not authenticated
execution evidence, native parity or full migration closure.

## Contract verification evidence boundary (2026-10-14)

Base: `cba7e58c0e7b4c38aef800efe320f635f47b12b1`. The public
`pfp verify-contracts` command returned exit 0 and claimed 111 verified contracts
without a candidate or executed semantic checker. The use case assigned
confluence, normal-form and named-invariant success from specification metadata;
its pilot overload also replaced the original response and promoted trial status.

The repair preserves those public entrypoints and typed input/error handling,
but refuses unavailable execution verification. It leaves pilot fields intact.
The existing `pfp_normal_forms audit-contracts` command remains the structural
audit; on the baseline catalog it reported zero findings. A structural audit
is not a substitute for the original transition and normal-form obligations.

The worker observed three deciding failures before repair, then 27 focused
controls passed, including four corrected legacy expectations. Root re-ran the
public commands: semantic verification exits 1 with `HOST_VERIFIER_UNAVAILABLE`;
the explicitly structural audit exits 0 with zero findings. Existing relational
examples also execute successfully. These observations establish refusal and
audit behavior, not broad mathematical correctness or model performance.

Current migration-map hashes cover only the changed current implementation,
controls and this validation note. Historical map baselines, YAML specifications,
scientific task sources and receipts remain unchanged. Semantic contract
execution, native parity and full PFP/Adversary migration remain open.

## Consistency teaching ownership (2026-10-13)

Base: `3c8463026109bd0d80334c99764d3b5814fce233`. The retained Education scene
could not import after `bench/head_to_head` was deleted. Its original task source
at `bc42aa0a7156fcdf2122f0c8c43a52268e9eac84` supplies the generator, exact
potential-propagation judge, prompts and verdict parser recovered into the
existing `tests/demo_004/a_mechanism/consistency_teaching` profile. The
[profile provenance](../../tests/demo_004/a_mechanism/consistency_teaching/README.md)
names the original hashes and limited source adaptations. The unused historical
minimizer and paper-path bootstrap are not imported into current execution.

Shared recording lives in `infrastructure/consistency_teaching.py` and reuses the
existing PFP/accounted turn. Education delegates recording and keeps its renderer.
The original public case arguments, prompt text and verdict semantics remain;
new captures retain the actual checked exchange, use fresh output paths and share
the caller's continuing allowance. Historical JSON/MP4 bytes are unchanged.

The current source map adds only this slice's current owners/controls and updates
this document's binding. Earlier source hashes, relocation records and review
metadata retain their meaning. These Python changes do not establish Rust parity,
model efficacy, whole-migration closure or the original empirical protocol.

## Public runner export ownership (2026-10-13)

Base: `9d8646b27fc9a393944251c6129407e0cd67028e`. Importing the advertised
`pfp.infrastructure.UnifiedPfpDemoRunner` failed because its lazy
mapping still named the absent `demo_runners.unified_runner`. It now resolves
the existing `pilot_runners.pilot_dispatch` class. Public names, lazy loading,
unknown-name `AttributeError`, canonical identity and runner behavior remain.
No forwarding package or duplicate runtime was added.

A structural audit of 545 declared mappings across ten lazy public facades
found this one missing owner before repair and none afterward. This is an
owner-path check, not semantic verification of every exported operation.
The existing `RunDemoUseCase` consumer now imports the public name: its RED
collection failure became one passing selected case. The public installed-probe
control also changed from import failure to a passing check of canonical class
identity and the existing unknown-demo refusal. No original task, judge or
historical artifact changed. Full migration and original protocols remain open.

A fresh wheel built from the declared tracked package sources contains the exact
repaired runtime bytes. Its isolated `python -I` probe ran outside the checkout
with networking blocked, loaded 276 Core modules exclusively from the installed
tree and exercised the public runner/refusal. Wheel SHA-256:
`cae8b5a08ff3e003d84d7db5ec50947043618ad7b901f3418b421ae7e51289e5`.
This is selected public API evidence, not a rerun of all installed probes, live
providers or registered demos. No native build was needed.

## Canonical Python prompt-artifact parity (2026-10-13)

Initial source base: `e62217fdcffef68ce30b15c733fe4b0eb467a368`.
Final integration base: `0acb16d89c8ef0dfd2c8566f436ff4c970836b77`. Incoming demo, graph,
challenge and provider-composition PFP work is preserved. Rust, OEOS and
dependency configuration did not change from the initial base. Earlier driver and reconciliation reviews remain
bound to their immutable landing snapshots.

The native `prompt_artifact` action compiles the full canonical Python wire,
renders structured bodies, validates identity/body bindings and checks the
existing reply-field presence contract. The existing reply action also admits
the canonical artifact before inspection. The Python application wrappers share
the domain compiler and renderer. Repairs cover typed-ID ordering/joining,
prior-digest carrier sorting, enum display text, exact boolean options and
nonempty normalized reply labels.

The first 118-case actual-process differential run had 39 passes and 79 failures,
all from the Python prior-digest `ContentDigest.value` attribute error. Sorting
the digest carrier through its string value repaired the defect; the same
unchanged cases then passed. Tests compare both Python compiler/render entry
points, every wire field, canonical serialized artifacts, exact body bytes,
all regime kinds, nested normalization, large integers, tampering, limits and
CLI/MCP refusals. The real PFP/OEOS seam carries a full 1 MiB byte body.

Independent extra MCP controls compare 300 finite renderer values in one call,
the exact integer `2**1023`, missing root/nested fields, a 4,194,642-byte compile
request and an unrelated oversized ping. These are bounded deterministic
controls, not independent model trials. Rust controls exercise the custom JSON
parser, artifact operations and native CLI/MCP reader behavior; the tagged
identity golden is also checked with ordered JSON maps enabled.

The [evidence folder](../../../_ic/adversary/python_prompt_artifact_parity_20261013/README.md)
contains exact source/executable hashes, prior failures, independent reviews,
the additive source-map delta and final targeted check results. Existing
dependency contract-accounting warnings are not certified by these checks.
No full CI, installed-wheel validation, live provider call or SDK installation
was performed. Canonical artifact parity does not close Python persistence,
payload construction, elimination receipts, the legacy driver profile or
mathematical step acceptance. All wider roadmap requirements remain explicit.

## Current matrix harness integration (2026-10-13)

Base: `9d8646b27fc9a393944251c6129407e0cd67028e`. Current C051-C055/C059
dual harnesses now compose with the existing accounted PFP helper. The old
Adversary matrix adapter is retired before dispatch; it no longer duplicates the
provider ledger or manufactures replacement response bodies. The current C059
matrix test resolves the relocated pilot namespace. Original cases, source
solvers, independent judges and historical provider packets are unchanged.

Controls exercise actual preparation, pre-send reservation, bound synthetic
reply checking, original judges and SQLite answer replay. Fixtures establish
integration and refusal behavior; they do not reproduce a live model. The
current map refresh covers only changed test/documentation paths and retains
original baseline/relocation hashes and prior review records. No native parity,
full sender-inventory closure or original scientific-protocol completion is
inferred from this slice.

Fresh focused checks: the six pilot files passed 12 selected tests; the related
C059 unified-store/replay check passed separately. The 13 Adversary matrix controls
are covered by passing scoped runs: the initial batch passed 12 and exposed one
synthetic model-admission defect; after explicit fixture admission/pricing, the
C059 and pre-dispatch cost controls both passed. C059 exercised all ten original
cases and both judges (eight accepted, two warranted refusals), retaining its
8,192-token direct profile. The CLI control separately recorded its explicit
256-token override. Ruff F and whitespace checks passed. No paid calls, broad
grid, new concurrency work or native rebuild was performed.

## Numbered seed stages through the accounted gateway (2026-10-13)

Base: `0622e7e666877c61ae9330fe55b6a223965e23eb`. Current `pfp run-seed`
uses the existing PFP/accounted gateway with explicit live call, output-token,
financial and HTTP timeout selection. Original numbered prompts, decoding,
stage validators, modes and Stage5 host verification retain their owners.
Current captures use `python-json-sorted-ascii-v1`; old pricing-based captures
and the historical serializer retain their original replay contract.

The adapter's 24 focused synthetic controls passed, including current and old
zero-send replay, tampering, unknown accounting, no-send refusal, original
decoding and invalid Unicode custody. Independent review then reproduced a
malformed-reply replay `KeyError`: the checker had refused before producing an
answer field. The repair reads that field only after successful checking; all
27 adapter controls now pass, including preservation of the original malformed,
wrong-binding and invalid-Unicode refusal and known cost with zero replay sends.
The CLI/gateway batch had 36 passes and
one missing-native-helper failure; that one control passed with the existing
binary explicitly selected. After syncing main, three factory/trace composition
controls passed, preserving both merged tracing support and the new timeout.
Ten inventory, historical-map custody and legacy-preflight controls passed.
No paid calls, full pilot grid or native rebuild were performed.

Interrupted partial captures preserve their unknown outcome and available raw
bytes, but automatic continuation/replay of a partially written capture is not
claimed. Retained hashes are provenance, not authentication or independent
settlement. This slice closes the selected numbered-stage sender; native parity,
final live effectiveness and the full migration remain open.

## Catalog demo PFP boundary (2026-10-13)

Base: `46eb53cdd7826fb3d2ea669526bbb0490deb4903`. Current catalog live
demos now use `complete_pilot_turn` and the existing accounted gateway. The
existing durable transport wraps the raw socket before reply decoding, retaining
the original encrypted dispatch trace. Callers supply explicit model, output,
call and financial limits; invalid bindings and unknown accounting cannot reach
the original host judge or continue to another proposal. Fixture execution and
the original protocol matrix remain separate and unchanged.

The first controls also exposed a stale current implementation-digest lookup:
two provider files had moved to Adversary. The reader now names those exact current
owners and includes the new PFP turn dependencies. It never falls back to retired
files. The catalog, fixture pins, old receipts and source archives are unchanged;
old receipts still require their recorded implementation rather than a repin.

Focused synthetic controls exercise actual PFP bindings, malformed replies,
unknown cost, no second send after refusal, explicit bounds, the composed raw
transport/trace path and the original protocol host. An unparseable model answer
produced `UNPARSED_MODEL_MOVES`, not a certificate. Raw encrypted bytes matched
the synthetic provider response; empty dispatch evidence refused verification.
The three affected demo files passed 19 controls. Three separately selected
current-source controls also passed, checking deterministic hashing, changed
canonical bytes and missing canonical source refusal. Commands used the existing
Python environment and native helper, with writable temporary directories:

```powershell
python -B -m pytest pfp/tests/test_demo_pfp_boundary.py pfp/tests/test_demo_live_receipt.py pfp/tests/test_demo_3_live_receipt.py -q -o addopts="" -p no:cacheprovider
python -B -m pytest pfp/tests/test_demo_registry_closure.py -k implementation -q -o addopts="" -p no:cacheprovider
```

The actual `pfp.entrypoints.cli.symbol_game` module also ran
`demo_3` offline and verified it as `VERIFIED_FIXTURE`. A live invocation without
financial limits refused before output creation. These commands used the current
source on `PYTHONPATH` from an external working directory, not a wheel. Earlier
probes of the package-root parser and the CLI package did not execute a demo;
the usage guide now points to the verified module. Scoped Ruff F checks passed.

The initial map check reported 125 `SOURCE_CHANGED` findings outside the patch.
Direct Git-blob comparison showed that every recorded hash already matched HEAD;
the existing checkout copies differed only by CRLF line endings. Their before
bytes were retained in a verified temporary archive outside the repository, then
the checkout copies were restored from those exact Git blobs. The map check
passed with 14,395 current paths and no findings. No historical source, map pin
or receipt was rewritten in Git. When a custody hash fails, compare the actual
bytes and original Git source before refreshing a map; Git's clean text status
alone does not establish byte equality.

These are local route/custody controls, with no paid provider request. They do
not establish model performance, completion of the original live matrix, native
parity, installed-package coverage or closure of the full migration goal. The
[ownership guide](../../../education/documentation/004_oepfp/docs/17_runtime_ownership_and_replay.md#current-catalog-demos-through-pfp)
gives bounded commands and their limits.

## Native driver prompt-policy binding (2026-10-13)

Base: `681a4dbbd7d7f3d03cd51f06e90e93900ee9cfa6`. The active native driver
ignored the supplied regime pin and used a round-only prompt ID. The retained
baseline probes (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/adversary/native_driver_prompt_binding_20261013/baseline.json`)
bind an existing cached executable; they do not claim a fresh build of that base.
Source review independently identifies the same defect at the fixed revision.
The CLI also accepted duplicate nested policy keys before typed validation.

The repair binds complete typed state, effective normalized policy and normalized
body custody under a driver-specific canonical domain. It preserves the supplied
regime digest, returns typed policy refusals, rejects unknown state/policy fields
and rejects duplicate CLI keys before converting JSON into a typed request.
The Python controller retains native refusal evidence and returns an error.
Actual process probes then exposed a private-number-marker object being
reinterpreted as an integer during a second `Value` deserialization. CLI and
MCP now preserve parsed payload types directly; focused controls require both
marker-object refusal and genuine arbitrary-precision integer preservation.
The finding receipt (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/adversary/native_driver_prompt_binding_20261013/intake_finding.json`)
retains the exact pre-repair binary and request. An inherited intake assertion
also expected the ordinary 64 KiB limit for an unread envelope beyond the
existing larger DAG cap; its exact limit expectation and additional maximum-plus-one
witness now match the fixed-base contract without weakening no-dispatch checks.

Focused native, real-controller and independent golden controls cover repeated
identity, same-round changes, effective defaults, Unicode byte lengths, raw-state
versus LF-body custody, unknown/malformed inputs and bounded process intake.
The first native run found a bare-CR fragment/template-join failure; it is retained
separately from the repaired run. The historical map reconciliation test now
checks its immutable landing rather than rejecting every later reviewed edit.
A separate current-map delta test preserves all preceding rows and pins.

See the scoped validation receipt (`git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/adversary/native_driver_prompt_binding_20261013/README.md`) and the digestion `_ic/adversary/native_driver_prompt_binding_20261013_digestion.md`
for exact commands, source hashes, the built executable and both agent reviews.
No full CI, model call or fresh installed-wheel proof is claimed. The legacy
native artifact is not the full Python artifact wire contract. Declared token
configuration is not billing enforcement; the regime pin is not verification of
unseen definition bytes, and declared step metrics are not mathematical acceptance.

## Current braid tournament (2026-10-13)

Base: `c97c6a23dec5f706312a7c38f0689bb84670f59c`. The current runner derives
the reusable tournament from the frozen Paper 022 deposit without rewriting
its source, CLI, tests, manifests or recorded results. The original source SHA-256
is `1f07ad20268e3eb1829c81f1889f4426c9b7da04892dffe7c08098ed68712dfc`.
Both Atlas Majorana source files remain unchanged and are explicitly packaged
for the current consumer. No old source identity or migration-introduction
commitment is repinned.

Before publication, the slice was rebased onto main
`20d9d41c684f6a88ff856b8434dfe97202a8b5fe`, retaining that revision's later
pilot-owner relocation, package selection and migration map.

The current live path uses the existing PFP/accounted gateway and checks actual
reply bindings before the original referee. Failures remain failures; missing
credentials or invalid replies cannot select an offline schedule. One allowance
covers every selected model and round, with unknown cost stopping continuation.
Deterministic configurations do not claim model observations. Existing output
directories refuse without overwriting their bytes.

The first control reproduced the absent canonical owner. The eight focused
controls then passed with synthetic provider replies and zero network sends.
An independent AST comparison found ten unchanged original definitions,
including the four schedule builders, coupling generator, leaderboard and
digest function, and preserved the frozen receipt fields/decorator. This is a
finite source/route check, not native parity or the paper's empirical protocol.
The original referee checks SO/noise conditions; requested target-operation
equivalence and physical device performance are not established.

Independent Adversary review reproduced a report-grading defect: a configured live
proposer could produce no judged result while the report claimed model/referee
evidence. Grades now follow actual judged live/deterministic observations;
zero judged results remain explicit, and offline accounting says `no_provider`.
Partial mixed runs retain their stop reason without promoting deterministic
results. The original public parameter annotations were also restored. All nine
focused controls passed after those repairs on the rebased source.

A fresh wheel included exact copies of both current runtime files and the two
original referee sources. From its extracted installation in an empty working
directory, an isolated Python process ran the public one-budget CLI with socket
connections disabled: four deterministic strategies reached the original referee,
zero provider calls and no observed models. The probe's first attempt failed
because its socket replacement prevented Python's SSL module from importing;
correcting only that temporary interception allowed the unchanged wheel to run.
This checks the selected braid dependency path, not the entire distribution.
The same probe passed on a newly built wheel after the rebase and report repair.
Current byte coverage accounts for 14,394 PFP paths. Static ownership/provenance
returned no findings after the retired directory's 232 ignored bytecode caches
were retained outside the checkout; no source or historical evidence was deleted.
Scoped Ruff F and the existing limited release checker passed.

## Dossier replay ownership and source names (2026-10-13)

Base: `ef4860cc3829f3f3d7182340d7780a84382621c6`. The retained dossier reader
joined every capsule identity to Education even after pilots 0000000–0000005
moved at `d7e2fb959c9efb12ac3acd1b07283e3003ee3a81`. Its environment list also
named removed provider files. Archived authorization uses the original Education
checker key, whereas its custody test indexed the newer PFP key.

The reader now selects the documented owner for each capsule before checking
its recorded input digest. Known historical source names map explicitly to
current checker/provider owners, retaining exact digest comparison. Missing or
tampered canonical data cannot fall back to an old duplicate. Preserved Education pilot paths, including the retired runner snapshot, are
read from the Adversary tests owner. The historical manifests themselves are not
rewritten. This changes the
reader and current controls, not historical plans, inputs, requests, provider
responses, authorization, source archives or pins.

Four selected retained inputs (primary pilot 0 and 188, free-followup pilot 0,
and guidance pilot 0) match their original plan digests and their pre-move Git
bytes. This is input custody evidence, not a reissue of the old model verdicts.
Original request construction, grading and replay predicates remain unchanged;
the archived checker/environment mismatch must still refuse historical replay.
Current synthetic replay fixtures exercise the current environment separately.

Eight new deciding controls initially reported seven failures and one unchanged
Education-owner pass. After repair, all eighteen selected controls passed:
owner selection, no fallback from missing/tampered current bytes, path refusal,
source-name/digest checks, retained custody, billing and six replay mutations,
plus guidance-parent preservation. A source review then identified one prior
intermediate legacy-key set to retain; the extended positive/negative source-key
control passed again after that correction. Original request/grading/replay
definitions remained byte-identical. A fresh-process read of the four real
capsules succeeded, while a retained free-followup reply returned the expected
`REPLAY_BINDING_MISMATCH`; its authorization digest was unchanged.

Focused command (no full 250-case campaign execution):

```powershell
python -m pytest adversary/tests/pilots/replay_runners/dossier_capsules/test_campaign.py -k "capsule_reader or current_environment_and_explicit or replay_tampering_refuses or preserved_source_bytes or budget_and_unknown_billing or retired_plan_is_read_only or guidance_preserves" -q -o addopts="" -p no:cacheprovider
```

The C052 example in the pilot runbook now names its actual
`pfp.tests.pilots` owner; the exact public command with `--help`
ran successfully in a fresh process. No paid run, grid, native build or original
scientific-protocol closure is claimed by this reader/documentation slice.

## Retired capsule live paths (2026-10-13)

Base: `ad49ca44b04c39ba07427c9dc79a24695e1ccd52`. Source inspection found that
the mode replay adapter still called a fixed live sweep and rewrote pilot specs;
the dossier CLI refused `--live`, but only after loading a historical plan, and
its public `live()` function still dispatched. These campaigns were already
retired. Their live entry points now refuse before mutation, credential access,
pricing or transport. Current task execution remains with existing PFP/Adversary;
the fixed campaigns are not reintroduced as a replacement runner.

The public `prepare-task`/`check-task` CLI exercised the original public seed
from `pilot_0000006` and an actual IDE-authored reply. Correct bindings passed
the shape check with `UNVERIFIED` evidence; the same bytes with a wrong attempt
were rejected as `TASK_ENVELOPE`. Both checks reported zero provider calls.
Neither result claims mode execution, mathematical acceptance or model efficacy.

Nine focused retirement, snapshot, model-budget and oracle-helper controls passed.
The six new retirement cases first failed against the old entry points and then
passed after the repair. A separate selected dossier replay check reported one
pass and eight failures: seven require the already-moved Education test-31 input,
and one expects a current PFP checker key in archived authorization metadata.
Read-only reproduction against this branch's exact base confirmed those inherited
conditions. The archived source-binding check still refuses on both versions;
no historical path, digest or authorization was rewritten to manufacture success.
Seventeen retained request, grading and replay definitions match their original
definition bytes and ASTs. Scoped Ruff F passed for the three changed code files.

Original source snapshots, pinned campaign metadata, source-binding checks and
independent replay grading remain at their existing owners. Historical checker
drift remains a refusal. Current inventory metadata separately reconciles the
seven added and fourteen changed PFP paths inherited from merged PR #927,
without changing original baseline fields or reissuing its execution claims.
Mode and dossier campaign entry points refuse before side effects. Other sender
inventory and final PFP/Adversary integration stay open.

Merged main at `ef4860cc3829f3f3d7182340d7780a84382621c6` after PR #928 landed. Its current
inventory and C005 source/validation records are retained alongside this slice.

## Accounted pilot-suite execution (2026-10-13)

Base: `ad49ca44b04c39ba07427c9dc79a24695e1ccd52`. An isolated fake-transport
reproduction of the original `OpenRouterLiveProvider` made a second attempt
after an ambiguous timeout and reported a response without `usage.cost` as zero
USD. The probe made no network call. The active controller/provider route now
uses the existing PFP/accounted boundary with one continuing allowance, explicit
live policy and fresh output. No retry path or historical result overwrite is
retained in this command. Original source prompt builders, host judges and pilot
data remain at their existing owners.

The strict-JSON sanitizer no longer falls back to permissive decoding after a
duplicate-key refusal. PFP binding failures stay separate from mathematical
judgments, and unknown cost stays distinct from known subtotals. New report
labels name the accounted v2 output rather than claiming compatibility with
historical v1 schemas that cannot represent these partial/unknown states.

Observed here: all 32 final pilot-suite checks passed, including retained schema,
historical response and original checker controls. The public CLI completed two
original `pilot_0000000` prompts in dry mode with zero provider calls and the
`HOST_REFERENCE_SELF_CONSISTENCY` grade. This exercises reporting and host
checks, not a model or paired performance. A direct AST comparison retained 16
existing provider, prompt-builder and unrelated controller/CLI definitions;
source pilot, checker, schema and migration-history paths have no byte changes.
The worker's focused red-to-green controls cover binding refusal, exact raw
reply retention, unknown cost, pending settlement, explicit allowance and
fresh-output refusal. No live provider, large grid or new native build ran.
The final filename correction separately reproduced four Windows alias/ledger
collision refusals as failures, then passed all four after preflight rejected
case aliases, trailing dots/spaces and accounting output names. Static current
Python ownership and immutable introduction provenance returned zero findings;
the unchanged epic auditor accepted all 55 epics. Independent Adversary review
also reproduced a paired-ratio defect with an extra malformed case. The repair
requires every compared observation to form a unique completed eligible pair;
malformed and duplicate controls now refuse ratios while the valid pair remains
available and all costs remain in overall totals. Scoped Ruff F passed.

This merge keeps main's later hashes for the integration PR #927 rows and the
C005 benchmark rows. It refreshes only this slice's provider, controller,
use-case, CLI, pilot-matrix, test, and validation rows. Original baseline
fields, previous-map recovery and immutable migration-introduction commitments
remain unchanged. This refresh does not reissue upstream model, native or
installed results. Mode and dossier live entry points now refuse before
mutation, credentials, pricing or transport. Full original protocols and final
whole-estate PFP/Adversary closure remain open.

## C005 scratchpad and hybrid benchmark routing (2026-10-13)

Base: `3b63d72e86b0deceba1bcb06779e38798b7c342b`. Importing the three-arm
benchmark reproduced `ModuleNotFoundError: projects`. Both retained
benchmarks now load current owners and execute through the existing PFP/accounted
gateway. Original schema constants, factorization, McNemar functions and arm
prompt expressions are compared with that base. The existing report helper has
only owner-import/bootstrap changes; task data, source judges, historical reports
and migration-introduction records remain unchanged.

One continuing allowance covers sequential arms and cases. The default direct
arm remains at 256 output tokens, with 512 for the other arms. Wrappers with these
different token bounds share the same financial scope. An explicit common-token
override is a changed experimental setting and is recorded. Unknown cost remains
unknown, ambiguous dispatch stops further calls, and original raw responses stay
in the report. An unattempted arm is not scored as an incorrect model answer.

Focused controls cover actual PFP binding/schema checks with deterministic local
provider fixtures, original certificate/canary negatives, shared allowance,
unknown/ambiguous accounting, missing policy and preservation of existing output.
All 31 focused C005 tests passed. Both direct-script commands ran from outside
the checkout on two cases each: six three-arm and four hybrid observations,
zero provider calls and no stopping refusal. Both persisted summaries retain
the fixture grade and `NOT_ADJUDICATED` fields. Offline command runs are
host-reference self-consistency only. No hosted model,
native build or broad protocol grid is part of this slice. The original judge
does not verify every intermediate scratchpad or chord entry, and factorized
arms include host-computed tree potentials. Provider-honored controls, matched
compute comparisons, original full protocols and final assembled migration
closure remain open.

After merging integration PR #927 at
`884bfa78b77b743d61ca5f361c66c34466ad5001`, the benchmark, pilot-matrix and
estimated-gateway controls passed: 73 initially, then the remaining mode-switch
control passed with the existing native host explicitly configured. The first
mode-switch attempt stopped at `HOST_BINARY_NOT_FOUND`; no test or runtime check
was weakened. This is 74 focused controls in total, not a fresh native build.
Supplemental independent source review confirmed compatibility with upstream
durable action claims and the shared 256/512-token allowance.

The same merge added seven PFP Python files and changed fourteen mapped files.
Their current bytes, AST declarations and imports are inventoried separately in
`current_review.merged_oev1rc_inventory`; the complete map now covers 14,385 paths.
This structural reconciliation does not reissue upstream mechanism, installed
package, live-provider or native results. Historical map fields, original
source-introduction commitments and recorded source/result bytes are unchanged.

## Pilot-relocation inventory (2026-10-13)

Base: `81ac733a24195aa48a77a68df84593d7250e45f6`, following the move at
`d7e2fb959c9efb12ac3acd1b07283e3003ee3a81`. This slice accounts for 14,378
current paths, adds 8,113 missing rows and refreshes nine inherited stale rows.
New records resolve the original pre-move Git blobs and retain SHA-256 for both
original and current bytes. There are 7,921 identical relocations, 101 files
changed in the move only and 91 changed later. Eleven of the later-edited files
also changed in the move, making 112 move-time edits in total. These are observed
source relationships, not fresh
execution or semantic-equivalence results.

The complete candidate map reproduced `MAP_UNAVAILABLE` at the old 8 MiB bound.
The reader allowance is now 16 MiB; per-source bounds, duplicate/path checks,
negative controls and historical commitments are retained. OERUST-011 and -013
keep their finite implementation scope separately from the existing `LIVE`
lifecycle. Their historical execution claims and open obligations are unchanged.
The lifecycle vocabulary was not expanded to make the audit pass.

Observed checks: all 19 focused migration controls passed, including the actual
complete map and exact-limit/extra-byte refusal. Static current-Python ownership
and immutable introduction provenance returned zero findings; the unchanged epic
auditor accepted all 55 epics. Scoped Ruff F also passed. These results do not
reissue runtime or mathematical checks for the moved corpus.

Current commands for this slice:

```powershell
python -m pytest pfp/tests/test_migration_fitness.py -q
python -m pfp.infrastructure.migration_fitness --current-python
python -m product_planning_office.use_cases.epic_manifest_audit
```

These checks concern inventory, byte/provenance custody and planning metadata.
Original scientific protocols, installed use after all moves, live Adversary/PFP
route closure and native parity remain open. The earlier results below retain
their original revisions and scopes; they are not fresh results for this map.

## Current source reconciliation (2026-10-13)

The Windows review reconciles exact current Git-index coverage and source bytes
against the retained prior map at `e09492620a7219b76be114c10c0c2729c6283700`.
It preserves that map's Git recovery/digest and original 4,803-file baseline.
Changed/new source inspection is structural: Python ASTs, structured-asset
parsing, source/call boundaries and relevant native module declarations.
Ownership-only AST matches are distinguished from changed behavior; no native
build, paid provider run or whole-estate behavior suite is part of this review.

The current map gate and focused mutation controls check coverage, reviewed
bytes, duplicate/path refusal, missing native targets and recovery of the prior
map. Native correspondence remains scoped/unestablished where fresh evidence
is absent. The malformed retained normal-form JSON receipt is recorded as
unparsed historical data, with its bytes preserved.

Observed current results: the unchanged default map CLI returned `PASS` with
zero findings, and `tests/test_migration_fitness.py` passed all 18 focused cases,
including current definition/byte-size metadata consistency.
These results cover inventory/custody and their falsifiers, not native behavior.

## Shared matrix owner relocation (2026-10-13)

Both Education matrix helpers move byte-for-byte into canonical PFP infrastructure.
Fresh isolated interpreters reject Education/legacy import aliases and load the
new owners. The focused checks pass: 16 formal, 11 synthesis, three ownership/CLI
and 10 C051-C055 entry-point cases (40 total). C059 CLI help exposed a missing
`sys` import, now fixed; it sends no provider request. Original helpers, task
data, independent judges and retained result/snapshot bytes are unchanged.

The the city estate-wide OEOS ledger test fails with 79 extra and 15 stale imports.
Mapping the moved helper back to its exact original source and using the original
ledger yields identical failure sets. This slice updates the existing helper row
only; it does not absorb unrelated runtime or historical-snapshot ledger drift.
Legacy Education task imports/transport tests and installed-wheel/full live-route
verification remain open. No paid run, native build or broad suite was attempted.

## Current Education matrix callers (2026-10-13)

C043-C050 and C056-C058 current matrix commands now load their Education task
owners and canonical PFP matrix helpers without retired import aliases. The
eight formal runners expose explicit model, case, output, call and estimated-cost
selection through the existing helper. Their no-argument Python APIs retain
original behavior. Selected settings and original limits appear in the existing
run record; there is no new runtime, sender or evidence store.

All eleven isolated direct-script help checks first failed on retired imports.
After repair, those checks and their coverage assertion pass (12 cases), with
network access blocked and an external working directory. The new formal CLI
checks and existing formal PFP checks passed together (32 cases). Review then
found empty-case output creation; its new regression failed before the guard
and passed afterward (one additional case). Ten selected original C043/C056
judge controls and three C043 prompt checks also pass. These are 58 distinct
focused checks across these executions, not a fresh whole-estate result.
Four additional import-only smoke checks exposed and then cleared stale root
depths in C047-C049/C058 participant scripts, without executing their solvers.

The source comparison preserves 279 existing task function/class definitions
after normalizing only the owner import prefix; the eight formal entry wrappers
add optional CLI routing. Original task data, judges, solver bodies, historical
outputs and source snapshots are unchanged. The helpers' introduction digests
remain immutable; the current source map records subsequent canonical changes.
No provider calls, native build, case generation or protocol grid were run.
C041/C042 experiment consumers, installed M1-E and full original protocols remain
open. The inherited the city ledger failure described above was not rerun or reset.

## Current C041/C042 experiment consumers (2026-10-13)

The branch was refreshed to merged main
`8d43a0f9bbc57b327b884aa1a90a9fdf8052972f` before final checks.
The new accounted-experiment tests, isolated entrypoint/report tests and original
C041 custody tests passed together (29 cases); original C042 leakage, refusal
and custody tests passed separately (22 cases). These 51 scoped controls use
deterministic provider fixtures, the actual PFP/ledger boundary and the original
SAT judge. They are not live model or fresh Lean-build evidence. C041 retry tests
explicitly inject the judge where needed; original refusal controls stay intact.

Deciding failures were reproduced before their fixes: the ambiguous local judge
imports, unknown-cost report formatting, missing accounted gateway, and an
ambiguous transport outcome incorrectly reported as zero cost. The repair carries
one allowance across arms/cases/retries, retains raw bound replies and stops on
unknown accounting. All three direct-script help commands run offline from an
external directory. No implicit model or financial allowance is admitted.

Source comparison covers 29 active task files: 25 import-only repairs and four
experiment/report files. It retains 150 existing definitions after normalizing
only owner imports, preserves all prompt formatter bodies and changes nine
existing orchestration/report definitions. No mathematical function body, task
data, historical commitment, recorded result or frozen snapshot is changed.
Existing commitments describe their original source revisions, not this update;
they were not regenerated. New explanatory documentation distinguishes prompt
variants from actual neural attention/logit hooks.

Merged PR #905 also changed 38 PFP source/test files without refreshing the map.
Their provider-owner transitions and four pilot fixture path changes were
reviewed, and only their current hashes/definitions were refreshed. This does
not claim fresh execution of every inherited provider control. Historical map
fields and the helpers' immutable source-introduction commitments are preserved.
Installed M1-E, original full protocols, native parity and the full migration
remain open. No paid calls, native build or broad protocol grid were run.

## Current two-stage challenge boundary

The retained baseline/typed-witness/transfer runner now accepts its caller's
existing accounted gateway and checks actual outer PFP bindings before invoking
the original inner SPK judge. It no longer creates a separate campaign ledger,
selects raw transport or writes a claimed user authorization. The CLI requires
explicit model, token, call and cost limits; existing outputs and accounting
paths refuse before provider resolution. Both stages share the same allowance.

Review caught an unintended decoding change in the first candidate. The final
route keeps the original provider decoding settings: no added response-format
constraint. Invalid inner SPK still follows the original ENVELOPE repair rule;
invalid outer bindings and uncertain accounting stop before judging. New capture
records recheck exact requests/replies, sources, PFP and original judgments with
zero sends. Historical records keep their original schema and source requirements.

An independent review also reproduced a lone-surrogate answer crashing current
capture persistence. Current capture JSON now uses a named sorted-key ASCII
escape profile; provider and historical bytes remain exact. The runner records
`INVALID_COMPLETION_UNICODE` and stops, and replay reproduces that refusal.

Bounded synthetic controls cover original C050 rejection/repair, missing gateway,
malformed and wrong-bound replies, unknown cost, wrong model, output preservation
and zero-send replay. Saved completion text is reused only as explicitly synthetic
current input; no new historical execution or paid model result is claimed.
CLI policy/terminal controls and direct-script help outside the checkout pass.
After the Unicode repair, 18 runner/replay controls and five CLI controls passed;
two current-map/historical-baseline controls passed before the affected map refresh.
The publication rebase retained main's native-driver updates and exposed two
unmapped files added by merged PR #946: the WDP abstention adapter and its use
case. Their bytes match main; the map now records current hashes, definitions
and Python ownership. This is inventory reconciliation, not fresh WDP execution.
The original frozen C005 checkout replay, full protocols, native parity and full
M1-M6 migration remain outside this slice. Historical task/evidence bytes remain
unchanged; the current map refresh preserves baseline and introduction bindings.

## Current Paper 008 execution derivative

The canonical retraction benchmark preserves fourteen original graph/type,
certificate, prompt, parser and digest blocks from the retained Paper 008
source. Twenty-eight focused controls passed for current PFP/accounted execution,
refused and unknown-cost replies, one continuing allowance, all twenty-four
offline graph/condition combinations, exact source equality and replay
mutation refusals. Review repairs distinguish proven no-dispatch zero cost from
unknown attempted-send cost and check accounting summaries during replay.
Output checks use cross-version file attributes; a simulated missing
`Path.is_junction` check passed, without claiming a Python 3.10 interpreter run.
The documented four-row CLI exercise completed with three
matches and the expected blind poisoned-graph stub miss; all four replayed
with zero provider calls. No observed model, native rebuild, installed-wheel
validation, original empirical protocol or broad migration closure is claimed.
The paper deposit and its historical v2 records remain unchanged. Current-map
rows record this derivative separately without rewriting earlier provenance.

## Finite-gauge workbench checker ownership

Base: `f6ee8d03cbc6e89b55f413281e2ed996b2305abf`. The current workbench's two
computed `research.*` import bases had no owner. An ordinary even-triangle run
returned `FAILED` before generating any candidate. The canonical PFP adapter
now contains byte-identical copies of the original `sign_graph.py` and
`frontier_search.py`, and the workbench loads that single module pair.
Historical paper files and receipts remain unchanged. Existing search ordering,
exact witness checks, receipt digests and the one-worker call are preserved;
no scheduler or concurrency behavior is changed.

Eight focused workbench checks passed, including the FastAPI route/event stream,
all three finite terminals, invalid/resealed witnesses, source-byte/type custody
and isolated `python -I -S` loading from a selected source copy without Education
or the checkout. The three documented CLI commands separately produced
`GAUGE_VERIFIED`, `RESTRICTED_OBSTRUCTION` and `UNKNOWN`, each with a rechecked
receipt. These are zero-provider finite controls. Isolated source loading is
not a full wheel build or installed-distribution test.

The current source map records these current copies and their retained source
hashes separately from earlier relocation provenance. This selected ownership
repair does not establish native parity, full installed distribution coverage,
LLM efficacy, a physical Hamiltonian reduction or complete M1-M6 migration.

## Current public demo admission repair

Base: `f6ee8d03cbc6e89b55f413281e2ed996b2305abf`. The public command
`pfp run-demo demo_003` returned `PASS`, `Exact` and `all_passed=True` from
three literal success flags with no associated execution. A second consumer,
`RunDemoUseCase.run_pilot`, looked for the nonexistent `all_checks_passed`
attribute and defaulted to success, including for a refused typed receipt.

The current runner retains all three original obligations as unmet and explains
their retired or unavailable implementation. The public CLI lists the reasons.
Pilot transitions now use the actual typed receipt result and retain that result
in the aggregate's existing evidence field. The current MUB6/Regge illustration,
retired cohomology scenario and original reports remain unchanged. This is a
correction of false admission, not an implementation of the original aggregate
or completion of M1-M6. Existing independent scenarios keep their own scope.

Focused controls cover the refused aggregate, actual receipt preservation,
missing/untyped runner results, an executed positive demo and the existing
token-frontier scenario's execution/replay. The actual `pfp run-demo demo_003`
command now exits 2 with all three reasons; `demo_001` still passes its existing
gate controls. These are provider-free checks of current admission, not model
performance or historical reissuance.

## Public prompt assembly consumer (2026-10-14)

Base: `cba7e58c0e7b4c38aef800efe320f635f47b12b1`. The actual `pfp assemble`
command failed with `AttributeError` on `PromptPacket.packet_id`; its next
summary field also referenced the absent `envelope_sha256`. The command now
reports the existing identity and content hashes and offers `--json` for the
actual system/user/schema packet. It performs no provider call.

The public assembler now binds the requested demo identity in a copied model-stage
schema instead of returning `DEMO_ID_BOUND_BY_HOST`. Other schema requirements,
stage 0/host-only stage 5 behavior and the existing digest algorithm remain.
Controls cover an original stage-1 witness, wrong/placeholder identities,
required content, independent repeated assemblies and both actual CLI outputs.
Original numbered YAML, historical prompt versions and recorded evidence retain
their bytes. The existing pipeline already bound its identity and is unchanged.

The current source map records these changed owners and controls without changing
historical source bindings or claiming native parity. This closes one public
preparation defect; installed use, live stages, original protocols and the full
M1-M6 migration remain open.

## Current judge-packet audit owner (2026-10-14)

Base: `cba7e58c0e7b4c38aef800efe320f635f47b12b1`. The real offline audit command
failed during discovery because its task root still named the deleted
`projects/mssn_sn_symgam/challenges` tree. The existing Adversary audit
now discovers the current PFP task tree, builds current execution descriptors,
checks that tree for mutation and records the current command. Relocated audit
tests and their synthetic task fixtures import the actual owners.

Static source analysis retains recognition of original import spellings; it
does not install runtime aliases or rewrite scientific task/judge files. Unknown
or empty package selections refuse. Deciding controls compare a sound synthetic
judge with one that wrongly accepts refusal and check the current discovery and
source classification. A selected C014 source-only command exercises the public
entry point without running the corpus or models. That command inspected one
selected package with 62 cases and 52 mutation entries; it retained custody
discrepancies and reported the source tree unchanged. Unselected special checks
were absent. The scoped relocated audit suite passed 56 checks; hanging and
sharded controls were not rerun because their execution machinery is unchanged.
Static observations remain distinct from executed checker acceptance.

The current PFP map records changed audit controls and this document while
retaining earlier source bindings. Original task, case, judge, mutation,
commitment and historical audit bytes are unchanged. This repairs one migration
consumer; native parity, installed use, complete judge independence, original
protocol execution and the full M1-M6 migration remain open.

## Historical validation scope

The following records describe the earlier managed Linux execution. They are
retained historical results, not fresh validation of this reconciliation. No
hosted CI or paid model calls were part of that evidence; the full repository
suite was unrun.

## Executed native checks

| Scoped target | Outcome |
| --- | --- |
| `core_symbol_game/tests/mcp_transport.rs` | Passed initialization, registry-derived tool discovery, exact outcome preservation, duplicate/ID refusal, byte ceilings, multi-frame stdio, and compiled-binary execution outside the checkout. Filesystem tools are excluded. |
| `core_symbol_game/tests/scoring_migration.rs` | Passed strict obstruction parsing, exact tiny residual preservation, explicit policy, canonical rationals and malformed-field refusal. |
| `core_symbol_game/tests/reply_control_contract.rs` | Passed fenced-block syntax, Unicode whitespace and ordered declaration refusals. Python compares native fields and insertion order with the retained independent regex contract. |
| `core_symbol_game::signed_transport::tests` | Passed gauge/cycle replay, witness tampering, schema and dimension/scalar limits. |
| `core_symbol_game_runtime/tests/stabilizer_certificate_binding.rs` | Passed case identity, basis substitution, decomposition identity/mask/phase substitution and UNKNOWN-code tampering. |
| `core_sandbox/tests/hostile_scripts.rs` | POSIX refuses before launching the submitted command. Windows resource controls are unrun on this host. |

The native build also revealed an existing missing `HashMap` import in
`core_symbol_game::challenge`; using the sandbox environment field's default
restores compilation without introducing a nondeterministic certificate map.

## Executed Python checks

Targeted files cover host CLI custody, unconfigured CEC refusal, exact scoring,
native Q40, signed transport, sandbox refusal, mode discovery, architectural
fitness, token-frontier refusal and migration-map negative controls. The native
Q40 route checks all 40 declared cases and optional dense spectra, retains 80
solve/check envelopes, and exercises forged certificate coordinates. Its input
and outcome hashes appear in the receipt. The checker re-solves through the
native implementation; no independently implemented Rust algorithm is claimed.

Legacy scoring policy/ordering functions and the meron-2d fixture were checked
separately against their native-backed path. Windows-only sandbox tests are
skipped on Linux. Historical rich quantum source/tests are retained byte-identically
and excluded from active collection after their contract's retirement.

The exact-solver governance script passes. The broader ROP governance script
fails because the existing canonical skill-compiler `eval_runner.py` is absent;
it does not execute the new MCP or scoring code. This unrelated missing runner
remains open. No check was weakened or replaced to claim a pass.

## Evidence limits

A manual native MCP session ran from `/tmp` with Python absent from the child
process PATH: initialization, discovery of 78 computational tools, exact rank
and native reply parsing produced four responses with the expected rank and
field order. The tested debug binary SHA256 is
`5726a7cdbf14a10d28acd0cf7de6b9116ae1886dc9aa5b3b01209507a1a5e8c9`.

The complete map verifies file accounting, source byte custody and real Rust
owner paths. Every starting file received structural inspection; active owners
received semantic review. This does not independently prove every mathematical
claim in the historical fixture estate, or certify every proposed native port.

The native stdio server is an implemented single-executable surface for the
registered computational tools. Full Python retirement remains open for the
prompt/turn lifecycle, provider budget/custody barriers, web sessions, event
transactions, research replay and installed-demo resource packaging identified
in [README.md](README.md). POSIX isolation has an explicit unsupported outcome.
Input framing limits do not assert a universal computation-time limit.

Source diff formatting checks pass. The byte-identical historical quantum test
archive retains its pre-existing trailing blank line; its original bytes were
checked against the starting Git tree rather than reformatted.
