---
documentation_contract: symbol-game-documentation/v1
title: "Current PFP types, capabilities and lessons"
kind: reference
audience: [engineers, coding-agents, researchers]
status: active
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp/domain/contracts/pfp_runtime.py
  - pfp/domain/stages/stages.py
  - pfp/domain/prompts/prompts.py
  - operads/contracts/typed_capabilities_v1.py
source_revision: 305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d
last_verified: 2026-10-22
verification_scope: mode sets rechecked and unchanged; typed-capability path and six wire classes rechecked at operads; PO035 token figures not re-counted; no test run
---

# Current PFP types, capabilities and lessons

The active application is `pfp`. Older `ow/...`,
`education.pfp` and `symbol_game` runtime paths in
historical manuals are not current command locations. Python orchestration and
both native Symbol Game crates share the existing boundaries; this update adds
documentation, not another framework.

Start with the [practical play guide](../_how_to_play/13_practical_pfp_and_discovery.md).
The tables below reference existing code. They distinguish wire/type validity,
host evaluation, captured evidence and admission rather than treating them as
interchangeable PASS labels.

## Prompt, stage and candidate types

| Existing type or function | Relevant fields or role | Source |
| --- | --- | --- |
| `PfpPromptTemplate`, `PfpTaskPrompt`, `PfpPrompt` | System/user text, task/case and response schema; template requires `[USER PROMPT]`. | [Runtime contracts](../../../../pfp/domain/contracts/pfp_runtime.py) |
| `PfpPreparedStage` | Prepared payload/wire body and integer `reserved_microusd`, bounded by the existing cap. | [Runtime contracts](../../../../pfp/domain/contracts/pfp_runtime.py) |
| `PfpStagePromptInput`, `PfpPipelineStep`, `PfpPipelineRun` | Stage assembly inputs; response/continuation; completed stages and terminal summary. | [Runtime contracts](../../../../pfp/domain/contracts/pfp_runtime.py) |
| `PfpStagePort`, `PfpPipelinePort` | Existing injected boundaries for dispatch, host evaluation and continuation. | [Runtime contracts](../../../../pfp/domain/contracts/pfp_runtime.py) |
| `PromptTemplate`, `PromptSlot`, `PromptPacket` | Slots and rendered text/schema with seed, template and controller bindings. | [Prompt models](../../../../pfp/domain/prompts/prompts.py) |
| `PacketEnvelope` | Task data, protected boundary, budget, candidate payload and witness data. | [Packet models](../../../../pfp/domain/prompts/packets.py) |
| `StageFile`, `StageController` | Ordered stages and prerequisites; stage 5 uses the host executor. | [Stage models](../../../../pfp/domain/stages/stages.py) |
| `Stage1Response` through `Stage11Response` | Stage-specific fields plus candidate/demo identity, policy and continuation. Stage 5 includes host verdict, exact checks and survivors. Stages 7 and 8 are separate `BaseModel` classes; the other nine extend `BaseStageResponse`. | [Stage models](../../../../pfp/domain/stages/stages.py) |
| `DemoSpec`, `DemoCatalog` | Stable seed IDs, exact seed/catalog hashes, declared modes and source path. Historical folder labels are not current directories. | [Seed models](../../../../pfp/domain/stages/demos.py) |
| `seed_candidate_schema(seed_id)` | Seed-specific JSON Schema, with structural fields rather than supplied answers. The witness is not a newly invented Pydantic class. | [Seed checks](../../../../pfp/infrastructure/pilot_runners/seed_checks.py) (line 613) |
| `GateResult` | `passed`, failure reasons and evidence computed from the actual candidate. Three separate classes share this name, in `mssn_checks.py`, `gate_checks.py` and `declaration_checks.py` under `pilot_runners/`; import the one that matches the checker. | [Seed evaluator](../../../../pfp/infrastructure/pilot_runners/mssn_checks.py) |
| `PipelineExecutionReceipt` | Completed-stage tuple, responses and final terminal; this is the existing result type, not a request for another receipt system. | [Pipeline use case](../../../../pfp/use_cases/execute_stage_pipeline.py) |
| `TerminalStatus`, `RefusalCode` | Typed outcomes including refusal, unavailable oracle, budget exhaustion and infrastructure failure. | [Result types](../../../../pfp/domain/kernel/result.py) |

For DEMO_07, the candidate fields are `potential` (three entries), `d0` (2×3),
`original` (two entries) and `residual` (two entries). The host binds the declared
problem, fixes the gauge and recomputes the residual. Exact rational strings
are supported where declared; floats/booleans are not interchangeable with
exact arithmetic. A structurally valid object still needs the host check.

**Worked DEMO_07 check.** `_check_exact_potential` in
[seed_checks.py](../../../../pfp/infrastructure/pilot_runners/seed_checks.py)
(lines 451-468) fixes the problem as

```text
d0 = [[-1, 1, 0],      edge 1: vertex 0 -> vertex 1
      [ 0,-1, 1]]      edge 2: vertex 1 -> vertex 2
c  = [2, -3]           observed edge values
```

It requires `potential[0] = 0` (code `GAUGE_NOT_FIXED` otherwise) and computes
`residual_e = c_e - (d0 g)_e`. A zero residual needs `-g0 + g1 = 2` and
`-g1 + g2 = -3`. With `g0 = 0` this gives `g1 = 2` and `g2 = -1`.

| Candidate | `(d0 g)` | Residual | Host result |
| --- | --- | --- | --- |
| `potential = [0, 2, -1]` | `[2, -3]` | `[0, 0]` | accepted |
| `potential = [0, 2, 0]` | `[2, -2]` | `[0, -1]` | `NONZERO_RESIDUAL` |
| `potential = [1, 3, 0]` | `[2, -3]` | `[0, 0]` | `GAUGE_NOT_FIXED` |

The third row has the right differences but a shifted potential. The gauge rule
makes the witness unique, so the host can compare it exactly. The candidate must
also echo `d0` and `original` exactly, and report the residual the host
recomputes. This table was derived by hand from the source on 2026-10-20; it is
not a test run.

## Mode capability map

These are finite deciding checks, not claims that every theory named in a mode
has been implemented or that every mode has been exercised in a live run.

| Modes | Current behavior and boundary |
| --- | --- |
| 2, 14 | Direct pipeline support: sealed source and predicted-refusal control. A correctly predicted refusal is a successful control, not candidate acceptance. |
| 1 | Declared glyph roundtrip and supported level-0/1 alphabet. |
| 4 | Prompt-attached procedural anti-op with harmful and benign controls; not automatic empirical antibody admission. |
| 5 | Existing typed instruction resources, dependency/colour checks and finite composition. |
| 7, 8 | Supplied finite permutation/braid and exact involution checks. |
| 9 | Actual fixed-target Lean elaboration and axiom audit, requiring its toolchain. |
| 10, 11 | Typed cemetery regression replay and an existing finite Adversary checker. |
| 12, 13 | Supplied simplicial/connection and relational lossless/dependency/confluence checks. |
| 16, 17 | Finite perturbation/repair and provenance/independent seed-witness checks. |
| 18, 19, 20 | Supplied exact MUB triad, finite two-mark separation and bounded proposer/adversary witnesses. |
| 3, 6, 15 | Explicitly unavailable model-internal or interactive hooks. |

Source sets at the 2026-10-20 pin: `EXECUTABLE_MODES = {1, 4, 5, 7, 8, 13, 19}` in
`pfp_mode_checks.py` and `ADDITIONAL_MODES = {9, 10, 11, 12, 16, 17, 18, 20}` in
`pfp_mode_additional_checks.py`, 15 of the 20 catalog modes. Modes 2 and 14 are
handled by the pipeline itself; 3, 6 and 15 have no executor and refuse with
`MODE_EXECUTOR_UNAVAILABLE`.

Conditional modes require inputs through `--mode-inputs`, a JSON object keyed
by mode number. Read the exact field checks in
[core mode checks](../../../../pfp/use_cases/pfp_mode_checks.py) and
[additional mode checks](../../../../pfp/infrastructure/pilot_runners/pfp_mode_additional_checks.py).
Missing inputs/tools must remain distinguishable from rejected mathematics.
The seed CLI supports a contiguous stage prefix, not arbitrary ordering or loops:
`run-seed --stages N` accepts N from 1 to 11, default 5
([pfp.py](../../../../pfp/entrypoints/cli/pfp.py) line 75).

## Reuse typed learning material

The existing
[typed capability contract](../../../../operads/contracts/typed_capabilities_v1.py)
supports six discriminated kinds:

| Kind / type | Concrete content |
| --- | --- |
| `skill` / `SkillWireV1` | Declared inputs/output, instruction resource, dependencies and guard. |
| `anti_skill` / `AntiSkillWireV1` | Existing bounded predicate, trigger, finding enforcement and fixtures. |
| `rule` / `RuleWireV1` | Trigger, predicate and response. |
| `helpful_pattern` / `HelpfulPatternWireV1` | Conditions, construction and example. |
| `anti_pattern` / `AntiPatternWireV1` | Failure, witness and repair. |
| `antibody` / `AntibodyWireV1` | Prompt resource and URI, two declared signals, harmful/benign examples and candidate pharmacy status. |

Digested guidance shares `DigestedLessonWireV1`: exact source resource/revision,
evidence excerpt, failed claim, counterexample, cause, correction, verification,
applicability and exceptions. This gives discovery a place in the existing
system. An anecdote does not require creating another framework or automatically
becoming a global rule.

The wire profile is `oewas.sorted-ascii-json.v1`, not an RFC 8785 claim. Contracts
remain `Unadmitted`; generating IDE Markdown does not activate a detector or
establish its accuracy. Reuse the existing compiler after changing a reviewed
typed source:

```powershell
python -m operads.infrastructure.typed_contract_compiler --repo-root . --check
python -m operads.infrastructure.typed_contract_compiler --repo-root . --write
```

## Discoveries and applied repairs

The [Adversary challenge runbook](18_original_challenge_play.md) adds the
original-judge play route, actual IDE/OpenRouter outcomes and repairs to replay,
candidate progress, learning feedback and C023/C024/C027 checking. It keeps
finite witness acceptance separate from original experiment completion.

| Observation from the bounded work | Applied lesson or remaining limit |
| --- | --- |
| The model supplied the wrong candidate identity. | Render the selected identity in the model-visible schema, including negative controls; do not repair identity by transplanting another candidate's result. |
| Pricing refusal, HTTP 429 and ambiguous transport outcomes occurred. | Preserve safe diagnostic codes and unresolved accounting; missing cost is not zero and fallback is not implicit. |
| Offline fixtures had the right stage shape but no mathematical witness. | Use them for plumbing; a generic fixture cannot manufacture host acceptance. |
| A captured raw reply was changed. | Existing replay rejected the binding with zero provider calls; do not rewrite historical capture bytes. |
| Consolidation exposed import cycles, moved resources and omitted wheel assets. | Package ownership and installed resources need concrete checks; moving files alone does not establish a working application. |
| Some checks depend on native context, Lean or unavailable hooks. | Report an unavailable prerequisite truthfully, without declaring the mathematical claim false or fabricating a PASS. |

The [recorded consolidation results](../../../../pfp/documentation/pfp_consolidation_plan.md#bounded-implementation-handoff--2026-10-12)
contain the successful live/replay observation, failed attempts and outstanding
limits. This documentation update does not reissue those results as a new run.

The fixed grid and generator are retired. Reuse across tasks is a design goal;
the current evidence is finite. New tests should answer an improvement or
discovery question, produce a reusable lesson when warranted, and stay within
a declared budget. PFP may need additional engineering where observed failures
justify it.
