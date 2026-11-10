# Actual final Woland run, 2026-10-15

The current IDE executed the mandatory Retinue perspectives through the shared
backend, PFP reply checking and Rust operation validation. These perspectives
were supplied by one worker, not 22 independent reviewers. The root, kernel and
provider workers separately contributed implementation and focused reviews.

The original checker returned exit 1, `BOUNDED_PILOT_NOT_COMPLETED`. The required
provider continuation was unavailable after the separate campaign's ambiguous
transport failure. The candidate stayed intact while the existing partial-run
path performed AutoP/auto-learn, digestion and native storage. Learning does not
accept the original task. See `summary.json` for the actual terminal, role
coverage and remaining native diagnostic obligations.

`run.zip` preserves exact state, PFP replies, host observations, original checker
source/output and native readbacks. Member hashes and the archive hash are in
`summary.json`. It excludes runtime binaries, credentials and caches. The earlier
deleted partial run was not reconstructed. The captured source precedes the
subsequent merge from remote main; it is historical evidence for those exact
candidate hashes, not a fresh check of later edits.

## Commands used

These commands were run from the repository root. Paths are intentionally the
original local execution paths. For a new run, use a new state directory and
rebind the current checker, source and independently copied native binary.

```powershell
$v = '.scratch/oewas012/venv/Scripts/python.exe'
$f = '.scratch/oewas012/woland-final'
$env:PYTHONPATH = '.'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TMP = (Resolve-Path .scratch/oewas012).Path
$env:TEMP = $env:TMP
$env:OMEGA_SYMBOL_GAME_HOST = (Resolve-Path .scratch/oewas012/oewas012-native.exe).Path

& $v -B -m omega_engine_woland.entrypoints.cli teamwork start `
  --state "$f/state.json" `
  --objective 'Verify and integrate OEWAS-012 I0-I4, all 22 Retinue operation bindings, practical learned-detector regulation and the bounded P0-P4 Anthropic pilot under one two-dollar cap. Preserve historical v1 bytes and the external MUB exact-count ownership. Recheck actual current source, retain dissent, and finish AutoP learning without frameworks or concurrency.' `
  --run-id oewas012-final-bound-retinue `
  --checker-id oewas012-completion-v2 `
  --checker-source .scratch/oewas012/check_completion.py `
  --native-host .scratch/oewas012/oewas012-native.exe `
  --native-host-sha256 1e83ec688a73cea703b945c27b25d7cd51d9a267bc1ff8a7c24de206e9819364 `
  --check-command $v -B .scratch/oewas012/check_completion.py

& $v -B -m omega_engine_woland.entrypoints.cli teamwork check --state "$f/state.json"
& $v -B -m omega_engine_woland.entrypoints.cli teamwork native-gates --state "$f/state.json"
```

Each returned PFP system/user/schema was read before composing its role reply.
For each role the existing `teamwork submit --state ... --raw-reply ... --worker
...` command checked the exact envelope; Jeremy additionally used `--host-result`
for actual candidate file hashes. `drive.py` and `session.py` in the archive retain
this sequential CLI transport. They do not fabricate answers or mutate workflow
state. Numbered stdout/reply files preserve the exact order and bindings.

After the 21 pre-learning roles:

```powershell
& $v -B -m omega_engine_woland.entrypoints.cli teamwork native-gates --state "$f/state.json"
& $v -B -m omega_engine_woland.entrypoints.cli teamwork recheck --state "$f/state.json" --timeout-seconds 300
& $v -B -m omega_engine_woland.entrypoints.cli teamwork tool-unavailable `
  --state "$f/state.json" --tool anthropic-campaign-continuation `
  --reason 'Original checker returned BOUNDED_PILOT_NOT_COMPLETED. Campaign first send is TRANSPORT_ERROR with unknown outcome and a retained 1014-micro-USD reservation. Required provider continuation is unavailable until accounting is reconciled; no retries or fallback are authorized. Preserve the current implementation candidate and perform bounded partial learning.'
& $v -B -m omega_engine_woland.entrypoints.cli teamwork ddc-store --state "$f/state.json" --output-dir "$f/ddc"
# Submit the exact bound Bezdomny reply, after reading the native DDC context.
& $v -B -m omega_engine_woland.entrypoints.cli teamwork digest --state "$f/state.json" --output-dir "$f/ddc"
& $v -B -m omega_engine_woland.entrypoints.cli teamwork native-gates --state "$f/state.json"
& $v -B -m omega_engine_woland.entrypoints.cli teamwork ddc-complete --state "$f/state.json" --output-dir "$f/ddc"
```

The first DDC storage attempt encountered a Windows temporary-directory ACL
refusal. The actual refusal is retained; repeating host storage with the explicit
workspace `TMP`/`TEMP` above succeeded. No provider request was retried. Remaining
host finish commands and their actual outcomes are preserved in numbered files.

## Learning applied

The candidate already contains independently checked detector regulation,
source-bound compact prompt expansion, honest skill execution records, checked
Retinue operation bindings and raw provider replay validation. Existing typed
check-sensitivity and stale-task-antibody guidance carries the practical lessons.
Bezdomny recorded a justified no-additional-change result: more code or guidance
cannot settle an ambiguous external send. This IDE run's host-observed billing is
`UNOBSERVED` with zero provider attempts; the separate paid campaign is not
misrepresented as IDE accounting.
