# Choose a PFP workflow

**Start with [WF1](Workflow-WF1.md): one task, one reply, one independent check.**
Add another mechanism when your work needs it. You can stop at any workflow.

**QM benchmark:** [five recipes and one repair](Workflow-QM-Benchmark.md) cover
a direct solver, self-critique, and rational counterexample panels. The
[first live pilot](Workflow-QM-Pilot-2026-11-10.md) cost USD 0.008398 across six
attempts; none produced a complete solution. Implementation is in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58); raw receipts remain in
the working checkout, pending publication to main. The WF1–WF5 measurements below
concern the earlier integer-addition task.

The [Hamiltonian workflows](Workflow-QM-Hamiltonian.md) now add an exact public-input
matrix check, one bounded correction, and ungated/host-computation controls. Their
eight-run comparison demonstrates refusal of incorrect representations, not a
complete or more accurate final solution.

The [output-allowance comparison](Workflow-QM-Hamiltonian.md#output-allowance-control)
scored 62/100 for a longer direct response. A subsequent [five-section control](Workflow-QM-Sections.md)
scored 26/100 at higher cost. Another model's direct answer scored 83/100;
[self-critique](Workflow-QM-Controls.md#deepseek-direct-versus-self-critique) scored
88/100 at greater money, token and time cost. None is fully correct, and these
single-item observations do not establish a system-level advantage.
Implementation is reviewable in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58).

The new [native polynomial-check workflows](Workflow-QM-Charpoly.md) connect exact
Rust arithmetic to proposal, optional repair and synthesis. Their first comparison
delivered no answer in the checked arm and an incomplete answer in the unchecked
arm; this provides no evidence of a performance improvement.

## Where the files are

Every workflow has one folder in the repository, numbered the same as here:
[`workflows/wf01_typed_answer/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf01_typed_answer)
through `workflows/wf49_…`. Each folder's README says how to run and replay
it and links to its code. The full list is the
[workflows index](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/README.md).

## Pick the problem you have

| I need to… | Choose | Adds to WF1 | Model calls | Evidence so far |
| --- | --- | --- | ---: | --- |
| Get one answer in a declared format and check it | [WF1 — typed answer](Workflow-WF1.md) | (the base) | 1 | 1 task; accepted on two models (Oct 28 prototype, Nov 6 shipped runner) |
| Keep the operations, missing information and proposed repair moves | [WF2 — full slots](Workflow-WF2.md) | a larger response contract | 1 | 1 task; accepted on two models; repair moves never exercised |
| Prepare operation guidance before solving | [WF3 — mine, then solve](Workflow-WF3.md) | a mining stage | 2 | 1 task; the Oct 28 2-call figure is stitched from two runs (real path 10 actions, $0.0043); refused on Nov 6 at its 1,300-token solver limit |
| Compare five isolated answers against one global check | [WF4 — five agents + LGGR](Workflow-WF4.md) | five isolated solvers and a global check | 6 | 1 task; all five correct on two models |
| Preserve the task through a grammar rewrite before WF4 | [WF5 — checked rewrite](Workflow-WF5.md) | a deterministic rewrite step | 6 | 1 task; accepted Oct 28 after 4 failed miners; Nov 6 miner refused on schema |

**What the evidence shows.** Every result so far is one integer-addition task.
On the earlier prototype all five gave the right answer, and none was cheaper, faster or
more accurate than WF1 on it. That is a starting point, not a ranking: pick
the extension your task needs, not the highest number. See
[Results and costs](Workflow-Results.md) for every attempt, including failures.

WF4/WF5 share one mining call across five solvers. The demonstrated WF5 rewrite
is deterministic and adds zero model calls. Repairs and failed attempts are
additional actions and stay in the accounting.

## One base, several extensions

WF2–WF5 are WF1 plus one switch each: a larger response contract (WF2), a
mining stage before solving (WF3), five isolated solvers with a global check
(WF4), and a deterministic rewrite before WF4 (WF5). The
[workflow DAG](Workflow-DAG.md) uses that shape for everything else: one base
workflow, a few procedure extensions, experiment designs that wrap any
workflow, and design proposals (WF6–WF23) that have **no runner and no run
yet**. WF24–WF49 were added on 2026-11-06 from the certified-challenge
findings notes and the papers, together with 46 recorded perturbations
(variations of an existing workflow's settings or steps, such as scratchpad
on or off, completion ceilings, hint levels or neutral case identifiers).

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

- [Workflow DAG](Workflow-DAG.md): WF1–WF49, their dependencies, teams and boost steps.
- [Frozen QM benchmark](Workflow-QM-Benchmark.md): controls, rational panels, budgets and evidence limits.
- [Workflow library](Workflow-Library.md): base families and versioned recipes.
- [Troubleshooting](Workflow-Troubleshooting.md): what a refusal means and what to do.
- [Results and costs](Workflow-Results.md): successful paths **and** failed attempts.
- [Glossary](Workflow-Glossary.md): short explanations when a term gets in the way.
- [Exact examples](Workflow-Examples.md): prepared prompts and typed contracts.
- [Author a recipe](Workflow-Authoring.md): the route for adding future variants.

**Read only what you need.** The detailed [contracts](Workflow-Contracts.md)
and [recipe template](Workflow-Recipe-Template.md) are reference pages.
