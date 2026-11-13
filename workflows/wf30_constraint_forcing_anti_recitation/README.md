# WF30: Constraint-forcing anti-recitation

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF1](../wf01_typed_answer/README.md).

**Goal:** Separate solving from recall.

## How it works

1. Add task constraints that break memorised textbook answers (forced prefix, forbidden step)
2. Check with the exact property (e.g. the 0-1 principle)

## The check

Host check: exact property checker.

- `a comparator network sorts all inputs iff it sorts all 2^n binary inputs`

## Where it comes from

Sources: F c057_*_sorting_network_findings.

Live: 70B and 8B recited the textbook network and failed every constrained case.

## Team

Pattern `solo`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when none: recitation is a finding, not a retry (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf30) · [machine-readable entry](../dag/workflow_dag.json)
