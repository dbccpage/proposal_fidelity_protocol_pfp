# WF47: Resumable bounded frontier search

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md).

**Goal:** Search that can stop and resume without changing the question.

## How it works

1. Deterministic lexicographic batches
2. Statuses: verified, unknown with suffix, restricted obstruction
3. Continuing requires replaying the contiguous chain from index 0

## The check

Host check: exact sign-gauge verifier.

- `the presentation key includes basis and representation, so a resumed search cannot silently change problem`

## Where it comes from

Sources: P002(signed) §4.

Offline worked trace; no benchmark.

## Team

Pattern `relay`: coder ×1 (sonnet); host_checker ×1 (none).

Boost: when none: unknown is a lawful result (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf47) · [machine-readable entry](../dag/workflow_dag.json)
