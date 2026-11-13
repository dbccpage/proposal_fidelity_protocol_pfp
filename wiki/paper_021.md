# Paper 021: The workflow DAG — process and mathematics of WF1–WF49

**Status:** Author-review draft; not an external deposit  
**Folder:** [`atlas/archive/pfp/021_pfp_workflow_dag_process_and_mathematics`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/atlas/archive/pfp/021_pfp_workflow_dag_process_and_mathematics)

## In brief

Five workflows run today. The retained pilot experiments used many more
procedures that were never named. This paper names eighteen of them,
WF6–WF23, places all twenty-three in one dependency graph, and writes down
what each one does and which mathematics its check relies on.

## What it covers

- The common shape of a workflow: frozen task, procedure, host check, budget
  and retained record, with the rule that only the host check accepts.
- For each family: the process, the acceptance mathematics (preservation of
  rewrites, rank conditions for refusal, seal chains, cochain repair, first
  cohomology and local-green/global-red, LP duality and Farkas certificates,
  negative selection, Kripke model checking, double-pushout rewriting, paired
  tests) and the pilots it came from.
- A team design per family: a goal, roles on Sonnet, Run O or Run F, a
  teamwork pattern and a bounded boost step.

## What it does not claim

WF6–WF23 are designs, not runners, and many source pilots were never
dispatched. The model-tier assignments are a starting design, not a
measurement. See the [workflow DAG](workflow_dag.md).

---

Previous: [Paper 020](paper_020.md) · [Papers](papers.md)
