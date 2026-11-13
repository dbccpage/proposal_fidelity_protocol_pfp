# Steering examples

These pages collect the distinct ways the source project steered language
models: what it put into a prompt, what it masked or changed while a model was
decoding, and what it refused to accept from a reply. Each page describes one
example, how to replicate it with the tools in this repository, and how it
relates to PFP, the [Epistemic Immune System](eis.md) and
[Prompt Civilization](pciv.md).

The examples were mined from the source project's documentation, experiment
folders and tests. Tests that were already ported to `workflows/` are not repeated
here; the [test catalog](test_catalog.md) links them, and the table at the end
of this page points to the relevant ones.

## The common rule

Almost every example follows one rule: **a model's reply is a proposal, and only
a host check can turn it into a result.** Steering changes what the model is
likely to propose. It never changes who decides. Where an example did change
model behaviour directly (decode masks, attention edits), the host still checks
the output afterwards.

## Tools used for replication

| Tool | What it can replicate | How to start it |
| --- | --- | --- |
| [PFP Lab](pfp_lab.md) | The host side: claims checked by recomputation, refusals kept in the receipt, retraction | `python -m pfp_lab.cli.main run --pack refusal-gallery` |
| Pure Python modules in `pfp/`, `eis/` and `ops/adversary/` | Single checks such as clarification, two-signal admission and pressure screens | Set `$env:PYTHONPATH = "ops;."` in PowerShell, then import them |
| The local swarm in `ops/adversary/` | The full multi-role run (prompt preparation, turns, checks, reports) | See [Running the local swarm](#running-the-local-swarm) below |
| `HfLocalRunner` in `pfp/infrastructure/adapters/decode_controls/` | Decode masks, attention edits and activation steering on a local model | Needs PyTorch, `transformers` and a locally cached small model |
| Native host in `code/rust/` | Prompt geometry, the immune-fence renderer and critique parsing | `cargo build --manifest-path code/rust/Cargo.toml -p pfp`; the local swarm finds it through `CORE_SYMBOL_GAME_HOST` |

Every page marks which of these it needs. Snippets marked "checked" were run on
Windows with Python 3.14 on 2026-10-27.

## Running the local swarm

The swarm in `ops/adversary/` runs one task through a panel of 22 roles. Each
role is one PFP turn: the host prepares a bound prompt, a model (by default you,
in your own IDE session) writes the reply, and the host checks it. The role
roster in `ops/adversary/roles/adversary_panel.yaml` was written for this
repository: neutral names and a one-line duty per role. A role name never
authenticates a worker, and one worker playing all roles is not 22 independent
reviewers.

It needs the `pfp` binary from `code/rust` (`cargo build --manifest-path code/rust/Cargo.toml -p pfp`).
Run it from the `ops` folder; the repository root has its own `governance`
package that would otherwise shadow the one in `ops`. In PowerShell:

```powershell
cd ops
$env:PYTHONPATH = ".;.."
$env:CORE_SYMBOL_GAME_HOST = "<path to>\pfp.exe"
$tw = "python -B -m adversary.entrypoints.cli teamwork"

# Start: a task must come with its own acceptance check, or start refuses.
iex "$tw start --state .scratch/run/state.json --objective 'Add two integers 2 and 3' --checker-id my-check-v1 --checker-source .scratch/run/checker.py --check-command python .scratch/run/checker.py"
iex "$tw check --state .scratch/run/state.json"         # run the bound checker once
iex "$tw next --state .scratch/run/state.json"          # first action: native checks
iex "$tw native-gates --state .scratch/run/state.json"
iex "$tw next --state .scratch/run/state.json"          # first model turn
```

The `next` output holds `pfp_turn.system`, `pfp_turn.user` and
`pfp_turn.response_schema`. Write a reply that copies `task_id`, `attempt_id` and
`input_sha256` from `pfp_turn.binding` and puts the role's answer under `answer`,
save it, then:

```powershell
iex "$tw submit --state .scratch/run/state.json --raw-reply .scratch/run/reply.json"
iex "$tw next --state .scratch/run/state.json"
```

Repeat until `work_status` is terminal; `next` tells you when a host step
(`check`, `native-gates`, `ddc-store` and so on) is due instead of a model turn.
Checked on 2026-10-27 as far as the second role's turn. `teamwork --help` lists
the other commands, including `run` for a routed provider, `resume` and
`persist`. Optional schedules are in `ops/adversary/roles/panel_schedules.yaml`
(`--schedule quorum3` and others); with none, every role runs in order.

## Examples

### Shaping the prompt

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Prompt geometry](steering_prompt_geometry.md) | Measure prompts and replies without letting the measurement choose a rewrite | PFP, PCIV |
| [Admitted guidance](steering_admitted_guidance.md) | Only reviewed guidance may be rendered into a prompt | EIS |
| [Compact prompt profiles](steering_compact_prompt_profiles.md) | Replace repeated history with labelled digests so long runs fit | PFP, PCIV |
| [Selected hint](steering_selected_hint.md) | Attach one fixed hint and recheck the task with the original checker | PFP, Operads |
| [Plain seed experiment](steering_plain_seed_experiment.md) | Give the model the user's one-line task, not a long designed seed | PFP |
| [Prompt families](steering_prompt_families.md) | A prompt is a relation to a reader; its label is a proposal | PCIV |

### Shaping decoding

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Self-certification masking](steering_self_certification_masking.md) | Mask tokens such as `VERIFIED` so a proposer cannot certify itself | PFP |
| [Attention and activation interventions](steering_attention_and_activation.md) | Mask distractor keys, patch heads, add steering vectors | PFP |

### Shaping what is accepted

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Clarify instead of inventing](steering_clarify_instead_of_inventing.md) | A checked request for missing inputs is a valid outcome, never a solution | PFP |
| [Closed artifact schema](steering_closed_artifact_schema.md) | The model fills a closed object; the host encodes it | PFP |
| [Checked reuse](steering_checked_reuse.md) | The model acknowledges a registered procedure; the host applies checked bytes | PFP, Operads |
| [Honest verdicts](steering_honest_verdicts.md) | Verdicts come only from bound, exact evidence, never from wording | PFP |
| [Truthful turn record](steering_truthful_turn_record.md) | Record the reply as sent; never fabricate a turn | PFP |
| [Mediated model calls](steering_mediated_model_calls.md) | Every model call goes through the PFP exchange | PFP |
| [Critique loop](steering_critique_loop.md) | Typed critiques, a diff oracle and a ledger of rejected candidates | PFP, PCIV |
| [Pressure screens](steering_pressure_screens.md) | Detect false urgency, yielding without evidence and manufactured consensus | EIS |
| [Self-certification screen](steering_self_certification_screen.md) | Two independent signals before anything is suppressed | EIS |
| [Failure-first accounting](steering_failure_first_accounting.md) | Approvals carry no weight; "none found" is not evidence | PFP |

### Learning from runs

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Learning from runs](steering_learning_from_runs.md) | A lesson needs two runs and no counterexample; an antibody needs a reproduced refutation | EIS, PCIV |
| [Harness evolution](steering_harness_evolution.md) | Evolve the harness, not the model, under a frozen protocol and budget | PCIV |

## Already covered by test pages

| Steering idea in the source | Page here |
| --- | --- |
| Prompts built by repeated string replacement can rewrite their own data | [Template substitution](test_template_substitution.md) |
| Strict decoding of a provider's JSON reply | [Strict provider reply JSON](test_strict_provider_reply_json.md) |
| Byte ceilings on prompt and reply | [Provider byte ceilings](test_provider_byte_ceilings.md) |
| Prompt plus checker tasks that refuse misses and drifted prompts | [Calibration task bank](test_calibration_task_bank.md) |
| Comparing prompt or model arms with exact statistics | [Yardstick arm statistics](test_yardstick_arm_statistics.md) |
| Telemetry for multi-round candidate revision | [Candidate revision telemetry](test_candidate_revision_telemetry.md) |
| Comparing two roles' submissions literally | [Role submission comparison](test_role_submission_comparison.md) |
| Role-gated review transitions | [Paper-run role-gated transitions](test_paper_run_role_gated_transitions.md) |
| Append-only stage receipts | [Stage receipt tape](test_stage_receipt_tape.md) |

## Not included

Some source documents are not about steering a model and have no page here:
archive recovery and byte-transfer custody, a sandbox for bounding the original
checker's resources, crash recovery for multi-agent runs, a signed live circuit
whose subject is budgeting and signing, provider error-handling repairs, a
finite report operation, notes on digesting older packets, and an ion-channel
binding experiment that measures conditional energies rather than model
behaviour. Role-specific gate and persona designs are not published.
