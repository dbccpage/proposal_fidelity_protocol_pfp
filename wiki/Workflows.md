# Choose a PFP workflow

**Start with [WF1](Workflow-WF1.md): one task, one reply, one independent check.**
Add another mechanism when your work needs it. You can stop at any workflow.

## Pick the problem you have

| I need to… | Choose | Model calls on the normal path |
| --- | --- | ---: |
| Get one answer in a declared format and check it | [WF1 — typed answer](Workflow-WF1.md) | 1 |
| Keep the operations, missing information and proposed repair moves | [WF2 — full slots](Workflow-WF2.md) | 1 |
| Prepare useful operation guidance before solving | [WF3 — mine, then solve](Workflow-WF3.md) | 2 |
| Compare five isolated answers against one global check | [WF4 — five agents + LGGR](Workflow-WF4.md) | 6 |
| Preserve the task through a grammar rewrite before WF4 | [WF5 — checked rewrite](Workflow-WF5.md) | 6 |

WF4/WF5 share one mining call across five solvers. The demonstrated WF5 rewrite
is deterministic and adds zero model calls. Repairs and failed attempts are
additional actions and stay in the accounting.

## Your shortest route

1. [Get a first result](Workflow-Start-Here.md).
2. Follow the numbered steps on one workflow page.
3. Keep the input, actual reply and check result together.
4. Stop when the named check gives you the evidence you need.

**Coming back later?** Open your run folder and find the last completed step.
The pages tell you what to keep before moving on.

## What is available

All five automated runners are available in the standalone migration branch.
[Install and run](Workflow-Running.md) gives exact commands, offline controls,
shared budgets and replay. The guides also retain a small manual WF1 walkthrough.
[Integration status](Workflow-Integration-Status.md) distinguishes migrated
versions from the original experiments.

The benchmark task was integer addition. Its results do not establish that the
workflows solve arbitrary research problems or eliminate hallucinations.

## Find the next thing

- [Workflow library](Workflow-Library.md): base families and versioned recipes.
- [Troubleshooting](Workflow-Troubleshooting.md): what a refusal means and what to do.
- [Results and costs](Workflow-Results.md): successful paths **and** failed attempts.
- [Glossary](Workflow-Glossary.md): short explanations when a term gets in the way.
- [Exact examples](Workflow-Examples.md): prepared prompts and typed contracts.
- [Author a recipe](Workflow-Authoring.md): the route for adding future variants.

**Read only what you need.** The detailed [contracts](Workflow-Contracts.md)
and [recipe template](Workflow-Recipe-Template.md) are reference pages.
