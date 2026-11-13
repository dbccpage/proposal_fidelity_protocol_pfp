# WF23: Judge-packet custody audit

**Status:** proposal: no runner and no run yet. **Kind:** harness gate. **Builds on:** [WF11](../wf11_dual_certificate_synthesis/README.md).

**Goal:** Show that every challenge packet is sealed and leak-free before any team runs it.

## How it works

1. Canonicalise participant and judge packets
2. Hash every file
3. Test that no expected answer is derivable from participant bytes
4. Verify the judge executes the sealed checker version

## The check

Host check: audit report.

- `leakage test: the expected answer does not appear in, and is not a declared function of, participant bytes`
- `custody: recorded SHA-256 equals the hash of the executed bytes`

## Where it comes from

Sources: judge_packet_audit.

Audit modules for canonical form, custody, execution, layout and leakage of challenge packets.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/judge_packet_audit/`](pilots/judge_packet_audit/) — pilot material

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when leak found: block the challenge until it is resealed (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| witness integrity | fabricated verifier id, unbound witness, tampered hash | all refused | code | P030 §4.2 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf23) · [machine-readable entry](../dag/workflow_dag.json)
