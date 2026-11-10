# Checked occurrences and the selected protected hint

AuthorityEffect: None. Implementation: PR #1094, building on #1093.
HoTT goals were removed by the user on 2026-10-16; historical evidence is retained.

The existing OEWAS interpreter can now check actual invocation values before
dispatching a parent. Selected native negatives retain the exact stopped root
profile; unavailable observations and forwarded reason strings do not create
a `NullTree`. All 22 primary gates have strict opt-in request/witness contracts
and sealed Rust selectors. See [the formal contract](formal_operad_contract.md)
for APIs, predicate scope and remaining correspondence obligations.

## Observed checks

The frozen original-task checker passed 167 Python cases, two Rust selector
tests, 15 witness tests, one source/intergate test and the central 11-job Lean
build. Both ledgered evaluations ran the same checker and unchanged source
hashes. They are repeated checks, not an additive test total. An additional
67 existing DDC/typed-operation/native-execution compatibility cases passed;
generic occurrence and input-action controls also passed.

Three actual review defects received RED-to-GREEN controls: ignored operator
specification pins, equal-valued but differently selected operand coordinates,
and a rehashed nested binary identity. Declared source changes and unsupported
external witness configuration refuse explicitly before a new gate check.

The prior final native capture retained SHA-256
`6192e62370e7da5663cea8a62a12419db8b3ad70667862dc2aada8c59a7ba0e5`.
Its 35 results and 10 transitions replayed against its original pinned host.
Its previously refused 133,927-byte Natasha payload passed the current host
after lossless pooling to 67,974 bytes, including actual catalog negotiation.
The old bytes and refusal were not changed. Neither global size cap increased.

## Actual selected-hint recheck

The current-IDE shared-backend run is
`a6d39ed197d841e79ea6de8ba0b47970`, working state
`.scratch/woland-occurrences/teamwork.json`. All 22 named Retinue perspectives
contributed through existing PFP preparation/submission. The captured model
worker is the actual IDE agent, not 22 independent workers.

The single scoped AutoP/auto-learn finish retained the applied binding,
pre-dispatch timing, transport and premise fixes without adding duplicate
guidance. The selected hint used the already-budgeted second original-task
evaluation, through the existing `admitted_recheck`; no checker override or
metadata rewrite was used. The retained precheck state had 5,747,081 exact bytes
and 351 source documents. One fixed hint/context attachment changed 48 parts
and 47 links to 49 parts and 48 links. Source bytes remained identical.

The actual host check accepted. The existing CDC validator returned `Preserve`
for its declared protected-session query, with sufficient evidence and
`authorized=false`. There were no historically declared task premises; the
empty premise object is explicitly caller-bound. This is a checked structural
hint and software-task recheck, not evidence that the hint improves an LLM or
repairs a nonzero cochain. The selected graph pushout proofs have their stated
fixed-document scope; general serialization refinement remains open.

The finished run retained 33 observations, all 22 roles and 22 actual PFP
captures, with one learning reply and exactly two completed ledger episodes.
Both saved check observations matched their ledger rows byte-for-byte. The
state's 6,432,159 bytes have SHA-256
`e3cf0ec695e601dad4f1826824b1ea5cd0588e83c9726f671ffe5bcd834c5cb2`.
All 22 bound source files and both pinned host binaries remained unchanged.
No external model provider was dispatched; IDE billing remains unobserved.
Digestion had zero findings/coverage gaps and its actual Koroviev review and
final DDC readback completed. `HOST_REPORTED_COMPLETE`, `work_status=completed`,
the literal `OPEN_RESIDUAL` and null generic original-task outcome keep their
existing meanings. The two accepting software checks are separate evidence.

The immutable workflow host retained 24 HOLD, nine BLOCKED, one PASS and one
Natasha resource REFUSE. Those diagnostics were not upgraded to success; the
fresh current-host pooled-transport control above is separate evidence. The
broader formal goal remains active, including further gate-specific bindings
and runtime/model correspondence. This result report was added after the run.

Reporting-only persistence finalized the existing canonical sink at
`_ic/woland/runs/a6d39ed197d841e79ea6de8ba0b47970-e72a5b340f30` without changing
the state. All five payload digests were independently checked. The canonical
UNS SHA-256 is
`fdf42a4c4212883c1d0e15680206e062481fbebe72240f0686a0f67cf9675e86`;
UTS is `754e55aeb8fbf548f20c9648520cae18b61a9ac61b5302f9dae135a7baccf973`.
Working report hashes differ because their source references differ.

## Commands used in this checkout

The run's original checker is retained at
`.scratch/woland-occurrences/acceptance.py`, SHA-256
`9c27257397d971548be93b2313f469c7c39f298b9e1f370f01c5b0c203840c48`.
Its four owning commands are reproduced below. Use the repository's existing
Python environment; temporary outputs stay outside tracked fixtures.

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:TEMP = "$PWD/.scratch/woland-history"
$env:TMP = $env:TEMP
$taskPython = "$PWD/.scratch/oewas012/venv/Scripts/python.exe"
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
cargo build --offline --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --bin omega_symbol_game -j 1 --target-dir .scratch/oewas012/native-target
$env:OMEGA_SYMBOL_GAME_HOST = "$PWD/.scratch/oewas012/native-target/debug/omega_symbol_game.exe"
& $taskPython -B -m pytest --override-ini addopts= -q omega_engine_woland/tests/test_gate_contracts.py omega_engine_woland/tests/test_gate_occurrences.py omega_engine_woland/tests/test_prompt_transport_profile.py omega_engine_woland/tests/test_session_acset.py omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py --basetemp .scratch/woland-occurrences/pytest-operator
cargo test --offline --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_woland --lib primary_gates -j 1 --target-dir .scratch/woland-formal-rust
cargo test --offline --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_woland --test witness_parity --test source_contract_intergates -j 1 --target-dir .scratch/woland-formal-rust
Push-Location lean4
& "$env:USERPROFILE/.elan/bin/elan.exe" run leanprover/lean4:v4.34.0 lake build WolandFormal
Pop-Location
```

The demonstration's compiled current host SHA-256 was
`05380c9768c29a79c0d1f1c51407b7db371706484cb30e6e2b9da05fb5b60158`.
The immutable earlier workflow/reporting host remained separate, preserving
historical replay. A fresh local compilation can have a different build digest;
pin its actual bytes rather than copying this observation as a new attestation.
