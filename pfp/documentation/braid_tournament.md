# Bounded braid tournament

AuthorityEffect: None.

The current runner is `omega_engine_pfp.infrastructure.braid_tournament`. It
derives the original tournament's schedules, rational noise construction and
round order from the retained
[Paper 022 source](../../omega_engine_education/documentation/004_oepfp/papers/omega_engine_symbol_game/022_pfp_frontier_research/code/adaptive_braid_tournament_demo.py).
The paper deposit, its old scripts, manifests and recorded results remain
unchanged. Use the current command below for new runs; the historical scripts
retain their original dependencies and fallback behavior.

## Try one deterministic round

```powershell
python -m omega_engine_pfp.entrypoints.braid_tournament --output-dir braid-one --noise-budgets 1/100 --max-rounds 1
```

`--output-dir` must be new. The command writes `tournament.json` containing
the results and execution report. Offline mode uses the original deterministic
strategies and makes zero provider calls. Historical model names are configuration
labels only; an offline result does not evaluate those models. One selected
noise value is a smoke check, not evidence of model performance or robustness
across noise regimes.

Without narrowing flags, the original two-qubit configuration, four rational
noise budgets (`1/100`, `1/50`, `1/20`, `1/10`) and tolerance multiplier two remain.
Exact fractions are preserved. The CLI runs sequentially.

## Explicit live selection

For an authorized OpenRouter attempt, select the model and allowance explicitly:

```powershell
python -m omega_engine_pfp.entrypoints.braid_tournament --output-dir braid-live-one --live --models YOUR_MODEL_ID --noise-budgets 1/100 --max-rounds 1 --max-output-tokens 1024 --max-provider-calls 1 --max-estimated-cost-microusd 10000
```

Replace `YOUR_MODEL_ID` with an intended supported model. The existing provider
factory resolves credentials and verifies current pricing and capabilities.
Optional `--env-file` selects an existing credential file. The command does
not default live execution to the paper's historical model list. The original
1024-token setting now includes PFP's bound envelope; changing it changes the
experimental setting.

The runner prepares each public request through PFP, reserves using the existing
Providers ledger, checks the actual returned binding and answer shape, then
submits the accepted schedule to the original referee. All selected models and
rounds share one continuing allowance. Missing policy, provider failures,
malformed replies and unknown costs stay visible. Live failure never selects a
deterministic replacement. Uncertain accounting stops subsequent dispatch;
there is no automatic retry or new budget. The estimated allowance is not an
enforceable maximum vendor bill.

The report retains provider wire bytes, PFP checks, refusals and observed costs
separately from successful finite judgments. Unknown cost remains unknown.
Evidence grades follow actual judged observations: a configured live model with
no checked result yields `NO_REFEREE_RESULTS`, and a partial mixed run cannot
relabel deterministic results as model evidence. Read the completed counts and
stop reason alongside the original leaderboard.
Existing output directories refuse before gateway construction and are not
overwritten. The original immutable result dataclasses and `run_sweep` return
type remain available to Python callers; `tournament.report` carries current
execution observations.

## What the result establishes

The independent referee is the unchanged Atlas Majorana implementation. Its two
source files are included as package data, so this command can run from an
installed distribution outside the repository. Acceptance checks the selected
finite matrix conditions and noise threshold. It does not establish target-gate
equivalence, physical device performance, general model reasoning or superiority
over another model. A SHA-256 digest is a content check, not a signature.

Validation uses deterministic and synthetic-provider controls plus a bounded
offline command. No fresh paid model evidence is claimed for this migration.
The original empirical protocol, broader native parity and whole-estate
PFP/Woland integration remain open under OEPFP-009.
