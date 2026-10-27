# 12. Current outputs, troubleshooting and seed to P*

AuthorityEffect: None. Source inspected 2026-10-12:
[seed CLI](../../../../pfp/entrypoints/cli/pfp.py) and
[campaign adapter](../../../../pfp/infrastructure/adapters/pfp_campaign.py).

## Seed-run capture

A live `run-seed` uses a new directory. The numbered model stages retain:

```text
<new-output>/
  config.json
  pricing.json
  budget.sqlite3
  stage_1/                  # likewise other dispatched model stages
    request.json
    reservation.json
    provider_response.json
    receipt.json
    transport_failure.json  # when an attempt fails
```

Stage 5 is a host check, so it is not another provider-stage directory. The
seed CLI prints the pipeline summary and host checks as JSON to stdout. Collate
that output with the existing capture rather than assuming a manifest.yaml or
summary.json is written by every interface. The separate bounded challenge
campaign has its own summary layout.

Replay reads captured configuration, pricing, request, raw reply and evaluation
bindings. It makes zero provider calls. The displayed cost describes the
original capture; it is not new spending. Preserve these bytes for replay, and
apply new learning to guidance/code rather than rewriting a historical run.

## Troubleshooting

| Observation | Action |
| --- | --- |
| `PREPARED_ONLY` | The seed was assembled, not executed. Supply a witness or explicitly run a model. |
| Completed prefix before stage 5 | Treat it as stage execution, not mathematical acceptance. |
| Host rejection | Inspect the actual candidate and failure reasons. A model's PASS claim is insufficient. |
| Missing mode inputs or mode 3/6/15 hook | Supply the supported mode contract or record unavailability; this is not mathematical disproof. |
| `REPLAY_SEED_MISMATCH` / `REPLAY_BINDING_MISMATCH` | Use the original capture and matching inputs; do not rewrite digests or captured bytes. |
| Existing output directory | Choose a new live directory; use `--replay` to inspect the existing one. |
| Pricing-profile refusal or HTTP 429 | Retain the diagnostic and stop this attempt. There is no implicit fallback. |
| Unknown transport outcome or missing billing | Preserve the unresolved reservation. Unknown cost is not zero. |
| Missing native/Lean/source context | Report the prerequisite as unavailable; do not substitute a synthetic witness or fabricated acceptance. |

The [practical guide](13_practical_pfp_and_discovery.md) contains the commands;
[types and lessons](../docs/16_current_types_and_learnings.md) explains the
interfaces and applied repairs. Do not tune a pilot indefinitely: collate the
bounded result, remaining error and useful lesson, then move on.

## Seed to P*

`build_seed_requests` preserves the catalog seed inside the existing SPK-001
prompt template without a provider call:

```powershell
python -m pfp.infrastructure.pilot_runner --seed-id DEMO_07
```

The [template](../../../../pfp/infrastructure/yaml/prompts/prompt_template.yaml)
and [seed catalog](../../../pilots/matrix/seeds.yaml) are the current sources.
`PromptTemplate`, `PromptPacket` and `PfpStagePromptInput` provide the existing
programmatic contracts for variable prompt/response experiments. The seed CLI
does not expose a `--template` flag. Assembly alone does not demonstrate an
improvement in model output.
