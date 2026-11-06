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

## Beyond WF5: eighteen derived families

WF6–WF23 extend the five runners into the procedures that the retained
pilots used: dialect sweeps, typed refusal, staged packets, bounded repair,
obstruction certificates, dual certificates, tribunals, rule transfer and
more. **They are designs, not runners yet.** Each one has a goal, a host
check, a process, its mathematics, and a team with a bounded boost step.

| Family | Goal | Builds on |
| --- | --- | --- |
| [WF6 — Dialect sweep](Workflow-DAG.md#wf6) | Measure, item by item, which presentation of the same task the host accepts more often, without changing the task. | WF5 |
| [WF7 — Typed refusal](Workflow-DAG.md#wf7) | Return the correct refusal code whenever the premises do not determine an answer. | WF1 |
| [WF8 — Staged sealed packets](Workflow-DAG.md#wf8) | Each stage produces a sealed, typed output; the final answer checks. | WF2, WF5 |
| [WF9 — Bounded check-and-repair](Workflow-DAG.md#wf9) | An accepted reply within L attempts, or a recorded stop at the limit. | WF2 |
| [WF10 — Local-to-global obstruction certificate](Workflow-DAG.md#wf10) | A checked gluing witness or a checked obstruction class for the declared cover. | WF4, WF9 |
| [WF11 — Dual-certificate synthesis](Workflow-DAG.md#wf11) | A frozen solver whose every output carries a certificate the judge accepts on hidden cases. | WF3, WF9 |
| [WF12 — Mechanism-control arms](Workflow-DAG.md#wf12) | An arm comparison on a fixed carrier whose only difference is the mechanism note. | WF6, WF3 |
| [WF13 — Exact-domain capsule battery](Workflow-DAG.md#wf13) | One checked answer or refusal per domain capsule. | WF1, WF7 |
| [WF14 — Immune failure classification](Workflow-DAG.md#wf14) | Detectors that catch the recorded failures and never fire on the sealed self panel. | WF7, WF12 |
| [WF15 — Adversary tribunal](Workflow-DAG.md#wf15) | A verdict that the finite check supports, with both sides frozen first. | WF4, WF14 |
| [WF16 — Substrate crosswalk](Workflow-DAG.md#wf16) | A translation that preserves every declared relation, with alternatives recorded. | WF5, WF10 |
| [WF17 — Witnessed-difference programme](Workflow-DAG.md#wf17) | Each claimed difference has a checked witness and each equivalence a checked certificate. | WF10, WF11 |
| [WF18 — Dossier replay campaign](Workflow-DAG.md#wf18) | A replayable 5 x 5 + 5 campaign whose every grade reproduces from stored bytes. | WF6, WF12 |
| [WF19 — Failure-derived rule transfer](Workflow-DAG.md#wf19) | A rule that improves held-out acceptance without new false positives. | WF12, WF14 |
| [WF20 — Derivation loop with lift grants](Workflow-DAG.md#wf20) | Discharge the named obligations or stop with a typed record at the loop limit. | WF9, WF10, WF19 |
| [WF21 — Structural prompt rewriting](Workflow-DAG.md#wf21) | Rewrites that attach hints or encodings without touching protected bytes. | WF5 |
| [WF22 — Certified cost ladder](Workflow-DAG.md#wf22) | Decide each pre-registered hypothesis on this bank, at this rung, with this gate. | WF6, WF8, WF18 |
| [WF23 — Judge-packet custody audit](Workflow-DAG.md#wf23) | Show that every challenge packet is sealed and leak-free before any team runs it. | WF11 |

See the [workflow DAG](Workflow-DAG.md) for the dependency graph, the team
for each family and how the boost step works. The machine-readable graph is
[`workflows/dag/workflow_dag.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/dag/workflow_dag.json).

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

- [Workflow DAG](Workflow-DAG.md): WF1–WF23, their dependencies, teams and boost steps.
- [Workflow library](Workflow-Library.md): base families and versioned recipes.
- [Troubleshooting](Workflow-Troubleshooting.md): what a refusal means and what to do.
- [Results and costs](Workflow-Results.md): successful paths **and** failed attempts.
- [Glossary](Workflow-Glossary.md): short explanations when a term gets in the way.
- [Exact examples](Workflow-Examples.md): prepared prompts and typed contracts.
- [Author a recipe](Workflow-Authoring.md): the route for adding future variants.

**Read only what you need.** The detailed [contracts](Workflow-Contracts.md)
and [recipe template](Workflow-Recipe-Template.md) are reference pages.
