---
documentation_contract: symbol-game-documentation/v1
title: "Runtime Ownership and Historical Replay"
kind: reference
audience: [players, engineers, coding-agents]
status: active
maturity: experimental
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp/README.md
  - adversary/tests/pilots/relational_spacetime
  - pfp/use_cases/pfp_calculation_contracts.py
  - pfp/infrastructure/adapters/pfp_frozen_replay.py
  - adversary/tests/pilots/evidence/pfp_ownership_migration_20261012
last_verified: 2026-10-20
verification_scope: module paths, CLI flags, stage executors and linked files checked at c419cc6beb; no command or test was run
---

# 17. Runtime ownership and historical replay

AuthorityEffect: None.

> **Source check (2026-10-20, pin `c419cc6beb`).** Every `python -m` module and every flag in the commands below exists at the pin, with two corrections made in place: the C059 matrix module is now under `adversary.tests.pilots`, and the stage numbering for `assemble` is restated against the current 11-stage controller. The Paper 008 and Paper 002 links now point to the Atlas `015_pfp` deposits. `finite_gauge/sign_graph.py` and `finite_gauge/frontier_search.py` still have the same SHA-256 as the Paper 002 copies. The numbers in this page (40, 15 and 25 replay calls, 106 modules, 12 collisions, 111 contracts, 28 controls) are historical observations from 2026-10-12 and earlier; they were not re-counted.

PFP research identifiers are provenance, not application boundaries. A paper
number such as PO035 belongs in a seed's citation and evidence record. Active
code for that research is discoverable as
`adversary/tests/pilots/relational_spacetime`, with
`tasks`, `finite_checks`, `trial_prompts`, `parameter_trials`, `compact_prompts`,
`compact_checks`, and `compact_trials` modules.

The Symbol Game engine owns shared prompt assembly, bounded stage orchestration,
provider/budget adapters, calculation/workpad contracts, exact typed agreement,
and frozen-runtime execution. Task-specific seeds and independent mathematical
judges stay beside the pilots. Calculation agreement checks type and value,
including nested arrays; it does not prove an expression or a theorem.

Other ownership repairs remove numbered runner filenames, move challenge and
judge-audit compositions beside the pilots, separate executable normal-form code
from YAML/SQL assets, retire duplicate canonical-type monoliths, and replace the
type census's legacy alias search with exact current paths. The
[package ownership map](../../../../pfp/README.md) gives the direct entry points.

The public `pfp.infrastructure.UnifiedPfpDemoRunner` name resolves
to the same class as `infrastructure.pilot_runners.pilot_dispatch`. It does not
load a retired `demo_runners` module or introduce a replacement implementation.
For example, an unsupported demo remains an explicit refusal:

```python
from pfp import DemoCatalog, DemoSpec
from pfp.infrastructure import UnifiedPfpDemoRunner

catalog = DemoCatalog(demos=[DemoSpec(
    id="unregistered-example", title="Unknown demo", seed="public input")])
result = UnifiedPfpDemoRunner().run_all(catalog)[0]
assert result.terminal_status == "Refused" and not result.all_passed
```

This checks public API use, not completion of a demo or its original protocol.
Registered runners retain their existing resource, native and historical-context
requirements. A successful package import does not establish that every lazy
public name resolves; the installed probe exercises the public runner itself.

The retired `demo_003` aggregate previously returned `Exact` from three literal
success flags: a twelve-demo census, a zero Regge deficit and a cohomology
nilpotency claim. None executed its asserted check. The current facade retains
those obligations as failed checks with explicit reasons; it does not promote
the retained MUB6/Regge illustration or retired cohomology scenario into evidence.
`RunDemoUseCase.run_pilot` now reads the real receipt's `all_passed` field, so
a refused demo cannot become a passing pilot through a missing-attribute default.

```powershell
python -m pfp.entrypoints.cli.pfp run-demo demo_003
python -m pfp.entrypoints.cli.pfp run-demo demo_001
```

The first command refuses with exit 2 and lists the unmet original checks.
The second executes the existing gate controls. Neither is an LLM experiment.
Use `symbol-game demo list` to select a current named scenario explicitly;
its result is scoped to that scenario, not a replacement for the original
twelve-demo aggregate or its mathematical obligations. Historical artifacts,
fixtures and prior reports remain unchanged.

The consolidated application owner is `pfp`, merged on main in
PR #829. This cleanup follows that owner and does not recreate the retired apps.
Its current inventory records 106 model/enum modules and 12 public-name
collisions across the combined package. Distinct records remain under semantic
review; equal names do not establish interchangeable contracts. The move does
not establish that one prompt works for every task.

One remaining contract mismatch is explicit: pilot `0000000` has recorded
`pfp.dossier-response.v1` refusals, while its old roundtrip test expects
`pfp.pilot-response.v1`. The artifacts and test remain unchanged. Resolving that
lesson/dossier boundary belongs to the remaining application absorption.

Prepare a numbered-stage prompt through the current public command:

```powershell
python -m pfp.entrypoints.cli.pfp assemble --demo-id demo_002 --stage 1
python -m pfp.entrypoints.cli.pfp assemble --demo-id demo_002 --stage 1 --seed-json public-task.json --json
```

`public-task.json` supplies public prompt data, for example
`{"seed": "State the finite task and its declared inputs."}`. The default output
shows the actual demo/stage and system, user and schema hashes. `--json` returns
the existing `PromptPacket`, including `system`, `user` and `response_schema`;
it contains the supplied prompt data, so choose inputs intended for the model.
For model stages 1–4 and 6–8, the copied schema binds `demo_id` to the requested
identity. Its remaining stage requirements and source YAML stay unchanged;
stage 0 and host-only stage 5 retain their existing empty model schema.
(Stage numbers corrected 2026-10-20: `assemble` now accepts stages 0 to 11
(`STAGE_COUNT = 11`). [controller.yaml](../../../../pfp/infrastructure/yaml/stages/controller.yaml)
marks stages 2, 3, 4, 6 and 11 as model stages and 1, 5, 7, 8, 9 and 10 as host
stages. `AssemblePromptUseCase` loads a model schema for every non-host stage and
for stage 1, whose file carries a repair-turn schema; stage 0 and the other host
stages get an empty schema ([assemble_prompt.py](../../../../pfp/use_cases/assemble_prompt.py)
lines 42-58). The CLI help text still says "Stage index (0-8)".)
Assembly performs no model dispatch or independent task checking. A valid
response shape still needs the selected stage's host checks. The existing
schema hash uses Python's dictionary representation, not RFC 8785 serialization.

The numbered prompt roles have an opt-in, **undispatched** `1.0.2` relocation
version. Its instructions and output contract are unchanged from the failed
`1.0.0` experiment. Updating module ownership does not establish better model
results. Original versions, raw replies, and verdicts retain their exact bytes.

The previous current renderer selected append-only `1.0.3`, which binds the current
Atlas paper while preserving its unchanged section-5 excerpt, original seeds,
participant contracts and limits. The `1.0.2` files and paper pin are unchanged;
they still refuse current-paper drift. Current installed-resource rendering and
historical campaign replay are separate checks. No new provider campaign or
improvement claim follows from the loading repair.

The final pilot-owner move selects append-only `1.0.4` for current relocated
task/source paths. Original v1.0.0-v1.0.3 files and records are unchanged. This
resource relocation does not create another provider trial or accuracy result.

Run historical records through their pinned runtime, without recreating legacy
imports in the active application:

```powershell
.venv/Scripts/python.exe -m pfp.infrastructure.adapters.pfp_frozen_replay --bundle adversary/tests/pilots/evidence/pfp_ownership_migration_20261012 --profile scratchpad-temperature-logit
.venv/Scripts/python.exe -m pfp.infrastructure.adapters.pfp_frozen_replay --bundle adversary/tests/pilots/evidence/pfp_ownership_migration_20261012 --profile compact-three-stage
.venv/Scripts/python.exe -m pfp.infrastructure.adapters.pfp_frozen_replay --bundle adversary/tests/pilots/evidence/pfp_ownership_migration_20261012 --profile five-final-prompts
```

These profiles verify 40 experiment calls, 15 compact-round calls, and 25 source
calls plus five reviewed final prompts, respectively. Frozen bytes are checked
before execution in a disposable scratch directory; Python socket access is
blocked before historical modules import. No provider call or prompt repair is
part of replay. Current-source replay continues to refuse source drift.

## Audit the current original judge packets

The existing audit runner lives in
`adversary.tests.pilots.judge_packet_audit`; its current task tree is
`pfp/tests/demo_004`. Select the packages needed for the question.
For a source-only inspection of the retained Hodge packet:

```powershell
python -m adversary.tests.pilots.judge_packet_audit.audit --repo-root . --packages C014 --skip-execution --out "$env:TEMP/c014-audit-new" --work-dir "$env:TEMP/c014-audit-work-new"
```

Choose fresh output/work directories to retain earlier audit packets. Inspect
the selected package record, `summary.json` and `run_info.json`; successful
collection is not a verdict that the judges are sound. `--skip-execution` keeps
checker/solver execution unavailable in the report. Omit it only for a deliberate
bounded execution of the selected checkers; the audit makes no model calls.
An unknown or empty package selection refuses instead of reporting an empty audit.

Current descriptors and source-tree checks use the current owners. Static
analysis also recognizes retained historical import spelling so it can report
checker dependencies without rewriting those source files. That recognition
does not install old module aliases or make an unavailable historical checker
executable. Original task, judge, case, commitment and recorded audit bytes stay
unchanged; original scientific protocols remain separate obligations.

## Current catalog demos through PFP

`symbol-game demo run` keeps the catalog's original fixtures and
host judges. Offline execution remains a deterministic fixture replay. Live
proposals use the shared PFP envelope and accounted OpenRouter gateway, with
the existing trace retaining the actual provider response bytes. A valid PFP
envelope only admits the answer to the host judge; it does not certify it.

Select a model and explicit output, call and financial limits. For example,
this deliberately permits only one provider attempt:

```powershell
python -m pfp.entrypoints.cli.symbol_game demo run demo_3 --live --model YOUR_MODEL_ID --output-dir "$env:TEMP/demo3-pfp-one" --max-output-tokens 1024 --max-provider-calls 1 --max-estimated-cost-microusd 4000
```

Use a new output directory each time. The estimate is not a vendor-enforced
maximum bill. The existing hard-budget option requires transport maximum
liability and can refuse when it is unavailable. Missing policy, invalid PFP
bindings, exhausted allowances and unknown costs stop execution; they never
select a fixture or a new budget. The demo 3 runner still requests its original
host matrix, so the one-call example normally stops before matrix completion.
Its retained transcript reports the attempted turn and refusal, not a completed
experiment. No fixed grid or repeated paid campaign is required.

```powershell
python -m pfp.entrypoints.cli.symbol_game demo run demo_3 --output-dir "$env:TEMP/demo3-offline"
python -m pfp.entrypoints.cli.symbol_game demo verify "$env:TEMP/demo3-offline/receipt.json"
```

The package-root `python -m pfp` exposes a different command set;
use the explicit module above or the installed `symbol-game` entrypoint.
Successful live verification remains an integrity check, not model replay or
an efficacy claim. Preserve old output directories and run old artifacts with
their pinned implementation; do not change their hashes to fit current code.

## Current matrix integration and original judges

The C051-C055 and C059 integration harnesses use the same accounted PFP helper
as current matrix execution. Their original solvers and independent judges stay
at their existing owners. A synthetic reply must carry the actual prepared
task/attempt/input binding before its answer can reach a judge. SQLite replay
checks the retained answer against those judges without calling a provider.
This is fixture integration, not evidence of a model solving the original task.

When migrating a harness, let its fixture solver read the actual transmitted
public case. Falling back to the first case or returning a precomputed answer
can hide a broken prompt route. Pair a valid bound reply with malformed and
wrong-binding replies that must stop before the original judges. Declare fixture
model admission and prices as synthetic; an outdated vendor allowlist is not a
reason to shrink the original case set or token limit. The current matrix
controls demonstrate this procedure without claiming live model performance.

The old `AdversaryMatrixTransportAdapter` is retired. It kept a second post-hoc
float budget, collapsed conversation fields, and manufactured a replacement
provider response. Current callers inject an existing gateway directly into
`synthesis_matrix.run_matrix` or `formal_matrix`; they do not patch a private
`_transport` on an obsolete wrapper. Original provider bytes, known/unknown
cost and the PFP check remain separate from the answer sent to the judge.

For an explicitly authorized one-case trial, select a current model and make
the smaller output bound visible. This example changes C059's original
8,192-token protocol to a bounded 512-token demonstration:

```python
from dataclasses import replace
from pathlib import Path
from pfp.infrastructure.pilot_matrix import make_pilot_gateways
from pfp.infrastructure.synthesis_matrix import run_matrix
from adversary.tests.pilots.c059_sql_null_total_query_synthesis.run_c059_matrix import SPEC

model = "<explicit authorized OpenRouter model>"
spec = replace(SPEC, cases=SPEC.cases[:1], max_tokens=512,
    models=[{"id": model, "name": model}],
    notes={"scope": "one-case bounded trial", "original_max_tokens": SPEC.max_tokens})
gateways = make_pilot_gateways([model], max_output_tokens=512,
    max_estimated_cost_microusd=5000, max_calls=1,
    accounting_path=Path("c059-one-case.sqlite3"))
summary = run_matrix(spec, Path("c059-one-case-results"),
    gateways=gateways, pause_s=0)
```

Use a fresh result directory and retain the gateway/ledger for continuation.
An unknown or ambiguous bill stops further sends; a new wrapper cannot reset
the allowance. The estimated policy is not a vendor-enforced bill ceiling.
Preserve the original 8,192-token setting and full case set as separate protocol
obligations. A smaller trial and successful local reference solver do not close
those obligations or establish neural performance.

## Numbered seed stages and refusal replay

The [numbered-stage runbook](../../../../pfp/documentation/pfp_seed_execution.md)
uses the same accounted PFP boundary for `pfp run-seed`. Select explicit model,
call, output-token and financial limits. Start with the shortest useful prefix;
Stage5 remains the independent host verification step. Original stage prompts,
mode inputs and decoding stay inside the bound task/reply exchange. Adding a
provider `response_format` constraint would change that original protocol, so
this migration does not add one.

Replay the failure path as well as a successful candidate. During this migration,
the live checker correctly refused malformed JSON, but replay indexed an absent
`answer` and raised `KeyError`, losing its known-cost observation. The adapter
now extracts an answer only after schema/binding success. The existing
`test_refused_shape_replay_retains_original_failure_and_known_cost` control
covers malformed JSON, wrong bindings and invalid Unicode: the original refusal,
cost and captured bytes survive with zero replay sends.

Keep confirmed pre-send refusal separate from an ambiguous dispatched attempt.
The former preserves the known subtotal; missing billing after a send remains
unknown and stops later stages. Current capture JSON uses an explicit ASCII
escape profile so rejected Unicode can be retained, while provider bytes remain
exact. Historical capture serializers and hashes are unchanged. Partially
written interrupted captures are retained for inspection; automatic replay or
continuation of them is not claimed. These controls establish failure handling,
not mathematical acceptance or improved model performance.

## Current PO035 research loops through PFP

The derivation and experiment adapters now prepare and check the actual model
reply through the shared PFP task-turn contract. The existing durable SQLite
ledger and killable subprocess deadlines remain their provider boundary. The
original prompt, seed, temperature, logit intervention, output limit and observer
remain in force; the original proposal is carried inside the bound PFP answer.
No provider `response_format` is added to these experiments. A valid envelope
only admits a proposal to its original scientific judge.

Live entrypoints require an explicit model, selected pilot and fresh output
outside the historical pilot estate. The default derivation still allows five
loops; this smaller example selects one, so it does not complete that protocol:

```powershell
python -m adversary.tests.pilots.relational_spacetime.baseline --run pilot_0000199 --model YOUR_FREE_MODEL_ID --loops 1 --output "$env:TEMP/po035-current-one"
python -m adversary.tests.pilots.relational_spacetime.baseline --replay --pilot pilot_0000199 --output "$env:TEMP/po035-current-one"
```

The selected model must satisfy the existing zero-price and decoding capability
checks. Each pilot retains the original limits: at most five proposals, 120,000
provider tokens, 180 seconds and USD 0.05. Scratchpad, temperature/logit and
compact profiles keep their respective four, two and three stages. An uncertain
send or unknown bill stops the loop; the output retains both known cost and the
unsettled reservation. These local accounting limits are not provider-enforced
maximum-liability caps. No automatic retry or budget reset follows a stop.

Compact runs retain preparation and source-drift refusal before dispatch:

```powershell
python -m adversary.tests.pilots.relational_spacetime.compact_trials prepare --model YOUR_FREE_MODEL_ID --output "$env:TEMP/po035-compact-prep"
python -m adversary.tests.pilots.relational_spacetime.compact_trials run --pilot pilot_0000199 --model YOUR_FREE_MODEL_ID --preflight "$env:TEMP/po035-compact-prep/preflight.json" --output "$env:TEMP/po035-compact-current"
python -m adversary.tests.pilots.relational_spacetime.compact_trials replay --pilot pilot_0000199 --output "$env:TEMP/po035-compact-current"
```

`parameter_trials run scratchpad|temperature|logit` likewise requires `--pilot`,
`--model` and `--output`; `replay` uses that same output and sends nothing. Logit
keeps its pinned Qwen model/tokenizer and refreshes public endpoint prices before
dispatch. `typed_signals --run` accepts `--prior-run` for a prior baseline capture
and subtracts that pilot's spent budget. Its default remains the historical
baseline. Exhausted or unreconciled prior work cannot receive a fresh allowance.

Current v2 replay rechecks the actual raw reply, PFP bindings, ledger and original
observer. Current source drift refuses; original v1 captures and snapshots retain
their bytes and use the frozen replay commands above. Malformed completion text
has an explicit refusal, not a missing-answer crash. Finite fixture controls do
not establish model efficacy, the PO035 analytical claims, complete Adversary
accounting integration or completion of the original campaigns.

Two implementation lessons are now exercised by the current controls. A host
observer that writes insertion-order-sensitive YAML must receive the same
serialized receipt order during capture and replay; equal JSON mappings alone
do not ensure equal YAML bytes. Normalize the new version's handoff, never old
evidence. Also commit observed provider usage before raising a terminal stop:
raising inside the ledger transaction rolls that observation back. Duplicate
generation IDs still refuse admission and retain a reservation; preserving their
reported liability does not turn them into an accepted independent generation.

## Governed research proposals through PFP

The [two governed research CLIs](../../099_project_sentinel/001_fully_governed_and_auditable_agentic_ai_systems/README.md#current-bounded-research-runner)
reuse one accounted gateway for their original stress and solver-coupling
experiments. A proposal travels as a string inside the checked PFP answer, then
passes unchanged to its original strict parser and perimeter. Declaration key
order affects that parser's verdict; a parsed and normalized JSON object is not
an equivalent transport for this experiment.

The original nine scenarios, four graphs, task prompts and witness bindings
remain. Both comparative arms spend the same allowance. Operational/PFP refusal
does not count as mathematical rejection, and uncertain cost or dispatch stops
the remaining arms. New reports expose evaluated denominators, unattempted arms
and actual raw exchanges. Offline fixtures remain explicitly classified; no new
live-model result or original-protocol equivalence follows from a synthetic pass.

The existing DDA bridge reads the retained exact-repair and residual-projection
source leaves from their current archive location. It copies neither solver,
does not alter archived bytes and retains the original G4 unprojected-tree
obligation. These are checkout-local research dependencies. All current reports
use a fresh explicit output directory; historical metrics and judges are retained.

## Run a pilot through the numbered stages

The existing `ExecuteStagePipelineUseCase` has two PilotAggregate entrypoints.
`run_for_pilot(pilot)` returns the current pipeline receipt, including stage
responses and the host verdict. `execute_pilot(pilot)` runs the same path and
returns an updated pilot summary. Choose the return type you need; calling both
would execute the pipeline twice.

```python
# pipeline is the existing use case with storage, provider, catalog and host verifier.
result = pipeline.run_for_pilot(pilot)
if result.is_err:
    print(result.unwrap_err())
else:
    receipt = result.unwrap()
    print(receipt.completed_stages, receipt.final_terminal_status)
    print(receipt.stage_responses.get(5))
```

Both entrypoints preserve the same original prompt and pilot/checker identity.
The updated summary records current pipeline progress and clears a previous
answer/evaluation. Completing stages is distinct from establishing a new answer
under the pilot's answer checker. A stopped run cannot inherit an old ACCEPTED
answer. Inspect the current receipt for the stage candidate and independent host
result. The original pilot and historical files remain unchanged.

A new pipeline summary also clears the retained `response` field. The original
pilot keeps that reply for explicit offline rechecking; evaluating the new summary
cannot silently reuse it as the new run's answer.

## Pilot transitions retain observations

`PilotAggregate.with_transition` copies an existing pilot and applies explicit
changes. It no longer invents an execution-evidence string for PASS/COMPLETED or
fills an absent observed answer from the oracle. Successful execution states
require nonblank supplied or retained evidence. ACCEPTED requires an observed
answer consistent with the original checker obligation; metadata alone cannot
provide it. This local consistency check does not authenticate an evidence string.

Omitting `extracted_answer` retains the previous observation; explicitly passing
`extracted_answer=None` clears it. A rejected copy transition leaves the source
unchanged. The mutating `record_execution` and `evaluate_result` methods also
validate their proposed changes before updating the original pilot, so catching
an invalid evaluation cannot leave it marked ACCEPTED.

The evaluation use case retains the existing gate's observed answer for both
accepted and rejected proposals, and clears stale answers when no observation
is available. Valid checker representations keep their meaning: for example,
the determinant checker returns a `{"det": n}` observation against a scalar
oracle, and the epistemic checker permits its existing case-insensitive reason
match. Preserve those observations instead of replacing them with the expected
answer or refusing a valid result only because its representation differs.
Original checkers, historical responses and scientific protocols retain their
owners and bytes. These repairs establish state consistency, not execution of
every pilot or completion of the PFP/Adversary migration.

## Evaluate an existing typed pilot response

The existing document models now carry a response through conversion to the
pilot aggregate and into its evaluator:

```python
from pathlib import Path
from pfp.domain.types.pilot_spec import PilotSpec
from pfp.domain.types.seed_prompts import SeedPrompt
from pfp.domain.types.pilot_response import PilotResponse
from pfp.use_cases.evaluate_pilot import EvaluatePilotUseCase

spec = PilotSpec.from_yaml(Path("spec.yaml").read_text(encoding="utf-8"))
seed = SeedPrompt.from_yaml(Path("seed.yaml").read_text(encoding="utf-8"))
response = PilotResponse.from_yaml(Path("response.yaml").read_text(encoding="utf-8"))
pilot = spec.to_aggregate(seed, response)
result = EvaluatePilotUseCase().execute(pilot)
if result.is_err:
    print(result.unwrap_err())
else:
    print(result.unwrap().evaluation_status.value)
```

Conversion checks the existing pilot, request and checker identities, retains
the original response and starts local evaluation as NOT_RUN. A response's
stored PASS/ACCEPTED label or extracted answer does not become a new verdict.
The evaluator checks the actual `raw_reply` with the existing parser and original
checker. Cached parsed answers cannot replace malformed or missing raw text.
The original response remains available for inspection after checking.

These are offline checks of retained response text and declared identities.
They neither authenticate its provenance nor retroactively add a shared PFP
task/attempt/input binding to an old record. Use the existing shared turn path
for current Adversary model interactions and the original versioned replay readers
for historical custody. The old YAML schemas and files remain unchanged.

## Examiner quiz through the shared PFP turn

The [Examiner quiz runner](../../_lev_examiner_theoretical_minimum_quiz/z_solutions_and_verifiers/llm_quiz_runner.py)
retains its thirteen current layer specifications, original zero/few-shot
conversation, mock fixtures and independent quiz checks. Its live transport
delegates to the existing PFP/accounted boundary. The original wire answer is
carried inside the bound PFP answer; this envelope changes the outer protocol,
so historical bare-wire observations are not directly interchangeable.

Only a checked model answer reaches the original quiz evaluator. A network
failure, malformed envelope or wrong task binding is an operational refusal,
not a synthetic `<exception<...>>` answer and not a mathematical NONDESCENT
finding. Retain the actual reply and known/unknown accounting observations.
An uncertain send or bill stops later layers under the same allowance.
Neither a `:free` model suffix nor a private API key authorizes a fresh budget.

The [quiz usage instructions](../../_lev_examiner_theoretical_minimum_quiz/README.md)
show explicit model, call and financial selection with fresh output paths.
Temperature remains zero and the original output bound is 150 tokens; no
provider schema constraint or answer-bearing fixture is added to the request.
Explicit few-shot exemplars remain part of their original condition. Historical
JSON receipts are unchanged. A quiz PASS has only the scope of the existing
finite/template checker; it does not prove the scientific assertions suggested
by a layer name or demonstrate a general model advantage.

## Plain prompt facades and prepared turns

The older two-prompt `LlmGateway.complete(system, user)` facade now uses the
existing accounted PFP gateway. Its answer passes the shared task/attempt/input
check, while `LlmReply.raw_response` preserves the original decoded vendor
envelope. Supply the same gateway across callers to retain the continuing call
and cost allowance; a key or an extra facade instance cannot create new spend
authority. See the [Python composition](../../../../adversary/documentation/shared_teamwork.md#two-prompt-python-completion-facade).

Review the callable facade as well as the preferred backend when checking a
migration. The earlier backend migration did not cover this separate exported
API. Conversely, an already-prepared PFP task should retain its current adapter:
adding another envelope changes the task the original checker expects. Preserve
both the checked answer and original wire as distinct values. Existing historical
files remain unchanged, and this selected route repair does not close the full
sender inventory or establish a new model-performance result.

## Consistency teaching scene through PFP

The retained `naked_prompt_launder.py` scene used the deleted
`bench/head_to_head` directory. Its generator, direct/CoT prompts, verdict parser
and exact potential-propagation judge now live in the existing task-profile
estate at `pfp.tests.demo_004.a_mechanism.consistency_teaching`.
They come from [the original source at bc42aa0](https://github.com/dbccpage/the_symbol_game/tree/bc42aa0a7156fcdf2122f0c8c43a52268e9eac84/bench/head_to_head).
Only the used judge is recovered: the historical exponential `phi1` minimizer
and its paper-path bootstrap remain historical. The graph construction, verdict
logic and original direct/CoT prompt text are retained.

For a zero-provider exercise, compare the original clean and poisoned instances:

```python
from pfp.tests.demo_004.a_mechanism.consistency_teaching.tasks import generate_instance
from pfp.tests.demo_004.a_mechanism.consistency_teaching.host import host_verdict

clean = generate_instance(n_items=3, n_relations=3, poisoned=False, seed=1)
poisoned = generate_instance(n_items=3, n_relations=3, poisoned=True, seed=1)
assert host_verdict(clean) == "CONSISTENT"
assert host_verdict(poisoned) == "CONTRADICTION"
```

This checks exact finite constraints. It does not measure what an LLM will say,
and a model can correctly identify the poisoned graph. A recorded wrong answer
is a finding about that response, not a general law of model behavior.

Current recording belongs to `pfp.infrastructure.consistency_teaching`.
Its `record_one(..., gateway=existing_gateway)` accepts the enclosing run's
accounted gateway. Use that same gateway for successive cases. Original public
arguments and the 2,048-token default remain; no key-only sender or implicit
`.env` loading is restored. Education delegates recording and owns video display.

From the repository root, select an explicit model and a new output directory:

```powershell
python education/documentation/004_oepfp/curriculum/scenes/naked_prompt_launder.py record --model YOUR_MODEL --output-dir NEW_DIRECTORY --max-provider-calls 2 --max-output-tokens 2048 --max-estimated-cost-microusd 500
```

The estimated allowance uses the existing gateway policy; it is not a hard
vendor billing guarantee. The two original cases are the direct three-cycle and
the eight-item/fourteen-relation CoT instance. The same gateway and ledger cover
both. Binding, malformed-response and accounting refusals retain their actual
evidence and stop the sequence. No refused reply becomes a host verdict or
silent retry. Existing capture paths are refused before dispatch.

Rendering is separate and makes no provider call. It requires the existing
Matplotlib/FFmpeg tools and a fresh MP4 path:

```powershell
python education/documentation/004_oepfp/curriculum/scenes/naked_prompt_launder.py render --input SAVED_CAPTURE.json --output NEW_CLIP.mp4
```

Historical `_render` JSON/MP4 files retain their bytes and old meaning. Rendering
one does not retroactively add a PFP binding or reissue the model observation.
The current route adds checked transport around the original prompts; comparisons
with historical naked-prompt observations must account for that changed envelope.
This repair does not reproduce the old benchmark or establish improvement.

## Interactive notebook completions

The teaching `SymbolGameLLMClient` now delegates live work to the existing PFP
task-turn contract and the enclosing run's accounted provider gateway. See the
[notebook composition examples](../../../education_app/frontend/notebook_lib/README.md).
Keep the same gateway for successive calls and clients; the notebook does not
create another allowance. OpenRouter credentials and local endpoint configuration
belong to that supplied gateway. Selecting a provider in a widget does not create
a transport or authorize a fresh budget.

Explicit `mode="mock"` keeps the original deterministic teaching outputs. A
missing key, failed request or invalid live reply no longer substitutes those
outputs. In particular, `LAND 0` from an offline fixture cannot stand in for a
failed live derivation. The actual answer must carry the prepared task, attempt
and input bindings; passing this check still leaves the mathematics unverified.
Original prompts, temperatures and the 512-token bound remain part of the
teaching experiment. The fence and fluff scores are instructional heuristics,
not a semantic proof checker or evidence of a general model advantage.

This applies the existing fixture-isolation rule at a real teaching boundary.
Review active notebook helpers alongside CLI facades: a mediated preferred
backend alone does not cover a separate direct HTTP client. Historical receipts,
notebooks and output files retain their bytes. The focused controls use synthetic
provider responses; no live provider/local run or full sender coverage is claimed.

## Contract specifications and execution verification

To inspect the current normal-form YAML specifications, use the existing audit:

```powershell
python -m pfp.entrypoints.cli.pfp_normal_forms audit-contracts
```

It checks the catalog against its declared standard. Zero findings means the
specifications satisfy that audit; it does not establish confluence, a completed
chase, zero candidate defects or any stage-transition invariant. The existing
`run-examples` command in the same module exercises selected relational examples.
Those finite results do not certify every registered normal form.

`python -m pfp.entrypoints.cli.pfp verify-contracts` and the
`VerifyPfpContractsUseCase` execution-verification methods cannot establish those
claims from metadata alone. They now return an explicit unavailable-verifier
refusal instead of constructing successful execution receipts. Missing or
malformed specifications retain their input errors. A pilot's expected outcome,
claimed evidence or existing status is not a check of its current execution;
calling this verifier leaves its original fields intact.

This fixes a reproduced false success: the previous CLI printed that 111
contracts across normal forms and stages were verified after only loading
normal-form metadata. Full verification remains open until actual candidate
inputs reach the appropriate existing checker and satisfy the original
obligations. Do not reinterpret a structural audit or a typed refusal as closure.
Historical YAML, scientific sources and receipts retain their bytes and meaning.

## Current Paper 008 graph benchmark

New runs use `pfp.infrastructure.retraction_benchmark` and its
`pfp.entrypoints.retraction_benchmark` command. The original
[Paper 008 runner](../../../../atlas/coda_atlas/F004_papers/015_pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks/code/retraction_benchmark_runner.py),
paper deposit and recorded results retain their bytes and historical behavior.
The current derivative retains the six graphs, integer potential/cycle checks,
prompt text and verdict parser. It replaces direct HTTP and the old float budget
with the existing PFP task turn and enclosing accounted gateway.

The four original conditions answer different questions:

| Condition | Participant input and interpretation |
| --- | --- |
| `baseline` | Graph and verdict request. No host answer is supplied. |
| `hinted` | Adds host residuals that determine the answer. This is assisted, answer-bearing input and cannot support a blind-reasoning claim. |
| `scratchpad` | Adds the original public propagation procedure. It does not supply the host's computed answer. |
| `exact_oracle` | Copies the host verdict as a zero-model control. It is not a model observation. |

For a small offline exercise with the original deterministic stub:

```powershell
python -m pfp.entrypoints.retraction_benchmark --conditions baseline hinted --tasks retract_01_tree_clean retract_03_triangle_poisoned --output-dir NEW_OFFLINE_DIRECTORY
```

The stub reads prompt text; it measures no LLM. In particular, its blind
poisoned-graph mistake and its success with answer-bearing hints demonstrate
the conditions and scoring, not model behavior or a general PFP advantage.

For a separately authorized live run, select the model and allowance explicitly:

```powershell
python -m pfp.entrypoints.retraction_benchmark --live --model YOUR_MODEL_ID --conditions baseline scratchpad --tasks retract_01_tree_clean --max-output-tokens 128 --max-provider-calls 2 --max-estimated-cost-microusd 1000 --output-dir NEW_LIVE_DIRECTORY
```

The original 128-token limit now includes the PFP envelope. A larger explicit
bound changes the experimental setting; report it when comparing runs. Provider
pricing and credentials come from the existing configured factory. The estimated
allowance is a reservation policy, not a provider-enforced maximum bill.
Python callers can pass the same accounted gateway as `client` to successive
`run_benchmark` calls or to `run_conditions`; one enclosing allowance covers
the selected cases and conditions. No new client or condition resets it.

The actual reply must pass PFP task/attempt/input checks before its verdict is
parsed, and its answer must remain text. The route preserves temperature zero
and does not add provider-side `response_format` decoding. The original exact
host still determines graph consistency. Malformed bindings, unknown cost and
ambiguous sends retain their observations and stop the live sequence. They
cannot become an offline answer, a zero-cost response or an automatic retry.
Reports retain the known subtotal and unknown-cost count even when the total
cannot be determined. A positively established refusal before dispatch adds
zero cost; a missing bill after an attempted send stays unknown. Replay checks
this distinction against the retained gateway observations. Existing output
directories refuse before dispatch.

Current captures retain raw wire, PFP checking and original host certificates.
Recheck them without credentials or provider calls:

```powershell
python -m pfp.entrypoints.retraction_benchmark --replay SAVED_CURRENT_DIRECTORY
```

Replay requires the current capture schema and matching source/prompt/reply
bindings. Historical v2 receipts keep their original reader and are never
silently upgraded. The native migration and full original empirical protocol
remain open; this route establishes practical execution and scoped checking.

The documented two-condition/two-task offline command produced four rows: three
matches and the expected baseline poisoned-graph miss. All four replayed with
zero provider calls and no observed models. Twenty-eight focused controls cover
the canonical route, original source equality, malformed and unknown-cost
replies, continuing allowance, pre-dispatch cost, output preservation and replay
tampering. These observations concern deterministic/synthetic execution, not a
paid model study.

## Finite signed-graph workbench

The existing `symbol-game search-gauge` and `symbol-game serve` routes use
`pfp.infrastructure.adapters.finite_gauge` for their checker.
The two current modules are byte-identical copies of the retained
[Paper 002 sign checker](../../../../atlas/coda_atlas/F004_papers/015_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/sign_graph.py)
and [bounded search checker](../../../../atlas/coda_atlas/F004_papers/015_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/frontier_search.py).
The paper deposit and its historical receipts remain unchanged. Current runs
load one canonical module pair, without the removed `research.*` namespaces or
a source-checkout fallback. The relative import preserves one set of current
witness types; historical classes are not aliases for current runtime types.

Run a small graph directly through the existing command:

```powershell
python -m pfp.entrypoints.cli.symbol_game search-gauge --fixture gauge_even_triangle --node-budget 8 --pace-ms 0
python -m pfp.entrypoints.cli.symbol_game search-gauge --fixture gauge_odd_triangle --node-budget 8 --pace-ms 0
python -m pfp.entrypoints.cli.symbol_game search-gauge --fixture gauge_odd_triangle --node-budget 3 --pace-ms 0
```

These exercise `GAUGE_VERIFIED`, `RESTRICTED_OBSTRUCTION` and budget-limited
`UNKNOWN`, respectively. The last JSONL event contains the independently
rechecked result. A partial search does not establish an obstruction. Use a new
`--output-dir` to retain the existing event and result files, or provide a typed
YAML packet with `--input-file pfp/fixtures/gauge_odd_triangle_input.yaml`.

With the existing optional `web` dependencies installed, the same implementation
drives the local workbench:

```powershell
python -m pfp.entrypoints.cli.symbol_game serve --port 8765
```

Open `http://127.0.0.1:8765`. The existing API and event stream retain their
behavior; the workbench's one-worker checker call and scheduling are unchanged.
This is a finite signed-graph control with no LLM or provider charge. It establishes
neither a physical Hamiltonian reduction nor a general sign-problem result.
The original checker versions, candidate ordering and receipt digests remain;
new snapshots bind the current packaged source bytes.
