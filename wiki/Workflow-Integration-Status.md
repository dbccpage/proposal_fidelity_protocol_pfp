# What runs where?

**Use this page before copying an older command.** The standalone repository
and the earlier monorepo experiments have different package layouts.

## Current repository entry points

| Entry point | Verified purpose | Scope |
| --- | --- | --- |
| `python -m pfp_lab.cli.main run ...` and `verify ...` | Run and replay a declared Lab scenario pack. | Exact finite teaching scenarios; no fresh LLM call. |
| `pfp` / `pfp.exe` released CLI | Check prompt/reply issues and work with its declared packet commands. | Follow the [CLI README](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/code/rust/pfp_cli); static checks are not an arbitrary task oracle. |
| `pfp.use_cases.pfp_prompt`, `pfp.infrastructure.task_turn` | Prepare/check a typed task with an injected independent judge. | [WF1's manual walkthrough](Workflow-WF1.md), from a source checkout with `jsonschema` installed. |

The WF1 example has its own saved preparation files and negative controls. It
does not claim the durable provider-accounting envelope of the historical runners.

## Historical integration prototypes

The first WF1–WF5 experiments used `omega_engine_pfp.workflows.wf0001` through
`wf0005` in the older integrated engine. Shared provider accounting and the LGGR
adapter came from sibling engine components. Their final historical versions
were WF1/WF2 0.1.0, WF3 0.3.0, WF4 0.1.0 and WF5 0.1.4.

Those runners are **not installed** by this repository's `pfp-lab` packaging.
Renaming an old command to `python -m pfp.workflows.wf0004` does not create a
supported runner. Some imported engine adapters still expect external sibling
packages. This documentation does not hide that integration boundary.

The published base guides are complete patterns/manual integration recipes.
Automatic standalone runners, other task families and provider adapters need
their own implemented and tested recipe versions before being marked runnable.
The [library registry](Workflow-Library.md) records these states separately.

## Evidence you can inspect

[Results and costs](Workflow-Results.md) publishes the retained measurements,
actual raw replies selected for this documentation, source hashes and failures.
Those historical observations are not a fresh Oct 31 provider test or proof
that a package install executes the older runners.

The previous original-workspace replay and test receipts remain historical
evidence. The new documentation checks exercise the current manual entry points,
links, registry and selected evidence independently. Digest checks provide
integrity relative to the records, not authenticated vendor invoices.

## If you need a new automatic integration

Start with the [recipe template](Workflow-Recipe-Template.md). Bind the task,
checker, provider accounting, concurrency, grammar and source versions; run a
positive and a decisive negative control. Publish actual availability rather
than marking a planned combination supported.

[Back to workflows](Workflows.md) · [Troubleshooting](Workflow-Troubleshooting.md)
