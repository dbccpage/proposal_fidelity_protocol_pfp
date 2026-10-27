# Demo 004: executable challenge entrypoints

AuthorityEffect: None. The shared campaign uses the retained participant tasks,
source-bound cases and their existing judges. It does not replace the challenges
with stored-answer comparisons.

Run one finite host control, with no provider call or new run directory:

```powershell
python -m education.pilots.challenge_suite --check --challenge C039
```

Grade a supplied SPK-001 JSON envelope against the same case:

```powershell
python -m education.pilots.challenge_suite --check --challenge C039 --reply candidate.json
```

The second command labels its input caller-supplied, unauthenticated evidence.
Both commands exit nonzero on rejection or unavailable infrastructure. Select
another case with `--ordinal 1`, or another partition with `--split held_out`.

Run a fresh bounded OpenRouter trial using existing credentials:

```powershell
python -m education.pilots.challenge_suite --live deepseek/deepseek-v3.2 --challenge C039 --arm typed_witness --output new-live-run
```

The existing adapter checks current model availability/pricing, refuses an
existing output directory and reserves at most USD 0.05 across two stages. It
stops on acceptance, unavailable verification or exhaustion. It has no hidden
retry or model fallback. Offline replay uses `--replay-live new-live-run` with
matching source bytes and performs zero provider calls.

`UnifiedPfpDemoRunner.run_demo(DemoSpec(id="demo_004", ...))` now executes one
finite control instead of returning three unconditional PASS results. Its
`expectations` may set `challenge_id` (default `C039`), `split` (default
`development`) and `ordinal` (default `"0"`). `FIXTURE_VERIFIED` applies only to
that selected case; it is not a whole-suite or neural success.

## Seed catalog and bounded experiments

Use the stable seed IDs in [`seeds.yaml`](../matrix/seeds.yaml). Its historical
`folder` labels do not identify directories in the current estate.

```powershell
python -m pfp.infrastructure.pilot_runner --check-seeds
python -m pfp.infrastructure.pilot_runner --seed-id DEMO_01
```

Seed preparation preserves the complete prompt, including its trailing newline,
under the existing SPK-001 template. All 74 digests are checked; the 50 MSS-N
entries must also match the existing Python catalog. Preparation does not run
their declared modes or eight stages, and does not supply a universal seed
grader. Seed-specific executable checks remain necessary.

The fixed grid and generator are retired. Start with one task, a typed
prompt/response contract and an independent check. Collate its result and cost,
then choose further runs to answer an improvement or failure-discovery question.
The [shared PFP guide](../../../pfp/documentation/pfp_seed_execution.md)
explains replay and extensions without requiring a combinatorial campaign.

The [existing integration evidence](../evidence/demo004_pfp_learning/README.md)
records historical failures and scoped successes. Mechanism interventions that
require unavailable model hooks, unexecuted challenge cases and held-out claims
remain open.
