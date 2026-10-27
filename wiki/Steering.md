# Steering examples

These pages collect the distinct ways the source project steered language
models: what it put into a prompt, what it masked or changed while a model was
decoding, and what it refused to accept from a reply. Each page describes one
example, how to replicate it with the tools in this repository, and how it
relates to PFP, the [Epistemic Immune System](EIS.md) and
[Prompt Civilization](PCIV.md).

The examples were mined from the source project's documentation, experiment
folders and tests. Tests that were already ported to `demos/` are not repeated
here; the [test catalog](Test-Catalog.md) links them, and the table at the end
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
| [PFP Lab](PFP-Lab.md) | The host side: claims checked by recomputation, refusals kept in the receipt, retraction | `python -m pfp_lab.cli.main run --pack refusal-gallery` |
| Pure Python modules in `pfp/`, `eis/` and `ops/adversary/` | Single checks such as clarification, two-signal admission and pressure screens | Set `$env:PYTHONPATH = "ops;."` in PowerShell, then import them |
| The local swarm in `ops/adversary/` | The full multi-role run (prompt preparation, turns, checks, reports) | Not runnable yet: its command line still needs governance modules that were not copied in |
| `HfLocalRunner` in `pfp/infrastructure/adapters/decode_controls/` | Decode masks, attention edits and activation steering on a local model | Needs PyTorch, `transformers` and a locally cached small model |
| Native host in `code/rust/` | Prompt geometry, the immune-fence renderer and critique parsing | `cargo build --manifest-path code/rust/Cargo.toml -p pfp` (wiring the built host into the Python adapters is not finished) |

Every page marks which of these it needs. Snippets marked "checked" were run on
Windows with Python 3.14 on 2026-10-27.

## Examples

### Shaping the prompt

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Prompt geometry](Steering-Prompt-Geometry.md) | Measure prompts and replies without letting the measurement choose a rewrite | PFP, PCIV |
| [Admitted guidance](Steering-Admitted-Guidance.md) | Only reviewed guidance may be rendered into a prompt | EIS |
| [Compact prompt profiles](Steering-Compact-Prompt-Profiles.md) | Replace repeated history with labelled digests so long runs fit | PFP, PCIV |
| [Selected hint](Steering-Selected-Hint.md) | Attach one fixed hint and recheck the task with the original checker | PFP, Operads |
| [Plain seed experiment](Steering-Plain-Seed-Experiment.md) | Give the model the user's one-line task, not a long designed seed | PFP |
| [Prompt families](Steering-Prompt-Families.md) | A prompt is a relation to a reader; its label is a proposal | PCIV |

### Shaping decoding

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Self-certification masking](Steering-Self-Certification-Masking.md) | Mask tokens such as `VERIFIED` so a proposer cannot certify itself | PFP |
| [Attention and activation interventions](Steering-Attention-And-Activation.md) | Mask distractor keys, patch heads, add steering vectors | PFP |

### Shaping what is accepted

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Clarify instead of inventing](Steering-Clarify-Instead-Of-Inventing.md) | A checked request for missing inputs is a valid outcome, never a solution | PFP |
| [Closed artifact schema](Steering-Closed-Artifact-Schema.md) | The model fills a closed object; the host encodes it | PFP |
| [Checked reuse](Steering-Checked-Reuse.md) | The model acknowledges a registered procedure; the host applies checked bytes | PFP, Operads |
| [Honest verdicts](Steering-Honest-Verdicts.md) | Verdicts come only from bound, exact evidence, never from wording | PFP |
| [Truthful turn record](Steering-Truthful-Turn-Record.md) | Record the reply as sent; never fabricate a turn | PFP |
| [Mediated model calls](Steering-Mediated-Model-Calls.md) | Every model call goes through the PFP exchange | PFP |
| [Critique loop](Steering-Critique-Loop.md) | Typed critiques, a diff oracle and a ledger of rejected candidates | PFP, PCIV |
| [Pressure screens](Steering-Pressure-Screens.md) | Detect false urgency, yielding without evidence and manufactured consensus | EIS |
| [Self-certification screen](Steering-Self-Certification-Screen.md) | Two independent signals before anything is suppressed | EIS |
| [Failure-first accounting](Steering-Failure-First-Accounting.md) | Approvals carry no weight; "none found" is not evidence | PFP |

### Learning from runs

| Page | Idea | Mainly relates to |
| --- | --- | --- |
| [Learning from runs](Steering-Learning-From-Runs.md) | A lesson needs two runs and no counterexample; an antibody needs a reproduced refutation | EIS, PCIV |
| [Harness evolution](Steering-Harness-Evolution.md) | Evolve the harness, not the model, under a frozen protocol and budget | PCIV |

## Already covered by test pages

| Steering idea in the source | Page here |
| --- | --- |
| Prompts built by repeated string replacement can rewrite their own data | [Template substitution](Test-Template-Substitution.md) |
| Strict decoding of a provider's JSON reply | [Strict provider reply JSON](Test-Strict-Provider-Reply-JSON.md) |
| Byte ceilings on prompt and reply | [Provider byte ceilings](Test-Provider-Byte-Ceilings.md) |
| Prompt plus checker tasks that refuse misses and drifted prompts | [Calibration task bank](Test-Calibration-Task-Bank.md) |
| Comparing prompt or model arms with exact statistics | [Yardstick arm statistics](Test-Yardstick-Arm-Statistics.md) |
| Telemetry for multi-round candidate revision | [Candidate revision telemetry](Test-Candidate-Revision-Telemetry.md) |
| Comparing two roles' submissions literally | [Role submission comparison](Test-Role-Submission-Comparison.md) |
| Role-gated review transitions | [Paper-run role-gated transitions](Test-Paper-Run-Role-Gated-Transitions.md) |
| Append-only stage receipts | [Stage receipt tape](Test-Stage-Receipt-Tape.md) |

## Not included

Some source documents are not about steering a model and have no page here:
archive recovery and byte-transfer custody, a sandbox for bounding the original
checker's resources, crash recovery for multi-agent runs, a signed live circuit
whose subject is budgeting and signing, provider error-handling repairs, a
finite report operation, notes on digesting older packets, and an ion-channel
binding experiment that measures conditional energies rather than model
behaviour. Role-specific gate and persona designs are not published.
