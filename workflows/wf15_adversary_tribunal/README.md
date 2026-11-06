# WF15: Adversary tribunal

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF4](../wf04_five_agents_lggr/README.md), [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** A verdict that the finite check supports, with both sides frozen first.

## How it works

1. Prosecutor and defender submit independently; submissions are frozen
2. Neither sees the other before freezing
3. The host checks each claim on the finite model
4. Verdict comes only from the check; rhetoric is not evidence

## The check

Host check: finite model checker.

- `Kripke model M = (W, R, V); M, w |= box phi iff phi holds at every R-successor of w`
- `argument acceptance: grounded extension of the attack graph, computed by the host`
- `finite predicate example: sum(left) <= sum(right) on 1..16 bounded integers`

## Where it comes from

Sources: 0000035, 0000135-0000144.

Pilot 35 freezes role submissions and checks them separately (118 tests, 17 mutations); 135-144 are planned tribunal capsules (e.g. modal model checking).

## Team

Pattern `tribunal`: prosecutor ×1 (run_f); defender ×1 (run_o); coder ×1 (sonnet); host_checker ×1 (none).

Boost: when both submissions fail the check: one fresh run_o round per side with the checker output (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| role omitted | each of six roles in turn | named failure label per omission | code | P004(role) §3 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf15) · [machine-readable entry](../dag/workflow_dag.json)
