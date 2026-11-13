# WF39: Authority firewall gate

**Status:** proposal: no runner and no run yet. **Kind:** harness gate. **Builds on:** [WF1](../wf01_typed_answer/README.md), [WF23](../wf23_judge_packet_custody_audit/README.md).

**Goal:** No path from a fluent wrong answer to authority.

## How it works

1. A rejected or obstructed reply can only become residual evidence, never an accept
2. Accept requires every guard: replay hash, replay match, terminaliser, exhaustion, zero defect, descent witness, freshness
3. Packet gates C1-C8 keep tool halt separate from authority
4. Witness must be bound to a registered verifier and the exact payload hash

## The check

Host check: guard vector over the reply.

- `accept iff AllGuardsPass; a non-zero obstruction class cannot satisfy a truthful zero-defect guard`

## Where it comes from

Sources: P027(firewall) §2.4, §3.8, P028(finite authority) §6, §12-14, P030 §4, P004(role) §3-8.

Code, tests and Lean; no model runs.

## Team

Pattern `solo`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when none: gates never escalate (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf39) · [machine-readable entry](../dag/workflow_dag.json)
