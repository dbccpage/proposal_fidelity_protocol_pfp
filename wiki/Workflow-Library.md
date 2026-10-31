# Workflow library

**Five base families. Many possible recipes. Every published version has a clear scope.**

Start with [Choose a workflow](Workflows.md). This page is for finding, naming
and maintaining variants as the library grows.

## A family is a pattern; a recipe is a particular use

`WF1` means one typed proposal and an independent check. A recipe says which
task, input/output contract, checker, prompt profile, tool adapter and version
make that pattern useful in a particular setting.

For example, a future code-review recipe and a future writing recipe could both
use WF1. They need different acceptance checks. Integer-sum results do not
validate either of them.

## The current library

| Recipe | Family | What you can use today | Evidence |
| --- | --- | --- | --- |
| `wf0001.integer_sum.manual.v1` | WF1 | Current-repository typed task-turn walkthrough | Executed offline example and negative controls. |
| `wf0002.integer_sum.reference.v1` | WF2 | Standalone full-slot runner and recipe | Retained Oct 28 single-response experiment. |
| `wf0003.integer_sum.reference.v1` | WF3 | Standalone mining/freeze/solve runner | Retained mining and repair history. |
| `wf0004.integer_sum.reference.v1` | WF4 | Standalone concurrent five-agent runner | Retained concurrent six-call experiment. |
| `wf0005.integer_sum.reference.v1` | WF5 | Standalone checked packet-rewrite runner | Retained failures and accepted six-call path. |

[Install and run](Workflow-Running.md) covers the automated runners. The manual
recipe IDs below remain historical documentation identities; the registry now
also includes a separate `.automated.v1` ID for each migrated runner.

The machine-readable registry is
[`docs/workflows/catalog.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/catalog.json).
It distinguishes documentation versions from historical runtime versions.
[Integration status](Workflow-Integration-Status.md) explains the current packaging boundary.

## Find a recipe by what matters

Use these axes rather than a single long list of hundreds of titles:

| Axis | Examples |
| --- | --- |
| Task | Integer arithmetic, writing, code review, a finite scientific certificate. |
| Acceptance | Exact computation, unit tests, schema-only, expert review. |
| Interface | Manual model response, IDE, accounted provider adapter. |
| Structure | Typed answer, full slots, frozen mining, five-agent LGGR, checked rewrite. |
| Resources | Call count, output ceiling, total cost/time allowance and stop rule. |
| Evidence | Documented, fixture-tested, measured, experimental, retired. |

The examples in this table are classification choices, not a claim that all
those recipes already exist. Only actual registry entries count as published recipes.

## Version rules

- Keep `WF1`–`WF5` as stable family names.
- Give each usable recipe its own ID, task domain and explicit version.
- Change the version when the prompt, schema, checker, grammar, composition or
  budget semantics change. Keep the earlier definition and results.
- A documentation correction has its own revision; do not quietly relabel old
  experimental results as measurements of the corrected runtime.
- Mark planned and retired recipes clearly. A draft page does not mean a runner exists.

## Add one useful recipe

Use the [recipe template](Workflow-Recipe-Template.md), follow the
[authoring checklist](Workflow-Authoring.md), and submit source, checks and
evidence through a pull request. Add it to the registry only with its actual
availability and validation state. We can grow to hundreds without inventing
hundreds of supported combinations in advance.
