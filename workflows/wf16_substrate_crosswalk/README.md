# WF16: Substrate crosswalk

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF5](../wf05_checked_rewrite/README.md), [WF10](../wf10_local_to_global_obstruction_certificate/README.md).

**Goal:** A translation that preserves every declared relation, with alternatives recorded.

## How it works

1. Declare source and target substrates (e.g. prose, Lean, finite tables)
2. Translate generators and relations
3. Check that relations are preserved on the target
4. Record every non-unique choice

## The check

Host check: relation-preservation checker (Lean or finite tables).

- `a crosswalk F: C -> D is accepted iff F(r) holds in D for every relation r of C`
- `non-uniqueness: F and F' both preserve relations yet differ on a generator; both are recorded`

## Where it comes from

Sources: 0000145-0000169.

Twenty-five planned capsules (G01-G25), e.g. reading non-uniqueness in Lean; none dispatched.

## Team

Pattern `research_cell`: coder ×1 (sonnet); deep_researcher ×1 (run_o); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when Lean or table check fails: run_o repairs the encoding from the error (limit 2).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf16) · [machine-readable entry](../dag/workflow_dag.json)
