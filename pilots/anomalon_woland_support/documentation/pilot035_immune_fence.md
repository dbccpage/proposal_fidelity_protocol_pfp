# Pilot 035: admitted guidance in a real Woland turn

Pilot 035 connects OEEIS pharmacy search, PFP prompt rendering and the shared
Woland IDE coordinator. It checks finite claims about all 225 cross-ratios of
the explicit Tao phase table. It does not establish a theorem about all complex
Hadamard matrices, Hadamard-cube slices or the unrestricted MUB(6) problem.

The runtime is in `omega_engine_woland`; OEWAS owns the task/template/binding
data under `data/pilots/pilot035`. The historical Atlas Pilot 035 packet and
the OEWAS-012 experiment captures retain their original bytes and meanings.

## Run in the current IDE

Build the existing host and mathematical executable, one job at a time:

```powershell
$env:CARGO_TARGET_DIR = Join-Path (Get-Location) '.scratch/pilot035/native-target'
cargo build --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --bin omega_symbol_game -j 1
cargo build --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_mub --bin mub_tao_confluence_verifier -j 1
$runtime = Join-Path (Get-Location) '.scratch/pilot035/runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
Copy-Item -LiteralPath (Join-Path $env:CARGO_TARGET_DIR 'debug/omega_symbol_game.exe') -Destination (Join-Path $runtime 'host.exe')
Copy-Item -LiteralPath (Join-Path $env:CARGO_TARGET_DIR 'debug/mub_tao_confluence_verifier.exe') -Destination (Join-Path $runtime 'checker.exe')
$env:OMEGA_SYMBOL_GAME_HOST = Join-Path $runtime 'host.exe'
$checker = Join-Path $runtime 'checker.exe'
$env:TEMP = Join-Path $runtime 'tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
python -m omega_engine_woland.entrypoints.cli pilot035 start --state .scratch/pilot035/my-run/state.json --checker $checker
```

In the IDE, the equivalent request is:

```text
/woland run Pilot 035 with the admitted immune fence using the current IDE session;
follow pilot035 start/next/submit/replay and the full Retinue, with no paid calls.
```

Read the returned `pfp_turn.system`, `pfp_turn.user` and response schema. Save
the actual bound response JSON, including task/attempt/input bindings, then:

```powershell
python -m omega_engine_woland.entrypoints.cli pilot035 submit --state .scratch/pilot035/my-run/state.json --raw-reply .scratch/pilot035/my-run/reply.json
python -m omega_engine_woland.entrypoints.cli pilot035 next --state .scratch/pilot035/my-run/state.json
python -m omega_engine_woland.entrypoints.cli pilot035 replay --state .scratch/pilot035/my-run/state.json
```

`submit` advances the existing host checks and returns the next real model
action. There is no shell command that borrows an IDE session or invents its
responses. One actual IDE worker may apply the 22 perspectives; this is not 22
independent reviewers. The coordinator permits one repair and retains its prior
candidate, original check and learning. Finish with the ordinary scoped AutoP.

## Continue a stopped pilot

Use the pilot's state-aware continuation command, preserving the parent:

```powershell
python -B -m omega_engine_woland.entrypoints.cli pilot035 resume --state .scratch/pilot035/my-run/state.json --output .scratch/pilot035/my-run/continued.json --reason "Retry the checked current-state boundary"
python -B -m omega_engine_woland.entrypoints.cli pilot035 next --state .scratch/pilot035/my-run/continued.json
python -B -m omega_engine_woland.entrypoints.cli pilot035 submit --state .scratch/pilot035/my-run/continued.json --raw-reply .scratch/pilot035/my-run/continued-reply.json
python -B -m omega_engine_woland.entrypoints.cli pilot035 replay --state .scratch/pilot035/my-run/continued.json
```

Finish pending work before resuming. Add only a needed `--additional-actions`
or `--additional-repairs` allowance; the ten-evaluation ceiling and continuing
episode ledger are unchanged. A parent whose recorded checks lag its ledger
refuses with `EPISODE_HISTORY_MISMATCH`; continue the descendant that contains
those attempts. Changed candidate files still require an explicit real repair.

The original v1 command embeds its initial state path. Generic `teamwork resume`
preserves that command and therefore cannot redirect it to a child. The pilot
command instead records `pilot035.continuation-check.v2` as an explicit wrapper
successor. It retains the original finite checker identity, source bytes and task
configuration, adds the immutable parent and wrapper sources, and records the
actual new argv. Earlier observations keep their original commands; replay
selects the successor only at its continuation marker. Tampered parents,
substituted tasks and redirected child paths refuse before finite checking.

A corrupt or inaccessible SQLite ledger returns the public CLI refusal
`EPISODE_LEDGER_UNAVAILABLE` with exit 2. It creates no continuation and does not
replace or reset the ledger. Review reproduced the corrupt-file failure before
the fix; the owning continuation/acceptance batch then passed all 18 cases.
This review repair follows the captured implementation run below; its retained
artifact hashes continue to identify the original run's bytes.

Historical replay may read an exact artifact version from a native checkpoint
already re-executed against its recorded action. The path and digest must both
match. Its `HISTORICAL_EXECUTION_ONLY` scope and `retained_artifact_paths` identify
that readback; live checks still require current output bytes. A changed version
without a validated snapshot refuses. Replay does not update historical states,
reset accounting or turn an old result into acceptance of today's files.

The original v1 `PILOT035_CHECK_NOT_PENDING` capture is reproducible only against
its exact hash-bound continuation parent, using the original command and matching
task/history. It remains an unavailable execution, counted separately in
`reproduced_unavailable_checks` from `accepted_checks`. Other errors, changed
parents and a parent with a pending recheck refuse. This lets the failed attempt
remain visible when replaying a subsequent repair.

The retained 34-observation descendant now returns `REPLAYED`: all 22 roles are
observed, one finite check is accepted and one unavailable check is reproduced.
Its state hash remains `94bb1c2ef7e43aacd4135c1f1852610e709ba7b44cc48f7edeee0edc97021aee`.
No provider calls occur, and its pending work stays pending. The focused replay,
Forge/PFP and capture batch passed 38 cases. Preparing its next action also
preserved the action, input binding, system/user text and schema while eliminating
an unnecessary deep copy of the freshly serialized geometry history. This is an
execution-overhead repair, not a claim of improved model accuracy.

## Native diagnostic witnesses

Role participation and gate measurement are separate. The historical examples
below retain their original 25 HOLD / 10 BLOCKED results. Investigation found:

| Cause | Current behavior |
|---|---|
| Diagnostic scans were accumulated as actual role traversals | New batches retain `actual-role-traversals-v1`; explicitly diagnostic edges no longer trigger fictitious repeated-traversal descent. Real declared traversals still do. Historical batches replay under their original profile. |
| Captured PFP preparation was not supplied to Natasha | Host-facts v2 compares retained system/user/schema/binding with independent preparation. The native checker verifies exact compact UTF-8 JSON bytes and field coordinates. This measures preparation preservation; IDE delivery remains unobserved. |
| Resumed native receipts used a predecessor wrapper binding | Their exact declared acceptance predecessor is validated alongside unchanged task, plan, native selection and source-read scope. Unrelated or modified receipts still refuse. |
| Other predicates received no scientific or operational witness | Missing evidence remains explicit; it is never filled from persona agreement or density measurements. |

In particular, the Tao task supplies no cochain carrier, primal/dual certificate,
Lean theorem or perturbation family for gates 01/02/05/06/07/10/13. Gates 15/20
require the existing authenticated process observation; gate 22 needs the
configured resource sandbox. Empirical gates require their actual token, attack
or e-graph experiments. Other operational gates need their complete typed inputs
(scar targets, obligations, custody chain, confidence, crisis or repair evidence).
These missing inputs do not mean that the native finite Tao check failed.

Intergates likewise require their own capacity, KL, critic, sandbox, independence,
quarantine or attestation evidence. An entropy score is not KL calibration;
22 role perspectives from one IDE worker do not establish independent sampling.
The false-urgency gate consumes actual host verification timing. Strict
`require_pass` policy continues to refuse any remaining diagnostic residual.

### Observed continuation control

The [bounded continuation example](pilot035_continuation_example.json) used
synthetic coordinator role history with two actual admitted subprocess checks
through the existing Rust Tao checker and immune screen. Public CLI resume and
replay succeeded; the new command named the child, both checks accepted, and
one continuing ledger contained exactly two evaluations. Parent bytes and the
original checker/source binding stayed unchanged. Replay left the child hash
unchanged and made no provider calls. This is an integration control, not a new
live IDE pilot or an accuracy comparison.

The separate actual IDE implementation run observed all 22 roles. Its full
native scan measured 24 HOLD, 9 BLOCKED and 2 PASS: Natasha's preparation check
and false-urgency host timing passed. The remaining predicates lack the witnesses
listed above. A helper's first native checkpoint failed on an unwritable worker
TEMP; that failure remains retained. Set TEMP/TMP inside the actual worker shell,
finish the stopped run's learning/DDC work, then explicitly resume its checkpoint.
Changing an earlier shell's environment does not configure later workers.

The resumed original-task acceptance command passed its 22 focused continuation
and gate cases in 53.30 seconds. This is a bounded implementation check, separate
from the finite Tao answer checks in the continuation control.

The outer run finished `completed` after 34 actions and 22 captured PFP replies,
with all 22 roles observed. Its ledger recorded one evaluation under the original
ten-evaluation ceiling and used no extra action or repair allowance. Digestion
found zero current findings/gaps; scoped AutoP/learning ran once and its actual
guidance change passed the learning review. UNS/UTS for both stopped parent and
completed child were finalized through the existing canonical sink after a
publication-only filesystem retry. Both state hashes remained unchanged.

The generic evidence verdict remains `OPEN_RESIDUAL`; the finite check does not
supply the missing scientific, authenticated-process or empirical witnesses.

The earlier 30- and 34-observation histories remain byte-identical. The older
parent lags its ledger; the descendant still has its recorded changed-artifact
repair pending. Neither is rewritten as a completed recovery.

Focused RED/GREEN controls passed: eight pilot-continuation cases, nine
acceptance/parent-scope cases, fourteen gate cases, four existing source-profile
cases, four public prefix-replay cases and three existing host-fact cases.
The native controls include actual predicate execution and harmful byte/field
mutations. Run owning batches sequentially with a copied native host:

```powershell
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/continuation-check omega_engine_woland/tests/test_pilot035_continuation.py omega_engine_woland/tests/geometry/test_pilot035_continuation_replay.py
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/gate-check omega_engine_woland/tests/test_teamwork_pilot035_gates.py omega_engine_woland/tests/test_teamwork_source_profile.py
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/parent-check omega_engine_woland/tests/test_teamwork_acceptance_continuation.py
```

An additional older continuation batch was interrupted after failures; it is
not reported green. Its representative action-count expectation reproduced
unchanged on the pre-repair `d70834089a` implementation and this branch:
`actions_used` was 11 while the test expected 10. No whole-suite pass is claimed.

## What the integration checks

`PharmacySearchIndex` uses Rust to select admitted, current, applicable rules.
Trusted task metadata defines domain, stage and prompt-field scope; content
cannot expand it. Snapshot drift, revoked/suspended rules, missing admission,
bad rule hashes and inconsistent projections cannot silently become active.

`PromptFamilyBinder` inserts reviewed guidance at one `[IMMUNE_FENCE]` anchor
before PFP hashes the input. It preserves whole guidance items within three
items and 2,048 UTF-8 bytes. Template, catalog, rule, admission and rendered
content bindings travel with the task. Fixtures and oracle results do not enter
the prompt. Legacy templates without a binding remain unchanged.

The two selected rules examine only the canonical structured `claims` object.
They do not scan quotations, explanations or the fence itself. The pinned MUB
checker independently evaluates the numerical answer and its declared scope.
The existing two-signal immune screen corroborates a detector hit with that
host result. Missing tooling remains unavailable verification, not a detected
mathematical defect. Freeform explanation text is retained but not certified.

## Admission, replay and limits

The repository owner admitted two exact rule revisions for the Pilot 035 prompt
URI on 2026-10-15. The source definitions remain candidates; the catalog records
the separate human decision and native eligibility assessment. Fixture
reproductions are labeled as fixtures, not independent model sightings or
cryptographic signatures. Harvesting never grants admission.

Runtime data stays in the chosen state directory. Replay rechecks actual raw
PFP replies, current bindings and the original native result without provider
dispatch. Replay requires the original catalog, templates, checker and retained
files; changed admission or rule bytes refuse rather than silently rebind a run.
Keep the originating repository revision and run directory when retaining a
demonstration. IDE token usage and billing are unobserved; zero external dispatches
does not mean measured zero IDE cost. A finite demonstration is not evidence
of a general accuracy improvement.

Host-crate separation and broader V1 application dependency cleanup remain
follow-up work. This integration introduces no scheduler or concurrency layer.

## Preserved pilot corpus

The branch incorporates main `370a629351e8d2c130bcc136799258b4914cc587`,
including the newer Atlas pilots, their patterns and all 1,067 existing catalog
records. The two separately approved revisions bring the catalog to 1,069.
An historical `admitted` label alone does not make those other records eligible
for this prompt. New repairs need their own scoped guidance, controls and decision.

## Observed IDE demonstration

The [collated example](pilot035_ide_example.json) records the actual current-IDE
run: all 22 roles, 22 bound model replies, 33 workflow actions and no repair.
Both original-task native checks accepted the structured answer. Replay returned
`REPLAYED` with the same full roster and two original checks. The selected two
antibodies rendered 604 UTF-8 bytes of guidance, with no omitted item.

The finite answer enumerated 225 ratios with phase exponents `{0, 8, 16}` modulo
24 and multiplicities `45, 93, 87`; it made neither broader-family nor MUB
exclusion claims. These results appear only in the captured answer/results,
not in the prepared task's expected-answer channel.

An independent temporary guard wrapped the existing Anthropic/OpenAI-compatible
dispatch and HTTP entrypoints for all 24 CLI invocations (start, 22 submissions,
replay): zero attempted external provider dispatches. IDE tokens and billing
remain unobserved. Raw replies, native output and DDC bytes remain in the local
`.scratch/pilot035/live` directory; the compact example is a result collation,
not a replacement for those bytes or a portable replay package.

Workflow completion and finite answer acceptance do not promote the generic
Woland evidence verdict: it remains `OPEN_RESIDUAL`, with 25 `HOLD` and 10
`BLOCKED` diagnostic gates. The example retains their reasons. The ordinary
AutoP/learning finish ran once; its changed-file lint found zero issues, and
learning reused the two scoped rules rather than inventing another detector.

## Focused verification

71 Python cases and 14 Rust cases passed. These are the owning batches; no
whole-repository or paid campaign was run. Keep the copied binaries above stable
while the run and its replay are in progress. A writable temporary directory is
needed by the existing large-file native bridge on restricted Windows hosts.

```powershell
$env:PILOT035_MUB_CHECKER = $checker
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/check-native omega_engine_epistemic_immune_system/tests/integration/test_native_pharmacy_search.py omega_engine_woland/tests/spine/test_native_immune_screen.py omega_engine_woland/tests/test_pilot035_play.py
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/check-guidance omega_engine_woland/tests/test_prompt_family_binder.py omega_engine_epistemic_immune_system/tests/unit/test_pilot_candidate_publication.py omega_engine_epistemic_immune_system/tests/unit/test_pharmacy_search.py
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/check-legacy omega_engine_operads/tests/unit/test_prompt_hierarchy.py
python -B -m pytest -o addopts='' -q --basetemp .scratch/pilot035/check-repair omega_engine_woland/tests/test_teamwork.py::test_repeated_findings_exhaust_one_repair_without_loop_or_success omega_engine_woland/tests/test_teamwork_continuation.py::test_blocked_repair_attempt_still_consumes_allowance
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_epistemic_immune_system --test pharmacy_search -j 1
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game_runtime --test immune_fence -j 1
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_mub --test test_tao_confluence_verifier -j 1 --no-default-features
python -B -m omega_engine_operations.use_cases.packaging.sync_cross_host_skills --check --skills woland
```
