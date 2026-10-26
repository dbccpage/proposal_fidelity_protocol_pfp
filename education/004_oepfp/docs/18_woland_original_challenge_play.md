---
documentation_contract: symbol-game-documentation/v1
title: "Woland, PFP and original challenge judges"
kind: runbook
audience: [players, engineers, coding-agents]
status: active
claim_status: source-grounded
authority_effect: "None"
last_verified: 2026-10-20
verification_scope: commands, flags, pilot paths and named receipt files checked at c419cc6beb; no run or replay
source_paths:
  - omega_engine_woland/infrastructure/challenge_play.py
  - omega_engine_pfp/infrastructure/challenge_execution.py
  - omega_engine_pfp/infrastructure/task_turn.py
  - omega_engine_pfp/infrastructure/formal_matrix.py
  - omega_engine_pfp/infrastructure/synthesis_matrix.py
  - omega_engine_woland/use_cases/teamwork.py
---

# Woland, PFP and original challenge judges

Use one existing Woland build → original host review → bounded repair workflow.
Both the current IDE session and OpenRouter use the same PFP task envelope and
original challenge judges. This route checks a proposed finite witness; it does
not execute model-generated code or finish the original scientific experiment.

The adapter selects C001, C005 and C011–C030. C001 uses its original generated
public prose, with distractors intact; parsed graphs and labelled spans stay
host-side. C002–C004 and C006–C010 still need their full original protocols.
An unavailable checker is an infrastructure outcome, not accepted mathematics.

## Play from the current IDE

From the repository root, prepare a public development case:

```powershell
python -m omega_engine_woland.entrypoints.cli challenge start --challenge C005 --split development --ordinal 0 --state "$env:TEMP/c005-ide.json"
```

Give the current assistant the returned `pfp_turn.system`, `pfp_turn.user` and
`response_schema`. Ask it to solve the public task and save its actual reply as
UTF-8 JSON. The response carries the supplied `task_id`, `attempt_id`,
`input_sha256` and original task witness in `answer`. Do not copy host answers or
replace these bindings after generation.

```powershell
python -m omega_engine_woland.entrypoints.cli challenge submit --state "$env:TEMP/c005-ide.json" --raw-reply "$env:TEMP/c005-reply.json"
python -m omega_engine_woland.entrypoints.cli challenge next --state "$env:TEMP/c005-ide.json"
python -m omega_engine_woland.entrypoints.cli challenge replay --state "$env:TEMP/c005-ide.json"
```

`submit` immediately runs the original host judge. If repair is pending, answer
the next prepared turn; the original run and repair allowance continue. Current
IDE billing is unavailable, represented by `cost_usd: null`, not measured zero.

From `/woland`, request the same operation:

> Use the shared challenge backend to attempt C005 development case 0 through
> PFP in this IDE. Submit the actual reply to the original judge, perform at most
> one repair, and retain the original scientific requirements as open.

Learning is on by default. At a successful candidate check, the next `learn`
turn asks the IDE to run `/auto-oe-autop` once; its finish invokes `/auto-learn`
once. Apply a supported correction to the existing owner or give a justified
no-change reason. An OpenRouter learning turn proposes lessons and cannot claim
installed edits. Use `--no-learn-after-run` only when an enclosing Woland run
owns this finish; the bounded attempts below used that arrangement.

## Installed use outside the checkout

With the built wheel and its declared dependencies installed, the same commands
work from an ordinary writable directory. For example, prepare the original
C054 linear-system task without credentials or a model call:

```powershell
python -m omega_engine_woland.entrypoints.cli challenge start --challenge C054 --split development --ordinal 0 --state "$env:TEMP/c054-installed-ide.json"
python -m omega_engine_pfp.entrypoints.cli.pfp --help
```

C051-C055 and C059 retain their canonical `omega_engine_pfp.tests.pilots`
namespace. (Path check 2026-10-20: at pin `c419cc6beb` that package is not
present; the six pilot directories are under `omega_engine_woland/tests/pilots/`,
for example `c054_exact_linear_systems/`. Wheel contents were not rechecked.) The wheel includes their active scripts, original tasks, cases,
reference solvers and judges; the surrounding test and historical-result trees
are not required to prepare a turn. Current readers resolve their retained
Education catalog paths to this owner and still require the original case hash.
They do not rewrite old catalog rows, results or checker commitments.

The installed probe prepares C001, C005, C011, C041, C051-C055 and C059 with
their actual source-bound PFP briefs. It also checks current v1.0.3 resources (v1.0.4 at the 2026-10-20 pin:
`installed_package_probe.py` line 51 asserts `prompts.VERSION == "1.0.4"`),
public task/teamwork CLI bindings, malformed replies and historical missing or
changed byte refusals, with network blocked. Preparation is not a completed
model attempt. One C054 host fixture also passes both original judges in an
installed subprocess, and an empty witness is rejected by both. This is host
plumbing evidence, not model performance. C041 still needs its declared Lean toolchain for judging; native
operations need an explicitly available binary. Historical relational-spacetime
campaign APIs intentionally return `REPOSITORY_CONTEXT_REQUIRED` without Git
context, rather than issuing a new historical result from current resources.

## Play through OpenRouter

This uses the existing credentials and accounted gateway. Choose a new state
path for each new run; replay never dispatches a model.

```powershell
python -m omega_engine_woland.entrypoints.cli challenge run --challenge C011 --split development --ordinal 0 --model openai/gpt-4o-mini --max-provider-calls 2 --max-repairs 1 --max-output-tokens 3000 --max-estimated-cost-microusd 5000 --state "$env:TEMP/c011-openrouter.json"
python -m omega_engine_woland.entrypoints.cli challenge replay --state "$env:TEMP/c011-openrouter.json"
```

All model steps share one reservation/accounting gateway. The cap also applies
to a requested learning turn; budget exhaustion leaves the workflow open.
Unknown cost, over-estimate and unsettled accounting stop before judging or
retrying. The CLI does not resume paid execution by silently creating a new
budget. `--env-file` selects an existing credential file if needed.

## Bounded formal-math and synthesis matrices

The original C043-C050, C056-C058 and C060 task scripts retain their Education judges
and public inputs. Their shared execution lives in PFP's `formal_matrix` and
`synthesis_matrix` modules. These scripts are separate from the C001-C030
challenge selector above; they do not extend that selector's scientific coverage.

Inspect the options without credentials or a provider call:

```powershell
py -3.12 -m omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.run_c043_matrix --help
py -3.12 -m omega_engine_pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.run_c056_matrix --help
py -3.12 -m omega_engine_pfp.tests.demo_004.f_program_synthesis.c060_self_verifying_checker_synthesis.run_c060_matrix --help
```

For an explicitly authorized OpenRouter attempt, select a declared model, a
small case prefix and a continuing call/cost limit. These examples request one
case and at most one provider call; the estimated allowance is 10,000 microusd
($0.01), not a provider-enforced billing maximum. They are usage examples,
not new measured model results:

```powershell
py -3.12 -m omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.run_c043_matrix --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-provider-calls 1 --max-estimated-cost-microusd 10000 --max-output-tokens 2048
py -3.12 -m omega_engine_pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.run_c056_matrix --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-provider-calls 1 --max-estimated-cost-microusd 10000 --max-output-tokens 2048 --output-dir "$env:TEMP/c056-selected-run"
```

Use a new output directory for synthesis. Formal runs print their newly created
`_ic/darpa/symbol_game/matrix_runs/<challenge>/...` path. Read that run's existing
`run_record.json`, or synthesis's `summary.json`, for actual attempts and outcomes.
An explicit output-token override changes this exploratory selection; it does
not complete the original full-profile protocol. The original catalogs and
historical results remain unchanged. Missing pricing or unsettled accounting
retains its refusal instead of selecting another model or resetting the budget.

From `/woland`, ask the IDE to run the selected command through the existing PFP
gateway, collate its actual output and apply useful learning with the normal
outer AutoP finish. Without explicit provider/model/spend authorization, limit
the task to `--help` or deterministic offline controls. Do not reconstruct model
replies or use the reference solver as evidence of model performance.

C060 now uses that same bounded synthesis helper, preserving its ten original
certificate cases, prompt invariants and both original judges. Its legacy
`query_openrouter` callable requires an injected accounted gateway; credentials
alone no longer dispatch. Only the checked PFP answer reaches the judges.
Provider reasoning is never substituted for an absent answer, and unknown
accounting stops the remaining cases/models. New runs use a new output directory;
the retained `empirical_results` files are not overwritten.

For example, after authorizing the provider/model and estimated allowance:

```powershell
python -m omega_engine_pfp.tests.demo_004.f_program_synthesis.c060_self_verifying_checker_synthesis.run_c060_matrix --output-dir "$env:TEMP/c060-selected-run" --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-provider-calls 1 --max-estimated-cost-microusd 10000 --max-output-tokens 2048
```

These twelve matrix commands discover the actual package directories, so their
module and direct-script `--help` work from an installed wheel without a repository
`pyproject.toml`. This verifies command availability. C060's per-case verdict
experiment does not by itself synthesize or validate a general checker program.

## C005 schema and logit-bias experiments

TEST-001 and TEST-002 use the existing PFP/accounted gateway. TEST-001's original
consistency or cycle-repair schema is nested under the bound reply's `answer`;
the shared adapter validates that schema before exposing an answer to the
original host checker. A generic object envelope cannot replace this experiment's
declared schema. TEST-002 retains the supplied token-ID bias map without adding
a provider JSON-schema constraint, which would change the comparison.

Both runners retain their original prompt text, case generator, exact checkers,
temperature zero and 96-token output default. The PFP envelope consumes part of
that output allowance. A larger explicit allowance is a new experimental setting;
neither setting reproduces the historical transport unchanged. The legacy
`concurrency` argument is retained for callers, with actual execution serial and
reported as one worker. One gateway allowance continues across the selected cases.

Inspect current commands without importing an SDK, reading credentials or sending:

```powershell
python -m omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_001_runner --help
python -m omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_002_runner --help
```

Exercise two host fixtures without a model call:

```powershell
python -m omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_001_runner --dry-run --max-cases 2 --output-dir "$env:TEMP/c005-schema-fixture"
```

For a separately authorized provider check, use a new output directory and an
explicit model, call allowance and estimated financial policy:

```powershell
python -m omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_001_runner --model nousresearch/hermes-3-llama-3.1-405b --max-cases 2 --max-output-tokens 96 --max-provider-calls 2 --max-estimated-cost-microusd 10000 --output-dir "$env:TEMP/c005-schema-live"
```

Live execution requires an accounted gateway or explicit bounded gateway policy.
A raw OpenAI client cannot dispatch through the retained case APIs. Output goes
only to a new explicit directory; historical reports and receipts remain intact.
Unreported cost stays unknown, and an ambiguous or unsettled attempt stops later
cases. Dry host fixtures are labelled `HOST_REFERENCE_SELF_CONSISTENCY` and do
not establish model performance or a provider honoring either decoding control.
They report zero provider calls separately from attempted host cases; ambiguous
dispatch leaves the call total unknown. Existing summary cost and latency fields
remain available without inventing missing provider usage.

For TEST-002, supply a tokenizer-specific bias map with provenance, or an explicit
locally available tokenizer. The runner must not download a tokenizer implicitly,
guess token IDs or silently use a map from another model. Recording a tokenizer
identity does not prove model compatibility or that the provider honored bias;
the original control probes remain an experimental obligation.

Paired analysis takes explicit compatible TEST-001 traces. Case identities and
bytes, original public tasks, model, token settings and evidence grade must match.
Duplicates, missing cases or incompatible traces leave analysis unavailable.
Historical matching filenames and a declared hash alone do not authenticate a run.
No fixed parseability percentage or claim of superiority is carried forward.
The three-arm scratchpad and Arm 4 hybrid runners also use this boundary. Their
original arm prompts, schemas, factorization and certificate/canary judges remain.
Run either with a new explicit output directory:

```powershell
python -m omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.benchmark_3arm_scratchpad --dry-run --max-cases 2 --output-dir "$env:TEMP/c005-three-arm-fixture"
python -m omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.benchmark_arm4_hybrid --dry-run --max-cases 2 --output-dir "$env:TEMP/c005-hybrid-fixture"
```

These commands write `master_evaluation_report.json` and `summary.json`. Dry
results are host-reference self-consistency, with no provider calls. For an
authorized hosted run, remove `--dry-run` and supply an explicit `--model`,
`--max-provider-calls` and `--max-estimated-cost-microusd`. The allowance is
shared across every arm and case, and execution is serial. Estimated reservations
do not enforce a provider's maximum bill. Unknown cost or ambiguous dispatch
stops the whole run; retained raw replies and partial arm records remain available.
Paired statistics use only actually completed compatible pairs.

By default the direct arm retains 256 output tokens and the scratchpad,
hieroglyphic and hybrid arms retain 512. `--max-output-tokens` explicitly changes
all arms to that bound; the report records both settings. PFP bindings consume
some output allowance. Python callers may supply accounted `gateways` keyed by
token bound, sharing the same financial scope, or one `gateway` with an explicit
common bound. No argument silently enables a live provider or loads credentials.

The original host judge checks the final certificate and, for Arm 4, the selected
canary residual. It does not validate every scratchpad entry or every claimed
chord computation. The factorized arms receive host-computed tree potentials,
so they are a different task representation with host preprocessing. Schema
acceptance, fixtures and these checks do not establish faithful model reasoning,
antibody activation, provider-honored decoding or a general PFP advantage.

## C017 prompt and immune-transfer experiments

The C017 Arm 5, Arm 6 and paired baseline/immune runners keep their original
prompt builders, five case selections and dual judges. Live calls use the same
accounted PFP boundary as Woland. A malformed or wrongly bound reply cannot reach
the judges, and unknown accounting stops the remaining arms/cases. Reported cost
stays unknown when appropriate, with the known subtotal shown separately.

Inspect the commands without credentials or dispatch:

```powershell
python -m omega_engine_pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.eval_arm5_hybrid --help
python -m omega_engine_pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.eval_arm6_hierarchical_decimation --help
python -m omega_engine_pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer --help
```

Use a fresh output directory for each command. A dry run checks host fixtures
against the original judges and is explicitly labelled as such:

```powershell
python -m omega_engine_pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer --dry-run --case base_01 --output-dir "$env:TEMP/c017-host-fixture"
```

For a separately authorized bounded provider run, choose the model, output limit,
call allowance and estimated cost explicitly:

```powershell
python -m omega_engine_pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer --model meta-llama/llama-3.3-70b-instruct --case base_01 --max-tokens 2000 --max-provider-calls 2 --max-estimated-cost-microusd 10000 --output-dir "$env:TEMP/c017-paired-run"
```

The paired runner shares one allowance between baseline and immune arms. Arm 5
retains its original 6,000-token default and Arm 6 its 4,000-token default; the
existing estimated gateway's smaller supported bound requires an explicit
override. Such a selection is exploratory and does not reproduce those original
settings. The legacy query APIs require an injected accounted gateway for live
use; an API key alone cannot dispatch. Direct dry/injected calls may return an
in-memory report. CLI runs require a new output directory and never overwrite the
historical `results` files.

Host-fixture success, prompt names and typed antibody text do not establish model
performance, immune transfer, a verified scratchpad or the original scientific
protocol. Retained historical reports remain separate observations.

One retained Arm 5 prompt limitation is concrete: its decision procedure labels
the periodic flat branch `FLAT_NONTRIVIAL` without testing for trivial global
holonomies. An all-identity periodic connection is `PURE_GAUGE`, accepted by both
original judges in a host check. This migration preserves that historical prompt
variant; a corrected prompt needs its own comparison and must not relabel the
earlier experiment's results.

## C041 and C042 experimental methods

The Lean C041 and SAT/DRAT C042 experiments retain their original task-specific
formatters and judges. Their selected methods, cases and repair rounds use one
continuing PFP/accounted gateway allowance. A terminal accounting refusal stops
the outer experiment; another method does not receive a fresh budget.

Inspect either command with `--help` first. For an explicitly authorized attempt:

```powershell
py -3.12 -m omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.symbol_game_experiment --model meta-llama/llama-3.1-8b-instruct --method M3_RETRACTION --case-limit 1 --max-provider-calls 3 --max-estimated-cost-microusd 10000 --max-output-tokens 512
py -3.12 -m omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.symbol_game_routing --model meta-llama/llama-3.1-8b-instruct --method M1_LOGITS --case-limit 1 --max-provider-calls 1 --max-estimated-cost-microusd 10000 --max-output-tokens 512
```

C041 keeps M1, M2, M3, M4 and M5; C042 keeps M1 and M3. These are experimental
prompt variants. The historical `LOGITS` and `ATTENTION` names do not establish
tokenizer masks, logit manipulation or model attention hooks. M3 reuses only its
own run/arm's failed candidates and checker diagnostics; a learned warning does
not establish a proof. C041 still requires its real Lean checker for acceptance.
C042 keeps nontrivial acceptance separate from trivial refutations and abstention.

Each new run retains the PFP check and provider response with its outcome.
Unknown cost remains unknown, with a separate known subtotal in C041 summaries.
The original profile limits, historical records and original-protocol obligations
remain distinct from these selected exploratory runs. These commands are usage
examples, not new measured model or kernel results.

## Actual bounded observations, 2026-10-12

| Case and executor | Actual result | Replies and cost | Observed time |
| --- | --- | --- | --- |
| C011 development 0, `openai/gpt-4o-mini` | Both original judges rejected the initial proposal and one repair: invalid refusal code `Vertices list exceeds bound`. Partial; replay reproduced rejection with zero sends. | 2 paid replies; $0.00102360 known cost; no unknown-cost reply. | 9.419 seconds end to end. |
| C005 `pub_cons_01`, `openai/gpt-4o-mini` | Both proposals said `INCONSISTENT` with an empty certificate. Original predicate rejected the verdict on the consistent system. Partial; zero-send replay reproduced rejection. | 2 paid replies; $0.00072585 known cost; no unknown-cost reply. | 12.154 seconds end to end. |
| C005 `pub_cons_01`, current IDE, final build | Public edges yielded potentials `n0=0, n1=4, n2=4, n3=-5`; original predicate accepted. Zero-send replay reproduced acceptance. | 1 IDE submission; 0 provider replies; IDE cost unavailable. | 0.322 seconds measured host judging only; IDE end-to-end time unmeasured. |
| C001 `c001_verdict_1000`, `qwen/qwen-2.5-7b-instruct` | Initial proposal and one repair failed the original equation check. Partial; zero-send replay reproduced rejection. This is hosted finite-witness checking, not C001's local neural experiment. | 2 paid replies; $0.00134730 known cost; no unknown-cost reply. | 5.175 seconds instrumented provider/judge intervals; end-to-end time unmeasured. |
| C001 `c001_verdict_1000`, current IDE | Solved from the original distractor prose; potential `A=0, B=-5404, C=-580, D=-1245, E=-5997, F=638, G=-4313, H=1732` passed the original Python witness checker. Replay reproduced acceptance with zero sends. | 1 IDE submission; IDE cost unavailable. | 0.357 seconds host judging only; IDE end-to-end time unmeasured. |
| C001 `c001_verdict_1001`, current IDE after syncing merged main | From the public prose, cycle `A→B→F→G→A` has signed sum 5. The original Python checker accepted this contradiction witness; zero-send replay reproduced acceptance. | 1 IDE submission; IDE cost unavailable. | 0.457 seconds host judging only; IDE end-to-end time unmeasured. |

The following sequential batch used `openai/gpt-4o-mini`, public development
ordinal 0, at most two calls/one repair, 3,000 output tokens and a 5,000-microusd
estimated cap per problem. These are actual attempts, not a hidden-set campaign.
All nineteen failed; every original captured state replayed with zero sends
before checker repairs. The source revision was
`5399938449736116ad45eb547b10fb1feaad8bc7`.

| Problem / actual case | Final failure | Paid replies | Known USD | End-to-end seconds |
| --- | --- | --- | --- | --- |
| C012 / `case_01_tree_path_p4` | SCOPE | 2 | 0.00119460 | 18.494 |
| C013 / `case_base_01` | CHECKER | 1 | 0.00038325 | 5.826 |
| C014 / `case_base_01` | SCOPE | 2 | 0.00105555 | 12.808 |
| C015 / `base_01` | CERTIFICATE | 2 | 0.00141975 | 14.833 |
| C016 / `base_01_torus_vs_wedge_3x3` | CHECKER | 1 | 0.00050805 | 11.071 |
| C017 / `base_01_s3` | SCOPE | 2 | 0.00079020 | 19.610 |
| C018 / `base_balanced_tree_01` | SCOPE | 2 | 0.00061095 | 15.942 |
| C019 / `base_q_extends_01` | SCOPE | 2 | 0.00062970 | 22.313 |
| C020 / `c020_base_01_col` | CERTIFICATE | 2 | 0.00082635 | 14.037 |
| C021 / `case_01` | SCOPE | 2 | 0.00108690 | 12.512 |
| C022 / `c022_base_01` | SCOPE | 2 | 0.00081900 | 11.452 |
| C023 / `c023_base_01` | SCOPE | 2 | 0.00089535 | 10.144 |
| C024 / `item_0` | CERTIFICATE | 2 | 0.00093345 | 10.953 |
| C025 / `base_03_d4_k5` | CERTIFICATE | 2 | 0.00064020 | 10.424 |
| C026 / `base_02_hardcore_c4` | CERTIFICATE | 2 | 0.00081075 | 10.894 |
| C027 / `base_02_peres_33` | TASK_ENVELOPE | 2 | 0.00072825 | 11.262 |
| C028 / `c028_base_04_jw_3mode_chain` | CERTIFICATE | 2 | 0.00061155 | 11.406 |
| C029 / `c029_base_02_rot_d3_sub1` | TASK_ENVELOPE | 2 | 0.00059205 | 9.948 |
| C030 / `c030_base_01_chain_3` | SCOPE | 2 | 0.00097020 | 8.679 |

Batch total: 36 paid replies, $0.01550610, 242.609 seconds end to end, no unknown
cost. Including the C001/C005/C011 bouts above: **42 paid replies, $0.01860285**.
IDE billing remains unavailable. Failures were retained without repeated tuning.
The [C006 session collation](19_bounded_mechanism_sessions.md#actual-bounded-runs-2026-10-12)
adds 45 paid replies/$0.01680190 and one accepted two-turn IDE session. The
combined known subtotal is **87 paid replies, $0.03540475**; unknown-cost replies
remain zero. C006's paid sessions exhausted fuel; their failures remain visible.
Raw captures remain outside the repository. Earlier source bytes are retained
there or at the named Git revision. Changed checker/source bindings refuse old
replay; a fresh zero-send recheck is labelled separately, never repinned history.
The pre-sync C001 captures bind source preserved at `b65f95aca`; after merging
the upstream reply-checker change, a fresh case/turn was used for the final IDE
exercise instead of rewriting those bindings.
There is no matched baseline and no claim of speed superiority, general
effectiveness or completion of all thirty original problems.

Arithmetic check of the totals above (recomputed 2026-10-20 from the table rows; no capture was replayed):

| Quantity | Rows | Sum |
| --- | --- | --- |
| Batch paid replies | 17 problems with 2 replies, C013 and C016 with 1 | 17 x 2 + 2 = 36 |
| Batch known USD | 19 rows | 0.01550610 |
| Batch seconds | 19 rows | 242.608 (the stated 242.609 differs by 0.001, consistent with rounding of the per-row values) |
| Three earlier paid bouts | C011 0.00102360 + C005 0.00072585 + C001 0.00134730 | 6 replies, 0.00309675 |
| Batch plus bouts | 36 + 6; 0.01550610 + 0.00309675 | 42 replies, 0.01860285 |
| Plus C006 sessions | 42 + 45; 0.01860285 + 0.01680190 | 87 replies, 0.03540475 |


`provider_replies` counts received OpenRouter replies; `ide_submissions` counts
actual IDE submissions. `known_cost_usd` is a known subtotal, accompanied by
`unknown_cost_replies`. `observed_elapsed_seconds` sums instrumented provider and
judge intervals and excludes human/IDE preparation time.

## Repairs learned from the implementation

| Concrete obstruction | Existing owner corrected |
| --- | --- |
| C023 host imported a nonexistent solver module; C024 passed its wrapper to judges expecting the enclosed input. | Execution adapter calls the actual synthesis solver and unwraps only C024's declared input envelope. |
| C027's second checker accepted a false uncolourability refutation and a fabricated parity context. | Independent checker validates its own contexts and checks non-parity refutations by independent enumeration up to 20 merged rays; larger such instances are explicitly unavailable. |
| A changed rejected review could replay as completed. | Replay compares the recomputed deterministic review, decision and candidate/checker bindings, excluding elapsed time. Editable state is not authentication. |
| Different failed candidates stopped despite remaining repair allowance. | Proposals populate the existing artifact progress signal with candidate digests. |
| Learning diagnostics could make the next repair prompt unrenderable. | Retain diagnostics locally, map participant feedback to the existing answer-free repair rules. |
| Legacy research dispatch and autonomous learning could choose a different provider route. | Retire unsupported dispatch before transport construction; prepare/check live learning through PFP and retain original raw bytes. |
| C001 had no shared catalog rows; returning the parsed graph would bypass its distractor task. | Select original public generator rows, bind source/case bytes, expose only original prose and validate its original witness variants. |
| Original task text buried the current finite assignment; an extra `input.case` wrapper changed its expected shape. | State the current assignment explicitly and render the original public case directly. This prompt change has not established an accuracy gain. |
| C013 hashed a nested-list vertex in an invalid refusal; C016 parsed symbolic placeholder coefficients outside rejection boundaries. | Both C013 judges validate witness vertices before hashing. C016 rejects malformed basis/cycle/primitive/index values at parsing boundaries; internal mathematical defects still propagate. Exact retained replies now reject normally in a fresh zero-send recheck. |
| Research stage routing retired only two unsupported providers. | Permit explicit fixtures and OpenRouter; refuse every other proposal provider before transport. IDE work uses prepare/submit. |
| A repeated zero-defect CUT could be recorded as obstructed AM-4. | The consumed scratch-space adapter requires positive host defect for a stationary-repeat observation; changed board/state/candidate and zero-defect controls remain benign. |
| Wrapping an old campaign in PFP accidentally added provider-enforced JSON decoding. | Retain original decoding settings and inner judge/repair rules; add only the outer binding. A negative control confirms malformed inner SPK still receives its original ENVELOPE feedback. Changing decoding is an explicit experiment, not a transport migration. |
| An escaped lone surrogate passed JSON shape checking but crashed capture persistence. | Current challenge capture JSON escapes strings losslessly, retains exact vendor bytes and records a replayable `INVALID_COMPLETION_UNICODE` refusal. Ordinary valid Unicode remains supported; never re-encode historical captures to apply this lesson. |

## Mechanism sessions and remaining protocols

`omega_engine_pfp.infrastructure.mechanism_scratch_space` exposes
`HostScratchLedger.from_host`, `prepare_scratch_cut_turn` and
`check_scratch_cut_turn`. The prepared PFP brief contains copied host observations
and the last two turns, bound to the original C006 protocol, board, state, task
and attempt. Submit the actual raw reply; provide the existing independent host
judge for mathematical admission. Without a judge, the answer remains
UNVERIFIED. AM-4 is an observation, not an activated antibody or session terminal.
No solution cochain or worked protocol answer is copied into the brief.

The [bounded mechanism-session runbook](19_bounded_mechanism_sessions.md) adds
the complete C006 ASSERT/CUT/LIFT_REQUEST/VERIFY loop through that existing
boundary, native weighted admission, submitted-potential checks, bounded fuel,
detector suspension and replay. It also documents the items below.

> **Evidence status (2026-10-20, pin `c419cc6beb`).** None of the nine receipt files named in this list is tracked in the repository: `c001_distractor_cochain_p_star_receipt.json`, `p_star_verified_guard_receipt.json`, `fable_5_1_guard_theorem_receipt.json`, `c004_40case_hidden_p_star_receipt.json`, `c005_dichotomic_fredholm_p_star_receipt.json`, `c006_overlap_basis_p_star_receipt.json`, `c006_higher_betti_p_star_receipt.json`, `c006_60board_hidden_p_star_receipt.json` and `b_cohomology_p_star_receipt.json`. `extended_checkers.py` is not tracked either. The success ratios below (12/12, 2/2, 38/40, 6/8, 5/5, 60/60, 8/60, 10/10) are therefore unverified historical statements until their receipts and raw replies are retained and replayed. Several ratios are small conditional denominators (for example 2/2 and 8/8 after abstentions); read them as counts, not rates.

- C001's distractor-filtered cochain and cohomological syndrome `P*` factorization (`C001-S1`, `c001_distractor_cochain_p_star_receipt.json`) with path-integrated $B_T^{-1}$ tree guard diagnostics across 12 public and poisoned cases (`12/12` solved vs. `1/12` un-staged, `0` false `SOLVED` verdicts),
- C004's BPE prefix-automaton integer-slot mask (`gbnf_slots=k`), Coloured Operad slot-grafting ($\circ_i$), 4-slot index-value binding, `C004-S5` verified Stage-1 guard retry (`p_star_verified_guard_receipt.json` + `fable_5_1_guard_theorem_receipt.json`), and the held-out 40-case hidden ladder (`C004-S6`, $k \in \{3, \dots, 12\}$, `c004_40case_hidden_p_star_receipt.json`, where `qwen/qwen-2.5-7b-instruct` achieved `0/40` optimal un-staged vs. `2/2` (`100%`) conditional Stage-2 $\ell_1$-optimality and `38/40` `NullTree` abstentions under $G_{\text{complete}}$, with `3` empirical Local Green / Global Red witnesses isolated on Attempt 1),
- C005's dichotomic Fredholm-alternative `P*` guarded separation (`C005-S1`, `c005_dichotomic_fredholm_p_star_receipt.json`) across `pub_cons_01`..`pub_cons_08` (`6/8` solved vs. `3/8` un-staged, `0` admitted false verdicts),
- C006's multi-cycle overlap-basis `P*` repair on $K_4$ (`C006-S6`, `c006_overlap_basis_p_star_receipt.json`), two-stage tree-then-chord `P*` factorization across higher-Betti graphs $b_1 \in \{4, 5, 6, 7\}$ ($K_{3,3}, Q_3, K_5, \text{Petersen}, W_7$; `C006-S7`, `c006_higher_betti_p_star_receipt.json`, `5/5` solved vs. `0/5` un-staged on `openai/gpt-4o-mini`), and the held-out 60-board hidden campaign across $b_1 \in \{3, \dots, 8\}$ (`C006-S8`, `c006_60board_hidden_p_star_receipt.json`, `60/60` `NO_LLM` exact baseline, `0/60` un-staged vs. `8/60` (`8/8 = 100.0%` conditional Stage-2 precision) solved and `208` downstream turns saved via `NullTree` on `qwen/qwen-2.5-7b-instruct`), and
- C011–C020's independent exact certificate checker (`certificate_checker.py`, `extended_checkers.py`, verified across all 328 JSON cases) and multi-stage `P*` certificate-guarded trial (`B-COH-S1`, `b_cohomology_p_star_receipt.json`, catching `10/10` false `SOLVED` claims from `qwen/qwen-2.5-7b-instruct` on Attempt 1 and abstaining via `NullTree` with `0` false `SOLVED` admissions).
These usable components and bounded paired trials do not close the remaining multi-seed or local 7B GPU campaigns.

All thirty problem identities remain in scope. C001/C005/C011–C030 have the
finite CLI route and actual attempts above; their full scientific protocols
remain open. The other eight have these concrete implementation prerequisites:

| Problem | Required original work still open |
| --- | --- |
| C002 | Actual eager attention-column bias and exact tokenizer offsets now have local null/change/undo controls. Original public delta/layer selection, hidden/random controls and specified 7B/8B models remain open. |
| C003 | Real pre-output-projection head capture, clean/corrupt patching and scaling are exercised locally. Original attribution ranking, selection and replicated hidden comparison remain open. |
| C004 | Fixed integer-slot grammar, BPE prefix-automaton GBNF slot mask, bounded 8-case `C004-S1`..`C004-S5` `P*` ablations, and the 40-case held-out hidden `C004-S6` campaign (`c004_40case_hidden_p_star_receipt.json` on local `0.5B` and OpenRouter `qwen/qwen-2.5-7b-instruct`) are recorded. Dedicated >16 GB VRAM local 7B GPU execution and multi-seed replications remain open. |
| C006 | Original session driver, native/independent admission, `C006-S6` ($K_4, b_1=3$), `C006-S7` ($b_1 \in \{4..7\}$), and the 60-board held-out hidden `C006-S8` campaign (`c006_60board_hidden_p_star_receipt.json` across $b_1 \in \{3..8\}$ on local `0.5B` anchor boards and OpenRouter `qwen/qwen-2.5-7b-instruct`) are recorded. Explicit `c006.panels.v2` relabel/poison multi-seed campaigns and dedicated local 7B GPU execution remain open. |
| C007 | Six-stage 30–48-turn text sessions, immutable IDs, false-restatement refusal, retention, final-union checking and zero-send raw replay are implemented. Original-sized task panels and real finite KV probes are available; the matched long-horizon KV campaign remains open. |
| C008 | Actual residual capture/addition and null/negated/undo mechanics exist. Target-conditioned calibration was found during review and excluded from blind results. Task-independent calibration replaces it; original normalized public selection, native parity and replication remain open. |
| C009 | Exact original route pins/drop rules and source-binding checks exist. Linked C061 chemistry and C071 economics source owners remain absent; no substitute task closes the five-anchor packet. |
| C010 | Exact unbiased Coverage@k, retained duplicate draws, distinct sample identities and raw two-judge rescoring are implemented. Original whole-session/hybrid campaign and missing C061 pool remain open. |

The explicit local feasibility runtime now uses CPU torch 2.8.0 and Transformers
4.57.1 with `HuggingFaceTB/SmolLM2-135M-Instruct`, revision
`12fd25f77366fa6b3b4b768ec3050bf629380bac`. The composition's existing model-custody
manifest binds all local files. Loading is local-only, safetensors-only and does
not execute remote model code. This tiny checkpoint is a mechanics probe; it
does not replace the original primary or replication models.

The existing HF adapter owns reversible attention, head and residual hooks,
additive output-logit bias, tokenizer offsets, a finite token trie and real KV
comparison. The named real-model tests compare null token/logit identity,
nonzero intervention, exact undo and cleanup on exceptions. Unconfigured local
adapters still refuse; ordinary test collection does not download a checkpoint.

`local-mechanism-v1.0.0` means the typed-input baseline with the original
certificate fields. `local-mechanism-v1.0.1` means one candidate calculation hint
and minimal private scratch, with the same cases and output contract. These
recipe roles and exact instructions live together in
`pilots/challenge_suite/local_mechanism_trials.py`. They are experiment recipes,
not new general templates or admitted antibodies. The initial failure was
schema copying on unmasked replies and correct shapes with wrong calculations
under the finite grammar. The result collation retains both arms, excluded
oracle-conditioned rows and affected-only corrected calibration runs.

To reproduce a selected local arm without a provider:

```powershell
git show 0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/woland/oev1rc_integration_closure/local_model_custody.json > $env:TEMP/local_model_custody.json
python -m omega_engine_woland.tests.pilots.challenge_suite.local_mechanism_trials --model-dir target/models/SmolLM2-135M-Instruct --model-id HuggingFaceTB/SmolLM2-135M-Instruct --revision 12fd25f77366fa6b3b4b768ec3050bf629380bac --custody-manifest $env:TEMP/local_model_custody.json --recipe local-mechanism-v1.0.1 --output "$env:TEMP/pfp-local-learned.json"
```

Local billed inference is zero; CPU compute is recorded but unpriced. Actual
raw replies, token IDs, prompts, checker outcomes and source pins remain in the
single OEV1RC collation in Git at `0622e7e666877c61ae9330fe55b6a223965e23eb:_ic/woland/oev1rc_integration_closure`. No original
protocol or general effectiveness claim follows from these bounded trials.

## Original obligations remain

Preserve original tasks, frozen source/fixture hashes, public/held-out separation,
program synthesis and sandbox requirements, decoding-control probes, model/budget
conditions and independent checker scope. A single accepted certificate does
not discharge those requirements. C025's second checker uses a numeric tolerance;
C027 does not supply the original LRAT machinery. Current C029 execution pairs
the retained matching-certificate judge with a separate exact GF(2) coset
optimality check. It derives the solution space from the supplied parity matrix
and weights without calling the matching solver. The historical C029 checker,
packet and commitment bytes remain unchanged; new executions bind the current
coset checker source and name it separately in their outcomes.

C029's current Python check is not the original Rust implementation or a model
campaign result. The original matching-dual certificate semantics, native judges,
decoder-program synthesis and matched hidden-case campaign still require their
own verification. A toric L=4 control demonstrates why: the retained primary
accepts a weight-4 correction with its current positive odd-set dual convention,
while the coset check finds a weight-3 correction with the same syndrome. The
composed route reports disagreement and does not accept that candidate. These
limits must survive into worker briefs and results.

To exercise the current C029 pair from the IDE, start a fresh state, read its
public case and return the bound witness through the same submit command used
above:

```powershell
python -m omega_engine_woland.entrypoints.cli challenge start --challenge C029 --ordinal 0 --state "$env:TEMP/c029-ide.json"
```

The bounded development check for `c029_base_02_rot_d3_sub1` accepted correction
`[0]`, weight 3, through both current judges and reproduced it by zero-send
replay. This demonstrates the route; it is not a hidden-case or paid campaign.

The live OEPFP-009 epic owns residual integration and all thirty problem
protocols. Raw replies, exact source bindings and existing state/accounting are
debugging inputs; useful learning belongs in the code, prompts or typed guidance.

## Accounted exploratory matrix helpers

The [PFP pilot runbook](../../../../omega_engine_pfp/documentation/pfp_pilot_matrix.md)
shows one original C052 synthesis case through the shared PFP/accounting adapter.
The formal-math and synthesis helpers preserve original judges and private-field
isolation, retain exact vendor replies, and stop all models on unknown cost or
budget exhaustion. This route repair does not complete the original C001–C030
scientific protocols. Check standalone commands outside pytest: its compatibility
aliases can hide retired namespace imports.

The same runbook includes `pfp run-pilot-suite` for the retained plain/P* prompt
comparisons. It now requires an explicit live model and allowance, writes only
to a fresh output directory and stops on unknown or ambiguous accounting. Use
its bounded `--dry-run` first to exercise the original host checker and report
path. Dry answers come from the host reference and are not model evidence;
partial prompt prefixes are not matched plain-versus-templated experiments.

## Retained two-stage baseline, witness and transfer campaign

The existing challenge-suite command keeps its original `baseline`,
`typed_witness` and `transfer` prompts, SPK-001 answer contract and original
challenge judge. Each current provider turn carries that contract inside the
shared PFP binding. Only a checked inner answer reaches the original judge;
schema compliance alone does not establish a correct witness.

Select one case and an explicit allowance, for example:

```powershell
python -m omega_engine_woland.tests.pilots.challenge_suite --live MODEL_ID --challenge C005 --split development --ordinal 0 --arm typed_witness --output "$env:TEMP/pfp-challenge-new" --max-output-tokens 3000 --max-provider-calls 2 --max-estimated-cost-microusd 50000
python -m omega_engine_woland.tests.pilots.challenge_suite --replay-live "$env:TEMP/pfp-challenge-new"
```

Replace `MODEL_ID` explicitly; this is a command example, not authorization or
a recorded live result. Estimated cost is a local reservation policy, not a
provider-enforced hard cap. The existing hard-cost option is
`--max-cost-microusd`; the CLI requires exactly one cost policy. Both stages
share the existing accounted gateway and its continuing call/spend allowance.
An uncertain cost or transport outcome stops dispatch. The campaign still runs
at most two stages and permits only its existing answer-free feedback rules.

The output directory and its sibling `<output>.budget.sqlite3` must be new.
Keep both when investigating an interrupted run; choosing a different output
starts a different run, not a continuation or permission to resend an ambiguous
attempt. Python callers pass their enclosing run's accounted gateway to
`challenge_live.live_run(..., gateway=gateway, max_output_tokens=3000,
max_provider_calls=2)`. Passing only a model or price no longer enables a send.

For `transfer`, also select `--split held_out` and `--transfer-from` a replayable
development run from the same challenge with a different case source and an
actual reusable failure rule. Transfer does not turn that rule into an admitted
antibody. Replay is zero-send and rechecks retained replies, prompts, bindings,
sequence and the original judge. Changed runtime sources refuse current replay;
old snapshots keep their original bytes and require their original environment.

CLI exit zero means the bounded observations were collated; read the printed
terminal and stage results for acceptance or ordinary rejection. Infrastructure
failure or no recorded stage exits nonzero. This route repair does not complete
original model/control experiments or establish a PFP performance advantage.
