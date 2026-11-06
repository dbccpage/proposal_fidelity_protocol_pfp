# WF36: Guarded staged slot materialisation

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF8](../wf08_staged_sealed_packets/README.md).

**Goal:** Admit only complete stage-1 packets; abstain otherwise.

## How it works

1. Stage 1 emits typed slots
2. A complete guard with one retry gates stage 2 or abstains
3. Two-stage tree-then-chord for higher cycle rank
4. A dichotomic guard removes the lazy false-refusal attractor

## The check

Host check: exact cochain check.

- `syndrome r* = S c shared across verdict, repair and audit; a partial guard leaves a false-green kernel`

## Where it comes from

Sources: P027 §5.3, §5.6-5.8.

Live on a local 0.5B model, gpt-4o-mini and a 7B model; 40-case ladder: 7B unstaged 9/40 exact, guarded 2/40 admitted and both optimal.

## Team

Pattern `relay`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when guard fails: one retry, then abstain (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf36) · [machine-readable entry](../dag/workflow_dag.json)
