---
documentation_contract: symbol-game-documentation/v1
title: "Practical PFP: run, replay, extend and discover"
kind: runbook
audience: [players, engineers, coding-agents]
status: active
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp/entrypoints/cli/pfp.py
  - pfp/infrastructure/demo_runners/seed_checks.py
  - pfp/infrastructure/adapters/pfp_campaign.py
source_revision: 45ba3a7dc032631d6697904cb73e20762b56353c
last_verified: 2026-10-12
---

# Practical PFP: run, replay, extend and discover

PFP starts with a task, a prompt/response contract and a way to check the
candidate. Use the simplest procedure that helps with that task. A model or a
person proposes; a host checker evaluates the declared property. If the check
exposes a repairable obstruction, use it to guide a bounded next attempt.

The primary goal is a useful, affordable, repeatable procedure with an explanation
of how and why to use it. The secondary goal is discovering LLM/system failures
and turning useful observations into antibodies, patterns, templates or code.
PFP remains work in progress. Its engineering needs follow from practical use.
There is no fixed pilot grid or required number of trials.

## Play without buying a model call

From the repository root, validate the retained seeds or prepare one prompt:

```powershell
python -m pfp.infrastructure.pilot_runner --check-seeds
python -m pfp.infrastructure.pilot_runner --seed-id DEMO_07
```

Preparation preserves the seed bytes under the existing prompt template. Its
`PREPARED_ONLY` result means zero provider calls, not a solved task. There are
74 retained seeds; choose one for a reason rather than running the whole catalog.

You can also author a witness yourself, or ask the current IDE assistant to
produce one, then submit it to the same checker. No IDE-backend flag is needed
for this caller-supplied route. This worked example solves the declared two-edge
problem, with fixed gauge `potential[0] = 0`:

```powershell
@'
{
  "potential": [0, 2, -1],
  "d0": [[-1, 1, 0], [0, -1, 1]],
  "original": [2, -3],
  "residual": [0, 0]
}
'@ | Set-Content -LiteralPath ./demo07-candidate.json -Encoding ascii
python -m pfp.entrypoints.cli.pfp check-seed DEMO_07 ./demo07-candidate.json
```

The checker recomputes `original - d0 * potential` using exact arithmetic.
The result is `[0, 0]`; `passed: true` and CLI exit 0 concern this witness and
this task only. The example is a published worked solution for a human reader,
not a hidden answer to include in an efficacy experiment's model prompt.

For a rejection exercise, change the final potential from `-1` to `0` while
keeping the claimed residual `[0, 0]`. The same command must reject that witness
with exit 2. This checks a real failure rather than counting another cosmetic
prompt variation as a new trial.

## Play with OpenRouter and replay the result

The shared application owner is `pfp`; its entrypoints include
`pfp`, `symbol-game` and `level-engine`. This example uses the model from the
recorded bounded run; availability and pricing are checked again at dispatch.
Use existing provider credentials and a new output directory:

```powershell
python -m pfp.entrypoints.cli.pfp run-seed DEMO_07 --stages 8 --modes 2 --model qwen/qwen3.8-flash --timeout 180 --output ./pfp-demo07-new
python -m pfp.entrypoints.cli.pfp run-seed DEMO_07 --replay ./pfp-demo07-new
```

The current seed CLI runs a contiguous prefix of stages 1–8. Stage 5 is the
independent host evaluation; stages 1–4 and 6–8 are model turns. An eight-stage
run therefore makes seven calls. A prefix before stage 5 cannot establish
mathematical acceptance. Eight stages are an available implementation, not a
requirement for every future task.

Replay uses the recorded configuration, seed, prompts, pricing and raw replies.
It makes zero new provider calls. A changed seed, prompt or captured reply can
invalidate the binding; do not edit an old run to make it pass. Fresh model
calls may produce different candidates even when replay is repeatable.

The current run cap is 50,000 microusd (USD 0.05), not a quoted run price.
Unknown billing stays unresolved. A model's `:free` suffix is not accounting
evidence. Do not use an existing output directory or combine `--replay` with
`--model`/`--output`.

## Choose a way to play for a specific question

| Route | How to use it | What it can establish |
| --- | --- | --- |
| Human or IDE witness | Author the seed-specific JSON and call `check-seed`. | The candidate satisfies or fails the supplied finite check. |
| Live proposal | Select one seed and bounded stage prefix with `run-seed`. | The actual model response and host outcome at the selected cost. |
| Replay | Recheck an existing capture with `--replay`. | Reproducibility of that captured result without another model call. |
| Counterexample hunt | Alter one relevant witness field or probe a suspected boundary. | A concrete failure, refusal or missing capability worth investigating. |
| Representation experiment | Supply mode 1's declared glyph input via `--mode-inputs`. | Roundtrip/allowed-alphabet behavior at the supported levels, not general semantic equivalence. |
| Prompt guard experiment | Supply mode 4's prompt, anti-op and harmful/benign controls. | The existing procedural detector's behavior on those payloads. |
| Composition experiment | Supply mode 5's typed contracts, instruction bytes and bindings. | The declared finite, typed instruction composition check. |
| Template or order experiment | Use the existing Python assembly/stage ports for a named change. | Only the comparison actually checked; arbitrary ordering is not a seed CLI option. |

Modes 2 and 14 have direct pipeline support. Other executable modes require
explicit inputs; modes 3, 6 and 15 require hooks that are currently unavailable.
See the [type and capability reference](../docs/16_current_types_and_learnings.md)
before selecting a mode. A missing tool or input is not a mathematical defect.

Hieroglyphic rewrites, variable prompt/response templates, new stages, loops and
orders of operations are extension directions. The current CLI has no
`--template`, arbitrary stage-order or automatic repair-loop option. Use the
existing programmatic contracts when adding an extension; do not imply that a
catalog name means the behavior already exists.

## Turn discovery into learning

Choose one question, such as whether a prompt can make the model claim success
without a witness, transplant another candidate's identity, or mistake missing
tooling for disproof. Bound the calls and cost. An unexpected result can motivate
another small experiment; no exhaustive matrix is required.

Keep the input and actual failure needed to reproduce the observation. Identify
its cause, correction, applicability and exceptions. Then update an existing
typed rule, helpful pattern, anti-pattern, prompt-attached antibody or code path.
An antibody needs a tangible prompt/operation attachment, the triggering failure,
and a benign control. A newly generated antibody remains a candidate until its
applicable admission checks are met.

For improvement claims, compare the same task/checker with a plain baseline and
report any extra turns and cost. Discovery can produce a valuable counterexample
without establishing how common it is or that the repair improves every task.

Collate the question, configuration, actual output, checked decision, calls,
cost, remaining error and applied lesson in the existing summary. Move on once
the bounded question is answered; avoid indefinite tuning and duplicate reports.

## What the bounded run taught us

The recorded DEMO_07 / mode 2 / stages 1–8 run reached `Verified`, with seven
provider calls and reported cost USD 0.006544. Offline replay reproduced the
result with zero calls. Changing a stage-4 raw reply was refused with zero calls.
Earlier attempts exposed candidate-identity mismatch, pricing-profile refusals
and transport ambiguity. Prompt/schema identity and safe transport diagnostics
were repaired; unknown billing was retained as unknown.

These are the recorded results in the
[consolidation handoff](../../../../pfp/documentation/pfp_consolidation_plan.md#bounded-implementation-handoff--2026-10-12),
not new live trials performed for this page. Successful-run cost is not total
campaign spending. They demonstrate one working path, not universal reasoning
improvement or a clean repository-wide suite.

## Ordinary Adversary work uses a smaller profile

An ordinary artifact, review or digestion lesson uses one task-bound response
envelope through the same Adversary backend. It does not need eight mathematical
stages. Start in the current IDE:

```text
/adversary create a short guide, review it and apply one supported lesson
/adversary-digests path/to/old-material
```

The skill reads the shared `pfp_turn` brief and submits the actual response with
`teamwork submit --raw-reply`. Python can drive the same prepare/submit handoff,
or explicitly choose an OpenRouter text-artifact bout. Follow the
[exact commands and replay example](../../../../pfp/documentation/pfp_task_turn.md#shared-adversary-use).
IDE cost is unavailable. Model text cannot execute commands or install guidance.

The bounded compatibility question was whether the ordinary role profile could
produce and review an artifact while retaining truthful accounting and checking:

| Observation | Actual outcome | Limit |
| --- | --- | --- |
| Initial GPT-OSS attempt with inherited reasoning-disable policy | HTTP400; one send, 337 microUSD reservation held, actual cost/tokens unknown | The error body had already been discarded; its precise cause is unverified. |
| Minimal role requirements with GPT-4o-mini | Completed build/review: two calls, 2,009 input/286 output tokens, $0.00047295 reported cost | Different model/configuration; this is compatibility discovery, not a controlled efficacy comparison. |
| Replay of both captured replies | Zero sends; original raw/task/candidate/checker bindings retained | Stale or tampered bindings require a fresh check. |
| Schema-valid finite wrong answer and whitespace-only role text | Independently rejected / refused respectively; ordinary prose admitted | Finite/shape controls do not prove unrestricted task correctness. |

Applied structure lives in the existing code: ordinary-role pricing checks only
required model capabilities, mathematical campaign defaults remain stricter,
typed role fields reject blank text, and HTTP error custody retains bounded bytes
for future diagnosis. This answered a practical obstruction without a pilot grid,
new framework or claim that more stages universally improve reasoning.

The final release bout used the same smaller role profile to produce exactly:

> Unknown provider cost remains unknown; stop before another dispatch until reconciled.

It completed build/review in two calls: 2,016 input and 247 output tokens,
$0.0004506 reported cost, 452 microUSD settled after per-call rounding. Host
readback confirmed the sentence; both reply/wire hashes matched and offline
replay made zero calls. Changing a task, input or checker binding or raw bytes
was refused. The run ID is `03dcffcefb0145008ee9ec12a32cd38f`; both model replies
remain UNVERIFIED. Across this release work there were five actual attempts:
four successful calls reported $0.00092355 in total, plus the earlier failed
attempt whose actual cost remains unknown. No complete total bill is claimed.

Use `python -m adversary.entrypoints.cli`, as shown in the linked guide;
`python -m adversary` has no package entrypoint. The next useful trial
should answer a new task or failure question, not increase a pilot count.

## Choose the checker separately from the prompt

The practical closeout adds two opt-in finite consumers to the same PFP owner.
`FiniteLevelEngineConsumer.judge` plugs into the existing task checking port for
`edge_endpoints`; the host fixes protected pairs before seeing the answer.
Changing candidate bytes invalidates its prepared binding. Fixture replay keeps
its literal RESEARCH_FIXTURE_REPLAY grade, even when the actual candidate fails.

For code changes, `pfp code-change-check-source-bound` binds a patch to selected
source bytes and a host-pinned native executable. It checks finite syntax,
ownership and protected-path restrictions. It does not establish that the patch
applies, fixes the task or has semantic correctness. Saved evidence is not a new
checker authorization. See the [commands and current limits](../../../../pfp/documentation/pfp_epic_closeout.md#use-the-finite-consumers).

The 2026-10-12 shared Adversary bout completed build/review/learning in three actual
calls, with 3,833 input/575 output tokens and $0.00091995 reported cost. All three
actual PFP replies replayed offline; changed task/input/checker/raw-byte controls
refused. The remote learning turn proposed guidance only. Applying a lesson still
requires the current host to edit its existing owner and recheck the task.
This is a repeatability observation, not a comparison establishing PFP efficacy.
